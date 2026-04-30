import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. CONNESSIONE
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
        # --- PARTE ALTA: RICERCA ---
        st.subheader("🔍 Cerca Prodotto")
        search_query = st.text_input("Inserisci nome o ID per filtrare", "").lower()
        mask = df.apply(lambda row: search_query in str(row['Nome']).lower() or 
                                    search_query in str(row['ID']).lower(), axis=1)
        df_filtered = df[mask]
        st.dataframe(df_filtered, use_container_width=True)
        
        # --- SIDEBAR: TUTTI I COMANDI ---
        st.sidebar.header("⚙️ Pannello di Controllo")

        # A. AGGIORNA QUANTITÀ (CARICO/SCARICO)
        with st.sidebar.expander("🔄 Carico/Scarico Merce"):
            lista_prodotti = df['Nome'].tolist()
            prod_scelto = st.selectbox("Prodotto", lista_prodotti)
            azione = st.radio("Cosa vuoi fare?", ["Aggiungi", "Sottrai"])
            quantita_var = st.number_input("Quantità", min_value=1, step=1)
            
            if st.button("Conferma Movimento"):
                idx = df[df['Nome'] == prod_scelto].index[0]
                qty_attuale = int(df.at[idx, 'Quantità'])
                riga = idx + 2
                
                nuova_qty = qty_attuale + quantita_var if azione == "Aggiungi" else qty_attuale - quantita_var
                
                if nuova_qty < 0:
                    st.error("⚠️ Scorta insufficiente!")
                else:
                    sh.update_cell(riga, 3, nuova_qty) # Colonna 3 è la Quantità
                    st.success(f"Fatto! Nuova Qty: {nuova_qty}")
                    st.rerun()

        # B. AGGIUNGI NUOVO ARTICOLO
        with st.sidebar.expander("➕ Nuovo Articolo"):
            with st.form("add_form"):
                n_id = st.number_input("ID", min_value=1)
                n_nome = st.text_input("Nome")
                n_qty = st.number_input("Quantità Iniziale", min_value=0)
                if st.form_submit_button("Salva"):
                    sh.append_row([n_id, n_nome, n_qty])
                    st.rerun()

        # C. ELIMINA DEFINITIVAMENTE
        with st.sidebar.expander("🗑️ Elimina"):
            prod_del = st.selectbox("Seleziona da eliminare", lista_prodotti, key="del")
            if st.button("Elimina per sempre"):
                idx_del = df[df['Nome'] == prod_del].index[0] + 2
                sh.delete_rows(int(idx_del))
                st.rerun()

    else:
        st.warning("Foglio vuoto o intestazioni mancanti.")

except Exception as e:
    st.error(f"Errore: {e}")
