import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. CONNESSIONE (Identica a prima)
def connect_to_sheet():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    client = gspread.authorize(creds)
    return client.open("Dati_Magazzino").sheet1

st.set_page_config(page_title="Magazzino Pro", layout="wide")
st.title("📦 Gestione Magazzino")

try:
    sh = connect_to_sheet()
    rows = sh.get_all_records()
    df = pd.DataFrame(rows)

    if not df.empty:
        # --- BARRA DI RICERCA ---
        st.subheader("🔍 Cerca Prodotto")
        search_query = st.text_input("Inserisci nome o ID per filtrare la tabella", "").lower()

        # Filtro dinamico
        mask = df.apply(lambda row: search_query in str(row['Nome']).lower() or 
                                    search_query in str(row['ID']).lower(), axis=1)
        df_filtered = df[mask]

        # Visualizzazione Tabella
        st.dataframe(df_filtered, use_container_width=True)
        
        # --- SIDEBAR: AGGIUNGI E RIMUOVI ---
        st.sidebar.header("⚙️ Pannello di Controllo")

        # AGGIUNGI
        with st.sidebar.expander("➕ Aggiungi Nuovo"):
            with st.form("add_form"):
                new_id = st.number_input("ID", min_value=1, step=1)
                new_nome = st.text_input("Nome Prodotto")
                new_qty = st.number_input("Quantità", min_value=0, step=1)
                submitted = st.form_submit_button("Salva")
                if submitted:
                    sh.append_row([new_id, new_nome, new_qty])
                    st.success("Aggiunto!")
                    st.rerun()

        # RIMUOVI
        with st.sidebar.expander("🗑️ Rimuovi Prodotto"):
            lista_nomi = df['Nome'].tolist()
            prodotto_da_eliminare = st.selectbox("Seleziona prodotto", lista_nomi)
            if st.button("Elimina Definitivamente"):
                index_to_remove = df[df['Nome'] == prodotto_da_eliminare].index[0] + 2
                sh.delete_rows(int(index_to_remove))
                st.success("Eliminato!")
                st.rerun()
    else:
        st.warning("Il foglio è vuoto. Aggiungi i titoli ID, Nome, Quantità su Google Sheets.")

except Exception as e:
    st.error(f"Si è verificato un errore: {e}")
