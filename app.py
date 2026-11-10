
"""Dashboard Streamlit connecté à PostgreSQL."""

import unicodedata

import folium
from folium.plugins import FastMarkerCluster
import pandas as pd
import plotly.express as px
import sqlalchemy as sa
import streamlit as st

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict
from streamlit_folium import st_folium


# ============================================================
# 1. CONFIGURATION ET CONNEXION POSTGRESQL
# ============================================================

st.set_page_config(
    page_title="Annuaire scolaire | PostgreSQL",
    page_icon="🏫",
    layout="wide"
)


class Reglages(BaseSettings):

    model_config = SettingsConfigDict(
        env_prefix="ANNUAIRE_",
        env_file=".env",
        extra="ignore"
    )

    base_url: PostgresDsn


@st.cache_resource(show_spinner=False)
def connexion(url):
    return sa.create_engine(
        sa.engine.make_url(url),
        pool_pre_ping=True
    )


@st.cache_data(
    ttl=120,
    show_spinner="Lecture de PostgreSQL..."
)
def charger_donnees(_moteur):

    colonnes = {
        champ["name"]
        for champ in sa.inspect(
            _moteur
        ).get_columns("etablissement")
    }

    geo_presente = {
        "latitude",
        "longitude"
    }.issubset(colonnes)

    partie_geo = (
        "latitude, longitude"
        if geo_presente
        else (
            "NULL::double precision AS latitude, "
            "NULL::double precision AS longitude"
        )
    )

    # Les noms sont ceux de la table PostgreSQL TP6.
    # Les alias retrouvent les noms du TP5.

    requete = sa.text(f"""
        SELECT
            identifiant AS identifiant_de_l_etablissement,
            nom AS nom_etablissement,
            statut AS statut_public_prive,
            type_etablissement,
            code_departement,
            departement AS libelle_departement,
            academie AS libelle_academie,
            region AS libelle_region,
            commune AS nom_commune,
            code_postal,
            adresse AS adresse_1,
            restauration,
            hebergement,
            ulis,
            segpa,
            charge_le,
            {partie_geo}
        FROM etablissement
        ORDER BY identifiant
    """)

    tableau = pd.read_sql_query(
        requete,
        _moteur
    )

    colonnes_texte = [
        c for c in tableau.columns
        if c not in {
            "latitude",
            "longitude",
            "charge_le"
        }
    ]

    for col in colonnes_texte:
        tableau[col] = (
            tableau[col]
            .fillna("")
            .astype(str)
        )

    return tableau, geo_presente


# ============================================================
# 2. FONCTIONS UTILITAIRES
# ============================================================

def format_nombre(valeur):
    return f"{int(valeur):,}".replace(",", " ")


def proportion(partie, ensemble):
    return (
        100 * partie / ensemble
        if ensemble else 0
    )


def normaliser(texte):

    texte = unicodedata.normalize(
        "NFKD",
        str(texte)
    )

    return "".join(
        c for c in texte
        if not unicodedata.combining(c)
    ).strip().lower()


def valeurs(frame, colonne):

    return sorted(
        v for v in frame[colonne].unique()
        if v.strip()
    )


def en_csv(frame):

    return frame.to_csv(
        index=False,
        sep=";"
    ).encode("utf-8-sig")


def diagramme_barres(
    frame,
    colonne,
    titre,
    limite=15
):

    st.subheader(titre)

    comptes = frame.loc[
        frame[colonne].str.strip().ne(""),
        colonne
    ].value_counts().head(limite)

    if comptes.empty:

        st.info(
            "Pas de données pour cette sélection."
        )
        return

    table = (
        comptes
        .rename_axis("Catégorie")
        .reset_index(name="Nombre")
    )

    table = table.sort_values("Nombre")

    figure = px.bar(
        table,
        x="Nombre",
        y="Catégorie",
        text="Nombre",
        orientation="h"
    )

    figure.update_layout(
        height=max(
            330,
            32 * len(table) + 90
        ),
        margin=dict(
            l=0,
            r=20,
            t=10,
            b=10
        ),
        yaxis_title=""
    )

    st.plotly_chart(
        figure,
        use_container_width=True
    )


# ============================================================
# 3. CHARGEMENT SQL
# ============================================================

try:

    reglages = Reglages()

    moteur = connexion(
        str(reglages.base_url)
    )

    with moteur.connect() as conn:
        conn.execute(
            sa.text("SELECT 1")
        )

    if st.sidebar.button(
        "🔄 Actualiser les données"
    ):
        charger_donnees.clear()

    source, geo_presente = charger_donnees(
        moteur
    )

