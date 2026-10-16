"""Fabrique les deux fichiers locaux du TP 3 : un CSV et un Parquet.

Les trois lecteurs que vous allez ecrire doivent produire le MEME resultat. Il faut donc que
les trois sources contiennent les memes donnees : on telecharge une fois, on ecrit deux
formats.

Ce script est volontairement autonome — il ne depend pas de votre paquet, vous pouvez le
lancer avant d'avoir ecrit la moindre ligne du TP.

Usage :  python3 preparer_donnees.py
Sortie : donnees/etablissements.csv  et  donnees/etablissements.parquet
"""

from pathlib import Path

import pandas as pd
import requests

URL = (
    "https://data.education.gouv.fr/api/explore/v2.1"
    "/catalog/datasets/fr-en-annuaire-education/records"
)
TAILLE_PAGE = 100
MAXIMUM = 3_000
# Sans tri, la pagination n'est pas deterministe : deux appels ne renvoient pas les memes
# enregistrements, et vos trois sources ne concorderaient jamais.
TRI = "identifiant_de_l_etablissement"

COLONNES = [
    "identifiant_de_l_etablissement", "nom_etablissement", "type_etablissement",
    "statut_public_prive", "code_postal", "nom_commune", "code_departement",
    "libelle_departement", "libelle_region", "etat", "date_ouverture",
]


def main() -> None:
    enregistrements = []
    for offset in range(0, MAXIMUM, TAILLE_PAGE):
        reponse = requests.get(
            URL,
            params={"limit": TAILLE_PAGE, "offset": offset, "order_by": TRI},
            timeout=30,
        )
        reponse.raise_for_status()
        enregistrements.extend(reponse.json()["results"])

    dossier = Path("donnees")
    dossier.mkdir(exist_ok=True)
    tableau = pd.DataFrame(enregistrements)[COLONNES]
    tableau.to_csv(dossier / "etablissements.csv", index=False)
    tableau.to_parquet(dossier / "etablissements.parquet", index=False)

    for nom in ("etablissements.csv", "etablissements.parquet"):
        chemin = dossier / nom
        print(f"{chemin} · {len(tableau)} lignes · {chemin.stat().st_size / 1024:.0f} Ko")


if __name__ == "__main__":
    main()
