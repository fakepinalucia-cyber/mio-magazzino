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

CATEGORIE = ["Piramidale", "A Cuneo", "Elegance", "Pannelli Acustici", "Altro"]

try:
    sh = connect_to_sheet()
    rows = sh.get_all_records()
    df = pd.DataFrame(rows)

    if not df.empty:
        # --- SCHEDE (TAB) PER CATEGORIA ---
        st.subheader("🔍 Filtra per Categoria")
        
        # Creiamo i tab nella parte centrale
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "Tutti i Prodotti", "Piramidale", "A Cuneo", "Elegance", "Pannelli Acustici", "Altro"
        ])

        with tab1:
            st.dataframe(df, use_container_width=True)

        with tab2:
            df_pir = df[df['Categoria'] == "Piramidale"]
            if not df_pir.empty:
                st.dataframe(df_pir, use_container_width=True)
            else:
                st.info("Nessun prodotto in questa categoria.")

        with tab3:
            df_cun = df[df['Categoria'] == "A Cuneo"]
            if not df_cun.empty:
                st.dataframe(df_cun, use_container_width=True)
            else:
                st.info("Nessun prodotto in questa categoria.")

        with tab4:
            df_el = df[df['Categoria'] == "Elegance"]
            if not df_el.empty:
                st.dataframe(df_el, use_container_width=True)
            else:
                st.info("Nessun prodotto in questa categoria.")

        with tab5:
            df_pan = df[df['Categoria'] == "Pannelli Acustici"]
            if not df_pan.empty:
                st.dataframe(df_pan, use_container_width=True)
            else:
                st.info("Nessun prodotto in questa categoria.")
                
        with tab6:
            df_alt = df[df['Categoria'] == "Altro"]
            if not df_alt.empty:
                st.dataframe(df_alt, use_container_width=True)
            else:
                st.info("Nessun prodotto in questa categoria.")

        # --- SIDEBAR: TUTTI I COMANDI ---
        st.sidebar.header("⚙️ Pannello di Controllo")

        # A. AGGIORNA QUANTITÀ
        with st.sidebar.expander("🔄 Carico/Scarico Merce"):
            lista_prodotti = df['Nome'].tolist()
            prod_scelto = st.selectbox("Prodotto", lista_prodotti)
            azione = st.radio("Operazione", ["Aggiungi", "Sottrai"])
            quantita_var = st.number_input("Quantità", min_value=1, step=1)
            
            if st.button("Conferma Movimento"):
                idx = df[df['Nome'] == prod_scelto].index[0]
                qty_attuale = int(df.at[idx, 'Quantità'])
                riga = idx + 2
                nuova_qty = qty_attuale + quantita_var if azione == "Aggiungi" else qty_attuale - quantita_var
                
                if nuova_qty < 0:
                    st.error("⚠️ Scorta insufficiente!")
                else:
                    sh.update_cell(riga, 4, nuova_qty) # Colonna 4 è la Quantità
                    st.success("Aggiornato!")
                    st.rerun()

        # B. AGGIUNGI NUOVO ARTICOLO
        with st.sidebar.expander("➕ Nuovo Articolo"):
            with st.form("add_form"):
                n_id = st.number_input("ID", min_value=1)
                n_nome = st.text_input("Nome")
                n_cat = st.selectbox("Categoria", CATEGORIE)
                n_qty = st.number_input("Quantità Iniziale", min_value=0)
                if st.form_submit_button("Salva"):
                    sh.append_row([n_id, n_nome, n_cat, n_qty])
                    st.rerun()

        # C. ELIMINA
        with st.sidebar.expander("🗑️ Elimina"):
            prod_del = st.selectbox("Seleziona da eliminare", lista_prodotti, key="del")
            if st.button("Conferma Eliminazione"):
                idx_del = df[df['Nome'] == prod_del].index[0] + 2
                sh.delete_rows(int(idx_del))
                st.rerun()

    else:
        st.warning("Foglio vuoto o intestazioni mancanti.")

except Exception as e:
    st.error(f"Errore: {e}")
