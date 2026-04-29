# --- RIGA 1: Le importazioni (Sempre in cima) ---
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. FUNZIONE DI CONNESSIONE (Lasciala come l'abbiamo scritta prima)
def connect_to_sheet():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    client = gspread.authorize(creds)
    return client.open("Dati_Magazzino").sheet1

st.title("📦 Gestione Magazzino")

# 2. INCOLLA QUI IL NUOVO BLOCCO
try:
    sh = connect_to_sheet()
    
    # Leggi i dati
    rows = sh.get_all_records()
    df = pd.DataFrame(rows)

    if not df.empty:
        st.subheader("📊 Inventario Attuale")
        st.dataframe(df, use_container_width=True)
        
        # Sidebar per aggiungere prodotti
        st.sidebar.header("➕ Aggiungi Prodotto")
        with st.sidebar.form("add_form"):
            new_id = st.number_input("ID", min_value=1, step=1)
            new_nome = st.text_input("Nome Prodotto")
            new_qty = st.number_input("Quantità", min_value=0, step=1)
            submitted = st.form_submit_button("Salva nel Foglio")
            
            if submitted:
                sh.append_row([new_id, new_nome, new_qty])
                st.sidebar.success("Prodotto aggiunto! Ricarica la pagina.")
    else:
        st.warning("Il foglio è connesso ma è vuoto. Scrivi ID, Nome, Quantità nella prima riga del foglio Google.")

except Exception as e:
    st.error(f"Errore: {e}")

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
