import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd
import polars as pl

RACINE = Path(__file__).resolve().parent.parent
DONNEES = RACINE / "donnees"
RESULTATS = RACINE / "resultats"

CSV = DONNEES / "etablissements.csv"
PARQUET = DONNEES / "etablissements_zstd.parquet"


# MÉTHODE 1 : PANDAS NAÏF
def methode_naive(limite):
    df = pd.read_csv(CSV, nrows=limite)

    comptes = {}

    for i in range(len(df)):
        ligne = df.iloc[i]

        if ligne["etat"] == "OUVERT":
            dep = str(ligne["libelle_departement"])

            comptes[dep] = comptes.get(dep, 0) + 1

    return comptes


# MÉTHODE 2 : PANDAS APPLY
def methode_apply(limite):
    df = pd.read_csv(CSV, nrows=limite)

    departements_ouverts = df.apply(
        lambda ligne: ligne["libelle_departement"]
        if ligne["etat"] == "OUVERT"
        else None,
        axis=1,
    )

    nombres = departements_ouverts.value_counts()

    return {
        str(dep): int(nombre)
        for dep, nombre in nombres.items()
    }


# MÉTHODE 3 : PANDAS OPTIMISÉ
def methode_optimisee(limite):
    df = pd.read_csv(
        CSV,
        usecols=["etat", "libelle_departement"],
        dtype={
            "etat": "category",
            "libelle_departement": "category",
        },
        nrows=limite,
    )

    # Filtrage vectorisé
    masque = df["etat"] == "OUVERT"

    # Comptage par département
    nombres = df.loc[
        masque, "libelle_departement"
    ].value_counts(sort=False)

    return {
        str(dep): int(nombre)
        for dep, nombre in nombres.items()
        if nombre > 0
    }


# MÉTHODE 4 : POLARS EN DIFFÉRÉ
def methode_polars(limite):
    requete = pl.scan_parquet(PARQUET)

    if limite is not None:
        requete = requete.head(limite)

    resultat = (
        requete
        .filter(pl.col("etat") == "OUVERT")
        .group_by("libelle_departement")
        .agg(pl.len().alias("nombre"))
        .collect()
    )

    return {
        str(dep): int(nombre)
        for dep, nombre in resultat.iter_rows()
    }


# MESURE DE LA MÉMOIRE
def pic_memoire_mio():
    if sys.platform == "win32":
        import psutil

        processus = psutil.Process()
        memoire = processus.memory_info().peak_wset

        return memoire / (1024 * 1024)

    import resource

    memoire = resource.getrusage(
        resource.RUSAGE_SELF
    ).ru_maxrss

    if sys.platform == "darwin":
        return memoire / (1024 * 1024)

    return memoire / 1024


# EXÉCUTION DU BENCHMARK
def main():
    parseur = argparse.ArgumentParser()

    parseur.add_argument(
        "methode",
        choices=["naif", "apply", "optimise", "polars"],
    )

    parseur.add_argument(
        "--limite",
        type=int,
        default=None,
    )

    args = parseur.parse_args()

    if args.limite is not None and args.limite < 1:
        parseur.error("La limite doit être supérieure à zéro.")

    methodes = {
        "naif": methode_naive,
        "apply": methode_apply,
        "optimise": methode_optimisee,
        "polars": methode_polars,
    }

    # Vérification du fichier
    fichier = PARQUET if args.methode == "polars" else CSV

    if not fichier.exists():
        raise FileNotFoundError(f"Fichier absent : {fichier}")

    # Mesure du temps
    debut = time.perf_counter()

    comptes = methodes[args.methode](args.limite)

    duree = time.perf_counter() - debut

    # Mesure de la mémoire
    memoire = pic_memoire_mio()

    # Résultats
    total = sum(comptes.values())

    RESULTATS.mkdir(parents=True, exist_ok=True)

    etiquette = (
        "complet" if args.limite is None else str(args.limite)
    )

    sortie = RESULTATS / f"{args.methode}_{etiquette}.json"

    donnees = {
        "methode": args.methode,
        "limite": args.limite,
        "duree_secondes": round(duree, 4),
        "pic_memoire_mio": round(memoire, 2),
        "total_ouverts": total,
        "par_departement": dict(sorted(comptes.items())),
    }

    sortie.write_text(
        json.dumps(donnees, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n===== RÉSULTATS =====")
    print(f"Méthode : {args.methode}")
    print(f"Établissements ouverts : {total}")
    print(f"Départements : {len(comptes)}")
    print(f"Durée : {duree:.4f} secondes")
    print(f"Pic mémoire : {memoire:.2f} MiB")
    print(f"Résultat enregistré : {sortie}")


if __name__ == "__main__":
    main()