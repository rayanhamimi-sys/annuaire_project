from typing import Any

import requests
from annuaire_project.config import API_URL, MAX_RECORDS, PAGE_SIZE


def recuperer_page(offset: int) -> list[dict[str, Any]]:
    response = requests.get(
        API_URL,
        params={"limit": PAGE_SIZE, "offset": offset},
    )
    response.raise_for_status()

    data = response.json()
    return data["results"]


def recuperer_etablissements() -> list[dict[str, Any]]:
    etablissements: list[dict[str, Any]] = []

    for offset in range(0, MAX_RECORDS, PAGE_SIZE):
        etablissements.extend(recuperer_page(offset))

    return etablissements[:MAX_RECORDS]
