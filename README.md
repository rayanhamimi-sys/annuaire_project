# Annuaire des établissements scolaires

Ce projet récupère les données de 3 000 établissements scolaires français depuis l'API de l'Annuaire de l'Éducation nationale.

Les données sont ensuite nettoyées et analysées afin d'obtenir notamment la répartition des établissements par département, la répartition public/privé et le nombre d'ouvertures par année.

## Installation

Cloner le dépôt :

```bash
git clone https://github.com/rayanhamimi-sys/annuaire_project.git
```

Se placer dans le projet :

```bash
cd annuaire_project
```

Installer les dépendances avec `uv` :

```bash
uv sync
```

## Lancement

Pour récupérer, nettoyer et analyser les données :

```bash
uv run python -m annuaire_project.main
```

## Source des données

Les données proviennent de l'API publique **Annuaire de l'Éducation nationale**, disponible sur la plateforme Open Data du ministère de l'Éducation nationale.

Le programme récupère jusqu'à **3 000 établissements scolaires**, par pages de 100 enregistrements.

Les données sont ensuite filtrées afin de conserver les colonnes utiles et les établissements ouverts disposant d'un département renseigné.