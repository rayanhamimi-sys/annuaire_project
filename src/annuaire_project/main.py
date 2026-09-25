from annuaire_project.analyse import (
    calculer_repartition_public_prive,
    compter_ouvertures_par_annee,
    obtenir_top_departements,
)
from annuaire_project.ingestion import recuperer_etablissements
from annuaire_project.nettoyage import creer_dataframe, nettoyer_etablissements


def main() -> None:
    etablissements = recuperer_etablissements()

    df = creer_dataframe(etablissements)
    df = nettoyer_etablissements(df)

    print("Top 10 des départements :")
    print(obtenir_top_departements(df))

    public, prive, pourcentage_public = calculer_repartition_public_prive(df)

    print("\nRépartition public / privé :")
    print(f"Public : {public}")
    print(f"Privé : {prive}")
    print(f"Pourcentage public : {pourcentage_public:.2f} %")

    print("\nOuvertures par année :")
    print(compter_ouvertures_par_annee(df))


if __name__ == "__main__":
    main()
