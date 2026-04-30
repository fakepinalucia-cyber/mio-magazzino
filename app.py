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
        # Convertiamo la colonna Quantità in numeri interi in modo sicuro
        df['Quantità'] = pd.to_numeric(df['Quantità'], errors='coerce').fillna(0).astype(int)

        # Aggiungiamo la colonna di stato con la soglia a 15
        df['Stato'] = df['Quantità'].apply(lambda x: '⚠️ In esaurimento' if x <= 15 else '✅ Buono')

        # --- RICERCA VELOCE ---
        st.subheader("🔍 Cerca nel Magazzino")
        search_query = st.text_input("Inserisci il nome del prodotto da cercare", "").lower()
        
        # Filtro ricerca
        mask = df.apply(lambda row: search_query in str(row['Nome']).lower(), axis=1)
        df_filtered = df[mask]

        # --- SCHEDE (TAB) PER CATEGORIA ---
        st.write("### 📋 Visualizza per Categoria")
        tab_titles = ["Tutti"] + CATEGORIE
        tabs = st.tabs(tab_titles)

        # Funzione per mostrare la tabella con priorità in alto
        def show_table(dataframe):
            if not dataframe.empty:
                # Ordiniamo per Quantità crescente (le quantità minori saranno in cima)
                df_sorted = dataframe.sort_values(by='Quantità', ascending=True)
                st.dataframe(df_sorted, use_container_width=True)
            else:
                st.info("Nessun prodotto trovato.")

        # Tab "Tutti"
        with tabs[0]:
            show_table(df_filtered)

        # Tab specifiche per categoria
        for i, cat in enumerate(CATEGORIE):
            with tabs[i+1]:
                df_cat = df_filtered[df_filtered['Categoria'] == cat]
                show_table(df_cat)

        # --- SIDEBAR: TUTTI I COMANDI ---
        st.sidebar.header("⚙️ Pannello di Controllo")

        # A. AGGIORNA QUANTITÀ (CARICO/SCARICO)
        with st.sidebar.expander("🔄 Carico/Scarico Merce"):
            lista_prodotti = df['Nome'].tolist()
            prod_scelto = st.selectbox("Seleziona Prodotto", lista_prodotti)
            azione = st.radio("Operazione", ["Aggiungi", "Sottrai"])
            quantita_var = st.number_input("Quantità da variare", min_value=1, step=1)
            
            if st.button("Conferma Movimento"):
                idx = df[df['Nome'] == prod_scelto].index[0]
                qty_attuale = int(df.at[idx, 'Quantità'])
                riga = idx + 2 # +1 per header, +1 perché gspread parte da 1
                
                nuova_qty = qty_attuale + quantita_var if azione == "Aggiungi" else qty_attuale - quantita_var
                
                if nuova_qty < 0:
                    st.error("⚠️ Errore: Scorte insufficienti!")
                else:
                    # AGGIORNAMENTO: La quantità è nella colonna 3 (C)
                    sh.update_cell(riga, 3, nuova_qty)
                    st.success(f"Aggiornato! Nuova Qty: {nuova_qty}")
                    st.rerun()

        # B. AGGIUNGI NUOVO ARTICOLO
        with st.sidebar.expander("➕ Nuovo Articolo"):
            with st.form("add_form"):
                n_cat = st.selectbox("Categoria", CATEGORIE)
                n_nome = st.text_input("Nome Prodotto")
                n_qty = st.number_input("Quantità Iniziale", min_value=0)
                
                if st.form_submit_button("Salva nel Database"):
                    # Salvataggio ordine: Categoria, Nome, Quantità
                    sh.append_row([n_cat, n_nome, n_qty])
                    st.success("Prodotto registrato!")
                    st.rerun()

        # C. ELIMINA ARTICOLO
        with st.sidebar.expander("🗑️ Elimina Prodotto"):
            prod_del = st.selectbox("Articolo da rimuovere", lista_prodotti, key="del_box")
            if st.button("Rimuovi Definitivamente"):
                idx_del = df[df['Nome'] == prod_del].index[0] + 2
                sh.delete_rows(int(idx_del))
                st.success("Eliminato!")
                st.rerun()

    else:
        st.warning("Il database è vuoto. Inserisci i titoli (Categoria, Nome, Quantità) nel Foglio Google.")

except Exception as e:
    st.error(f"⚠️ Errore critico: {e}")
