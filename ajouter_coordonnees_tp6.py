
"""Ajoute les coordonnées GPS des CSV TP5 dans PostgreSQL."""

import ast
import re
from pathlib import Path

import pandas as pd
import sqlalchemy as sa
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


# ============================================================
# CONFIGURATION
# ============================================================

class Reglages(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ANNUAIRE_",
        env_file=".env",
        extra="ignore"
    )

    base_url: PostgresDsn
    source: Path = Path("donnees/brut")


# ============================================================
# EXTRACTION DES COORDONNÉES
# ============================================================

def coordonnees(texte):
    """Lit une position en objet, liste ou 'latitude, longitude'."""

    if not texte or not str(texte).strip():
        return None, None

    if isinstance(texte, dict):
        return (
            texte.get("lat", texte.get("latitude")),
            texte.get("lon", texte.get("longitude"))
        )

    if isinstance(texte, (list, tuple)) and len(texte) >= 2:
        return texte[0], texte[1]

    texte = str(texte).strip()

    try:
        objet = ast.literal_eval(texte)

        if isinstance(objet, dict):
            return coordonnees(objet)

        if isinstance(objet, (list, tuple)) and len(objet) >= 2:
            return coordonnees(objet)

    except (
        ValueError,
        SyntaxError,
        TypeError,
        MemoryError,
        RecursionError
    ):
        pass

    correspondance = re.fullmatch(
        r"\s*(-?\d+(?:[.,]\d+)?)\s*[,;]\s*"
        r"(-?\d+(?:[.,]\d+)?)\s*",
        texte
    )

    return (
        correspondance.groups()
        if correspondance
        else (None, None)
    )


def convertir_nombre(valeur):
    if valeur is None or str(valeur).strip() == "":
        return None

    try:
        return float(str(valeur).replace(",", "."))

    except (ValueError, TypeError):
        return None


def point_valide(latitude, longitude):
    return (
        latitude is not None
        and longitude is not None
        and -90 <= latitude <= 90
        and -180 <= longitude <= 180
        and (latitude, longitude) != (0.0, 0.0)
    )


# ============================================================
# CHARGEMENT DES COORDONNÉES
# ============================================================

def main():

    reglages = Reglages()

    fichiers = sorted(
        reglages.source.glob("dep=*.csv")
    )

    if not fichiers:
        raise FileNotFoundError(
            f"Aucun fichier dep=*.csv dans {reglages.source}. "
            "Conserve les CSV départementaux du TP5."
        )

    moteur = sa.create_engine(
        sa.engine.make_url(str(reglages.base_url)),
        pool_pre_ping=True
    )

    rencontres = set()
    selection = []
    ignores = 0

    # On conserve la première occurrence de chaque UAI,
    # comme dans le script du TP6.

    for numero, fichier in enumerate(fichiers, 1):

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

        if "identifiant_de_l_etablissement" not in frame.columns:
            raise ValueError(
                f"Colonne UAI absente : {fichier.name}"
            )

        for ligne in frame.to_dict("records"):

            uai = str(
                ligne["identifiant_de_l_etablissement"]
            ).strip()

            if not uai or uai in rencontres:
                continue

            rencontres.add(uai)

            # Priorité au champ position, plus précis.

            latitude, longitude = coordonnees(
                ligne.get("position")
            )

            latitude = convertir_nombre(latitude)
            longitude = convertir_nombre(longitude)

            # Repli sur les colonnes latitude / longitude.

            if not point_valide(latitude, longitude):

                latitude = convertir_nombre(
                    ligne.get("latitude")
                )

                longitude = convertir_nombre(
                    ligne.get("longitude")
                )

            if point_valide(latitude, longitude):

                selection.append({
                    "uai": uai,
                    "lat": latitude,
                    "lon": longitude
                })

            else:
                ignores += 1

        print(
            f"[{numero}/{len(fichiers)}] "
            f"{fichier.name} lu"
        )

    print(f"UAI distincts lus : {len(rencontres):,}")
    print(f"Coordonnées valides : {len(selection):,}")
    print(f"Sans coordonnées valides : {ignores:,}")

    try:

        with moteur.begin() as connexion:

            # Ajouter les colonnes si elles n'existent pas.

            connexion.execute(sa.text(
                "ALTER TABLE etablissement "
                "ADD COLUMN IF NOT EXISTS latitude "
                "DOUBLE PRECISION"
            ))

            connexion.execute(sa.text(
                "ALTER TABLE etablissement "
                "ADD COLUMN IF NOT EXISTS longitude "
                "DOUBLE PRECISION"
            ))

            # Table temporaire d'import.

            connexion.execute(sa.text(
                "CREATE TEMP TABLE points_import ("
                "identifiant VARCHAR(8) PRIMARY KEY, "
                "latitude DOUBLE PRECISION, "
                "longitude DOUBLE PRECISION"
                ") ON COMMIT DROP"
            ))

            insertion = sa.text(
                "INSERT INTO points_import "
                "(identifiant, latitude, longitude) "
                "VALUES (:uai, :lat, :lon)"
            )

            for debut in range(0, len(selection), 2000):

                connexion.execute(
                    insertion,
                    selection[debut:debut + 2000]
                )

            # Modifier uniquement les coordonnées différentes.

            resultat = connexion.execute(sa.text(
                "UPDATE etablissement AS e "
                "SET latitude = p.latitude, "
                "longitude = p.longitude "
                "FROM points_import AS p "
                "WHERE e.identifiant = p.identifiant "
                "AND (e.latitude, e.longitude) "
                "IS DISTINCT FROM "
                "(p.latitude, p.longitude)"
            ))

            total = connexion.execute(sa.text(
                "SELECT COUNT(*) FROM etablissement "
                "WHERE latitude IS NOT NULL "
                "AND longitude IS NOT NULL"
            )).scalar_one()

        print(
            "Lignes géographiques ajoutées/modifiées :",
            resultat.rowcount
        )

        print(
            "Établissements géolocalisés en base :",
            total
        )

        print(
            "Terminé : les dates de chargement "
            "TP6 sont inchangées."
        )

    finally:
        moteur.dispose()


if __name__ == "__main__":
    main()
