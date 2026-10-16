
import csv
from collections.abc import Iterator
from pathlib import Path
from typing import cast


def lire_en_flux(chemin: Path) -> Iterator[dict[str, str]]:
    try:
        with chemin.open(newline="", encoding="utf-8") as fichier:
            lecteur = csv.DictReader(fichier)

            for ligne in lecteur:
                yield cast(dict[str, str], ligne)

    except FileNotFoundError:
        return
