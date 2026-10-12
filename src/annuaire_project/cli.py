
import argparse
from pathlib import Path

from .analysee import analyser
from .lecture import Lecteur, LecteurApi, LecteurCsv, LecteurParquet


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyser les établissements scolaires"
    )

    parser.add_argument(
        "--source",
        choices=["csv", "parquet", "api"],
        required=True,
        help="Source des données à analyser",
    )

    args = parser.parse_args()

    # Choisir le lecteur selon la source
    lecteur: Lecteur

    if args.source == "csv":
        lecteur = LecteurCsv(
            Path("donnees/etablissements.csv")
        )

    elif args.source == "parquet":
        lecteur = LecteurParquet(
            Path("donnees/etablissements.parquet")
        )

    else:
        lecteur = LecteurApi()

    # Même analyse, quelle que soit la source
    bilan = analyser(lecteur)

    print("Ouverts :", sum(bilan.ouverts.values()))
    print("Rejetés :", bilan.rejetes)
    print("Motifs :", sorted(bilan.motifs.items()))
    print(
        "Par département :",
        sorted(bilan.ouverts.items()),
    )


if __name__ == "__main__":
    main()
