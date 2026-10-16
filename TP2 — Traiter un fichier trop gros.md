# 🛠️ TP 2 — Traiter un fichier trop gros pour la mémoire

**Séance 2 · 65 minutes · même binôme que le projet**

> Vous travaillez dans le dépôt `annuaire` créé au TP 1. Ce TP y ajoute un module.

## Le problème

Votre pipeline lit aujourd'hui 3 000 établissements. En production, il en lira des millions.
La méthode du TP 1 — tout charger, puis filtrer — ne passera pas l'échelle.

Vous allez le constater par la mesure, puis le corriger.

## Étape 1 — Fabriquer le fichier · 5 min

```bash
python3 generer_donnees.py
```

Deux millions de lignes, environ **212 Mo**, une dizaine de secondes. Le fichier atterrit dans
`donnees/etablissements.csv`.

> Ajoutez `donnees/` à votre `.gitignore`. **On ne versionne pas 212 Mo.**

## Étape 2 — La version naïve, et sa mesure · 15 min

Écrivez la fonction qui compte les établissements **ouverts par département**, en chargeant
tout le fichier — au choix avec `pandas.read_csv` ou avec `list(csv.DictReader(f))`.

Mesurez son pic mémoire :

```python
import tracemalloc

tracemalloc.start()
resultat = votre_fonction()
_, pic = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"pic mémoire : {pic / 1_048_576:.0f} Mo")
```

Notez le chiffre. Il va servir de point de comparaison.

## Étape 3 — La version en flux · 25 min

Écrivez un **générateur** qui produit les lignes une à une, sans jamais construire la liste
complète :

```python
from collections.abc import Iterator
from pathlib import Path

def lire_en_flux(chemin: Path) -> Iterator[dict[str, str]]:
    ...
```

Puis recomposez le comptage **sans accumuler** : enchaînez une expression génératrice pour le
filtre, et laissez `collections.Counter` faire l'agrégation.

Trois règles pour ce TP :

1. **Aucune liste intermédiaire.** Si vous écrivez `[...]`, demandez-vous si `(...)` suffirait.
2. **Le fichier se ferme tout seul.** Utilisez `with` — c'est le sujet du cours C.
3. **Le fichier peut ne pas exister.** Attrapez `FileNotFoundError` et renvoyez un résultat vide
   plutôt que de laisser remonter la trace.

## Étape 4 — Comparer · 10 min

Mesurez la version en flux avec le même instrument. Remplissez :

| Approche | Durée | Pic mémoire |
|---|---|---|
| Tout en mémoire | | |
| En flux | | |

Puis répondez, dans votre README, à **une seule question** :

> Laquelle est la plus rapide, et pourquoi ce n'est pas forcément celle qu'il faut choisir ?

## Étape 5 — Intégrer au fil rouge · 10 min

Rangez `lire_en_flux` dans votre paquet, dans un module dont le nom dit ce qu'il fait.
`ruff check` et `mypy src/` doivent rester silencieux — les annotations de type comprises.

Committez.

---

## Ce qui sera regardé

| Critère | Ce qu'on vérifie |
|---|---|
| C'est bien un générateur | La fonction contient `yield` (ou `yield from`), et ne renvoie pas une liste |
| Rien ne s'accumule | Aucune liste intermédiaire entre la lecture et le `Counter` |
| Le fichier se ferme | `with`, pas un `open()` orphelin |
| L'absence du fichier est gérée | `FileNotFoundError` attrapée nommément — pas un `except` nu |
| La mesure est faite | Les deux chiffres sont dans le README, avec la conclusion |
| Le code reste propre | `ruff` et `mypy` silencieux, fonctions annotées |

## Si vous avez fini en avance

1. **Lire par blocs plutôt que ligne à ligne.** `itertools.islice` permet de traiter par paquets
   de 10 000. Mesurez : est-ce plus rapide ? Pourquoi ?
2. **Comparer à `pandas.read_csv(..., chunksize=...)`.** Même idée, outil différent.
3. **Compter autre chose sans relire le fichier deux fois** — par exemple ouverts *et* fermés en
   un seul passage. Indice : un générateur ne se relit pas.

## En cas de blocage

| Symptôme | Cause probable | Réponse |
|---|---|---|
| Le générateur semble vide à la deuxième lecture | Un générateur s'épuise | Relancez-le, ou collectez ce dont vous avez besoin en un passage |
| `ValueError: I/O operation on closed file` | Le `with` s'est refermé avant la consommation | Le `yield` doit être **à l'intérieur** du `with` |
| Le pic mémoire ne baisse pas | Une liste traîne quelque part | Cherchez les `[` et les `list(` |
| `MemoryError` sur la version naïve | C'est le but du TP | Notez-le, c'est votre meilleure mesure |
