import shutil
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
DONNEES = RACINE / "donnees"
CSV = DONNEES / "etablissements.csv"


def taille_mio(chemin):
    if chemin.is_file():
        octets = chemin.stat().st_size
    else:
        octets = sum(
            fichier.stat().st_size
            for fichier in chemin.rglob("*.parquet")
        )

    return octets / (1024 * 1024)


def main():
    if not CSV.exists():
        raise FileNotFoundError("Le fichier CSV est introuvable.")

    # Lecture du fichier CSV
    df = pd.read_csv(
        CSV,
        dtype={
            "identifiant": "string",
            "code_postal": "string",
            "code_departement": "string",
        },
    )

    print(f"Nombre de lignes : {len(df)}")

    # Chemins des fichiers Parquet
    sans = DONNEES / "etablissements_sans_compression.parquet"
    snappy = DONNEES / "etablissements_snappy.parquet"
    zstd = DONNEES / "etablissements_zstd.parquet"
    partitionne = DONNEES / "etablissements_zstd_partitionne"

    # 1. Parquet sans compression
    df.to_parquet(
        sans,
        compression=None,
        index=False,
        engine="pyarrow",
    )

    # 2. Parquet avec Snappy
    df.to_parquet(
        snappy,
        compression="snappy",
        index=False,
        engine="pyarrow",
    )

    # 3. Parquet avec ZSTD
    df.to_parquet(
        zstd,
        compression="zstd",
        index=False,
        engine="pyarrow",
    )

    # 4. Parquet ZSTD partitionné par département
    if partitionne.exists():
        shutil.rmtree(partitionne)

    df.to_parquet(
        partitionne,
        compression="zstd",
        partition_cols=["code_departement"],
        index=False,
        engine="pyarrow",
    )

    # Affichage des tailles
    print("\nComparaison des tailles :")

    fichiers = [
        ("CSV", CSV),
        ("Parquet sans compression", sans),
        ("Parquet Snappy", snappy),
        ("Parquet ZSTD", zstd),
        ("Parquet ZSTD partitionné", partitionne),
    ]

    for nom, chemin in fichiers:
        print(f"{nom} : {taille_mio(chemin):.2f} MiB")


if __name__ == "__main__":
    main()