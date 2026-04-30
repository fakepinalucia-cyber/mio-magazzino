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
        
        # --- SIDEBAR: GESTIONE PRODOTTI ---
        st.sidebar.header("⚙️ Gestione Magazzino")

        # Sezione AGGIUNGI
        with st.sidebar.expander("➕ Aggiungi Nuovo"):
            with st.form("add_form"):
                new_id = st.number_input("ID", min_value=1, step=1)
                new_nome = st.text_input("Nome Prodotto")
                new_qty = st.number_input("Quantità", min_value=0, step=1)
                submitted = st.form_submit_button("Salva")
                
                if submitted:
                    sh.append_row([new_id, new_nome, new_qty])
                    st.success("Aggiunto!")
                    st.rerun() # Ricarica l'app per aggiornare la tabella

        # Sezione RIMUOVI
        with st.sidebar.expander("🗑️ Rimuovi Prodotto"):
            # Crea una lista di nomi per il menu a tendina
            lista_nomi = df['Nome'].tolist()
            prodotto_da_eliminare = st.selectbox("Seleziona prodotto da eliminare", lista_nomi)
            
            if st.button("Elimina Definitivamente"):
                try:
                    # Trova la riga corrispondente (aggiungiamo 2 perché il foglio Google parte da 1 e ha l'intestazione)
                    index_to_remove = df[df['Nome'] == prodotto_da_eliminare].index[0] + 2
                    sh.delete_rows(int(index_to_remove))
                    st.success(f"{prodotto_da_eliminare} eliminato!")
                    st.rerun() # Ricarica l'app
                except Exception as e:
                    st.error(f"Errore durante l'eliminazione: {e}")
            
            if submitted:
                sh.append_row([new_id, new_nome, new_qty])
                st.sidebar.success("Prodotto aggiunto! Ricarica la pagina.")
    else:
        st.warning("Il foglio è connesso ma è vuoto. Scrivi ID, Nome, Quantità nella prima riga del foglio Google.")

except Exception as e:
    st.error(f"Errore: {e}")
