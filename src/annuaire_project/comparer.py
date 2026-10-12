"""Compare trois facons de compter les etablissements ouverts par departement.

C'est le coeur du TP 2 : la meme reponse, trois empreintes memoire.
"""

import csv
import time
import tracemalloc
from collections import Counter
from collections.abc import Iterator
from pathlib import Path

FICHIER = Path("donnees") / "etablissements.csv"


# --- 1. Tout charger en memoire avec pandas -------------------------------

def par_pandas() -> Counter:
    import pandas as pd
    tableau = pd.read_csv(FICHIER)
    ouverts = tableau[tableau["etat"] == "OUVERT"]
    return Counter(ouverts["libelle_departement"])


# --- 2. Tout charger en memoire, sans pandas ------------------------------

def par_liste() -> Counter:
    with FICHIER.open(encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))          # tout le fichier en RAM
    return Counter(l["libelle_departement"] for l in lignes if l["etat"] == "OUVERT")


# --- 3. En flux, par generateur -------------------------------------------

def lire_en_flux(chemin: Path) -> Iterator[dict[str, str]]:
    """Produit les lignes une a une : rien ne s'accumule."""
    with chemin.open(encoding="utf-8") as f:
        yield from csv.DictReader(f)


def par_generateur() -> Counter:
    ouverts = (l for l in lire_en_flux(FICHIER) if l["etat"] == "OUVERT")
    return Counter(l["libelle_departement"] for l in ouverts)


# --- Mesure ----------------------------------------------------------------

def mesurer(nom, fonction):
    tracemalloc.start()
    debut = time.perf_counter()
    resultat = fonction()
    duree = time.perf_counter() - debut
    _, pic = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"  {nom:24s} {duree:6.1f} s   pic mémoire {pic/1_048_576:8.1f} Mo")
    return resultat


if __name__ == "__main__":
    print(f"Fichier : {FICHIER.stat().st_size/1_048_576:.0f} Mo\n")
    a = mesurer("pandas (tout en RAM)", par_pandas)
    b = mesurer("liste (tout en RAM)", par_liste)
    c = mesurer("générateur (en flux)", par_generateur)
    print(f"\nMêmes résultats : {a == b == c}")
    print("Top 3 :", c.most_common(3))