except Exception as erreur:

    st.error(
        "Impossible de lire la base PostgreSQL."
    )

    st.code(str(erreur))

    st.info(
        "Vérifie que Docker fonctionne, "
        "que le fichier .env contient "
        "ANNUAIRE_BASE_URL et que le "
        "chargement TP6 a bien été exécuté."
    )

    st.stop()


if source.empty:

    st.warning(
        "La table etablissement est vide."
    )

    st.stop()


# ============================================================
# 4. FILTRES
# ============================================================

st.sidebar.header("🔎 Filtres")

df = source

for colonne, titre in [
    ("libelle_region", "Région"),
    ("libelle_academie", "Académie"),
    ("libelle_departement", "Département"),
    ("code_departement", "Code département"),
    ("type_etablissement", "Type d'établissement"),
    ("statut_public_prive", "Public / privé"),
]:

    choix = st.sidebar.multiselect(
        titre,
        valeurs(df, colonne)
    )

    if choix:

        df = df.loc[
            df[colonne].isin(choix)
        ]


recherche = st.sidebar.text_input(
    "Rechercher un établissement",
    placeholder=(
        "Nom, ville, adresse, "
        "code postal, UAI..."
    )
)

if recherche.strip():

    masque = pd.Series(
        False,
        index=df.index
    )

    for colonne in [
        "identifiant_de_l_etablissement",
        "nom_etablissement",
        "nom_commune",
        "code_postal",
        "adresse_1"
    ]:

        masque |= df[colonne].str.contains(
            recherche.strip(),
            case=False,
            regex=False,
            na=False
        )

    df = df.loc[masque]


# ============================================================
# 5. EN-TÊTE
# ============================================================

st.title(
    "🏫 Tableau de bord des établissements scolaires"
)

st.caption(
    "Données de l'Éducation nationale · "
    "Source : PostgreSQL · TP5 + TP6"
)

if df.empty:

    st.warning(
        "Aucun résultat : modifie les filtres."
    )

    st.stop()


# ============================================================
# 6. CALCUL DES INDICATEURS
# ============================================================

statut = df[
    "statut_public_prive"
].map(normaliser)

public = statut.eq("public")

prive = statut.str.contains(
    "prive",
    regex=False
)

statuts_connus = public | prive

uai_uniques = df[
    "identifiant_de_l_etablissement"
].nunique()

nb_public = int(public.sum())
nb_prive = int(prive.sum())
nb_connus = int(statuts_connus.sum())

nb_departements = df.loc[
    df["code_departement"].ne(""),
    "code_departement"
].nunique()


# Communes distinguées par département.

communes_valides = df.loc[
    df["nom_commune"].ne("")
]

nb_communes = len(
    communes_valides[
        ["code_departement", "nom_commune"]
    ].drop_duplicates()
)


# ============================================================
# 7. DONNÉES GÉOGRAPHIQUES
# ============================================================

carte = df.copy()

carte["latitude"] = pd.to_numeric(
    carte["latitude"],
    errors="coerce"
)

carte["longitude"] = pd.to_numeric(
    carte["longitude"],
    errors="coerce"
)

carte = carte.dropna(
    subset=["latitude", "longitude"]
)

carte = carte.loc[
    carte["latitude"].between(-90, 90)
    & carte["longitude"].between(-180, 180)
    & ~(
        (carte["latitude"] == 0)
        & (carte["longitude"] == 0)
    )
]


# ============================================================
# 8. CHIFFRES CLÉS EN HAUT
# ============================================================

st.subheader("📌 Chiffres clés")

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Établissements",
    format_nombre(len(df))
)

k2.metric(
    "Communes",
    format_nombre(nb_communes)
)

k3.metric(
    "Départements",
    format_nombre(nb_departements)
)

k4.metric(
    f"Géolocalisés ({proportion(len(carte), len(df)):.1f} %)",
    format_nombre(len(carte))
)

k5, k6, k7, k8 = st.columns(4)

k5.metric(
    "Publics",
    format_nombre(nb_public)
)

k6.metric(
    "Privés",
    format_nombre(nb_prive)
)

k7.metric(
    "Part du privé",
    (
        f"{proportion(nb_prive, nb_connus):.1f} %"
        if nb_connus else "—"
    )
)

k8.metric(
    "UAI distincts",
    format_nombre(uai_uniques)
)

st.caption(
    "Les chiffres suivent les filtres. "
    "La part du privé est calculée uniquement "
    "sur les établissements dont le statut "
    "est identifiable."
)

