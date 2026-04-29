# --- RIGA 1: Le importazioni (Sempre in cima) ---
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# --- RIGA 7-15: La funzione di connessione SICURA ---
def connect_to_sheet():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # Prende i dati dai "Secrets" di Streamlit, non dal codice!
    creds_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    
    client = gspread.authorize(creds)
    return client.open("Dati_Magazzino").sheet1

# --- DA QUI IN POI: Il resto del programma ---
st.title("📦 Gestione Magazzino")

try:
    sh = connect_to_sheet()
    st.success("Connessione OK!") # <--- Aggiungi questa
    
    # Prova a leggere i dati e stampali "grezzi"
    data = sh.get_all_records()
    st.write("Dati letti dal foglio:", data) # <--- Aggiungi questa
    
except Exception as e:
    st.error(f"Errore: {e}")
except Exception as e:
    st.error(f"Errore di configurazione: {e}")
