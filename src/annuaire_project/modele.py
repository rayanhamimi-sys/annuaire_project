
from typing import Literal

from pydantic import BaseModel, field_validator
from pydantic_core import PydanticCustomError


class Etablissement(BaseModel):
    identifiant: str
    nom: str
    type_etablissement: str
    statut: Literal["Public", "Privé"]
    code_departement: str
    departement: str
    region: str
    etat: Literal["OUVERT", "FERME", "À FERMER"]

    @field_validator("code_departement", mode="before")
    @classmethod
    def normaliser_code_departement(cls, valeur: object) -> str:
        if not isinstance(valeur, str):
            raise PydanticCustomError(
                "string_type",
                "Code département invalide",)

        code = valeur.strip()

        if len(code) not in (2, 3):
            raise ValueError("Le code département doit contenir 2 ou 3 caractères")

        return code.zfill(3)

    @property
    def est_ouvert(self) -> bool:
        return self.etat == "OUVERT"