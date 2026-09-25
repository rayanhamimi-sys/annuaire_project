import pandas as pd
from annuaire_project.config import (
    DEPARTMENT_COLUMN,
    OPENING_DATE_COLUMN,
    PUBLIC_PRIVATE_COLUMN,
    PUBLIC_STATUS,
    TOP_DEPARTMENTS,
    YEAR_COLUMN,
)


def compter_par_departement(df: pd.DataFrame) -> pd.Series:
    return df[DEPARTMENT_COLUMN].value_counts()


def obtenir_top_departements(df: pd.DataFrame) -> pd.Series:
    return compter_par_departement(df).head(TOP_DEPARTMENTS)


def calculer_repartition_public_prive(
    df: pd.DataFrame,
) -> tuple[int, int, float]:
    public = int((df[PUBLIC_PRIVATE_COLUMN] == PUBLIC_STATUS).sum())
    prive = len(df) - public

    pourcentage_public = public / (public + prive) * 100

    return public, prive, pourcentage_public


def compter_ouvertures_par_annee(df: pd.DataFrame) -> pd.Series:
    df = df.copy()
    df[YEAR_COLUMN] = df[OPENING_DATE_COLUMN].str[:4]

    return df.groupby(YEAR_COLUMN).size()
