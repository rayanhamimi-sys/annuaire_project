
"""TP6 - Chargement des CSV dans PostgreSQL."""

import hashlib
import json
import logging
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import sqlalchemy as sa
from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.dialects.postgresql import insert as insert_pg


# ============================================================
# 1. CONFIGURATION
# ============================================================

class Reglages(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ANNUAIRE_",
        env_file=".env",
        extra="ignore"
    )

    base_url: PostgresDsn
    source: Path = Path("donnees/brut")
    lot: int = Field(default=2000, ge=1, le=3000)
    log_json: bool = False
    log_file: Path = Path("journaux/chargement.log")

    @property
    def url_connexion(self):
        return sa.engine.make_url(str(self.base_url))

    @property
    def url_journal(self):
        url = self.url_connexion
        return (
            f"{url.drivername}://{url.username}@"
            f"{url.host}:{url.port}/{url.database}"
        )


# ============================================================
# 2. JOURNALISATION
# ============================================================

CHAMPS_STANDARD = set(
    logging.makeLogRecord({}).__dict__
) | {"message", "asctime", "execution", "taskName"}


class FiltreExecution(logging.Filter):

    def __init__(self, execution):
        super().__init__()
        self.execution = execution

    def filter(self, record):
        record.execution = self.execution
        return True


def contexte(record):
    return {
        cle: valeur
        for cle, valeur in record.__dict__.items()
        if cle not in CHAMPS_STANDARD
        and not cle.startswith("_")
    }


class FormatTexte(logging.Formatter):

    def __init__(self):
        super().__init__(
            "%(asctime)s %(levelname)-7s "
            "[%(execution)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    def format(self, record):
        texte = super().format(record)
        extras = contexte(record)

        if extras:
            texte += " | " + json.dumps(
                extras,
                ensure_ascii=False,
                default=str
            )

        return texte


class FormatJSON(logging.Formatter):

    def format(self, record):
        charge = {
            "heure": datetime.fromtimestamp(
                record.created, timezone.utc
            ).isoformat(),
            "niveau": record.levelname,
            "execution": getattr(
                record, "execution", "-"
            ),
            "origine": record.name,
            "message": record.getMessage(),
            **contexte(record),
        }

        if record.exc_info:
            charge["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(
            charge,
            ensure_ascii=False,
            default=str
        )


def configurer_journal(reglages, execution):

    reglages.log_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    filtre = FiltreExecution(execution)

    formateur = (
        FormatJSON()
        if reglages.log_json
        else FormatTexte()
    )

    racine = logging.getLogger()

    for ancien in racine.handlers[:]:
        racine.removeHandler(ancien)
        ancien.close()

    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            reglages.log_file,
            encoding="utf-8"
        )
    ]

    for handler in handlers:
        handler.addFilter(filtre)
        handler.setFormatter(formateur)
        racine.addHandler(handler)

    racine.setLevel(logging.INFO)

    logging.getLogger(
        "sqlalchemy.engine"
    ).setLevel(logging.WARNING)

    logging.getLogger(
        "httpx"
    ).setLevel(logging.WARNING)

    return logging.getLogger("chargement_tp6")


# ============================================================
# 3. SCHEMA POSTGRESQL
# ============================================================

# Correspondance :
# colonne de la base -> colonne du CSV

CORRESPONDANCE = {
    "identifiant": "identifiant_de_l_etablissement",
    "nom": "nom_etablissement",
    "statut": "statut_public_prive",
    "type_etablissement": "type_etablissement",
    "code_departement": "code_departement",
    "departement": "libelle_departement",
    "academie": "libelle_academie",
    "region": "libelle_region",
    "commune": "nom_commune",
    "code_postal": "code_postal",
    "adresse": "adresse_1",
    "restauration": "restauration",
    "hebergement": "hebergement",
    "ulis": "ulis",
    "segpa": "segpa",
}

metadonnees = sa.MetaData()

etablissement = sa.Table(
    "etablissement",
    metadonnees,

    sa.Column(
        "identifiant",
        sa.String(8),
        primary_key=True
    ),

    sa.Column(
        "nom",
        sa.Text,
        nullable=False
    ),

    sa.Column("statut", sa.Text),
    sa.Column("type_etablissement", sa.Text),

    sa.Column(
        "code_departement",
        sa.String(3),
        index=True
    ),

    sa.Column("departement", sa.Text),
    sa.Column("academie", sa.Text),
    sa.Column("region", sa.Text),
    sa.Column("commune", sa.Text),
    sa.Column("code_postal", sa.String(10)),
    sa.Column("adresse", sa.Text),
    sa.Column("restauration", sa.Text),
    sa.Column("hebergement", sa.Text),
    sa.Column("ulis", sa.Text),
    sa.Column("segpa", sa.Text),

    sa.Column(
        "charge_le",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False
    ),

    sa.Column(
        "execution",
        sa.String(40),
        nullable=False
    ),
)

