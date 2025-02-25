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
logo_url = 'https://raw.githubusercontent.com/FC-Versailles/care/main/assets/Versailles.png'
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
    player_data = df[(df['Nom'] == player_name) & (df['Motif consultation'].str.lower() != 'blessure')]
    st.write(f"Historique Médical de {player_name}")
    st.dataframe(player_data[['Date', 'Motif consultation', 'Localisation du soin', 'Remarque']], use_container_width=True, height=500)
    
    # Create a second dataframe only for 'blessure' consultations
    blessure_data = df[(df['Nom'] == player_name) & (df['Motif consultation'].str.lower() == 'blessure')]
    if not blessure_data.empty:
        st.write(f"Historique des Blessures de {player_name}")
        st.dataframe(blessure_data[['Date', 'Type de journee','Contexte de blessure','Type de blessure',
                                  'Localisation','Position ','Recidive','Mecanisme','Remarque']], use_container_width=True)

elif page == "Rappport de blessure":
    st.title("Rapport de Blessure")
    injury_data = df[df['Motif consultation'].str.lower() == 'blessure']
    st.dataframe(injury_data[['Nom', 'Date', 'Type de journee','Contexte de blessure','Type de blessure',
                              'Localisation','Position ','Recidive','Mecanisme','Remarque']].head(20), use_container_width=True,height=500)
    

elif page == "Rapport Quotidien":
    st.title("Rapport Quotidien")
    selected_date = st.selectbox("Select Date", sorted(df['Date'].unique(), reverse=True))
    daily_data = df[df['Date'] == selected_date]
    
    for motif in ['Absent', 'Adaptation', 'Maladie', 'Réathlétisation','Prévention','Renforcement', 'Soins']:
        st.write(f"**{motif}**")
        motif_data = daily_data[daily_data['Motif consultation'].str.lower() == motif.lower()]
        if not motif_data.empty:
            st.dataframe(motif_data[['Nom', 'Localisation du soin', 'Remarque']], use_container_width=True)
        else:
            st.write(f"Aucun cas de {motif} pour la date sélectionnée.")
            
elif page == "Bilan Médical":
    st.title("Bilan Médical")
    selected_date = st.selectbox("Select Date", sorted(df['Date'].unique(), reverse=True))
    daily_data = df[df['Date'] == selected_date]
    
    for motif in ['Visite Médicale', 'Osteopathie', 'Podologue']:
        st.write(f"**{motif}**")
        motif_data = daily_data[daily_data['Motif consultation'].str.lower() == motif.lower()]
        if not motif_data.empty:
            st.dataframe(motif_data[['Nom', 'Remarque']], use_container_width=True)
        else:
            st.write(f"Aucun cas de {motif} pour la date sélectionnée.")

