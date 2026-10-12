
import csv
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Protocol

import pyarrow.parquet as pq  # type: ignore[import-untyped]
import requests


# Contrat commun des lecteurs
class Lecteur(Protocol):
    def lire(self) -> Iterator[dict[str, Any]]:
        ...


# Lecteur 1 : fichier CSV
class LecteurCsv:
    def __init__(self, chemin: Path) -> None:
        self.chemin = chemin

    def lire(self) -> Iterator[dict[str, Any]]:
        with self.chemin.open(
            newline="", encoding="utf-8"
        ) as fichier:
            lecteur = csv.DictReader(fichier)

            for ligne in lecteur:
                yield {
                    cle: None if valeur in ("", None) else valeur
                    for cle, valeur in ligne.items()
                    if cle is not None
                }


# Lecteur 2 : fichier Parquet
class LecteurParquet:
    def __init__(self, chemin: Path) -> None:
        self.chemin = chemin

    def lire(self) -> Iterator[dict[str, Any]]:
        tableau = pq.read_table(self.chemin)

        yield from tableau.to_pylist()


# Lecteur 3 : API
class LecteurApi:
    URL = (
        "https://data.education.gouv.fr/api/explore/v2.1"
        "/catalog/datasets/fr-en-annuaire-education/records"
    )

    def lire(self) -> Iterator[dict[str, Any]]:
        for offset in range(0, 3000, 100):
            reponse = requests.get(
                self.URL, params={
                        "limit": "100",
                        "offset": str(offset),
                        "order_by": "identifiant_de_l_etablissement",
                            },
                        timeout=30,
                )

            reponse.raise_for_status()
            resultats: list[dict[str, Any]] = (
                reponse.json()["results"]
            )

            yield from resultats
