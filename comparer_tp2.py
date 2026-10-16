
import csv
import tracemalloc
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from time import perf_counter
from typing import cast

from .lecture_flux import lire_en_flux

CHEMIN = Path("donnees/etablissements.csv")


# Méthode 1 : tout charger en mémoire
def compter_naif(chemin: Path) -> Counter[str]:
    try:
        with chemin.open(newline="", encoding="utf-8") as fichier:
            lignes = list(csv.DictReader(fichier))
    except FileNotFoundError:
        return Counter()

    return Counter(
        cast(str, ligne["code_departement"])
        for ligne in lignes
        if ligne["etat"] == "OUVERT"
    )


# Méthode 2 : lecture en flux
def compter_flux(chemin: Path) -> Counter[str]:
    return Counter(
        ligne["code_departement"]
        for ligne in lire_en_flux(chemin)
        if ligne["etat"] == "OUVERT"
    )


# Mesurer le temps et la mémoire
def mesurer(
    nom: str,
    fonction: Callable[[Path], Counter[str]],
) -> Counter[str]:
    tracemalloc.start()

    debut = perf_counter()
    resultat = fonction(CHEMIN)
    duree = perf_counter() - debut

    _, pic = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(
        f"{nom} : {duree:.2f} secondes | "
        f"{pic / 1_048_576:.1f} Mo"
    )

    return resultat


def main() -> None:
    if not CHEMIN.is_file():
        print("Fichier absent : lance python generer_donnees.py")
        return

    naif = mesurer("Tout en mémoire", compter_naif)
    flux = mesurer("Lecture en flux", compter_flux)

    assert naif == flux, "Les résultats sont différents"

    print("Les deux méthodes donnent les mêmes résultats.")
    print("Total établissements ouverts :", sum(flux.values()))
    print("Résultats par département :", sorted(flux.items()))


if __name__ == "__main__":
    main()
