import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import locale
import numpy as np

st.set_page_config(layout="wide")

# Tenta definir o locale para pt_BR, mas formatação customizada será usada abaixo
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    locale.setlocale(locale.LC_ALL, '')

xlsx_path = "kpis_energia_por_unidade.xlsx"

@st.cache_data
def carregar_dados_fotovoltaico():
    df = pd.read_excel(xlsx_path)
    colunas_geracao = df.columns[1:-2].tolist()
    coluna_tarifa = df.columns[-2]
    coluna_gee = df.columns[-1]
    df_melt = df.melt(id_vars=["Tempo", coluna_tarifa, coluna_gee],
                      value_vars=colunas_geracao,
                      var_name="Unidade",
                      value_name="Geração (kWh)")
    df_melt["Tempo"] = pd.to_datetime(df_melt["Tempo"])
    df_melt["Ano"] = df_melt["Tempo"].dt.year
    df_melt["Mês"] = df_melt["Tempo"].dt.strftime("%b")
    df_melt["Geração (kWh)"] = pd.to_numeric(df_melt["Geração (kWh)"], errors="coerce")
    df_melt[coluna_tarifa] = pd.to_numeric(df_melt[coluna_tarifa], errors="coerce")
    df_melt[coluna_gee] = pd.to_numeric(df_melt[coluna_gee], errors="coerce")
    df_melt["Receita (R$)"] = df_melt["Geração (kWh)"] * df_melt[coluna_tarifa]
    df_melt["Redução GEE (tCO2)"] = (df_melt["Geração (kWh)"] / 1000) * df_melt[coluna_gee]
    df_melt.rename(columns={coluna_tarifa: "Tarifa (R$/kWh)"}, inplace=True)
    return df_melt

@st.cache_data
def carregar_dados_onibus(nome_aba):
    df = pd.read_excel(xlsx_path, sheet_name=nome_aba)
    df.columns = df.columns.str.strip()
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"])
    return df

def format_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_num(valor, casas=2):
    formato = f":,.{casas}f"
    return f"{valor{formato}}".replace(",", "X").replace(".", ",").replace("X", ".")

cores = {
    "Rodoviário": "#2563eb",  # Azul
    "Urbano": "#059669"       # Verde
}
icons = {
    "Rodoviário": "🚌 Rodoviário",
    "Urbano": "🚍 Urbano"
}

aba_principal = st.sidebar.radio(
    "Escolha o tema:",
    ["Mobilidade Elétrica", "Sistemas Fotovoltaicos"]
)

