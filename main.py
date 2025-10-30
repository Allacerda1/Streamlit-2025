import streamlit as st
import pandas as pd
import requests
import datetime

# Criando uma função para buscar os dados da Selic via API. 
@st.cache_data(ttl="1day")
def get_selic():
    url = "https://bcb.gov.br/api/servico/sitebcb/historicotaxasjuros"
    resp = requests.get(url)
    df = pd.DataFrame(resp.json()["conteudo"])
    df["DataInicioVigencia"] = pd.to_datetime(df["DataInicioVigencia"]).dt.date
    df["DataFimVigencia"] = pd.to_datetime(df["DataFimVigencia"]).dt.date
    df["DataFimVigencia"] = df["DataFimVigencia"].fillna(datetime.datetime.today().date())
    return df

    # Criando Estatística Básicas.
def calc_estatistica_geral(df):
    df_data = df.groupby(by="Data")[["Valor"]].sum()
    df_data["lag_1"] = df_data["Valor"].shift(1)
    df_data["Diferença Mensal"] = df_data["Valor"] - df_data["lag_1"]
    df_data["Média 6M Diferença Abs."] = df_data["Diferença Mensal"].rolling(6).mean()
    df_data["Média 12M Diferença Abs."] = df_data["Diferença Mensal"].rolling(12).mean()
    df_data["Diferença Mensal Relativa"] = df_data["Diferença Mensal"] / df_data["lag_1"] - 1

    # ✅ Correção dos avisos
    df_data["Evolução 6M Total"] = df_data["Valor"].rolling(6).apply(lambda x: x.iloc[-1] - x.iloc[0])
    df_data["Evolução 12M Total"] = df_data["Valor"].rolling(12).apply(lambda x: x.iloc[-1] - x.iloc[0])
    df_data["Evolução 6M Relativa"] = df_data["Evolução 6M Total"].rolling(6).apply(lambda x: x.iloc[-1] - x.iloc[0] - 1)
    df_data["Evolução 12M Relativa"] = df_data["Evolução 12M Total"].rolling(12).apply(lambda x: x.iloc[-1] - x.iloc[0] - 1)

    df_data = df_data.drop(columns=["lag_1"])
    return df_data


