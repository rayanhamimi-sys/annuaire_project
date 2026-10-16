# 🛠️ TP 3 — Trois sources, une seule logique métier

**Séance 3 · 70 minutes · en binôme**

> Vous travaillez dans le dépôt `annuaire`. Ce TP en réorganise le cœur.

## Le problème

Votre pipeline sait lire l'API. Demain on vous demandera de lire un export CSV, après-demain
un Parquet déposé sur un bucket. Aujourd'hui, changer de source voudrait dire réécrire
l'analyse.

À la fin de ce TP, **changer de source sera un argument en ligne de commande**, et pas une
ligne de la logique métier n'aura bougé.

## Étape 0 — Préparer les données · 5 min

```bash
python3 preparer_donnees.py
```

Produit `donnees/etablissements.csv` et `donnees/etablissements.parquet` — les mêmes 3 000
établissements dans deux formats. Ajoutez `donnees/` à votre `.gitignore`.

> Remarquez le `order_by` dans le script. Sans tri, deux appels à l'API ne renvoient pas les
> mêmes enregistrements, et vos trois sources ne concorderaient jamais.

## Étape 1 — L'entité, et sa validation · 20 min

Créez `modele.py`. Écrivez un modèle **Pydantic** `Etablissement` avec au minimum :
`identifiant`, `nom`, `type_etablissement`, `statut`, `code_departement`, `departement`,
`region`, `etat`.

Trois exigences :

1. **`statut` et `etat` sont des `Literal`.** `statut` ne peut valoir que `"Public"` ou
   `"Privé"` ; `etat` que `"OUVERT"`, `"FERME"` ou `"À FERMER"`. Rien d'autre n'entre.
2. **`code_departement` est normalisé sur trois caractères.** L'API mélange `"26"` et `"026"`.
   Tranchez à l'entrée avec un `field_validator`, une bonne fois.
3. **Une propriété `est_ouvert`.** La logique métier ne doit pas comparer des chaînes.

> **Pourquoi un modèle plutôt qu'un `dict` ?** Un `dict` accepte tout. Une faute de frappe sur
> une clé ne se voit qu'à la lecture, parfois des semaines plus tard. Un modèle refuse la
> donnée à l'entrée, là où on sait encore d'où elle vient.

## Étape 2 — Le contrat · 15 min

Créez `lecture.py`. Déclarez un **`Protocol`** :

```python
class Lecteur(Protocol):
    def lire(self) -> Iterator[dict[str, Any]]: ...
```

Puis trois classes qui le satisfont : `LecteurCsv`, `LecteurParquet`, `LecteurApi`.

**Aucune des trois n'hérite de `Lecteur`.** C'est le principe du typage structurel : si une
classe sait faire `lire()`, c'est un lecteur. `mypy` le vérifiera sans qu'aucun héritage ne
soit déclaré.

> ⚠️ **Le piège du CSV.** Un CSV ne sait pas représenter l'absence : une valeur manquante s'y
> écrit comme une chaîne vide, indiscernable d'une vraie chaîne vide. Si vous ne rétablissez
> pas le `None` dans `LecteurCsv`, cette source ne donnera **pas** le même résultat que les
> deux autres. Et vous ne le verrez pas.

## Étape 3 — La logique métier, enfin ignorante · 20 min

Dans `analyse.py`, réécrivez vos fonctions pour qu'elles prennent un `Lecteur` en paramètre :

```python
def ouverts_par_departement(lecteur: Lecteur) -> Counter[str]:
    ...
```

**Aucun `import` de `LecteurCsv` dans `analyse.py`.** Si vous en avez besoin, c'est que
l'abstraction a fui. La logique reçoit un lecteur ; elle ne va pas le chercher.

Écartez les enregistrements invalides — mais **comptez-les**. Un pipeline qui jette des lignes
en silence est un pipeline qui ment.

## Étape 4 — La preuve · 10 min

Dans `cli.py`, ajoutez `--source {csv,parquet,api}`. C'est le **seul** endroit du programme
qui choisit une source.

```bash
python3 -m annuaire.cli --source csv
python3 -m annuaire.cli --source parquet
python3 -m annuaire.cli --source api
```

**Les trois doivent afficher exactement le même résultat.** Si ce n'est pas le cas, relisez
l'avertissement de l'étape 2.

Committez.

---

## Ce qui sera regardé

| Critère | Ce qu'on vérifie |
|---|---|
| Le contrat est un `Protocol` | Aucune des trois classes n'hérite de `Lecteur` |
| La logique est ignorante | `analyse.py` n'importe aucune classe de lecteur concrète |
| La validation est stricte | `Literal` sur `statut` et `etat`, code département normalisé |
| Les rejets sont comptés | Le nombre d'écartés s'affiche, avec le motif |
| Les trois sources concordent | Même sortie pour `--source csv`, `parquet` et `api` |
| Le code reste propre | `ruff` et `mypy src/` silencieux |

## Si vous avez fini en avance

1. **Écrivez un test sans fichier ni réseau.** Créez une classe `LecteurFactice` qui renvoie
   trois dictionnaires en dur, et testez `ouverts_par_departement` avec. Quinze lignes.
   C'est le vrai bénéfice du `Protocol`, et vous venez de le gagner.
2. **Ajoutez une quatrième source** — un JSON, ou une liste en mémoire. Combien de lignes
   faut-il toucher hors du nouveau lecteur ? Si la réponse n'est pas « une, dans `cli.py` »,
   l'abstraction n'est pas étanche.
3. **Comparez `dataclass` et Pydantic.** Réécrivez `Etablissement` en `dataclass` simple :
   qu'est-ce que vous perdez, et qu'est-ce que vous gagnez ?

## En cas de blocage

| Symptôme | Cause probable | Réponse |
|---|---|---|
| `mypy` refuse `LecteurCsv` comme `Lecteur` | La signature de `lire()` diffère | Les types doivent correspondre exactement, annotation de retour comprise |
| Le CSV donne un résultat différent | Les `""` ne sont pas retraduits en `None` | Voir l'avertissement de l'étape 2 |
| L'API donne un résultat différent à chaque appel | Pagination sans tri | Vérifiez le `order_by` |
| `ValidationError` sur tout | Les noms de champs de l'API ne sont pas ceux du modèle | Faites une table de correspondance explicite |
| Tentation de mettre `if source == "csv"` dans `analyse.py` | L'abstraction a fui | Ce test n'a sa place que dans `cli.py` |