if aba_principal == "Mobilidade Elétrica":
    sub_aba = st.sidebar.radio("Mobilidade Elétrica", ["Rodoviário", "Urbano"])
    df_onibus = carregar_dados_onibus(sub_aba)
    cor_tema = cores[sub_aba]
    emoji = icons[sub_aba]

    # Título padrão branco centralizado
    st.markdown(
        f"<h2 style='color:white; text-align:center; font-weight:bold;'>{emoji} — Mobilidade Elétrica</h2>", 
        unsafe_allow_html=True
    )
    st.markdown(
        f"<h4 style='color:white; text-align:center; font-weight:bold;'>Relatório detalhado do ônibus {sub_aba}</h4>",
        unsafe_allow_html=True
    )

    # KPIs principais
    col1, col2, col3 = st.columns(3)
    col1.metric("Total km Rodados", format_num(df_onibus["km"].sum(), 0))
    col2.metric("Consumo Total (kWh)", format_num(df_onibus["kWh"].sum(), 0))
    col3.metric("Dias de Operação", format_num(df_onibus["Dias"].sum(), 0))

    st.divider()   # LINHA PADRÃO ENTRE OS BLOCOS

    # KPIs secundários (compactos)
    colA, colB = st.columns(2)
    with colA:
        economia = df_onibus["Economia"].sum()
        energia = df_onibus["Gasto em Energia Elétrica"].sum()
        colA.metric("Economia Total (R$)", format_real(economia))
        colA.metric("Gasto em Energia Elétrica (R$)", format_real(energia))
    with colB:
        diesel = df_onibus["Gasto em Diesel"].sum()
        colB.metric("Gasto em Diesel (R$)", format_real(diesel))
        if df_onibus["Percentual de Redução"].notnull().any():
            percentual = df_onibus["Percentual de Redução"].dropna().mean()
            # Ajuste para casos em que percentual está em fração ou já em %
            if percentual > 1:
                percentual_formatado = f"{percentual:,.2f}%"
            else:
                percentual_formatado = f"{percentual*100:,.2f}%"
            percentual_formatado = percentual_formatado.replace(",", "X").replace(".", ",").replace("X", ".")
            colB.metric("Percentual de Redução de GEE (%)", percentual_formatado)
        else:
            colB.metric("Percentual de Redução de GEE (%)", "N/A")

    st.divider()

    st.markdown(
        "<h4 style='color:white; text-align:center; font-weight:bold;'>Gráficos Mensais</h4>",
        unsafe_allow_html=True
    )
    fig1 = px.bar(df_onibus, x="Mês", y="kWh", title="Consumo de Energia Mensal (kWh)", color_discrete_sequence=[cor_tema])
    fig2 = px.bar(df_onibus, x="Mês", y="km", title="Distância Percorrida por Mês (km)", color_discrete_sequence=[cor_tema])
    fig3 = px.bar(df_onibus, x="Mês", y="Economia", title="Economia Mensal (R$)", color_discrete_sequence=[cor_tema])
    st.plotly_chart(fig1, use_container_width=True)
    st.plotly_chart(fig2, use_container_width=True)
    st.plotly_chart(fig3, use_container_width=True)

    st.divider()
    st.markdown(
        "<h4 style='color:white; text-align:center; font-weight:bold;'>Correlação entre Consumo e Distância</h4>",
        unsafe_allow_html=True
    )
    df_corr = df_onibus.dropna(subset=["kWh", "km"])
    if not df_corr.empty:
        fig_corr = px.scatter(
            df_corr, x="km", y="kWh",
            trendline="ols",
            title="Correlação: Consumo de Energia vs Distância Percorrida",
            labels={"km": "Distância Percorrida (km)", "kWh": "Consumo de Energia (kWh)"},
            color_discrete_sequence=[cor_tema]
        )
        st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.info("Não há dados suficientes para plotar a correlação.")

