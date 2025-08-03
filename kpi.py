import streamlit as st
import pandas as pd
import plotly.express as px
import locale

# Configuração da página
st.set_page_config(layout="wide", page_title="Painel de KPIs — Projeto de Gestão e Eficiência Energética da UFPA")

# Paleta institucional
COR_BG = "#f8f4ef"
COR_CARD = "#f3e7d7"
COR_TEXTO = "#473228"
COR_CARD_ESCURO = "#8d6052"
COR_CARD_CLARO = "#cbb197"

# Paleta de cores para os sistemas
CORES_SISTEMAS = {
    "PPGL": "#006EB8",
    "PRODERNA": "#3A9425",
    "PPGQ": "#C3403B",
    "SMA - Ceamazon": "#FFC93C",
    "Mirate - Prefeitura": "#FF914D",
    "ICB": "#73A9AD",
    "WEG - Mirante do Rio": "#D2DAFF",
    "Fronius - Ceamazon": "#F26B83",
    "Abaetetuba": "#9B59B6",
    "Controlador de Carga  - Ceamazon": "#A2A2A2",
}

# CSS customizado
st.markdown(f"""
    <style>
        body {{
            background: {COR_BG} !important;
            font-family: 'Montserrat', 'Segoe UI', Arial, sans-serif;
        }}
        .kpi-card {{
            background: {COR_CARD};
            border-radius: 24px;
            box-shadow: 0 4px 20px 0 #eee8de;
            padding: 28px 0 18px 0;
            text-align: center;
            margin-bottom: 18px;
            min-height: 140px;
            transition: box-shadow 0.2s;
        }}
        .kpi-card:hover {{
            box-shadow: 0 8px 40px 0 #cbb19730;
        }}
        .kpi-title {{
            color: {COR_TEXTO};
            font-weight: 600;
            font-size: 1.22em;
            margin-bottom: 0.2em;
        }}
        .kpi-value {{
            color: {COR_TEXTO};
            font-weight: 700;
            font-size: 2.4em;
            letter-spacing: 2px;
            margin-top: 0.22em;
        }}
        .side-menu {{
            background: {COR_CARD};
            border-radius: 16px;
            padding: 16px 14px 16px 22px;
            margin-bottom: 16px;
            min-width: 200px;
            font-size: 1.09em;
            font-weight: 600;
            color: {COR_TEXTO};
            box-shadow: 0 2px 18px 0 #eee8de;
        }}
        .side-menu-selected {{
            box-shadow: 0 4px 26px 0 #e1ccb7;
            border-left: 8px solid {COR_CARD_ESCURO};
        }}
        /* === ESTILO PARA TABELAS HTML DO COMPARATIVO ANUAL === */
        .my-table {{
            font-family: 'Montserrat', 'Segoe UI', Arial, sans-serif;
            font-size: 1.13em;
            color: {COR_TEXTO};
            background: {COR_CARD};
            border-radius: 18px;
            border: 1px solid #d3c6b9;
            margin-bottom: 24px;
            width: 100%;
            text-align: left;
        }}
        .my-table th, .my-table td {{
            padding: 10px 16px;
        }}
        .my-table th {{
            background: {COR_BG};
        }}
    </style>
""", unsafe_allow_html=True)


# Locale brasileiro
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    locale.setlocale(locale.LC_ALL, '')

def format_real(v):
    if pd.isna(v):
        return "R$ 0,00"
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_num(v, casas=2):
    if pd.isna(v):
        return "0"
    s = f"{v:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

# --- Barra lateral customizada ---
st.sidebar.markdown('<div style="height:32px;"></div>', unsafe_allow_html=True)
modulo = st.sidebar.radio(
    "Selecione o módulo:",
    [
        "🚍 Mobilidade Elétrica",
        "🌞 Sistemas Fotovoltaicos",
        "📊 Comparativo Anual",
        "👨‍💼 Equipe"
    ],
    key="modulo_menu"
)
st.sidebar.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
st.sidebar.image("logo-ceamazon-preta.png", use_container_width=True)

xlsx_path = "kpis_energia_por_unidade.xlsx"

