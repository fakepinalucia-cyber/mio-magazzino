import streamlit as st
import pandas as pd
from gspread_pandas import Spread
import os

st.set_page_config(page_title="Magazzino Semplice", layout="centered")

st.title("📦 Gestione Magazzino")

# Connessione a Google Sheets
@st.cache_resource
def connect_to_sheet():
    # 'Dati_Magazzino' è il nome del file su Google Drive
    return Spread("Dati_Magazzino")

try:
    spread = connect_to_sheet()
    df = spread.sheet_to_df(index=0)
except Exception as e:
    st.error("Connessione non riuscita. Verifica di aver condiviso il foglio con l'email del file JSON.")
    st.stop()

menu = ["Inventario", "Nuovo Prodotto", "Carico/Scarico"]
choice = st.sidebar.selectbox("Cosa vuoi fare?", menu)

# --- SEZIONE INVENTARIO ---
if choice == "Inventario":
    st.subheader("Scorte in tempo reale")
    if df.empty:
        st.info("Il magazzino è vuoto. Aggiungi un prodotto per iniziare.")
    else:
        for index, row in df.iterrows():
            with st.container():
                col1, col2 = st.columns([1, 3])
                with col1:
                    if row['URL_Foto']:
                        st.image(row['URL_Foto'], width=100)
                    else:
                        st.write("📷 No foto")
                with col2:
                    st.write(f"### {row['Nome']}")
                    st.write(f"**Quantità:** {row['Quantita']} unità (ID: {row['ID']})")
                st.divider()

# --- SEZIONE NUOVO PRODOTTO ---
elif choice == "Nuovo Prodotto":
    st.subheader("Registra un nuovo articolo")
    with st.form("form_nuovo"):
        id_p = st.text_input("Codice ID")
        nome = st.text_input("Nome Prodotto")
        foto = st.file_uploader("Scatta o allega foto", type=['jpg', 'png', 'jpeg'])
        
        if st.form_submit_button("Aggiungi al Magazzino"):
            if id_p and nome:
                # Nota: qui andrebbe la logica di upload su Google Drive per ottenere l'URL
                # Per ora inseriamo un placeholder per l'URL_Foto
                nuovo_item = pd.DataFrame([[id_p, nome, 0, ""]], columns=df.columns)
                updated_df = pd.concat([df, nuovo_item], ignore_index=True)
                spread.df_to_sheet(updated_df, index=False, replace=True)
                st.success(f"Prodotto '{nome}' aggiunto con successo!")
                st.rerun()
            else:
                st.warning("ID e Nome sono obbligatori.")

# --- SEZIONE CARICO E SCARICO ---
elif choice == "Carico/Scarico":
    st.subheader("Aggiorna quantità")
    if df.empty:
        st.error("Nessun prodotto disponibile.")
    else:
        nome_scelto = st.selectbox("Seleziona il prodotto", df['Nome'].tolist())
        operazione = st.radio("Operazione", ["Carico (+)", "Scarico (-)"])
        quant = st.number_input("Quanti pezzi?", min_value=1, step=1)
        
        if st.button("Conferma Movimento"):
            idx = df.index[df['Nome'] == nome_scelto].tolist()[0]
            attuale = int(df.at[idx, 'Quantita'])
            
            if operazione == "Carico (+)":
                df.at[idx, 'Quantita'] = attuale + quant
                st.success(f"Caricato! Nuova giacenza: {attuale + quant}")
            else:
                if attuale >= quant:
                    df.at[idx, 'Quantita'] = attuale - quant
                    st.warning(f"Scaricato! Nuova giacenza: {attuale - quant}")
                else:
                    st.error(f"Errore: Disponibilità insufficiente ({attuale} pezzi).")
            
            spread.df_to_sheet(df, index=False, replace=True)