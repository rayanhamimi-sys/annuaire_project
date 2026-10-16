import argparse
import json
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
RESULTATS = RACINE / "resultats"

METHODES = [
    ("naif", "Pandas naïf"),
    ("apply", "Pandas apply"),
    ("optimise", "Pandas optimisé"),
    ("polars", "Polars différé"),
]


def main():
    parseur = argparse.ArgumentParser()

    parseur.add_argument(
        "--limite",
        type=int,
        default=None,
    )

    args = parseur.parse_args()

    etiquette = (
        "complet" if args.limite is None else str(args.limite)
    )

    mesures = []

    # Récupération des quatre résultats
    for methode, nom in METHODES:
        fichier = RESULTATS / f"{methode}_{etiquette}.json"

        if not fichier.exists():
            raise FileNotFoundError(
                f"Mesure manquante : {fichier.name}"
            )

        donnees = json.loads(
            fichier.read_text(encoding="utf-8")
        )

        mesures.append((nom, donnees))

    # Vérification des résultats
    reference = mesures[0][1]["par_departement"]

    identiques = all(
        donnees["par_departement"] == reference
        for _, donnees in mesures
    )

    print("\n===== VÉRIFICATION =====")

    if identiques:
        print("Les quatre méthodes donnent le même résultat.")
    else:
        print("ATTENTION : les résultats sont différents.")
        return

    print(f"Total établissements ouverts : {sum(reference.values())}")

    # Affichage du tableau
    print("\n===== TABLEAU DE COMPARAISON =====\n")

    print("| Approche | Durée | Pic mémoire |")
    print("|---|---:|---:|")

    for nom, donnees in mesures:
        duree = donnees["duree_secondes"]
        memoire = donnees["pic_memoire_mio"]

        print(
            f"| {nom} | {duree:.4f} s | {memoire:.2f} MiB |"
        )

    # Calcul du gain de performance
    temps_naif = mesures[0][1]["duree_secondes"]
    temps_polars = mesures[3][1]["duree_secondes"]

    if temps_polars > 0:
        gain = temps_naif / temps_polars

        print(f"\nPolars est {gain:.1f} fois plus rapide que Pandas naïf.")


if __name__ == "__main__":
    main()