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

## TP1 — Récupération et analyse des données

### Lancement

Pour récupérer, nettoyer et analyser les données :

```bash
uv run python -m annuaire_project.main
```

### Source des données

Les données proviennent de l'API publique **Annuaire de l'Éducation nationale**, disponible sur la plateforme Open Data du ministère de l'Éducation nationale.

Le programme récupère jusqu'à **3 000 établissements scolaires**, par pages de 100 enregistrements.

Les données sont ensuite filtrées afin de conserver les colonnes utiles et les établissements ouverts disposant d'un département renseigné.

---

## TP2 — Traitement d'un fichier volumineux

### Objectif

L'objectif du TP2 est de comparer deux méthodes permettant de traiter un fichier CSV contenant 2 millions d'établissements scolaires.

Contrairement au TP1, les données utilisées ici sont générées artificiellement à l'aide du script `generer_donnees.py`.

Deux méthodes sont comparées :

- **Méthode naïve :** chargement de toutes les lignes du fichier en mémoire avant leur traitement.
- **Méthode en flux :** utilisation d'un générateur Python permettant de lire les lignes une par une.

Les deux méthodes comptent le nombre d'établissements ouverts par département.

### Génération des données

Pour générer le fichier CSV :

```bash
uv run python generer_donnees.py
```

Le programme crée le fichier `donnees/etablissements.csv` contenant 2 millions de lignes.

Le dossier `donnees/` est ajouté au `.gitignore` pour éviter de stocker ce fichier volumineux dans le dépôt Git.

### Lancement du TP2

Une fois les modules du TP2 intégrés au paquet `annuaire_project`, exécuter :

```bash
uv run python -m annuaire_project.comparer_tp2
```

Le programme mesure le temps d'exécution et le pic de mémoire Python des deux méthodes à l'aide de `perf_counter` et `tracemalloc`.

### Résultats obtenus

| Approche | Durée | Pic mémoire |
|---|---:|---:|
| Tout en mémoire | 96,88 s | 2 536,5 Mo |
| Lecture en flux | 64,01 s | 0,1 Mo |

### Analyse des résultats

La méthode en flux est la plus rapide lors de notre test.

Elle nécessite 64,01 secondes contre 96,88 secondes pour la méthode naïve, soit une réduction du temps d'exécution d'environ **34 %**.

La différence de consommation mémoire mesurée est encore plus importante.

La méthode naïve utilise `list(csv.DictReader(...))`, ce qui charge les 2 millions de lignes dans une liste et entraîne une forte consommation mémoire.

La méthode en flux repose sur un générateur utilisant `yield`. Les données sont traitées ligne par ligne, sans stocker l'intégralité du fichier.

Le pic mesuré avec `tracemalloc` passe ainsi de 2 536,5 Mo à environ 0,1 Mo. Cet outil mesure les allocations Python suivies, et non la totalité de la RAM du processus.

### Conclusion

Dans notre expérience, **la lecture en flux est à la fois plus rapide et nettement moins gourmande en mémoire**.

Cependant, la méthode la plus rapide n'est pas nécessairement celle qu'il faut choisir dans toutes les situations.

La consommation mémoire est également un critère essentiel, particulièrement lorsque les fichiers sont très volumineux.

La lecture en flux constitue donc une solution adaptée au traitement de millions de lignes, car elle permet de limiter fortement l'utilisation de la mémoire tout en conservant le même résultat de comptage.

### Mesure complémentaire de la mémoire réelle (RSS)

Afin de compléter les mesures réalisées avec `tracemalloc`, nous avons utilisé un script adapté à Windows pour mesurer le pic de mémoire RSS de chaque méthode.

| Approche | Durée | Pic mémoire RSS |
|---|---:|---:|
| Pandas (tout en RAM) | 12,1 s | 563 Mo |
| Liste (tout en RAM) | 17,2 s | 1 907 Mo |
| Générateur (en flux) | 8,8 s | 15 Mo |

### Analyse complémentaire

La méthode utilisant un générateur est la plus rapide, avec un temps d'exécution de 8,8 secondes contre 17,2 secondes pour la liste et 12,1 secondes pour Pandas.

Elle réduit également la consommation mémoire d'environ 99,2 % par rapport à la méthode utilisant une liste.