COLONNES_METIER = [
    nom
    for nom in CORRESPONDANCE
    if nom != "identifiant"
]


# ============================================================
# 4. LECTURE ET NETTOYAGE DES CSV
# ============================================================

def nettoyer(valeur):

    if valeur is None:
        return None

    valeur = str(valeur).strip()

    return valeur or None


def lire_partition(fichier, deja_vus):

    frame = pd.read_csv(
        fichier,
        sep=";",
        encoding="utf-8-sig",
        dtype=str,
        keep_default_na=False
    )

    frame.columns = (
        frame.columns.str.strip().str.lower()
    )

    requis = {
        "identifiant_de_l_etablissement",
        "nom_etablissement"
    }

    manquantes = requis - set(frame.columns)

    if manquantes:
        raise ValueError(
            f"{fichier.name} : colonnes manquantes "
            f"{sorted(manquantes)}"
        )

    lignes = []
    doublons = []
    sans_identifiant = 0

    for ligne in frame.to_dict(orient="records"):

        identifiant = nettoyer(
            ligne.get(
                "identifiant_de_l_etablissement"
            )
        )

        if not identifiant:
            sans_identifiant += 1
            continue

        if len(identifiant) != 8:
            raise ValueError(
                f"{fichier.name} : UAI invalide "
                f"{identifiant!r}"
            )

        # Première occurrence conservée.
        # Les doublons sont comptés et journalisés.

        if identifiant in deja_vus:
            doublons.append(identifiant)
            continue

        nom = nettoyer(
            ligne.get("nom_etablissement")
        )

        if not nom:
            raise ValueError(
                f"Nom manquant pour l'UAI "
                f"{identifiant}"
            )

        item = {
            cible: nettoyer(ligne.get(source))
            for cible, source in CORRESPONDANCE.items()
        }

        lignes.append(item)
        deja_vus.add(identifiant)

    return (
        lignes,
        len(frame),
        doublons,
        sans_identifiant
    )


# ============================================================
# 5. UPSERT IDEMPOTENT
# ============================================================

def ecrire_partition(
    moteur,
    lignes,
    taille_lot,
    execution
):

    ecrites = 0

    # Une transaction par département.

    with moteur.begin() as connexion:

        for debut in range(
            0,
            len(lignes),
            taille_lot
        ):

            paquet = [
                {
                    **item,
                    "execution": execution
                }
                for item in lignes[
                    debut:debut + taille_lot
                ]
            ]

            requete = insert_pg(
                etablissement
            ).values(paquet)

            nouvelles = requete.excluded

            champs_actuels = [
                etablissement.c[nom]
                for nom in COLONNES_METIER
            ]

            champs_nouveaux = [
                nouvelles[nom]
                for nom in COLONNES_METIER
            ]

            requete = requete.on_conflict_do_update(

                index_elements=[
                    etablissement.c.identifiant
                ],

                set_={
                    **{
                        nom: nouvelles[nom]
                        for nom in COLONNES_METIER
                    },
                    "charge_le": sa.func.now(),
                    "execution": execution,
                },

                where=sa.tuple_(
                    *champs_actuels
                ).is_distinct_from(
                    sa.tuple_(*champs_nouveaux)
                )

            ).returning(
                etablissement.c.identifiant
            )

            # RETURNING permet de compter
            # uniquement les écritures réelles.

            resultat = connexion.execute(
                requete
            )

            ecrites += len(
                resultat.scalars().all()
            )

    return ecrites


# ============================================================
# 6. CONTROLE ET EMPREINTE DE LA BASE
# ============================================================

def verifier_base(moteur):

    empreinte = hashlib.sha256()

    with moteur.connect() as connexion:

        total = connexion.execute(
            sa.select(
                sa.func.count()
            ).select_from(
                etablissement
            )
        ).scalar_one()

        lignes = connexion.execute(
            sa.select(
                etablissement
            ).order_by(
                etablissement.c.identifiant
            )
        )

        for ligne in lignes:

            representation = json.dumps(
                list(ligne),
                ensure_ascii=False,
                default=str,
                separators=(",", ":")
            )

            empreinte.update(
                representation.encode("utf-8")
            )

            empreinte.update(b"\n")

    return total, empreinte.hexdigest()