@st.cache_data
def carregar_dados_onibus(tipo):
    df = pd.read_excel(xlsx_path, sheet_name=tipo)
    df.columns = df.columns.str.strip()
    if "Tempo" in df.columns:
        df["Tempo"] = pd.to_datetime(df["Tempo"], errors="coerce")
        df["Ano"] = df["Tempo"].dt.year
        df["MesNum"] = df["Tempo"].dt.month
        df["Mês"] = df["Tempo"].dt.strftime("%b %Y")
    return df

@st.cache_data
def carregar_dados_fotovoltaico():
    df = pd.read_excel(xlsx_path, sheet_name=0)
    df.columns = df.columns.str.strip()

    col_tarifa = "Tarifa Fora Ponta (R$/kWh)"
    col_gee = "Fator de Emissão de Gases do Efeito Estufa (tCO2/MWh)"

    # pega todas as colunas de geração, exceto as Unnamed
    colunas_geracao = [
        col for col in df.columns
        if col not in ["Tempo", col_tarifa, col_gee] and not col.startswith("Unnamed")
    ]
    dfm = df.melt(
        id_vars=["Tempo", col_tarifa, col_gee],
        value_vars=colunas_geracao,
        var_name="Unidade", value_name="Geração (kWh)"
    )
    dfm["Tempo"] = pd.to_datetime(dfm["Tempo"], errors="coerce")
    dfm["Ano"] = dfm["Tempo"].dt.year
    dfm["MesNum"] = dfm["Tempo"].dt.month
    dfm["Mês"] = dfm["Tempo"].dt.strftime("%b %Y")
    dfm["Geração (kWh)"] = pd.to_numeric(dfm["Geração (kWh)"], errors="coerce")
    dfm[col_tarifa] = pd.to_numeric(dfm[col_tarifa], errors="coerce")
    dfm[col_gee] = pd.to_numeric(dfm[col_gee], errors="coerce")
    dfm["Receita (R$)"] = dfm["Geração (kWh)"] * dfm[col_tarifa]
    dfm["Redução GEE (tCO2)"] = (dfm["Geração (kWh)"] / 1000) * dfm[col_gee]
    dfm.rename(columns={col_tarifa: "Tarifa (R$/kWh)"}, inplace=True)
    return dfm
# --- Cabeçalho do Painel ---
st.markdown(
    f"""<h1 style='text-align:center; color:{COR_TEXTO}; font-size:2.3em; margin-bottom:1em;'>
    Painel de KPIs — Projeto de Gestão e Eficiência Energética da UFPA
    </h1>""", unsafe_allow_html=True
)
# ------------------------------------
#   Comparativo Anual (Fotovoltaico)
# ------------------------------------
@st.cache_data
def carregar_dados_sistema():
    df = pd.read_excel(xlsx_path, sheet_name="dados_sistema")
    df.columns = df.columns.str.strip()
    return df