Ces résultats confirment l'intérêt de la lecture en flux : les données sont traitées progressivement sans avoir besoin de charger l'intégralité du fichier en mémoire.

La mesure RSS permet d'observer la consommation mémoire du processus, tandis que `tracemalloc` mesure principalement les allocations Python suivies par l'interpréteur.

La lecture en flux constitue donc une solution particulièrement intéressante pour traiter des fichiers volumineux.

## TP3 — Trois sources, une seule logique métier

### Objectif

L'objectif du TP3 est de rendre le programme capable de traiter trois sources de données différentes : CSV, Parquet et API, sans modifier la logique métier.

### Fonctionnement

Le programme repose sur quatre modules :

- `modele.py` : définit le modèle `Etablissement` avec Pydantic et valide les données.
- `lecture.py` : contient les trois lecteurs et le `Protocol` commun.
- `analyse.py` : compte les établissements ouverts par département et les données rejetées.
- `cli.py` : permet de sélectionner la source depuis le terminal.

### Exécution

Depuis la racine du projet :

```bash
uv run python -m annuaire_project.cli --source csv
uv run python -m annuaire_project.cli --source parquet
uv run python -m annuaire_project.cli --source api
```

### Résultats

| Source | Établissements ouverts | Rejetés |
|---|---:|---:|
| CSV | 2 905 | 95 |
| Parquet | 2 905 | 95 |
| API | 2 905 | 95 |

Les 95 rejets correspondent à :

- 87 erreurs sur le statut.
- 8 erreurs sur le type d'établissement.

Les trois sources renvoient exactement les mêmes résultats, y compris la répartition par département.

### Conclusion

Ce TP montre l'intérêt du `Protocol` et de la séparation des responsabilités.

Les lecteurs récupèrent les données, Pydantic les valide et le module d'analyse applique les mêmes traitements indépendamment de la source.

Il est ainsi possible de changer de source sans modifier la logique métier du programme.

## TP4 — Optimisation des traitements avec Pandas et Polars

### Objectif

L'objectif du TP4 est de comparer différentes méthodes de traitement de données afin d'améliorer les performances d'un programme Python.

Nous utilisons le fichier CSV de 2 millions d'établissements scolaires généré lors du TP2.

Le but est de compter le nombre d'établissements ouverts par département en comparant quatre approches : Pandas naïf, Pandas `apply`, Pandas optimisé et Polars.

### Étape 1 — Comparaison des formats CSV et Parquet

Le fichier CSV est converti en quatre variantes du format Parquet :

- Parquet sans compression.
- Parquet avec compression Snappy.
- Parquet avec compression ZSTD.
- Parquet avec compression ZSTD et partitionnement par département.

La conversion est réalisée avec le fichier `scripts/convertir_parquet.py`.

**Commande :**

`uv run python scripts/convertir_parquet.py`

**Comparaison des tailles :**

| Format | Taille |
|---|---:|
| CSV | 212.00 MiB |
| Parquet sans compression | 40.19 MiB |
| Parquet Snappy | 23.55 MiB |
| Parquet ZSTD | 14.45 MiB |
| Parquet ZSTD partitionné | 29.26 MiB |

**Analyse des formats :**

Le format Parquet permet généralement une meilleure compression que le CSV, car il organise les données par colonne. Les valeurs identiques sont regroupées et peuvent être stockées plus efficacement.

Le partitionnement ne permet pas forcément de réduire la taille du fichier. Il sert principalement à organiser les données afin de pouvoir lire uniquement certains départements, sans parcourir toutes les données.

Enfin, convertir une colonne comme `libelle_departement` en type `category` ne réduit pas nécessairement la taille du Parquet, car ce format utilise déjà un encodage par dictionnaire pour les colonnes contenant beaucoup de valeurs répétées.

### Étape 2 — Comparaison des quatre méthodes

Quatre méthodes sont utilisées pour compter le nombre d'établissements ouverts par département.

**1. Pandas naïf**

Le programme charge le CSV complet puis parcourt chaque ligne avec une boucle `for` et `.iloc`.

Cette méthode est lente car elle effectue les opérations individuellement en Python.

**2. Pandas apply**

Le programme utilise `df.apply(axis=1)` pour appliquer une fonction sur chaque ligne.

Cette méthode évite d'écrire une boucle explicite, mais continue de traiter les lignes individuellement.