elif aba_principal == "Sistemas Fotovoltaicos":
    aba_fv = st.sidebar.radio(
        "Sistemas Fotovoltaicos",
        ["Sistemas Analisados", "Geral"]
    )
    df = carregar_dados_fotovoltaico()
    if aba_fv == "Sistemas Analisados":
        st.markdown(
            "<h2 style='color:white; text-align:center; font-weight:bold;'>📊 Sistemas Fotovoltaicos - Sistemas Analisados</h2>",
            unsafe_allow_html=True
        )
        unidade = st.selectbox("Selecione a Unidade:", df['Unidade'].unique())
        df_u = df[df['Unidade'] == unidade]

        # KPIs principais
        col1, col2 = st.columns(2)
        col1.metric("Geração Total (kWh)", format_num(df_u['Geração (kWh)'].sum(), 0))
        col2.metric("Receita Total (R$)", format_real(df_u['Receita (R$)'].sum()))
        col3, col4 = st.columns(2)
        col3.metric("Tarifa Média (R$/kWh)", format_num(df_u['Tarifa (R$/kWh)'].mean(), 4))
        col4.metric("Redução GEE (tCO2)", format_num(df_u['Redução GEE (tCO2)'].sum(), 2))

        st.divider()   # LINHA PADRÃO ENTRE OS BLOCOS

        # Gráficos Mensais
        st.markdown(
            "<h4 style='color:white; text-align:center; font-weight:bold;'>Gráficos Mensais</h4>",
            unsafe_allow_html=True
        )
        st.plotly_chart(px.line(df_u, x='Tempo', y='Geração (kWh)', title='Geração de Energia'), use_container_width=True)
        st.plotly_chart(px.bar(df_u, x='Tempo', y='Receita (R$)', title='Receita por Mês'), use_container_width=True)
        st.plotly_chart(px.area(df_u, x='Tempo', y='Redução GEE (tCO2)', title='Redução de GEE por Mês'), use_container_width=True)

    elif aba_fv == "Geral":
        st.markdown(
            "<h2 style='color:white; text-align:center; font-weight:bold;'>📈 Sistemas Fotovoltaicos - Geral</h2>",
            unsafe_allow_html=True
        )
        min_date = df["Tempo"].min().to_pydatetime()
        max_date = df["Tempo"].max().to_pydatetime()
        periodo = st.slider("Selecione o intervalo de tempo:", min_value=min_date, max_value=max_date, value=(min_date, max_date))
        df_filtrado = df[(df["Tempo"] >= pd.to_datetime(periodo[0])) & (df["Tempo"] <= pd.to_datetime(periodo[1]))]
        col1, col2, col3 = st.columns(3)
        col1.metric("Geração Total (kWh)", format_num(df_filtrado['Geração (kWh)'].sum(), 0))
        col2.metric("Receita Total (R$)", format_real(df_filtrado['Receita (R$)'].sum()))
        col3.metric("Redução GEE (tCO2)", format_num(df_filtrado['Redução GEE (tCO2)'].sum(), 2))

        st.divider()

        st.markdown(
            "<h4 style='color:white; text-align:center; font-weight:bold;'>Gráficos Consolidados</h4>",
            unsafe_allow_html=True
        )
        indicadores = {
            "Geração (kWh)": {"titulo": "Geração de Energia", "cor": "red"},
            "Receita (R$)": {"titulo": "Receita Estimada", "cor": "green"},
            "Redução GEE (tCO2)": {"titulo": "Redução de GEE", "cor": "orange"}
        }
        for indicador, config in indicadores.items():
            df_stacked = df_filtrado.groupby(['Tempo', 'Unidade'])[indicador].sum().reset_index()
            df_total = df_stacked.groupby('Tempo')[indicador].sum().reset_index()
            fig = go.Figure()
            for unidade in df_stacked['Unidade'].unique():
                dados_u = df_stacked[df_stacked['Unidade'] == unidade]
                fig.add_trace(go.Bar(
                    x=dados_u["Tempo"],
                    y=dados_u[indicador],
                    name=unidade,
                    marker=dict(opacity=0.85)
                ))
            fig.add_trace(go.Scatter(
                x=df_total["Tempo"],
                y=df_total[indicador],
                name="Total",
                mode="lines+markers",
                line=dict(color=config["cor"], width=2),
                marker=dict(size=5)
            ))
            fig.update_layout(
                title=config["titulo"],
                barmode="stack",
                xaxis_title="Tempo",
                yaxis_title=indicador,
                hovermode="x",
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
        st.markdown(
            "<h4 style='color:white; text-align:center; font-weight:bold;'>Comparativo entre Unidades</h4>",
            unsafe_allow_html=True
        )
        df_unidades = df_filtrado.groupby("Unidade").agg({
            "Geração (kWh)": "sum",
            "Receita (R$)": "sum",
            "Redução GEE (tCO2)": "sum"
        }).reset_index()
        st.plotly_chart(px.bar(df_unidades, x="Unidade", y="Geração (kWh)", title="Geração por Unidade"))
        st.plotly_chart(px.bar(df_unidades, x="Unidade", y="Receita (R$)", title="Receita por Unidade"))
        st.plotly_chart(px.bar(df_unidades, x="Unidade", y="Redução GEE (tCO2)", title="Redução GEE por Unidade"))