if not geo_presente:

    st.warning(
        "La base ne contient pas encore "
        "latitude et longitude. "
        "Exécute ajouter_coordonnees_tp6.py "
        "puis actualise les données."
    )

st.divider()


# ============================================================
# 9. ONGLETS
# ============================================================

(
    vue,
    carte_tab,
    territoires,
    services,
    qualite,
    exploration
) = st.tabs([
    "📊 Vue d'ensemble",
    "🛰️ Carte satellite",
    "🗺️ Territoires",
    "♿ Services et inclusion",
    "🧪 Qualité des données",
    "📋 Données et export"
])


# ============================================================
# 10. VUE D'ENSEMBLE
# ============================================================

with vue:

    gauche, droite = st.columns(2)

    with gauche:

        st.subheader("Public / privé")

        if nb_connus:

            repartition = pd.DataFrame({
                "Statut": ["Public", "Privé"],
                "Établissements": [
                    nb_public,
                    nb_prive
                ]
            })

            figure = px.pie(
                repartition,
                names="Statut",
                values="Établissements",
                hole=0.5
            )

            st.plotly_chart(
                figure,
                use_container_width=True
            )

        else:

            st.info(
                "Aucun statut public/privé identifiable."
            )

    with droite:

        diagramme_barres(
            df,
            "type_etablissement",
            "Types d'établissements",
            12
        )

    gauche, droite = st.columns(2)

    with gauche:

        diagramme_barres(
            df,
            "libelle_region",
            "Régions",
            20
        )

    with droite:

        diagramme_barres(
            df,
            "libelle_academie",
            "Académies",
            20
        )


# ============================================================
# 11. CARTE SATELLITE
# ============================================================

with carte_tab:

    st.subheader(
        "🛰️ Carte satellite des établissements"
    )

    st.write(
        "Zoome jusqu'aux bâtiments et clique "
        "sur un établissement pour voir "
        "ses informations."
    )

    if carte.empty:

        st.info(
            "Aucun établissement géolocalisé "
            "dans cette sélection. "
            "Si nécessaire, exécute "
            "ajouter_coordonnees_tp6.py."
        )

    else:

        limite_points = st.select_slider(
            "Nombre maximal de points sur la carte",
            options=[
                500,
                2000,
                5000,
                10000,
                20000
            ],
            value=5000
        )

        positions = (
            carte
            if len(carte) <= limite_points
            else carte.sample(
                n=limite_points,
                random_state=42
            )
        )

        lat_centre = float(
            positions["latitude"].median()
        )

        lon_centre = float(
            positions["longitude"].median()
        )

        etendue = max(
            (
                positions["latitude"].max()
                - positions["latitude"].min()
            ),
            (
                positions["longitude"].max()
                - positions["longitude"].min()
            )
        )

        if etendue < 0.05:
            zoom = 13
        elif etendue < 0.5:
            zoom = 10
        elif etendue < 5:
            zoom = 7
        else:
            zoom = 5

        m = folium.Map(
            location=[lat_centre, lon_centre],
            zoom_start=zoom,
            tiles=None,
            control_scale=True
        )

        # Couche satellite

        folium.TileLayer(
            tiles=(
                "https://server.arcgisonline.com/"
                "ArcGIS/rest/services/"
                "World_Imagery/MapServer/"
                "tile/{z}/{y}/{x}"
            ),
            attr=(
                "Esri, Maxar, Earthstar Geographics "
                "et GIS User Community"
            ),
            name="Satellite (Esri)",
            overlay=False,
            show=True
        ).add_to(m)

        # Couche classique

        folium.TileLayer(
            "OpenStreetMap",
            name="Plan classique",
            overlay=False,
            show=False
        ).add_to(m)

        colonnes_carte = [
            "latitude",
            "longitude",
            "nom_etablissement",
            "nom_commune",
            "type_etablissement",
            "statut_public_prive",
            "identifiant_de_l_etablissement",
            "adresse_1",
            "code_postal"
        ]

        lignes = (
            positions[colonnes_carte]
            .fillna("")
            .values.tolist()
        )

        # Popup sécurisée :
        # les textes sont insérés comme texte,
        # et non interprétés comme du HTML.

        callback = """
        function(row) {

            var statut = (row[5] || '').toLowerCase();

            var couleur =
                statut.indexOf('priv') >= 0
                ? '#e39d23'
                : statut === 'public'
                ? '#2563eb'
                : '#64748b';

            var icone = L.divIcon({
                className: '',
                iconSize: [16, 16],
                iconAnchor: [8, 8],
                html:
                    '<div style="width:14px;height:14px;'
                    + 'border-radius:50%;'
                    + 'border:2px solid white;background:'
                    + couleur
                    + ';box-shadow:0 1px 5px #555;"></div>'
            });

            var marqueur = L.marker(
                [row[0], row[1]],
                {icon: icone}
            );

            var popup = document.createElement('div');

            var titre = document.createElement('h4');
            titre.textContent = row[2] || 'Établissement';
            popup.appendChild(titre);

            function ajouter(etiquette, valeur) {

                if (!valeur) return;

                var paragraphe = document.createElement('p');
                paragraphe.style.margin = '3px 0';

                var fort = document.createElement('strong');
                fort.textContent = etiquette + ' : ';

                paragraphe.appendChild(fort);

                paragraphe.appendChild(
                    document.createTextNode(valeur)
                );

                popup.appendChild(paragraphe);
            }

            ajouter('Commune', row[3]);
            ajouter('Type', row[4]);
            ajouter('Statut', row[5]);
            ajouter('UAI', row[6]);

            ajouter(
                'Adresse',
                (row[7] || '') + ' ' + (row[8] || '')
            );

            marqueur.bindPopup(
                popup,
                {maxWidth: 320}
            );

            marqueur.bindTooltip(
                document.createTextNode(
                    row[2] || 'Établissement'
                )
            );

            return marqueur;
        }
        """

        FastMarkerCluster(
            lignes,
            callback=callback,
            name="Établissements",
            max_cluster_radius=60
        ).add_to(m)

        folium.LayerControl(
            collapsed=False
        ).add_to(m)

        st_folium(
            m,
            height=620,
            use_container_width=True,
            returned_objects=[],
            key="carte_postgresql"
        )

        st.caption(
            f"{format_nombre(len(positions))} points "
            f"affichés sur {format_nombre(len(carte))} "
            "établissements géolocalisés. "
            "Bleu = public · Orange = privé · "
            "Gris = autre. "
            "La carte satellite nécessite Internet."
        )


