import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.title("Configuration du Rapport SFCR")

# 1. Charger les données
@st.cache_data
def load_data():
    try:
        return pd.read_csv("base_de_donnees_esilv.csv", sep=';', encoding='latin-1')
    except:
       return pd.read_csv("base_de_donnees_esilv.csv", sep=';', encoding='latin-1')

df = load_data()
df['Année'] = df['Année'].astype(str)

# Sauvegarder pour les autres pages
st.session_state.df = df
toutes_entreprises = sorted(df['Entreprise'].unique())


# SECTION 1 : QUI ÊTES-VOUS ?

st.header("Qui êtes-vous ?")

profil = st.radio(
    "Sélectionnez votre profil :",
    ["Assureur", "Personne (consultant/externe)"],
    horizontal=True
)

if profil == "Assureur":
    votre_entreprise = st.selectbox("Votre compagnie :", toutes_entreprises)
    st.info(f"Le rapport sera centré sur {votre_entreprise}")
else:
    votre_entreprise = None
    st.info("Vue globale : tous les assureurs seront affichés")

 
# SECTION 2 : GROUPES DE COMPARAISON

st.header("Groupes de comparaison")

st.markdown("""
Créez des **groupes d'assureurs** à comparer.  
Chaque groupe = **une barre** dans les graphiques (moyenne du groupe).
""")

# Liste des entreprises disponibles pour les groupes
if profil == "Assureur" and votre_entreprise:
    entreprises_disponibles = [e for e in toutes_entreprises if e != votre_entreprise]
else:
    entreprises_disponibles = toutes_entreprises.copy()

# Groupe 1
st.subheader("Groupe 1")
groupe1 = st.multiselect(
    "Sélectionnez les assureurs pour le Groupe 1 :",
    entreprises_disponibles,
    placeholder="Choisissez une ou plusieurs compagnies...",
    key="groupe1"
)

# Groupe 2 (optionnel)
st.subheader("Groupe 2 (optionnel)")
ajouter_groupe2 = st.checkbox("Ajouter un second groupe de comparaison")

if ajouter_groupe2:
    # Enlever celles déjà dans groupe1
    entreprises_restantes = [e for e in entreprises_disponibles if e not in groupe1]
    groupe2 = st.multiselect(
        "Sélectionnez les assureurs pour le Groupe 2 :",
        entreprises_restantes,
        placeholder="Choisissez une ou plusieurs compagnies...",
        key="groupe2"
    )
else:
    groupe2 = []


# SECTION 3 : INDICATEUR À ANALYSER
 
st.header("Indicateur à analyser")

indicateurs = df['Indicateur'].unique()
indicateur_choisi = st.selectbox(
    "Sélectionnez l'indicateur :",
    indicateurs[:20],
    key="indicateur"
)


# SECTION 4 : VISUALISATION

st.header("Visualisation")

if st.button("Générer le rapport", type="primary"):
    
    # CAS 1 : PROFIL "PERSONNE" → TOUS LES ASSUREURS
    if profil == "Personne":
        st.subheader("📈 Vue globale - Tous les assureurs")
        
        # Filtrer pour l'indicateur choisi
        donnees_filtrees = df[df['Indicateur'] == indicateur_choisi]
        
        if not donnees_filtrees.empty:
            fig = px.bar(
                donnees_filtrees,
                x='Entreprise',
                y='Valeur',
                color='Année',
                barmode='group',
                title=f"{indicateur_choisi} - Tous les assureurs"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Aucune donnée pour cet indicateur")
    
    # CAS 2 : PROFIL "ASSUREUR" → COMPARAISON AVEC GROUPES
    elif profil == "Assureur" and votre_entreprise:
        
        # 1. Vos données
        vos_donnees = df[
            (df['Entreprise'] == votre_entreprise) & 
            (df['Indicateur'] == indicateur_choisi)
        ]
        
        # Préparer les données pour le graphique
        data_for_chart = []
        
        # Ajouter vos données
        for _, row in vos_donnees.iterrows():
            data_for_chart.append({
                'Catégorie': votre_entreprise,
                'Année': row['Année'],
                'Valeur': row['Valeur']
            })
        
        # 2. Groupe 1
        if groupe1:
            donnees_groupe1 = df[
                (df['Entreprise'].isin(groupe1)) & 
                (df['Indicateur'] == indicateur_choisi)
            ]
            if not donnees_groupe1.empty:
                moyennes_g1 = donnees_groupe1.groupby('Année')['Valeur'].mean().reset_index()
                for _, row in moyennes_g1.iterrows():
                    data_for_chart.append({
                        'Catégorie': f"Moyenne Groupe 1 ({len(groupe1)} co.)",
                        'Année': row['Année'],
                        'Valeur': row['Valeur']
                    })
        
        # 3. Groupe 2
        if groupe2:
            donnees_groupe2 = df[
                (df['Entreprise'].isin(groupe2)) & 
                (df['Indicateur'] == indicateur_choisi)
            ]
            if not donnees_groupe2.empty:
                moyennes_g2 = donnees_groupe2.groupby('Année')['Valeur'].mean().reset_index()
                for _, row in moyennes_g2.iterrows():
                    data_for_chart.append({
                        'Catégorie': f"Moyenne Groupe 2 ({len(groupe2)} co.)",
                        'Année': row['Année'],
                        'Valeur': row['Valeur']
                    })
        
        # 4. Créer le graphique
        if data_for_chart:
            chart_df = pd.DataFrame(data_for_chart)
            
            fig = px.bar(
                chart_df,
                x='Catégorie',
                y='Valeur',
                color='Année',
                barmode='group',
                title=f"Comparaison : {votre_entreprise} vs Groupes"
            )
            
            # Ajouter les valeurs sur les barres (optionnel)
            fig.update_traces(texttemplate='%{y:.2f}', textposition='outside')
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 5. Afficher les valeurs détaillées
            st.subheader("📋 Détails des valeurs")
            
            # Vos valeurs
            st.write(f"**{votre_entreprise}**")
            st.dataframe(vos_donnees[['Année', 'Valeur']])
            
            # Moyennes des groupes
            if groupe1:
                st.write(f"**Moyenne Groupe 1** ({', '.join(groupe1)})")
                st.dataframe(moyennes_g1)
            
            if groupe2:
                st.write(f"**Moyenne Groupe 2** ({', '.join(groupe2)})")
                st.dataframe(moyennes_g2)
        
        else:
            st.warning("Aucune donnée disponible pour cette configuration")