# -------------------------------
#      Mobilidade Elétrica
# -------------------------------
if modulo.startswith("🚍"):
    st.write("")
    tipo_onibus = st.radio("Tipo de ônibus:", ["Rodoviário", "Urbano"], horizontal=True, key="tipo_onibus")
    df = carregar_dados_onibus(tipo_onibus) 

    # Filtro de período
    if "Ano" in df.columns and "Tempo" in df.columns:
        anos = sorted(df["Ano"].dropna().unique())
        ano_sel = st.selectbox("Ano:", anos, index=len(anos)-1, key="ano_onibus")
        meses = df[df["Ano"] == ano_sel]["MesNum"].unique()
        meses_map = {1:"Janeiro",2:"Fevereiro",3:"Março",4:"Abril",5:"Maio",6:"Junho",7:"Julho",8:"Agosto",9:"Setembro",10:"Outubro",11:"Novembro",12:"Dezembro"}
        meses_disp = sorted(meses)
        if len(meses_disp) > 1:
            mes_sel = st.selectbox("Mês:", [meses_map[m] for m in meses_disp], key="mes_onibus")
            mes_num = [k for k,v in meses_map.items() if v == mes_sel][0]
            df = df[(df["Ano"] == ano_sel) & (df["MesNum"] == mes_num)]
        else:
            df = df[df["Ano"] == ano_sel]

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Total km Rodados</div>
                <div class="kpi-value">{format_num(df["km"].sum(), 0)}</div>
            </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Consumo Total (kWh)</div>
                <div class="kpi-value">{format_num(df["kWh"].sum(), 0)}</div>
            </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Redução CO<sub>2</sub> (t)</div>
                <div class="kpi-value">{format_num(df.get("Redução da Emissão", df.get("Redução CO2", pd.Series([0]))).sum(), 1)}</div>
            </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Economia Total (R$)</div>
                <div class="kpi-value">{format_real(df["Economia"].sum())}</div>
            </div>""", unsafe_allow_html=True)

    st.write("")
    c = st.columns([1,2,1])
    with c[1]:
        gasto_total = pd.DataFrame({
            "Tipo": ["Diesel", "Energia Elétrica"],
            "Valor (R$)": [df["Gasto em Diesel"].sum(), df["Gasto em Energia Elétrica"].sum()]
        })
        fig3 = px.bar(
            gasto_total, x="Tipo", y="Valor (R$)", color="Tipo",
            color_discrete_sequence=[COR_CARD_ESCURO, COR_CARD_CLARO],
            text="Valor (R$)"
        )
        fig3.update_traces(texttemplate='%{text:.2s}', textposition='outside')
        fig3.update_layout(
            title={
                'text': "Equivalente gasto por Tipo de Energia",
                'y': 0.96,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=23, color=COR_TEXTO, family="Montserrat, Segoe UI, Arial, sans-serif"),
            },
            height=480,
            margin=dict(t=75, b=25, l=0, r=0),
            showlegend=False,
            plot_bgcolor=COR_BG,
            paper_bgcolor=COR_BG,
            font=dict(color=COR_TEXTO, size=15)
        )
        fig3.update_xaxes(title_text="Tipo")
        fig3.update_yaxes(title_text="Valor (R$)")
        st.plotly_chart(fig3, use_container_width=True)
# ------------------------------------
#   Sistemas Fotovoltaicos - GERAL
# ------------------------------------
elif modulo.startswith("🌞"):
    df_fv = carregar_dados_fotovoltaico()

    st.markdown(
        f"""<h2 style='text-align:center; color:{COR_TEXTO}; font-size:1.55em; margin-bottom:1em;'>
        Sistemas Fotovoltaicos — Visão Geral
        </h2>""", unsafe_allow_html=True
    )

    # Filtro de período (ano ou ano+mês)
    anos = sorted(df_fv["Ano"].dropna().unique())
    ano_sel = st.selectbox("Ano:", anos, index=len(anos)-1, key="ano_fv")
    meses_disp = sorted(df_fv[df_fv["Ano"] == ano_sel]["MesNum"].unique())
    meses_map = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}
    filtro_mes = st.checkbox("Filtrar por mês específico")
    if filtro_mes and len(meses_disp) > 1:
        mes_sel = st.selectbox("Mês:", [meses_map[m] for m in meses_disp], key="mes_fv")
        mes_num = [k for k,v in meses_map.items() if v == mes_sel][0]
        df_filt = df_fv[(df_fv["Ano"] == ano_sel) & (df_fv["MesNum"] == mes_num)]
    else:
        df_filt = df_fv[df_fv["Ano"] == ano_sel]

    # Totais gerais
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Geração de Energia (kWh)</div>
                <div class="kpi-value">🌞{format_num(df_filt["Geração (kWh)"].sum(), 0)}</div>
            </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Receita (R$)</div>
                <div class="kpi-value">💸{format_real(df_filt["Receita (R$)"].sum())}</div>
            </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Redução GEE (tCO₂)</div>
                <div class="kpi-value">🌱{format_num(df_filt["Redução GEE (tCO2)"].sum(), 2)}</div>
            </div>""", unsafe_allow_html=True)
    st.write("")
    # --- Gráfico de barras empilhadas ---
    st.markdown(
        '<div style="font-weight:700;font-size:1.13em;color:#473228;text-align:center;">Geração por Unidade (kWh)</div>',
        unsafe_allow_html=True)
    if not df_filt.empty:
        df_pivot = df_filt.pivot_table(index="MesNum", columns="Unidade", values="Geração (kWh)", aggfunc="sum").fillna(0)
        df_pivot = df_pivot.sort_index()
        color_map = {unid: CORES_SISTEMAS.get(unid, "#cccccc") for unid in df_pivot.columns}
        fig_stacked = px.bar(
            df_pivot,
            x=df_pivot.index,
            y=df_pivot.columns,
            labels={"value": "Geração (kWh)", "MesNum": "Mês"},
            template="simple_white",
            color_discrete_map=color_map
        )
        fig_stacked.update_layout(
            barmode='stack', height=350, xaxis_title="Mês", yaxis_title="kWh",
            legend_title="Unidade", margin=dict(t=45))
        fig_stacked.update_xaxes(
            tickvals=list(range(1,13)),
            ticktext=["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        )
        st.plotly_chart(fig_stacked, use_container_width=True)
    else:
        st.info("Não há dados para o período selecionado.")
    # Gráfico empilhado — Receita por Unidade (R$)
    st.markdown(
        '<div style="font-weight:700;font-size:1.13em;color:#473228;text-align:center;">Receita por Unidade (R$)</div>',
        unsafe_allow_html=True)
    if not df_filt.empty:
        df_pivot_receita = df_filt.pivot_table(index="MesNum", columns="Unidade", values="Receita (R$)", aggfunc="sum").fillna(0)
        df_pivot_receita = df_pivot_receita.sort_index()
        color_map = {unid: CORES_SISTEMAS.get(unid, "#cccccc") for unid in df_pivot_receita.columns}
        fig_receita = px.bar(
            df_pivot_receita,
            x=df_pivot_receita.index,
            y=df_pivot_receita.columns,
            labels={"value": "Receita (R$)", "MesNum": "Mês"},
            template="simple_white",
            color_discrete_map=color_map
        )
        fig_receita.update_layout(
            barmode='stack', height=350, xaxis_title="Mês", yaxis_title="R$",
            legend_title="Unidade", margin=dict(t=45),
            font=dict(family="Montserrat, Segoe UI, Arial, sans-serif", size=15, color=COR_TEXTO)
        )
        fig_receita.update_xaxes(
            tickvals=list(range(1,13)),
            ticktext=["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        )
        st.plotly_chart(fig_receita, use_container_width=True)
    else:
        st.info("Não há dados para o período selecionado.")

    # Gráfico empilhado — Redução GEE por Unidade (tCO2)
    st.markdown(
        '<div style="font-weight:700;font-size:1.13em;color:#473228;text-align:center;">Redução GEE por Unidade (tCO₂)</div>',
        unsafe_allow_html=True)
    if not df_filt.empty:
        df_pivot_gee = df_filt.pivot_table(index="MesNum", columns="Unidade", values="Redução GEE (tCO2)", aggfunc="sum").fillna(0)
        df_pivot_gee = df_pivot_gee.sort_index()
        color_map = {unid: CORES_SISTEMAS.get(unid, "#cccccc") for unid in df_pivot_gee.columns}
        fig_gee = px.bar(
            df_pivot_gee,
            x=df_pivot_gee.index,
            y=df_pivot_gee.columns,
            labels={"value": "Redução GEE (tCO₂)", "MesNum": "Mês"},
            template="simple_white",
            color_discrete_map=color_map
        )
        fig_gee.update_layout(
            barmode='stack', height=350, xaxis_title="Mês", yaxis_title="tCO₂",
            legend_title="Unidade", margin=dict(t=45),
            font=dict(family="Montserrat, Segoe UI, Arial, sans-serif", size=15, color=COR_TEXTO)
        )
        fig_gee.update_xaxes(
            tickvals=list(range(1,13)),
            ticktext=["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        )
        st.plotly_chart(fig_gee, use_container_width=True)
    else:
        st.info("Não há dados para o período selecionado.")
    # --- Gráfico de pizza/donut - Participação por unidade ---
    st.markdown(
        '<div style="font-weight:700;font-size:1.13em;color:#473228;text-align:center;">Participação de Cada Sistema</div>',
        unsafe_allow_html=True)
    soma_sistemas = df_filt.groupby("Unidade")["Geração (kWh)"].sum().reset_index()
    unidades_excluir = ["Tarifa Fora Ponta (R$/kWh)", "Fator de Emissão de Gases do Efeito Estufa (tCO2/MWh)"]
    soma_sistemas = soma_sistemas[~soma_sistemas["Unidade"].isin(unidades_excluir)]

    if not soma_sistemas.empty and soma_sistemas["Geração (kWh)"].sum() > 0:
        fig_pizza = px.pie(
            soma_sistemas,
            names="Unidade",
            values="Geração (kWh)",
            hole=0.45,
            labels={"Unidade": "Sistema", "Geração (kWh)": "Geração"},
            color="Unidade",
            color_discrete_map=CORES_SISTEMAS
        )
        fig_pizza.update_traces(textinfo='percent+label', pull=[0.04]*len(soma_sistemas))
        fig_pizza.update_layout(showlegend=True, height=340)
        st.plotly_chart(fig_pizza, use_container_width=True)
    else:
        st.info("Não há geração para exibir participação dos sistemas nesse período.")

    # --- Visão por unidade individual ---
    st.markdown("---")
    st.markdown(
        f"""<h3 style='text-align:center; color:{COR_TEXTO}; font-size:1.25em; margin-bottom:1em;'>
        Análise Detalhada por Unidade
        </h3>""", unsafe_allow_html=True
    )
    unidades_opcoes = [u for u in df_fv["Unidade"].unique() if u not in unidades_excluir]
    unidade = st.selectbox("Selecione a Unidade:", unidades_opcoes)
    df_uni = df_fv[df_fv["Unidade"] == unidade]
    df_uni = df_uni[df_uni["Ano"] == ano_sel]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Geração Total (kWh)</div>
                <div class="kpi-value">{format_num(df_uni["Geração (kWh)"].sum(), 0)}</div>
            </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Receita Total (R$)</div>
                <div class="kpi-value">{format_real(df_uni["Receita (R$)"].sum())}</div>
            </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Redução GEE (tCO<sub>2</sub>)</div>
                <div class="kpi-value">{format_num(df_uni["Redução GEE (tCO2)"].sum(), 2)}</div>
            </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Tarifa Média (R$/kWh)</div>
                <div class="kpi-value">{format_num(df_uni["Tarifa (R$/kWh)"].mean(), 4)}</div>
            </div>""", unsafe_allow_html=True)

    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            '<div style="font-weight:700;font-size:1.18em;color:#473228;text-align:center;margin-bottom:-16px;">Geração Mensal (kWh)</div>',
            unsafe_allow_html=True)
        fig1 = px.bar(df_uni, x="MesNum", y="Geração (kWh)", color_discrete_sequence=[COR_CARD_CLARO])
        fig1.update_layout(title="", height=340, margin=dict(t=45,b=25,l=0,r=0),
                           plot_bgcolor=COR_BG, paper_bgcolor=COR_BG, font=dict(color=COR_TEXTO, size=15))
        fig1.update_xaxes(
            title_text="Mês",
            tickvals=list(range(1,13)),
            ticktext=["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        )
        fig1.update_yaxes(title_text="kWh")
        st.plotly_chart(fig1, use_container_width=True)
    with c2:
        st.markdown(
            '<div style="font-weight:700;font-size:1.18em;color:#473228;text-align:center;margin-bottom:-16px;">Receita Mensal (R$)</div>',
            unsafe_allow_html=True)
        fig2 = px.bar(df_uni, x="MesNum", y="Receita (R$)", color_discrete_sequence=[COR_CARD_ESCURO])
        fig2.update_layout(title="", height=340, margin=dict(t=45,b=25,l=0,r=0),
                           plot_bgcolor=COR_BG, paper_bgcolor=COR_BG, font=dict(color=COR_TEXTO, size=15))
        fig2.update_xaxes(
            title_text="Mês",
            tickvals=list(range(1,13)),
            ticktext=["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        )
        fig2.update_yaxes(title_text="R$")
        st.plotly_chart(fig2, use_container_width=True)
    with c3:
        st.markdown(
            '<div style="font-weight:700;font-size:1.18em;color:#473228;text-align:center;margin-bottom:-16px;">Redução GEE (tCO₂)</div>',
            unsafe_allow_html=True)
        fig3 = px.bar(df_uni, x="MesNum", y="Redução GEE (tCO2)", color_discrete_sequence=[COR_CARD_CLARO])
        fig3.update_layout(title="", height=340, margin=dict(t=45,b=25,l=0,r=0),
                           plot_bgcolor=COR_BG, paper_bgcolor=COR_BG, font=dict(color=COR_TEXTO, size=15))
        fig3.update_xaxes(
            title_text="Mês",
            tickvals=list(range(1,13)),
            ticktext=["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        )
        fig3.update_yaxes(title_text="tCO₂")
        st.plotly_chart(fig3, use_container_width=True)
# ------------------------------------
#   Comparativo Anual (Fotovoltaico)
# ------------------------------------
elif modulo.startswith("📊"):
    df_fv = carregar_dados_fotovoltaico()
    df_meta = carregar_dados_sistema()
    df_meta.columns = df_meta.columns.str.strip()
    df_meta = df_meta.rename(columns={"Unnamed: 0": "Unidade"})

    st.markdown(
        f"""<h2 style='text-align:center; color:{COR_TEXTO}; font-size:1.55em; margin-bottom:1em;'>
        Comparativo Anual — Geração por Sistema
        </h2>""", unsafe_allow_html=True
    )

    anos_disp = sorted(df_fv["Ano"].unique())
    anos_sel = st.multiselect("Selecione anos para comparar:", anos_disp, default=anos_disp[-2:])
    df_anos = df_fv[df_fv["Ano"].isin(anos_sel)]

    tabela_anos = df_anos.groupby(["Unidade", "Ano"])[["Geração (kWh)", "Receita (R$)", "Redução GEE (tCO2)"]].sum().reset_index()
    tabela_anos = tabela_anos.merge(df_meta, on="Unidade", how="left")
    tabela_anos.columns = tabela_anos.columns.str.strip()
    tabela_anos["Eficiência (kWh/kWp)"] = tabela_anos["Geração (kWh)"] / tabela_anos["Capacidade Instalada (kW)"]
    if "Area" in tabela_anos.columns:
        tabela_anos["Area"] = pd.to_numeric(tabela_anos["Area"], errors="coerce")
        tabela_anos["Receita por área (R$/m²)"] = tabela_anos["Receita (R$)"] / tabela_anos["Area"]
    else:
        tabela_anos["Receita por área (R$/m²)"] = None

    tabela_anos["Variação %"] = tabela_anos.groupby("Unidade")["Geração (kWh)"].pct_change().round(4) * 100

    # Texto explicativo: destaque do ano recorde de geração
    total_geracao = tabela_anos.groupby("Ano")["Geração (kWh)"].sum()
    ano_recorde = total_geracao.idxmax()
    valor_recorde = total_geracao.max()
    unidade_lider = tabela_anos[tabela_anos["Ano"] == ano_recorde].sort_values("Geração (kWh)", ascending=False)["Unidade"].iloc[0]

    st.markdown(f"""
    <div style='background:{COR_CARD};border-radius:16px;padding:18px 26px;margin-bottom:18px;box-shadow:0 1px 10px #eee8de;'>
        <b>Resumo:</b><br>
        O ano de <b>{ano_recorde}</b> registrou a maior geração total do período, com <b>{format_num(valor_recorde, 0)} kWh</b> somados entre todos os sistemas.<br>
        O sistema de maior destaque foi <b>{unidade_lider}</b>.<br>
        Use os gráficos abaixo para comparar visualmente o desempenho anual dos sistemas e suas evoluções.
    </div>
    """, unsafe_allow_html=True)

    # Gráfico de barras - Geração
    st.markdown("**Geração anual por sistema:**")
    fig_comp = px.bar(
        tabela_anos, x="Unidade", y="Geração (kWh)", color="Ano", barmode="group",
        text_auto=True, labels={"Geração (kWh)": "Geração Total (kWh)"}, template="simple_white")
    fig_comp.update_layout(
        font=dict(family="Montserrat, Segoe UI, Arial, sans-serif", size=17, color=COR_TEXTO),
        height=380, xaxis_title="Sistema", yaxis_title="kWh", legend_title="Ano", margin=dict(t=50)
    )
    st.plotly_chart(fig_comp, use_container_width=True)

    # Gráfico de barras - Eficiência
    st.markdown("**Eficiência (kWh/kWp) anual por sistema:**")
    fig_eff = px.bar(
        tabela_anos, x="Unidade", y="Eficiência (kWh/kWp)", color="Ano", barmode="group",
        text_auto=True, labels={"Eficiência (kWh/kWp)": "kWh/kWp"}, template="simple_white")
    fig_eff.update_layout(
        font=dict(family="Montserrat, Segoe UI, Arial, sans-serif", size=17, color=COR_TEXTO),
        height=350, xaxis_title="Sistema", yaxis_title="Eficiência (kWh/kWp)", legend_title="Ano", margin=dict(t=35)
    )
    st.plotly_chart(fig_eff, use_container_width=True)

    # Radar/Polígono para comparar métricas normalizadas
    st.markdown("**Radar de comparação de desempenho (normalizado):**")
    indic_cols = ["Geração (kWh)", "Eficiência (kWh/kWp)", "Receita (R$)", "Receita por área (R$/m²)", "Redução GEE (tCO2)"]
    radardata = []
    for ano in anos_sel:
        df_rad = tabela_anos[tabela_anos["Ano"] == ano].copy()
        if df_rad.empty: continue
        for col in indic_cols:
            max_val = df_rad[col].max()
            df_rad[col + " N"] = df_rad[col] / max_val if max_val > 0 else 0
        for idx, row in df_rad.iterrows():
            radardata.append({
                "Sistema": row["Unidade"],
                "Ano": str(row["Ano"]),
                **{col: row[col + " N"] for col in indic_cols}
            })
    if radardata:
        df_radar = pd.DataFrame(radardata)
        for ano in anos_sel:
            df_radar_ano = df_radar[df_radar["Ano"] == str(ano)]
            fig_radar = px.line_polar(
                df_radar_ano.melt(id_vars=["Sistema"], value_vars=indic_cols, var_name="Indicador", value_name="Valor"),
                r="Valor", theta="Indicador", color="Sistema", line_close=True,
                title=f"Radar {ano}"
            )
            fig_radar.update_layout(
                font=dict(family="Montserrat, Segoe UI, Arial, sans-serif", size=15, color=COR_TEXTO),
                height=410
            )
            st.plotly_chart(fig_radar, use_container_width=True)
    else:
        st.info("Não há dados suficientes para gerar o radar.")
# ------------------------------------
#            Equipe
# ------------------------------------
elif modulo.startswith("👨‍💼"):
    st.markdown(
        f"""<h2 style='text-align:center; color:{COR_TEXTO}; font-size:2.0em; margin-bottom:1em;'>
        Equipe: Sistemas Fotovoltaicos e Mobilidade Elétrica — CEAMAZON
        </h2>""", unsafe_allow_html=True
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="kpi-card" style="min-height:175px;">
            <div class="kpi-title" style="font-size:1.10em;">Doutorado</div>
            <ul style="text-align:left;margin-top:18px;font-size:1.11em;">
                <li><b>Dr. Bruno Santana de Albuquerque</b></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-card" style="min-height:175px;">
            <div class="kpi-title" style="font-size:1.10em;">Estudantes de Mestrado</div>
            <ul style="text-align:left;margin-top:18px;font-size:1.11em;">
                <li><b>Ayrton Lucas Lisboa do Nascimento</b></li>
                <li><b>Carlos Sarubi</b></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="kpi-card" style="min-height:175px;">
            <div class="kpi-title" style="font-size:1.10em;">Estudantes de Graduação</div>
            <ul style="text-align:left;margin-top:18px;font-size:1.11em;">
                <li><b>Luiz Borges</b></li>
                <li><b>Nome Graduando 2</b></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    st.write("")
    st.write("")
    st.markdown(
        f"""
        <div style="display:flex;justify-content:center;margin-top:6px;">
            <div class="kpi-card" style="background:{COR_CARD_CLARO};min-width:630px;max-width:900px;">
                <div style="font-size:1.13em;font-weight:600;margin-bottom:8px;">Desenvolvido e revisado por:</div>
                <div style="font-size:1.07em;"><b>Ayrton Lucas Lisboa do Nascimento</b> e <b>Dr. Bruno Santana de Albuquerque</b><br>
                E-mail: ayrtonl.nascimento@gmail.com</div>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

# ---- Rodapé institucional ----
st.markdown(
    f"<div style='text-align:center;font-size:1em;color:{COR_TEXTO};opacity:0.57;margin-top:4em;'>© Sistemas Fotovoltaicos e Mobilidade Elétrica - CEAMAZON — 2025</div>",
    unsafe_allow_html=True
)