# ============================================================
# 7. DEMONSTRATION INJECTION SQL
# ============================================================

def demonstration_injection(moteur):

    code = "059' OR '1'='1"

    with moteur.connect() as connexion:

        # Version volontairement vulnérable :
        # uniquement pour la démonstration du TP.

        mauvaise = sa.text(
            "SELECT count(*) FROM etablissement "
            f"WHERE code_departement = '{code}'"
        )

        # Version sécurisée, avec paramètre.

        bonne = sa.text(
            "SELECT count(*) FROM etablissement "
            "WHERE code_departement = :code"
        )

        fragile = connexion.execute(
            mauvaise
        ).scalar_one()

        protege = connexion.execute(
            bonne,
            {"code": code}
        ).scalar_one()

    return fragile, protege


# ============================================================
# 8. PROGRAMME PRINCIPAL
# ============================================================

def main():

    reglages = Reglages()

    execution = (
        time.strftime("%Y%m%dT%H%M%S")
        + "-"
        + uuid.uuid4().hex[:6]
    )

    journal = configurer_journal(
        reglages,
        execution
    )

    debut = time.monotonic()

    journal.info(
        "démarrage",
        extra={
            "source": str(reglages.source),
            "lot": reglages.lot,
            "base": reglages.url_journal,
        }
    )

    fichiers = sorted(
        reglages.source.glob("dep=*.csv")
    )

    if not fichiers:
        raise FileNotFoundError(
            "Aucun fichier dep=*.csv trouvé "
            "dans donnees/brut. "
            "Lance d'abord l'ingestion TP5."
        )

    moteur = sa.create_engine(
        reglages.url_connexion,
        pool_pre_ping=True
    )

    deja_vus = set()

    somme_lues = 0
    somme_retenues = 0
    somme_ecrites = 0
    somme_doublons = 0
    somme_sans_uai = 0

    try:

        metadonnees.create_all(moteur)

        for numero, fichier in enumerate(
            fichiers,
            start=1
        ):

            top = time.monotonic()

            (
                lignes,
                lues,
                doublons,
                sans_uai
            ) = lire_partition(
                fichier,
                deja_vus
            )

            ecrites = ecrire_partition(
                moteur,
                lignes,
                reglages.lot,
                execution
            )

            somme_lues += lues
            somme_retenues += len(lignes)
            somme_ecrites += ecrites
            somme_doublons += len(doublons)
            somme_sans_uai += sans_uai

            journal.info(
                "partition chargée",
                extra={
                    "fichier": fichier.name,
                    "numero": numero,
                    "partitions": len(fichiers),
                    "lues": lues,
                    "retenues": len(lignes),
                    "ecrites": ecrites,
                    "duree_ms": round(
                        (
                            time.monotonic() - top
                        ) * 1000
                    ),
                }
            )

            if doublons or sans_uai:

                journal.warning(
                    "lignes écartées",
                    extra={
                        "fichier": fichier.name,
                        "doublons_uai": len(doublons),
                        "uai_ecartes": doublons,
                        "sans_uai": sans_uai,
                        "politique": (
                            "première occurrence conservée"
                        ),
                    }
                )

        if somme_lues != (
            somme_retenues
            + somme_doublons
            + somme_sans_uai
        ):
            raise RuntimeError(
                "Bilan incohérent des lignes sources"
            )

        total, empreinte = verifier_base(
            moteur
        )

        fragile, protege = (
            demonstration_injection(moteur)
        )

        journal.info(
            "chargement terminé",
            extra={
                "partitions": len(fichiers),
                "lues": somme_lues,
                "retenues": somme_retenues,
                "ecrites": somme_ecrites,
                "doublons_ecartes": somme_doublons,
                "sans_uai_ecartes": somme_sans_uai,
                "lignes_en_base": total,
                "empreinte_sha256": empreinte,
                "duree_ms": round(
                    (
                        time.monotonic() - debut
                    ) * 1000
                ),
            }
        )

        journal.info(
            "comparaison injection SQL",
            extra={
                "code_test": "059' OR '1'='1",
                "requete_f_string": fragile,
                "requete_parametree": protege,
            }
        )

    except Exception:

        journal.exception(
            "échec du chargement"
        )

        raise

    finally:
        moteur.dispose()


if __name__ == "__main__":
    main()
