
from collections import Counter
from dataclasses import dataclass, field

from pydantic import ValidationError

from .lecture import Lecteur
from .modele import Etablissement

# Correspondance entre les colonnes sources et notre modèle
COLONNES = {
    "identifiant": "identifiant_de_l_etablissement",
    "nom": "nom_etablissement",
    "type_etablissement": "type_etablissement",
    "statut": "statut_public_prive",
    "code_departement": "code_departement",
    "departement": "libelle_departement",
    "region": "libelle_region",
    "etat": "etat",
}


# Stockage des résultats de l'analyse
@dataclass
class BilanAnalyse:
    ouverts: Counter[str] = field(default_factory=Counter)
    rejetes: int = 0
    motifs: Counter[str] = field(default_factory=Counter)


# Analyse des établissements
def analyser(lecteur: Lecteur) -> BilanAnalyse:
    bilan = BilanAnalyse()

    for ligne in lecteur.lire():
        donnees = {
            champ: ligne.get(colonne)
            for champ, colonne in COLONNES.items()
        }

        try:
            etablissement = Etablissement.model_validate(donnees)

        except ValidationError as erreur:
            bilan.rejetes += 1

            for detail in erreur.errors():
                champ = ".".join(str(x) for x in detail["loc"])
                motif = f"{champ} : {detail['type']}"
                bilan.motifs[motif] += 1

            continue

        if etablissement.est_ouvert:
            bilan.ouverts[etablissement.code_departement] += 1

    return bilan


# Fonction principale demandée par le TP
def ouverts_par_departement(lecteur: Lecteur) -> Counter[str]:
    return analyser(lecteur).ouverts
