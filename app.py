try:
    sh = connect_to_sheet()
    
    # 1. Leggi i dati dal foglio
    rows = sh.get_all_records()
    df = pd.DataFrame(rows)

    if not df.empty:
        st.subheader("📊 Inventario Attuale")
        # Mostra la tabella in modo elegante
        st.dataframe(df, use_container_width=True)
        
        # 2. Sidebar per aggiungere prodotti
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
        st.warning("Il foglio è connesso ma sembra vuoto. Aggiungi i titoli (ID, Nome, Quantità) nella prima riga del Foglio Google.")

except Exception as e:
    st.error(f"Errore durante la lettura: {e}")lio:", data) # <--- Aggiungi questa
    
except Exception as e:
    st.error(f"Errore: {e}")
except Exception as e:
    st.error(f"Errore di configurazione: {e}")
