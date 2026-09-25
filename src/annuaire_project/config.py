API_URL = (
    "https://data.education.gouv.fr/api/explore/v2.1/"
    "catalog/datasets/fr-en-annuaire-education/records"
)

PAGE_SIZE = 100
MAX_RECORDS = 3000

COLUMNS = [
    "identifiant_de_l_etablissement",
    "nom_etablissement",
    "type_etablissement",
    "statut_public_prive",
    "code_postal",
    "nom_commune",
    "code_departement",
    "libelle_departement",
    "libelle_region",
    "etat",
    "date_ouverture",
]

DEPARTMENT_COLUMN = "libelle_departement"
STATUS_COLUMN = "etat"
OPEN_STATUS = "OUVERT"
PUBLIC_PRIVATE_COLUMN = "statut_public_prive"
PUBLIC_STATUS = "Public"
OPENING_DATE_COLUMN = "date_ouverture"
YEAR_COLUMN = "annee"

TOP_DEPARTMENTS = 10
