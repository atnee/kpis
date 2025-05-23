
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import locale

st.set_page_config(layout="wide")

# Localização para formato brasileiro
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    locale.setlocale(locale.LC_ALL, '')

# Caminho para a planilha no formato original (colunas por unidade)
xlsx_path = "kpis_energia_por_unidade.xlsx"

@st.cache_data
def carregar_dados():
    df = pd.read_excel(xlsx_path)

    # Identificar colunas de geração (entre a coluna 'Tempo' e as duas últimas)
    colunas_geracao = df.columns[1:-2].tolist()
    coluna_tarifa = df.columns[-2]
    coluna_gee = df.columns[-1]

    # Transformar para formato longo
    df_melt = df.melt(id_vars=["Tempo", coluna_tarifa, coluna_gee],
                      value_vars=colunas_geracao,
                      var_name="Unidade",
                      value_name="Geração (kWh)")

    df_melt["Tempo"] = pd.to_datetime(df_melt["Tempo"])
    df_melt["Ano"] = df_melt["Tempo"].dt.year
    df_melt["Mês"] = df_melt["Tempo"].dt.strftime("%b")

    # Conversões seguras
    df_melt["Geração (kWh)"] = pd.to_numeric(df_melt["Geração (kWh)"], errors="coerce")
    df_melt[coluna_tarifa] = pd.to_numeric(df_melt[coluna_tarifa], errors="coerce")
    df_melt[coluna_gee] = pd.to_numeric(df_melt[coluna_gee], errors="coerce")

    # Cálculos
    df_melt["Receita (R$)"] = df_melt["Geração (kWh)"] * df_melt[coluna_tarifa]
    df_melt["Redução GEE (tCO2)"] = (df_melt["Geração (kWh)"] / 1000) * df_melt[coluna_gee]
    df_melt.rename(columns={coluna_tarifa: "Tarifa (R$/kWh)"}, inplace=True)

    return df_melt

df = carregar_dados()

pagina = st.sidebar.selectbox("Selecione a Página", ["Dashboard", "Exportações", "Relatório Integrado"])

if pagina == "Dashboard":
    st.title("📊 Dashboard Interativo - KPIs de Energia por Unidade")

    unidade = st.selectbox("Selecione a Unidade:", df['Unidade'].unique())
    df_u = df[df['Unidade'] == unidade]

    col1, col2 = st.columns(2)
    col1.metric("Geração Total (kWh)", locale.format_string("%.0f", df_u['Geração (kWh)'].sum(), grouping=True))
    col2.metric("Receita Total (R$)", "R$ " + locale.format_string("%.2f", df_u['Receita (R$)'].sum(), grouping=True))

    col3, col4 = st.columns(2)
    col3.metric("Tarifa Média (R$/kWh)", locale.format_string("%.4f", df_u['Tarifa (R$/kWh)'].mean(), grouping=True))
    col4.metric("Redução GEE (tCO2)", locale.format_string("%.2f", df_u['Redução GEE (tCO2)'].sum(), grouping=True))

    st.plotly_chart(px.line(df_u, x='Tempo', y='Geração (kWh)', title='Geração de Energia'))
    st.plotly_chart(px.bar(df_u, x='Tempo', y='Receita (R$)', title='Receita por Mês'))
    st.plotly_chart(px.area(df_u, x='Tempo', y='Redução GEE (tCO2)', title='Redução de GEE por Mês'))

elif pagina == "Exportações":
    st.title("📥 Exportação de Dados de KPIs")

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📂 Baixar CSV Geral", data=csv, file_name="kpis_dashboard.csv", mime="text/csv")

    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='KPIs Energia', index=False)
    st.download_button("📊 Baixar Excel Geral", data=excel_buffer.getvalue(),
                       file_name="kpis_dashboard.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

elif pagina == "Relatório Integrado":
    st.title("📈 Relatório Integrado - Indicadores Consolidados")

    min_date = df["Tempo"].min().to_pydatetime()
    max_date = df["Tempo"].max().to_pydatetime()
    periodo = st.slider("Selecione o intervalo de tempo:", min_value=min_date, max_value=max_date,
                        value=(min_date, max_date))

    df_filtrado = df[(df["Tempo"] >= pd.to_datetime(periodo[0])) & (df["Tempo"] <= pd.to_datetime(periodo[1]))]

    col1, col2, col3 = st.columns(3)
    col1.metric("Geração Total (kWh)", locale.format_string("%.0f", df_filtrado['Geração (kWh)'].sum(), grouping=True))
    col2.metric("Receita Total (R$)", "R$ " + locale.format_string("%.2f", df_filtrado['Receita (R$)'].sum(), grouping=True))
    col3.metric("Redução GEE (tCO2)", locale.format_string("%.2f", df_filtrado['Redução GEE (tCO2)'].sum(), grouping=True))

    st.subheader("📊 Gráficos por Mês (Empilhado + Linha Total)")
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

    st.subheader("📊 Comparativo entre Unidades")
    df_unidades = df_filtrado.groupby("Unidade").agg({
        "Geração (kWh)": "sum",
        "Receita (R$)": "sum",
        "Redução GEE (tCO2)": "sum"
    }).reset_index()

    st.plotly_chart(px.bar(df_unidades, x="Unidade", y="Geração (kWh)", title="Geração por Unidade"))
    st.plotly_chart(px.bar(df_unidades, x="Unidade", y="Receita (R$)", title="Receita por Unidade"))
    st.plotly_chart(px.bar(df_unidades, x="Unidade", y="Redução GEE (tCO2)", title="Redução GEE por Unidade"))
