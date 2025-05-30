import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import locale
import numpy as np
import statsmodels  

# 1) Configuração da página
st.set_page_config(layout="wide")

# 2) Detecta tema nativo
base    = (st.get_option("theme.base") or "light").lower()
is_dark = base == "dark"
plotly_template  = "plotly_dark" if is_dark else "plotly_white"
annotation_color = "white"       if is_dark else "black"

# 3) Mostra somente a logo correta usando st.image()
if is_dark:
    st.sidebar.image("logo-ceamazon-branca.png", use_container_width=True)
else:
    st.sidebar.image("logo-ceamazon-preta.png", use_container_width=True)

# 4) Injeção de CSS para títulos adaptáveis
st.markdown("""
<style>
  html[data-theme="dark"]  .titulo { color: white !important; }
  html[data-theme="light"] .titulo { color: black !important; }
</style>
""", unsafe_allow_html=True)

# 5) Locale pt_BR
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    locale.setlocale(locale.LC_ALL, '')

# 6) Helpers de formatação
def format_real(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_num(v, casas=2):
    s = f"{v:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

# 7) Carregamento de dados
xlsx_path = "kpis_energia_por_unidade.xlsx"

@st.cache_data
def carregar_dados_onibus(aba):
    df = pd.read_excel(xlsx_path, sheet_name=aba)
    df.columns = df.columns.str.strip()
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"])
    return df

@st.cache_data
def carregar_dados_fotovoltaico():
    df = pd.read_excel(xlsx_path)
    cols_gen = df.columns[1:-2].tolist()
    col_tar  = df.columns[-2]
    col_gee  = df.columns[-1]
    dfm = df.melt(
        id_vars=["Tempo", col_tar, col_gee],
        value_vars=cols_gen,
        var_name="Unidade", value_name="Geração (kWh)"
    )
    dfm["Tempo"] = pd.to_datetime(dfm["Tempo"])
    dfm["Ano"]   = dfm["Tempo"].dt.year
    dfm["Mês"]   = dfm["Tempo"].dt.strftime("%b")
    dfm["Geração (kWh)"]      = pd.to_numeric(dfm["Geração (kWh)"], errors="coerce")
    dfm[col_tar]              = pd.to_numeric(dfm[col_tar], errors="coerce")
    dfm[col_gee]              = pd.to_numeric(dfm[col_gee], errors="coerce")
    dfm["Receita (R$)"]       = dfm["Geração (kWh)"] * dfm[col_tar]
    dfm["Redução GEE (tCO2)"] = (dfm["Geração (kWh)"] / 1000) * dfm[col_gee]
    dfm.rename(columns={col_tar: "Tarifa (R$/kWh)"}, inplace=True)
    return dfm

# 8) Cores e ícones
cores = {"Rodoviário": "#2563eb", "Urbano": "#059669"}
icons = {"Rodoviário": "🚌 Ônibus Rodoviário", "Urbano": "🚍 Ônibus Urbano"}

# 9) Navegação
relatorio = st.sidebar.radio("Selecione Relatório:", ["Mobilidade Elétrica", "Sistemas Fotovoltaicos"])

if relatorio == "Mobilidade Elétrica":
    linha     = st.sidebar.radio("Ônibus Elétrico:", ["Rodoviário", "Urbano"])
    df_onibus = carregar_dados_onibus(linha)
    cor_tema  = cores[linha]
    emoji     = icons[linha]

    # Filtro de intervalo de datas
    if "Data" in df_onibus.columns:
        data_min = df_onibus["Data"].min().to_pydatetime()
        data_max = df_onibus["Data"].max().to_pydatetime()
        intervalo = st.slider("Intervalo de Tempo:", min_value=data_min, max_value=data_max, value=(data_min, data_max))
        df_onibus = df_onibus[(df_onibus["Data"] >= pd.to_datetime(intervalo[0])) & (df_onibus["Data"] <= pd.to_datetime(intervalo[1]))]
        df_onibus["Mês"] = df_onibus["Data"].dt.strftime("%b")

    st.markdown(
        f"<h2 class='titulo' style='text-align:center; font-weight:bold;'>{emoji} — Mobilidade Elétrica</h2>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<h4 class='titulo' style='text-align:center; font-weight:bold;'>Relatório detalhado do ônibus {linha}</h4>",
        unsafe_allow_html=True
    )

    # KPIs principais
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total km Rodados", format_num(df_onibus["km"].sum(), 0))
    c2.metric("Consumo Total (kWh)", format_num(df_onibus["kWh"].sum(), 0))
    c3.metric("Dias de Operação", format_num(df_onibus["Dias"].sum(), 0))
    if "Redução da Emissão" in df_onibus.columns:
        c4.metric("Redução da Emissão (tCO2)", format_num(df_onibus["Redução da Emissão"].sum(), 2))
    else:
        c4.metric("Redução da Emissão (tCO2)", "N/A")

    st.divider()

    # KPIs secundários
    ca, cb = st.columns(2)
    with ca:
        ca.metric("Economia Total (R$)", format_real(df_onibus["Economia"].sum()))
        ca.metric("Gasto em Energia (R$)", format_real(df_onibus["Gasto em Energia Elétrica"].sum()))
    with cb:
        cb.metric("Gasto em Diesel (R$)", format_real(df_onibus["Gasto em Diesel"].sum()))
        if df_onibus["Percentual de Redução"].notnull().any():
            p   = df_onibus["Percentual de Redução"].dropna().mean()
            txt = f"{p*100:.2f}%" if p <= 1 else f"{p:.2f}%"
            cb.metric("Redução de GEE (%)", txt.replace(".", ","))
        else:
            cb.metric("Redução de GEE (%)", "N/A")

    st.divider()

    # Gráficos Mensais
    st.markdown(
        "<h4 class='titulo' style='text-align:center; font-weight:bold;'>Gráficos Mensais</h4>",
        unsafe_allow_html=True
    )
    for campo, titulo in [("kWh", "Consumo"), ("km", "Distância"), ("Economia", "Economia")]:
        fig = px.bar(
            df_onibus, x="Mês", y=campo,
            title=f"{titulo} Mensal",
            color_discrete_sequence=[cor_tema],
            template=plotly_template
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Correlação
    st.markdown(
        "<h4 class='titulo' style='text-align:center; font-weight:bold;'>Gráfico de Dispersão e Tendência: Consumo vs Distância</h4>",
        unsafe_allow_html=True
    )
    df_corr = df_onibus.dropna(subset=["kWh", "km"])
    if not df_corr.empty:
        corr      = df_corr["km"].corr(df_corr["kWh"])
        corr_text = f"Coef. correlação: {corr:.2f}"
        fig_corr  = px.scatter(
            df_corr, x="km", y="kWh",
            labels={"km":"Distância (km)", "kWh":"Consumo (kWh)"},
            color_discrete_sequence=[cor_tema],
            template=plotly_template,
            trendline="ols",
            trendline_color_override=cor_tema
        )
        fig_corr.add_annotation(
            text=corr_text,
            xref="paper", yref="paper", x=0.05, y=0.95,
            showarrow=False,
            font=dict(color=annotation_color, size=14),
            align="left",
            bgcolor=("rgba(0,0,0,0.7)" if is_dark else "rgba(255,255,255,0.7)")
        )
        st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.info("Não há dados suficientes para plotar a correlação.")

else:
    modo = st.sidebar.radio("Sistemas Fotovoltaicos:", ["Sistemas Analisados", "Geral"])
    df_fv = carregar_dados_fotovoltaico()

    # Paleta de cores padronizada por unidade
    cores_unidades = {
        unidade: cor for unidade, cor in zip(
            sorted(df_fv["Unidade"].unique()),
            px.colors.qualitative.Plotly
        )
    }

    if modo == "Sistemas Analisados":
        st.markdown(
            "<h2 class='titulo' style='text-align:center; font-weight:bold;'>📊 Sistemas Fotovoltaicos – Analisados</h2>",
            unsafe_allow_html=True
        )
        unidade = st.selectbox("Selecione Unidade:", df_fv["Unidade"].unique())
        df_uni  = df_fv[df_fv["Unidade"] == unidade]

        c1, c2 = st.columns(2)
        c1.metric("Geração (kWh)", format_num(df_uni["Geração (kWh)"].sum(), 0))
        c2.metric("Receita (R$)", format_real(df_uni["Receita (R$)"].sum()))
        c3, c4 = st.columns(2)
        c3.metric("Tarifa Média (R$/kWh)", format_num(df_uni["Tarifa (R$/kWh)"].mean(), 4))
        c4.metric("Redução GEE (tCO2)", format_num(df_uni["Redução GEE (tCO2)"].sum(), 2))

        st.divider()

        st.markdown(
            "<h4 class='titulo' style='text-align:center; font-weight:bold;'>Gráficos Mensais</h4>",
            unsafe_allow_html=True
        )
        st.plotly_chart(px.line(
            df_uni, x="Tempo", y="Geração (kWh)", color="Unidade",
            template=plotly_template, color_discrete_map=cores_unidades
        ), use_container_width=True)

        st.plotly_chart(px.bar(
            df_uni, x="Tempo", y="Receita (R$)", color="Unidade",
            template=plotly_template, color_discrete_map=cores_unidades
        ), use_container_width=True)

        st.plotly_chart(px.area(
            df_uni, x="Tempo", y="Redução GEE (tCO2)", color="Unidade",
            template=plotly_template, color_discrete_map=cores_unidades
        ), use_container_width=True)

    else:
        st.markdown(
            "<h2 class='titulo' style='text-align:center; font-weight:bold;'>📈 Sistemas Fotovoltaicos – Geral</h2>",
            unsafe_allow_html=True
        )
        mn = df_fv["Tempo"].min().to_pydatetime()
        mx = df_fv["Tempo"].max().to_pydatetime()
        intervalo = st.slider("Intervalo de Tempo:", min_value=mn, max_value=mx, value=(mn, mx))
        df_filtrado = df_fv[
            (df_fv["Tempo"] >= pd.to_datetime(intervalo[0])) &
            (df_fv["Tempo"] <= pd.to_datetime(intervalo[1]))
        ]

        c1, c2, c3 = st.columns(3)
        c1.metric("Geração (kWh)", format_num(df_filtrado["Geração (kWh)"].sum(), 0))
        c2.metric("Receita (R$)", format_real(df_filtrado["Receita (R$)"].sum()))
        c3.metric("Redução GEE (tCO2)", format_num(df_filtrado["Redução GEE (tCO2)"].sum(), 2))

        st.divider()

        st.markdown(
            "<h4 class='titulo' style='text-align:center; font-weight:bold;'>Gráficos Consolidados</h4>",
            unsafe_allow_html=True
        )
        indicadores = {
            "Geração (kWh)": ("Geração","red"),
            "Receita (R$)" : ("Receita","green"),
            "Redução GEE (tCO2)": ("Redução","orange")
        }
        for campo, (ttl, cor) in indicadores.items():
            df_stack = df_filtrado.groupby(["Tempo","Unidade"])[campo].sum().reset_index()
            df_tot   = df_stack.groupby("Tempo")[campo].sum().reset_index()
            fig = go.Figure()
            for u in df_stack["Unidade"].unique():
                tmp = df_stack[df_stack["Unidade"] == u]
                fig.add_trace(go.Bar(x=tmp["Tempo"], y=tmp[campo], name=u,
                                     marker=dict(opacity=0.85, color=cores_unidades.get(u, None))))
            fig.add_trace(go.Scatter(x=df_tot["Tempo"], y=df_tot[campo], name="Total",
                                     mode="lines+markers", line=dict(color=cor)))
            fig.update_layout(
                title=ttl, barmode="stack",
                xaxis_title="Tempo", yaxis_title=campo,
                template=plotly_template
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown(
            "<h4 class='titulo' style='text-align:center; font-weight:bold;'>Comparativo Unidades</h4>",
            unsafe_allow_html=True
        )
        df_uni_agg = df_filtrado.groupby("Unidade").agg({k:"sum" for k in indicadores}).reset_index()
        for k in indicadores:
            st.plotly_chart(px.bar(
                df_uni_agg, x="Unidade", y=k, title=k,
                template=plotly_template, color="Unidade",
                color_discrete_map=cores_unidades
            ), use_container_width=True)