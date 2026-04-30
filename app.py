import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import base64

# Funzione per convertire il file SVG in base64 per mostrarlo correttamente in Streamlit
def render_svg(svg_file_path):
    with open(svg_file_path, "r", encoding="utf-8") as f:
        svg_content = f.read()
    b64 = base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")
    html = f'<img src="data:image/svg+xml;base64,{b64}" width="250">'
    return html

def render_svg_sidebar(svg_file_path):
    with open(svg_file_path, "r", encoding="utf-8") as f:
        svg_content = f.read()
    b64 = base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")
    html = f'<img src="data:image/svg+xml;base64,{b64}" width="180">'
    return html

# 1. CONNESSIONE
def connect_to_sheet():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    client = gspread.authorize(creds)
    return client.open("Dati_Magazzino").sheet1

st.set_page_config(page_title="Lenacustica - Magazzino", page_icon="⚙️", layout="wide")

# Visualizzazione Logo SVG in cima
try:
    st.markdown(render_svg("logo.svg"), unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("⚠️ File 'logo.svg' non trovato nella cartella del progetto. Carica il file nella stessa cartella dello script.")

st.title("Gestione Magazzino")

# Categorie (inclusa Spesa Ufficio)
CATEGORIE = ["Piramidale", "A Cuneo", "Elegance", "Pannelli Acustici", "Altro", "Spesa Ufficio"]

try:
    sh = connect_to_sheet()
    rows = sh.get_all_records()
    df = pd.DataFrame(rows)

    if not df.empty:
        # Conversione Quantità
        df['Quantità'] = pd.to_numeric(df['Quantità'], errors='coerce').fillna(0).astype(int)

        # Colonna di stato
        df['Stato'] = df['Quantità'].apply(lambda x: '⚠️ In esaurimento' if x <= 15 else '✅ Buono')

        # --- RICERCA VELOCE ---
        st.subheader("🔍 Cerca nel Magazzino")
        search_query = st.text_input("Inserisci il nome del prodotto da cercare", "").lower()
        
        mask = df.apply(lambda row: search_query in str(row['Nome']).lower(), axis=1)
        df_filtered = df[mask]

        # --- SCHEDE (TAB) PER CATEGORIA ---
        st.write("### 📋 Visualizza per Categoria")
        tab_titles = ["Tutti"] + CATEGORIE
        tabs = st.tabs(tab_titles)

        # Tab "Tutti" (Ordinato per Categoria e Nome)
        with tabs[0]:
            if not df_filtered.empty:
                df_sorted_all = df_filtered.sort_values(by=['Categoria', 'Nome'], ascending=True)
                st.dataframe(df_sorted_all, use_container_width=True)
            else:
                st.info("Nessun prodotto trovato.")

        # Tab specifiche per categoria
        for i, cat in enumerate(CATEGORIE):
            with tabs[i+1]:
                df_cat = df_filtered[df_filtered['Categoria'] == cat]
                if not df_cat.empty:
                    df_sorted = df_cat.sort_values(by='Quantità', ascending=True)
                    st.dataframe(df_sorted, use_container_width=True)
                else:
                    st.info(f"Nessun prodotto nella categoria {cat}")

        # --- SIDEBAR: PANNELLO DI CONTROLLO ---
        try:
            st.sidebar.markdown(render_svg_sidebar("logo.svg"), unsafe_allow_html=True)
        except FileNotFoundError:
            st.sidebar.warning("⚠️ Logo non trovato.")
            
        st.sidebar.header("⚙️ Pannello di Controllo")

        # 1. GESTIONE SPESA UFFICIO
        with st.sidebar.expander("🛒 Gestione Spesa Ufficio"):
            st.write("##### 🛒 Rimuovi prodotto acquistato")
            df_spesa = df[df['Categoria'] == "Spesa Ufficio"]
            if not df_spesa.empty:
                lista_spesa = df_spesa['Nome'].tolist()
                prod_da_rimuovere = st.selectbox("Seleziona prodotto acquistato", lista_spesa, key="sel_acq")
                if st.button("Rimuovi dalla Lista", key="btn_acq"):
                    idx_del = df[df['Nome'] == prod_da_rimuovere].index[0] + 2
                    sh.delete_rows(int(idx_del))
                    st.success("Acquistato e rimosso!")
                    st.rerun()
            else:
                st.info("Lista spesa vuota.")

            st.markdown("---")
            st.write("##### ➕ Aggiungi alla lista spesa")
            with st.form("spesa_form_unito"):
                n_nome_spesa = st.text_input("Nome del prodotto mancante")
                n_qty_spesa = st.number_input("Quantità da acquistare", min_value=1, value=1, step=1)
                if st.form_submit_button("Salva nella Lista"):
                    sh.append_row(["Spesa Ufficio", n_nome_spesa, n_qty_spesa])
                    st.success("Aggiunto alla spesa!")
                    st.rerun()

        # 2. AGGIORNA QUANTITÀ
        with st.sidebar.expander("🔄 Carico/Scarico Merce"):
            lista_prodotti = df['Nome'].tolist()
            prod_scelto = st.selectbox("Seleziona Prodotto", lista_prodotti)
            azione = st.radio("Operazione", ["Aggiungi", "Sottrai"])
            quantita_var = st.number_input("Quantità da variare", min_value=1, step=1)
            
            if st.button("Conferma Movimento"):
                idx = df[df['Nome'] == prod_scelto].index[0]
                qty_attuale = int(df.at[idx, 'Quantità'])
                riga = idx + 2
                nuova_qty = qty_attuale + quantita_var if azione == "Aggiungi" else qty_attuale - quantita_var
                
                if nuova_qty < 0:
                    st.error("⚠️ Scorte insufficienti!")
                else:
                    sh.update_cell(riga, 3, nuova_qty)
                    st.success(f"Aggiornato! Qty: {nuova_qty}")
                    st.rerun()

        # 3. AGGIUNGI NUOVO ARTICOLO
        with st.sidebar.expander("➕ Nuovo Articolo"):
            with st.form("add_form"):
                n_cat = st.selectbox("Categoria", CATEGORIE)
                n_nome = st.text_input("Nome Prodotto")
                n_qty = st.number_input("Quantità Iniziale", min_value=0)
                if st.form_submit_button("Salva nel Database"):
                    sh.append_row([n_cat, n_nome, n_qty])
                    st.success("Registrato!")
                    st.rerun()

        # 4. ELIMINA ARTICOLO
        with st.sidebar.expander("🗑️ Elimina Prodotto"):
            prod_del = st.selectbox("Articolo da rimuovere", df['Nome'].tolist(), key="del_box")
            if st.button("Rimuovi Definitivamente"):
                idx_del = df[df['Nome'] == prod_del].index[0] + 2
                sh.delete_rows(int(idx_del))
                st.success("Eliminato!")
                st.rerun()

    else:
        st.warning("Database vuoto.")

except Exception as e:
    st.error(f"⚠️ Errore critico: {e}")