def main_metas():
        col1, col2 = st.columns(2)

        data_inicio_meta = col1.date_input("Data de Início da Meta", max_value=df_status.index.max())

        data_filtrada = df_status.index[df_status.index <= data_inicio_meta][-1]

        custos_fixos = col1.number_input("Custos Fixos", min_value=0., format="%.2f")

        salario_bruto = col2.number_input("Salário Bruto", min_value=0., format="%.2f")
        salario_liquido = col2.number_input("Salário Liquido", min_value=0., format="%.2f")

        valor_inicio = df_status.loc[data_filtrada]["Valor"]
        col1.markdown(f"Valor do Inicio da Meta: R$ {valor_inicio:.2f}")

        selic_gov = get_selic()
        filtro_selic_data = (selic_gov["DataInicioVigencia"] <= data_inicio_meta) & (selic_gov["DataFimVigencia"] >= data_inicio_meta)
        selic_default = selic_gov[filtro_selic_data]["MetaSelic"].iloc[0]

        selic = st.number_input("Selic", min_value=selic_default, format="%.2f")
        selic_ano = selic / 100
        selic_mes = (selic_ano + 1)**(1/12) - 1

        rendimento_ano = valor_inicio * selic_ano
        rendimento_mes = valor_inicio * selic_mes

        col1_pot, col2_pot = st.columns(2)
        mensal = salario_liquido - custos_fixos + valor_inicio * selic_mes
        anual = 12*(salario_liquido - custos_fixos) + valor_inicio *selic_mes

        with col1_pot.container(border=True):
            st.markdown(f"Potencial Arrecadação Mês:\n\n R$ {mensal:.2f}", help=f"{salario_liquido:.2f} + (-{custos_fixos:.2f}) + {rendimento_mes:.2f}")
        
        with col2_pot.container(border=True):
            st.markdown(f"Potencial Arrecadação Anual:\n\n R$ {anual:.2f}", help=f" 12*({salario_liquido:.2f} + (-{custos_fixos:.2f})) + {rendimento_ano:.2f}")

        with st.container(border=True):
            col1_meta, col2_meta = st.columns(2)
            with col1_meta:
                meta_estipulada = st.number_input("Meta Estipulada Mensal", min_value=-999999999., format="%.2f", value=mensal)

            with col2_meta:
                patrimonio_final = meta_estipulada + valor_inicio
                st.markdown(f"Patrimônio Estimado pós Meta:\n\n R$ {patrimonio_final:.2f}")

        with st.container(border=True):
            col1_meta, col2_meta = st.columns(2)
            with col1_meta:
                meta_estipulada = st.number_input("Meta Estipulada Anual", min_value=-999999999., format="%.2f", value=anual)

            with col2_meta:
                patrimonio_final = meta_estipulada + valor_inicio
                st.markdown(f"Patrimônio Estimado pós Meta:\n\n R$ {patrimonio_final:.2f}")
        return data_inicio_meta, valor_inicio, meta_estipulada, patrimonio_final

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

    dados3 = st.expander("📋 Estatística Geral", expanded=False)
    # Cria tabela de estatística geral
    df_status = calc_estatistica_geral(df)
    # Formatar colunas em R$ e %
    coluna_formatada = {
         "Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
         "Diferença Mensal": st.column_config.NumberColumn("Diferença Mensal", format="R$ %.2f"),
         "Média 6M Diferença Abs.": st.column_config.NumberColumn("Média 6M Diferença Abs.", format="R$ %.2f"),
         "Média 12M Diferença Abs.": st.column_config.NumberColumn("Média 12M Diferença Abs.", format="R$ %.2f"),
         "Evolução 6M Total": st.column_config.NumberColumn("Evolução 6M Total", format="R$ %.2f"),
         "Evolução 12M Total": st.column_config.NumberColumn("Evolução 12M Total", format="R$ %.2f"),
         "Diferença Mensal Relativa": st.column_config.NumberColumn("Diferença Mensal Relativa", format="percent"),
         "Evolução 6M Relativa": st.column_config.NumberColumn("Evolução 6M Relativa", format="percent"),
         "Evolução 12M Relativa": st.column_config.NumberColumn("Evolução 12M Relativa", format="percent"),
    }

    tab_status,tab_abs, tab_rel = dados3.tabs(["📝 Dados", "📊 Histórico Evolução", "📊 Crecimento Relativo"])

    with tab_status:
     st.dataframe(df_status, column_config=coluna_formatada)
    
    with tab_abs:
        abs_colns = ["Diferença Mensal", "Média 6M Diferença Abs.", "Média 12M Diferença Abs."]
        st.line_chart(df_status[abs_colns])

    with tab_rel:
        rel_colns = ["Diferença Mensal Relativa", "Evolução 6M Relativa", "Evolução 12M Relativa"]
        st.line_chart(df_status[rel_colns])
        
    with st.expander("Metas", expanded=False):

        tab_main, tab_main_data, tab_grafh = st.tabs(tabs=["🔁 Configuração", "📝 Dados", "📊 Gráficos"])

        with tab_main:
            data_inicio_meta, valor_inicio, meta_estipulada, patrimonio_final = main_metas()

        with tab_main_data:
            meses = pd.DataFrame({
                "Data Referência":[(data_inicio_meta + pd.DateOffset(months=i)) for i in range(1,13)],
                "Meta Mensal":[valor_inicio + round(meta_estipulada/12, 2) * i for i in range(1,13)],})
        
        meses["Data Referência"] = meses["Data Referência"].dt.strftime("%Y-%m")
        df_patrimonio = df_status.reset_index()[["Data", "Valor"]]
        df_patrimonio["Data Referência"] = pd.to_datetime(df_patrimonio["Data"]).dt.strftime("%Y-%m")
        meses = meses.merge(df_patrimonio, how="left", on="Data Referência")

        meses = meses[["Data Referência", "Meta Mensal", "Valor"]]
        meses["Atingimento (%)" ] = meses["Valor"] / meses["Meta Mensal"]
        meses["Atingimento Ano" ] = meses["Valor"] / patrimonio_final
        meses["Atingimento Esperado" ] = meses["Meta Mensal"] / patrimonio_final
        meses = meses.set_index("Data Referência")

        coluna_meses = {
                "Meta Mensal": st.column_config.NumberColumn("Meta Mensal", format="R$ %.2f"),
                "Valor": st.column_config.NumberColumn("Valor Atingido", format="R$ %.2f"),
                "Atingimento (%)": st.column_config.NumberColumn("Atingimento (%)", format="percent"),
                "Atingimento Ano": st.column_config.NumberColumn("Atingimento Ano", format="percent"),
                "Atingimento Esperado": st.column_config.NumberColumn("Atingimento Esperado", format="R$ %.2f"),
            }
        st.dataframe(meses, column_config=coluna_meses)

        with tab_grafh:
            st.line_chart(meses[["Atingimento Ano", "Atingimento Esperado"]])
        
     