# ============================================================
# 12. ANALYSE TERRITORIALE
# ============================================================

with territoires:

    st.subheader(
        "Analyse des territoires"
    )

    niveaux = {
        "Régions": "libelle_region",
        "Académies": "libelle_academie",
        "Départements": "libelle_departement",
        "Communes": "nom_commune"
    }

    niveau = st.selectbox(
        "Niveau géographique",
        list(niveaux)
    )

    champ = niveaux[niveau]

    base = df.loc[
        df[champ].ne("")
    ].copy()

    base["_prive"] = (
        prive.reindex(base.index).astype(int)
    )

    base["_connu"] = (
        statuts_connus.reindex(base.index).astype(int)
    )

    colonnes_groupement = (
        ["code_departement", "nom_commune"]
        if niveau == "Communes"
        else [champ]
    )

    tableau = base.groupby(
        colonnes_groupement,
        as_index=False
    ).agg(
        etablissements=(
            "identifiant_de_l_etablissement",
            "size"
        ),
        prives=("_prive", "sum"),
        statuts_connus=("_connu", "sum")
    )

    tableau["part_prive_pct"] = (
        100
        * tableau["prives"]
        / tableau["statuts_connus"].replace(
            0,
            float("nan")
        )
    ).round(1)

    tableau = tableau.sort_values(
        "etablissements",
        ascending=False
    )

    st.dataframe(
        tableau,
        hide_index=True,
        use_container_width=True
    )

    st.download_button(
        "⬇️ Télécharger le classement territorial",
        en_csv(tableau),
        "indicateurs_territoriaux.csv",
        "text/csv"
    )

    diagramme_barres(
        df,
        champ,
        f"Top 15 : {niveau}",
        15
    )

    if niveau == "Communes":

        st.caption(
            "Le tableau distingue les communes par "
            "département. Le graphique regroupe "
            "les communes portant le même nom."
        )


# ============================================================
# 13. SERVICES ET INCLUSION
# ============================================================

