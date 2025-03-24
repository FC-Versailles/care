#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 21 10:49:48 2025

@author: fcvmathieu
"""

import streamlit as st
import pandas as pd
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os
import pickle
import ast
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages
import plotly.express as px

# Constants for Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
TOKEN_FILE = 'token.pickle'
SPREADSHEET_ID = '1UP1kzcTX7hexglokW2b-INUXPamk7zEHB5e0ha5_1fs'  # Replace with your actual Spreadsheet ID
RANGE_NAME = 'Feuille 1'

st.set_page_config(layout='wide')

# Display the club logo from GitHub at the top right
logo_url = 'https://raw.githubusercontent.com/FC-Versailles/care/main/logo.png'
col1, col2 = st.columns([9, 1])
with col1:
    st.title("Médical | FC Versailles")
with col2:
    st.image(logo_url, use_container_width=True)
    
# Add a horizontal line to separate the header
st.markdown("<hr style='border:1px solid #ddd' />", unsafe_allow_html=True)

# Function to get Google Sheets credentials
def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    return creds

# Function to fetch data from Google Sheet
def fetch_google_sheet(spreadsheet_id, range_name):
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])
    if not values:
        st.error("No data found in the specified range.")
        return pd.DataFrame()
    header = values[0]
    data = values[1:]
    max_columns = len(header)
    adjusted_data = [
        row + [None] * (max_columns - len(row)) if len(row) < max_columns else row[:max_columns]
        for row in data
    ]
    return pd.DataFrame(adjusted_data, columns=header)


# Load data from Google Sheets
@st.cache_data(ttl=60)
def load_data():
    return fetch_google_sheet(SPREADSHEET_ID, RANGE_NAME)


df = load_data()

df = df[~df['Nom'].isin(['Agoro', 'Bangoura', 'Mbala','Karamoko'])]


# Sort dataframe by earliest date first without parsing dates
if 'Date' in df.columns:
    df = df.sort_values(by='Date', ascending=False)

# Page Navigation
st.sidebar.title("FC Versailles Medical")
page = st.sidebar.selectbox("Select Page", ["Rapport Quotidien","Historique du Joueur", "Rappport de blessure","Bilan Médical"])

if page == "Historique du Joueur":
    st.title("Fiche Joueur")

    player_name = st.selectbox("Select Player", sorted(df['Nom'].dropna().unique()))

    # S'assurer que 'Date' est bien en datetime et formatée pour l'affichage
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Historique médical hors blessure
    player_data = df[
    (df['Nom'] == player_name) &
    (df['Motif consultation'].str.lower().isin(['soins', 'massage']))]
    st.write(f"🩺 **Historique Médical de {player_name}**")
    if not player_data.empty:
        medical_cols = ['Date', 'Motif consultation', 'Localisation du soin','Niveau inquietude', 'Remarque']
        medical_cols = [col for col in medical_cols if col in player_data.columns]
        df_medical = player_data[medical_cols].copy()
        if 'Date' in df_medical.columns:
            df_medical['Date'] = df_medical['Date'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_medical, use_container_width=True, height=500)
    else:
        st.info("Aucun historique médical trouvé hors blessure.")

    # Historique des blessures
    blessure_data = df[(df['Nom'] == player_name) & (df['Motif consultation'].str.lower() == 'blessure')]
    if not blessure_data.empty:
        st.write(f"🚑 **Historique des Blessures de {player_name}**")
        blessure_cols = ['Date', 'Type de journee','Contexte de blessure','Type de blessure',
                         'Localisation','Position ','Recidive','Mecanisme','Remarque']
        blessure_cols = [col for col in blessure_cols if col in blessure_data.columns]
        df_blessure = blessure_data[blessure_cols].copy()
        df_blessure['Date'] = df_blessure['Date'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_blessure, use_container_width=True)
    
    # Section Gestion du Joueur
    st.write("⚙️ **Gestion du Joueur**")
    for motif, cols in {
        'Prevention': ['Date', 'Activité', 'Type', 'Remarque'],
        'Renforcement': ['Date', 'Activité', 'Type', 'Remarque'],
        'Adaptation': ['Date', 'Adaptation', 'Remarque']
    }.items():
        data = df[(df['Nom'] == player_name) & (df['Motif consultation'].str.lower() == motif.lower())]
        if not data.empty:
            st.write(f"**{motif}**")
            available_cols = [col for col in cols if col in data.columns]
            data = data[available_cols].copy()
            if 'Date' in data.columns:
                data['Date'] = data['Date'].dt.strftime('%d/%m/%Y')
            st.dataframe(data, use_container_width=True)
    
    # Section Return to Play
    st.write("🏃‍♂️ **Réathlétisation**")
    rtp_data = df[(df['Nom'] == player_name) & (df['Motif consultation'].str.lower() == 'réathlétisation')]
    if not rtp_data.empty:
        rtp_cols = ['Date', 'RTP', 'Physio', 'Cardio', 'Intensite', 'Force', 'Terrain', 'Remarque']
        available_cols = [col for col in rtp_cols if col in rtp_data.columns]
        rtp_data = rtp_data[available_cols].copy()
        rtp_data['Date'] = rtp_data['Date'].dt.strftime('%d/%m/%Y')
        st.dataframe(rtp_data, use_container_width=True)

elif page == "Rappport de blessure":
    st.title("Rapport de Blessure")

    # Assurer que la colonne Date est en datetime pour trier si besoin
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Table 1 : Blessures en cours
    st.subheader("📋 Blessures déclarées")
    injury_data = df[df['Motif consultation'].str.lower() == 'blessure']
    blessure_cols = ['Nom', 'Date', 'Type de journee','Contexte de blessure','Type de blessure',
                     'Localisation','Position ','Recidive','Mecanisme','Remarque']
    blessure_cols = [col for col in blessure_cols if col in injury_data.columns]
    injury_data['Date'] = injury_data['Date'].dt.strftime('%d/%m/%Y')
    st.dataframe(injury_data[blessure_cols].head(20), use_container_width=True, height=500)

    # Table 2 : Blessures Clôturées
    st.subheader("✅ Blessures Clôturées")
    closed_data = df[
        (df['Motif consultation'].str.lower() == 'réathlétisation') &
        (df['RTP'].str.lower() == 'cloture')
    ]
    closed_cols = ['Nom', 'Date', 'RTP', 'Physio', 'Cardio', 'Intensite', 'Force', 'Terrain', 'Remarque']
    closed_cols = [col for col in closed_cols if col in closed_data.columns]
    closed_data = closed_data[closed_cols].copy()
    closed_data['Date'] = closed_data['Date'].dt.strftime('%d/%m/%Y')
    st.dataframe(closed_data, use_container_width=True)

elif page == "Rapport Quotidien":
    st.title("Rapport Quotidien")

    # Convertir la colonne Date en datetime
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])

    # Sélecteur de date via calendrier
    selected_date = st.date_input("Sélectionnez une date", value=df['Date'].max(), 
                                  min_value=df['Date'].min(), max_value=df['Date'].max())

    # Filtrer les données du jour sélectionné
    daily_data = df[df['Date'].dt.date == selected_date]

    # Dictionnaire des colonnes à afficher par motif
    motif_columns = {
        'Absent': ['Nom', 'Absence', 'Remarque'],
        'Adaptation': ['Nom', 'Adaptation', 'Remarque'],
        'Réathlétisation': ['Nom', 'RTP', 'Physio', 'Cardio', 'Intensite', 'Force', 'Terrain', 'Remarque'],
        'Soins': ['Nom', 'Localisation du soin', 'Remarque'],  # pas mentionné, gardé comme avant
        'Prevention': ['Nom', 'Activité', 'Type', 'Remarque'],
        'Renforcement': ['Nom', 'Activité', 'Type', 'Remarque'],
        'Maladie': ['Nom', 'RTP', 'Physio', 'Cardio', 'Intensite', 'Force', 'Terrain', 'Remarque']
    }

    # Affichage par motif
    for motif in ['Absent', 'Adaptation', 'Réathlétisation', 'Soins', 'Prevention', 'Renforcement', 'Maladie']:
        st.write(f"**{motif}**")
        motif_data = daily_data[daily_data['Motif consultation'].str.lower() == motif.lower()]
        if not motif_data.empty:
            columns_to_display = motif_columns.get(motif, ['Nom', 'Remarque'])  # fallback
            available_columns = [col for col in columns_to_display if col in motif_data.columns]
            st.dataframe(motif_data[available_columns], use_container_width=True)
        else:
            st.write("--")

elif page == "Bilan Médical":
    st.title("Bilan Médical")

    # S'assurer que la colonne 'Date' est bien en datetime
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])

    # Sélecteur de semaine (on sélectionne un lundi)
    start_of_week = st.date_input("Sélectionnez le début de la semaine (lundi)", value=df['Date'].max())

    # Forcer le début de semaine au lundi (même si l'utilisateur choisit un autre jour)
    start_of_week = start_of_week - pd.to_timedelta(start_of_week.weekday(), unit='d')
    end_of_week = start_of_week + pd.Timedelta(days=6)

    # Filtrer les données de la semaine
    weekly_data = df[(df['Date'].dt.date >= start_of_week) & (df['Date'].dt.date <= end_of_week)]

    st.markdown(f"Semaine du **{start_of_week.strftime('%d/%m/%Y')}** au **{end_of_week.strftime('%d/%m/%Y')}**")

    # Colonnes spécifiques par motif
    motif_columns = {
        'Osteopathie': ['Date', 'Nom', 'Localisation du soin', 'Niveau inquietude', 'Remarque'],
        'Podologue': ['Date', 'Nom', 'inquietude', 'Remarque'],
        'Visite Medicale': ['Date', 'Nom', 'Localisation_', 'statut', 'Remarque']
    }

    for motif in ['Visite Medicale', 'Osteopathie', 'Podologue']:
        st.write(f"**{motif}**")
        motif_data = weekly_data[weekly_data['Motif consultation'].str.lower() == motif.lower()]
        if not motif_data.empty:
            columns_to_display = motif_columns.get(motif, ['Nom', 'Remarque'])
            available_columns = [col for col in columns_to_display if col in motif_data.columns]
            
            # Formater la colonne 'Date' si elle est utilisée
            if 'Date' in available_columns and 'Date' in motif_data.columns:
                motif_data['Date'] = motif_data['Date'].dt.strftime('%d/%m/%Y')
            
            st.dataframe(motif_data[available_columns], use_container_width=True)
        else:
            st.write(f"Aucun cas de {motif} durant cette semaine.")