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

# Definiamo le categorie fisse
CATEGORIE = ["Piramidale", "A Cuneo", "Elegance", "Pannelli Acustici", "Altro"]

try:
    sh = connect_to_sheet()
    rows = sh.get_all_records()
    df = pd.DataFrame(rows)

    if not df.empty:
        # --- TAB PER CATEGORIA ---
        st.subheader("📂 Filtra per Tipologia")
        
        # Creazione dei Tab
        nomi_tab = ["Tutti"] + CATEGORIE
        tabs = st.tabs(nomi_tab)

        # Tab "Tutti"
        with tabs[0]:
            st.dataframe(df, use_container_width=True)

        # Tab Dinamici per Categoria
        for i, cat in enumerate(CATEGORIE):
            with tabs[i+1]:
                df_filtrato = df[df['Categoria'] == cat]
                if not df_filtrato.empty:
                    st.dataframe(df_filtrato, use_container_width=True)
                else:
                    st.info(f"Nessun articolo nella categoria {cat}")

        # --- SIDEBAR: COMANDI ---
        st.sidebar.header("⚙️ Pannello di Controllo")

        # A. AGGIORNA QUANTITÀ
        with st.sidebar.expander("🔄 Carico/Scarico Merce"):
            lista_prodotti = df['Nome'].tolist()
            prod_scelto = st.selectbox("Seleziona Prodotto", lista_prodotti)
            azione = st.radio("Operazione", ["Aggiungi", "Sottrai"])
            quantita_var = st.number_input("Quantità", min_value=1, step=1)
            
            if st.button("Conferma Movimento"):
                idx = df[df['Nome'] == prod_scelto].index[0]
                qty_attuale = int(df.at[idx, 'Quantità'])
                riga = idx + 2 # +2 per compensare intestazione e indice 0
                
                nuova_qty = qty_attuale + quantita_var if azione == "Aggiungi" else qty_attuale - quantita_var
                
                if nuova_qty < 0:
                    st.error("⚠️ Attenzione: Scorta insufficiente!")
                else:
                    # AGGIORNAMENTO: La quantità è nella colonna 4 (D)
                    sh.update_cell(riga, 4, nuova_qty)
                    st.success(f"Aggiornato! Nuova Qty: {nuova_qty}")
                    st.rerun()

        # B. AGGIUNGI NUOVO ARTICOLO
        with st.sidebar.expander("➕ Nuovo Articolo"):
            with st.form("add_form"):
                n_id = st.number_input("ID", min_value=1)
                n_cat = st.selectbox("Categoria", CATEGORIE)
                n_nome = st.text_input("Nome")
                n_qty = st.number_input("Quantità Iniziale", min_value=0)
                if st.form_submit_button("Salva"):
                    # Ordine: ID, Categoria, Nome, Quantità
                    sh.append_row([n_id, n_cat, n_nome, n_qty])
                    st.rerun()

        # C. ELIMINA PRODOTTO
        with st.sidebar.expander("🗑️ Elimina"):
            prod_del = st.selectbox("Rimuovi prodotto", lista_prodotti, key="del")
            if st.button("Elimina per sempre"):
                idx_del = df[df['Nome'] == prod_del].index[0] + 2
                sh.delete_rows(int(idx_del))
                st.rerun()

    else:
        st.warning("Assicurati che il foglio abbia le intestazioni: ID, Categoria, Nome, Quantità")

except Exception as e:
    st.error(f"Si è verificato un errore: {e}")
