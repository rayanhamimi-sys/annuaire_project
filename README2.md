# Développement Python — Séance 2

**Vendredi 25 septembre 2026 · 13h45 – 17h30 · Salle 5**

## Au programme

Structures de données, **compréhensions**, **générateurs**, et la gestion des erreurs.
Puis un TP : faire tenir dans 16 Mo un traitement qui en réclamait 2 000.

## Les fichiers

| Document | Quand |
|---|---|
| `TP2 — Traiter un fichier trop gros.md` | En séance, à partir de 16h15 |
| `generer_donnees.py` | À lancer au début du TP — produit le fichier de travail |

## Avant le TP

Le script fabrique un CSV de **2 millions de lignes, environ 212 Mo** :

```bash
python3 generer_donnees.py
```

Une dizaine de secondes. Si votre disque est serré, réduisez :

```bash
python3 generer_donnees.py 500000
```

> Ajoutez `donnees/` à votre `.gitignore`. **On ne versionne pas 212 Mo.**

## Ce que vous repartez avec

Un module de lecture en flux dans votre dépôt `annuaire`, et deux chiffres qui justifient son
existence : le pic mémoire avant, le pic mémoire après.