**3. Pandas optimisé**

Le programme utilise `usecols` pour ne lire que les deux colonnes nécessaires, le type `category` pour réduire la mémoire et une comparaison vectorisée pour filtrer les établissements ouverts.

Cette méthode évite les boucles Python et améliore fortement les performances.

**4. Polars en différé**

Le programme utilise `scan_parquet`, puis `filter`, `group_by` et `collect`.

Polars permet d'optimiser la lecture et le traitement des données grâce à son moteur d'exécution et à l'évaluation différée.

### Lancement des tests

Les quatre méthodes sont exécutées séparément afin de mesurer leur temps d'exécution et leur consommation mémoire sans mélanger les mesures entre les programmes.

**Commandes utilisées :**

- Pandas naïf : `uv run python scripts/benchmark_tp4.py naif`
- Pandas apply : `uv run python scripts/benchmark_tp4.py apply`
- Pandas optimisé : `uv run python scripts/benchmark_tp4.py optimise`
- Polars : `uv run python scripts/benchmark_tp4.py polars`

Les résultats sont comparés avec :

`uv run python scripts/synthese_tp4.py`

### Résultats obtenus

Les quatre méthodes produisent exactement le même résultat.

**Nombre total d'établissements ouverts : 1 940 295**

| Approche | Durée | Pic mémoire |
|---|---:|---:|
| Pandas naïf | 426,1851 s | 726,75 MiB |
| Pandas apply | 55,1740 s | 1 335,56 MiB |
| Pandas optimisé | 4,5098 s | 134,71 MiB |
| Polars différé | 0,1747 s | 137,29 MiB |

Les pics mémoire correspondent aux mesures du processus réalisées sous Windows. Ils ne sont donc pas directement comparables aux mesures `tracemalloc` du TP2.

### Analyse des résultats

Les performances varient fortement selon la méthode utilisée.

La méthode Pandas naïve est la plus lente, avec 426,19 secondes, soit plus de 7 minutes.

La méthode `apply` est plus rapide, avec 55,17 secondes, mais elle consomme davantage de mémoire : 1 335,56 MiB contre 726,75 MiB pour la méthode naïve.

Pandas optimisé réduit le temps d'exécution à seulement 4,51 secondes et présente la plus faible consommation mémoire du test, avec 134,71 MiB.

Enfin, Polars est la méthode la plus rapide, avec seulement 0,17 seconde pour traiter les 2 millions de lignes.

**Polars est 2 439,5 fois plus rapide que Pandas naïf et environ 25,8 fois plus rapide que Pandas optimisé.**

### Pourquoi apply consomme-t-il plus de mémoire que la boucle iloc ?

Dans notre expérience, `apply` consomme environ 84 % de mémoire supplémentaire par rapport à la méthode naïve.

Cela s'explique notamment par la création d'objets intermédiaires lors du traitement des lignes.

La méthode naïve parcourt également les lignes individuellement, mais elle conserve principalement les compteurs dans un dictionnaire.

`apply` n'est donc pas nécessairement une méthode optimisée, même si son écriture paraît plus simple.

### Quels sont les trois principaux leviers d'optimisation ?

**1. La lecture sélective des données**

Avec `usecols` ou la lecture en colonnes de Parquet, nous pouvons charger uniquement les informations nécessaires au calcul.

**2. La suppression des boucles Python**

Les opérations vectorisées de Pandas et les expressions Polars permettent de traiter les données sans parcourir manuellement chaque ligne dans une boucle Python.

**3. L'utilisation de Parquet et de l'exécution différée**

Parquet permet une lecture efficace des colonnes, tandis que Polars peut optimiser le plan de traitement avant son exécution grâce à `scan_parquet`.

### Conclusion

Ce TP montre que le choix des bibliothèques, du format de stockage et de la méthode de traitement influence fortement les performances d'un programme Python.

Les quatre approches produisent le même résultat, mais leurs temps d'exécution et leurs consommations mémoire sont très différents.

**Polars est la solution la plus rapide dans notre test**, tandis que Pandas optimisé présente la consommation mémoire la plus faible.

Nous retenons qu'avant de chercher à optimiser un programme, il est important de mesurer ses performances et d'éviter les traitements ligne par ligne lorsque des opérations vectorisées sont possibles.