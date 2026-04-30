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

        # Tab "Tutti" (mostra la lista ordinata per Categoria e poi per Nome)
        with tabs[0]:
            if not df_filtered.empty:
                df_sorted_all = df_filtered.sort_values(by=['Categoria', 'Nome'], ascending=True)
                st.dataframe(df_sorted_all, use_container_width=True)
            else:
                st.info("Nessun prodotto trovato.")

        # Tab specifiche per categoria (con priorità in alto in base alle quantità)
        for i, cat in enumerate(CATEGORIE):
            with tabs[i+1]:
                df_cat = df_filtered[df_filtered['Categoria'] == cat]
                if not df_cat.empty:
                    df_sorted = df_cat.sort_values(by='Quantità', ascending=True)
                    st.dataframe(df_sorted, use_container_width=True)
                else:
                    st.info(f"Nessun prodotto nella categoria {cat}")

        # --- SIDEBAR: TUTTI I COMANDI ---
        st.sidebar.header("⚙️ Pannello di Controllo")
        
        # 1. Carico/Scarico Merce
        st.sidebar.subheader("🔄 Carico/Scarico Merce")
        prod_carico = st.sidebar.selectbox("Seleziona Prodotto", df['Nome'].tolist(), key="c_prod")
        azione_carico = st.sidebar.radio("Operazione", ["Aggiungi", "Sottrai"], key="c_azione")
        qnt_carico = st.sidebar.number_input("Quantità da variare", min_value=1, step=1, key="c_qnt")
        
        if st.sidebar.button("Conferma Movimento", key="c_btn"):
            idx = df[df['Nome'] == prod_carico].index[0]
            qty_attuale = int(df.at[idx, 'Quantità'])
            riga = idx + 2 # +1 per header, +1 perché gspread parte da 1
            
            nuova_qty = qty_attuale + qnt_carico if azione_carico == "Aggiungi" else qty_attuale - qnt_carico
            
            if nuova_qty < 0:
                st.error("⚠️ Errore: Scorte insufficienti!")
            else:
                sh.update_cell(riga, 3, nuova_qty)
                st.success(f"Aggiornato! Nuova Qty: {nuova_qty}")
                st.rerun()

        st.sidebar.markdown("---")

        # 2. Nuovo Articolo
        st.sidebar.subheader("➕ Nuovo Articolo")
        with st.sidebar.form("add_form"):
            n_cat = st.selectbox("Categoria", CATEGORIE, key="n_cat")
            n_nome = st.text_input("Nome Prodotto", key="n_nome")
            n_qty = st.number_input("Quantità Iniziale", min_value=0, key="n_qty")
            
            if st.form_submit_button("Salva nel Database"):
                sh.append_row([n_cat, n_nome, n_qty])
                st.success("Prodotto registrato!")
                st.rerun()

        st.sidebar.markdown("---")

        # 3. Elimina prodotto
        st.sidebar.subheader("🗑️ Elimina Prodotto")
        prod_del = st.sidebar.selectbox("Articolo da rimuovere dal magazzino", df['Nome'].tolist(), key="del_prod")
        
        if st.sidebar.button("Rimuovi Definitivamente", key="del_btn"):
            idx_del = df[df['Nome'] == prod_del].index[0] + 2
            sh.delete_rows(int(idx_del))
            st.success("Eliminato dal magazzino!")
            st.rerun()

    else:
        st.warning("Il database è vuoto. Inserisci i titoli (Categoria, Nome, Quantità) nel Foglio Google.")

except Exception as e:
    st.error(f"⚠️ Errore critico: {e}")
