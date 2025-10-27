import streamlit as st
import pandas as pd

# Configurações do app
st.set_page_config(page_title="Finanças", page_icon=":moneybag:", layout="centered")

st.markdown("""
# Seja Bem-Vindo ao Finanças!

## Seu APP de finanças pessoais!

Espero que você tenha uma ótima experiência com nossa solução para finanças pessoais!
""")

# Upload do CSV
arquivo = st.file_uploader("Faça upload dos dados do seu arquivo CSV aqui!", type=["csv"])

if arquivo:
    # Leitura segura do CSV
    df = pd.read_csv(arquivo)

    # Conversão robusta da coluna Data
    df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y").dt.date

    # Exibe tabela principal
    dados1 = st.expander("📋 Tabela de Dados Principal", expanded=False)
    with dados1:
        valores = {"Valor": st.column_config.NumberColumn("Valor", format="R$ %f")}
        st.dataframe(df,hide_index=True, column_config=valores)

    # Cria tabela pivô garantindo índice datetime
    dados2 = st.expander("📋 Resumo Instituição", expanded=False)
    df_instituicao = df.pivot_table(index="Data", columns="Instituição", values="Valor")

    tab_data, tab_history, tab_share = dados2.tabs(["📅 Dados", "📈 Histórico", "📊 Comparar"])

    with tab_data:
        st.dataframe(df_instituicao)

    with tab_history:
        st.line_chart(df_instituicao)

    with tab_share:
        data = st.selectbox("Selecione uma data", options= df_instituicao.index) 
        st.bar_chart(df_instituicao.loc[data])