with services:

    st.subheader(
        "Services et inclusion"
    )

    champs = {
        "Restauration": "restauration",
        "Hébergement": "hebergement",
        "ULIS": "ulis",
        "SEGPA": "segpa"
    }

    valeurs_oui = {
        "1",
        "oui",
        "true",
        "vrai",
        "o"
    }

    valeurs_non = {
        "0",
        "non",
        "false",
        "faux",
        "n"
    }

    lignes_stats = []

    for titre, col in champs.items():

        valeurs_normalisees = (
            df[col].map(normaliser)
        )

        connus_service = int(
            valeurs_normalisees.isin(
                valeurs_oui | valeurs_non
            ).sum()
        )

        positifs = int(
            valeurs_normalisees.isin(
                valeurs_oui
            ).sum()
        )

        lignes_stats.append({
            "Service": titre,
            "Établissements concernés": positifs,
            "Réponses connues": connus_service,
            "Taux (%)": (
                round(
                    proportion(
                        positifs,
                        connus_service
                    ),
                    1
                )
                if connus_service
                else None
            )
        })

    stats = pd.DataFrame(
        lignes_stats
    )

    st.dataframe(
        stats,
        hide_index=True,
        use_container_width=True
    )

    graphiques = stats.dropna(
        subset=["Taux (%)"]
    )

    if not graphiques.empty:

        figure = px.bar(
            graphiques.sort_values("Taux (%)"),
            x="Taux (%)",
            y="Service",
            orientation="h",
            text="Taux (%)"
        )

        st.plotly_chart(
            figure,
            use_container_width=True
        )

    st.caption(
        "Les taux sont calculés sur les réponses "
        "oui/non connues. Une valeur manquante "
        "n'est pas considérée comme une réponse négative."
    )

    st.download_button(
        "⬇️ Télécharger les statistiques des services",
        en_csv(stats),
        "services_et_inclusion.csv",
        "text/csv"
    )


# ============================================================
# 14. QUALITÉ DES DONNÉES
# ============================================================

with qualite:

    st.subheader(
        "Contrôle qualité PostgreSQL"
    )

    nb_repetes = (
        len(df) - uai_uniques
    )

    a, b, c = st.columns(3)

    a.metric(
        "Lignes sélectionnées",
        format_nombre(len(df))
    )

    b.metric(
        "UAI répétés en base",
        format_nombre(nb_repetes)
    )

    c.metric(
        "Sans géolocalisation",
        format_nombre(
            len(df) - len(carte)
        )
    )

    st.caption(
        "La table du TP6 impose une clé primaire "
        "sur l'identifiant UAI. "
        "Les doublons écartés lors du chargement "
        "sont consignés dans les journaux du TP6."
    )

    controles = pd.DataFrame([
        {
            "Colonne": c,
            "Valeurs manquantes": int(
                (
                    df[c].isna().sum()
                    if c in {
                        "latitude",
                        "longitude",
                        "charge_le"
                    }
                    else df[c].eq("").sum()
                )
            )
        }
        for c in df.columns
    ])

    controles["Taux manquant (%)"] = (
        controles["Valeurs manquantes"]
        / len(df)
        * 100
    ).round(1)

    controles = controles.sort_values(
        "Taux manquant (%)",
        ascending=False
    )

    st.dataframe(
        controles,
        hide_index=True,
        use_container_width=True
    )

    st.download_button(
        "⬇️ Télécharger les contrôles qualité",
        en_csv(controles),
        "qualite_postgresql.csv",
        "text/csv"
    )


# ============================================================
# 15. DONNÉES ET EXPORT CSV
# ============================================================

with exploration:

    st.subheader(
        "Données PostgreSQL et export CSV"
    )

    colonnes_defaut = [
        "identifiant_de_l_etablissement",
        "nom_etablissement",
        "type_etablissement",
        "statut_public_prive",
        "adresse_1",
        "code_postal",
        "nom_commune",
        "code_departement",
        "libelle_region",
        "latitude",
        "longitude"
    ]

    selection = st.multiselect(
        "Colonnes à afficher et exporter",
        list(df.columns),
        default=colonnes_defaut
    )

    if selection:

        maximum = st.select_slider(
            "Lignes dans l'aperçu",
            [
                100,
                250,
                500,
                1000,
                3000
            ],
            value=500
        )

        st.dataframe(
            df[selection].head(maximum),
            hide_index=True,
            use_container_width=True,
            height=500
        )

        st.download_button(
            "⬇️ Télécharger toutes les lignes filtrées en CSV",
            en_csv(df[selection]),
            "annuaire_postgresql_filtre.csv",
            "text/csv",
            type="primary"
        )

        st.caption(
            "Le fichier CSV contient toutes les "
            "lignes filtrées, et non uniquement "
            "les lignes affichées dans l'aperçu."
        )


# ============================================================
# 16. PIED DE PAGE
# ============================================================

st.divider()

st.caption(
    "Source : Annuaire de l'Éducation nationale | "
    "Stockage : PostgreSQL | "
    "Carte satellite : Esri World Imagery"
)
