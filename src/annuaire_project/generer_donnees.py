"""Fabrique le fichier volumineux du TP 2.

Pourquoi un script plutot qu'un fichier fourni : le CSV pese environ 250 Mo. On ne distribue
pas 250 Mo, on distribue les 30 lignes qui les produisent.

Usage :  python3 generer_donnees.py [nombre_de_lignes]
Sortie : donnees/etablissements.csv  (2 000 000 de lignes par defaut, ~250 Mo, ~40 s)
"""

import csv
import random
import sys
from pathlib import Path

COLONNES = [
    "identifiant", "nom_etablissement", "type_etablissement", "statut_public_prive",
    "code_postal", "nom_commune", "code_departement", "libelle_departement",
    "libelle_region", "etat", "date_ouverture",
]

DEPARTEMENTS = [
    ("059", "Nord", "Hauts-de-France"), ("013", "Bouches-du-Rhône", "Provence-Alpes-Côte d'Azur"),
    ("062", "Pas-de-Calais", "Hauts-de-France"), ("069", "Rhône", "Auvergne-Rhône-Alpes"),
    ("075", "Paris", "Île-de-France"), ("033", "Gironde", "Nouvelle-Aquitaine"),
    ("044", "Loire-Atlantique", "Pays de la Loire"), ("026", "Drôme", "Auvergne-Rhône-Alpes"),
    ("029", "Finistère", "Bretagne"), ("031", "Haute-Garonne", "Occitanie"),
    ("034", "Hérault", "Occitanie"), ("038", "Isère", "Auvergne-Rhône-Alpes"),
    ("067", "Bas-Rhin", "Grand Est"), ("076", "Seine-Maritime", "Normandie"),
    ("092", "Hauts-de-Seine", "Île-de-France"), ("974", "La Réunion", "La Réunion"),
]
TYPES = ["Ecole", "Collège", "Lycée", "Ecole", "Ecole"]
STATUTS = ["Public"] * 8 + ["Privé"] * 2
ETATS = ["OUVERT"] * 97 + ["FERME"] * 3
COMMUNES = ["Saint-Martin", "Villeneuve", "Beaulieu", "Montereau", "La Roche",
            "Sainte-Marie", "Castelnau", "Bourg-Neuf", "Val-d'Or", "Pontlieue"]


def main() -> None:
    lignes = int(sys.argv[1]) if len(sys.argv) > 1 else 2_000_000
    sortie = Path("donnees") / "etablissements.csv"
    sortie.parent.mkdir(exist_ok=True)
    alea = random.Random(20260925)  # graine fixe : tout le monde a le meme fichier

    with sortie.open("w", newline="", encoding="utf-8") as f:
        ecrivain = csv.writer(f)
        ecrivain.writerow(COLONNES)
        for i in range(lignes):
            code, dep, region = alea.choice(DEPARTEMENTS)
            ecrivain.writerow([
                f"{i:08d}A",
                f"{alea.choice(TYPES)} {alea.choice(COMMUNES)} {i % 997}",
                alea.choice(TYPES),
                alea.choice(STATUTS),
                f"{code[-2:]}{alea.randrange(100, 999)}",
                alea.choice(COMMUNES),
                code, dep, region,
                alea.choice(ETATS),
                f"{alea.randrange(1950, 2027)}-09-01",
            ])

    mo = sortie.stat().st_size / 1_048_576
    print(f"{sortie} · {lignes:,} lignes · {mo:.0f} Mo".replace(",", " "))


if __name__ == "__main__":
    main()
