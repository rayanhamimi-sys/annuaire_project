# Développement Python — Séance 3

**Lundi 12 octobre 2026 · 09h00 – 12h45 · Salle 6**

## Au programme

Modéliser et **valider** ce qui entre dans le système, puis découpler la logique métier de ses
sources de données. À la fin, changer de source sera un argument en ligne de commande.

## Les fichiers

| Document | Quand |
|---|---|
| `TP3 — Trois sources, une seule logique.md` | En séance, à partir de 11h20 |
| `preparer_donnees.py` | À lancer au début du TP |

## Avant le TP

```bash
python3 preparer_donnees.py
```

Télécharge 3 000 établissements et les écrit en **CSV** et en **Parquet** — les mêmes données
dans deux formats, pour que vos lecteurs soient comparables.

Il vous faudra `pandas`, `pyarrow`, `requests` et `pydantic` :

```bash
uv add pandas pyarrow requests pydantic
```

> Ajoutez `donnees/` à votre `.gitignore`.

## Ce que vous repartez avec

Un pipeline dont la logique métier ignore d'où viennent les données, et qui accepte trois
sources interchangeables sans qu'une seule ligne d'analyse ne change.

## À noter

**QCM 1 : vendredi 16 octobre, en ouverture de séance.** 30 minutes, 20 questions, sans
documentation. Périmètre : **séances 1 à 3** — structures de données, générateurs, POO,
typage. Rien de la séance 4 n'y figure.
