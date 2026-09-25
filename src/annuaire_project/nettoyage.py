from typing import Any

import pandas as pd
from annuaire_project.config import (
    COLUMNS,
    DEPARTMENT_COLUMN,
    OPEN_STATUS,
    STATUS_COLUMN,
)


def creer_dataframe(
    etablissements: list[dict[str, Any]],
) -> pd.DataFrame:
    return pd.DataFrame(etablissements)


def selectionner_colonnes(df: pd.DataFrame) -> pd.DataFrame:
    return df[COLUMNS].copy()


def supprimer_sans_departement(df: pd.DataFrame) -> pd.DataFrame:
    return df[df[DEPARTMENT_COLUMN].notna()].copy()


def garder_etablissements_ouverts(df: pd.DataFrame) -> pd.DataFrame:
    return df[df[STATUS_COLUMN] == OPEN_STATUS].copy()


def nettoyer_etablissements(df: pd.DataFrame) -> pd.DataFrame:
    df = selectionner_colonnes(df)
    df = supprimer_sans_departement(df)
    df = garder_etablissements_ouverts(df)

    return df
