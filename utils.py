import pandas as pd
import locale
from fpdf import FPDF
import io

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

def carregar_dados_onibus(xlsx_path, tipo):
    df = pd.read_excel(xlsx_path, sheet_name=tipo)
    df.columns = df.columns.str.strip()
    if "Tempo" in df.columns:
        df["Tempo"] = pd.to_datetime(df["Tempo"], errors="coerce")
        df["Ano"] = df["Tempo"].dt.year
        df["MesNum"] = df["Tempo"].dt.month
        df["Mês"] = df["Tempo"].dt.strftime("%b %Y")
    return df

def carregar_dados_fotovoltaico(xlsx_path):
    df = pd.read_excel(xlsx_path, sheet_name=0)
    df.columns = df.columns.str.strip()
    col_tarifa = "Tarifa Fora Ponta (R$/kWh)"
    col_gee = "Fator de Emissão de Gases do Efeito Estufa (tCO2/MWh)"
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

def carregar_dados_sistema(xlsx_path):
    df = pd.read_excel(xlsx_path, sheet_name="dados_sistema")
    df.columns = df.columns.str.strip()
    return df

def gerar_pdf_kpis(df, periodo_desc):
    from matplotlib import pyplot as plt
    import tempfile
    pdf = FPDF()
    pdf.add_page()
    # Faixa colorida no topo
    pdf.set_fill_color(248, 244, 239)  # cor de fundo institucional
    pdf.rect(0, 0, 210, 30, 'F')
    try:
        pdf.image("logo-ceamazon-preta.png", x=85, y=5, w=40)
    except Exception:
        pass
    pdf.set_y(32)
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(71, 50, 40)
    pdf.cell(0, 14, f"KPIs - {periodo_desc}", ln=True, align="C")
    pdf.set_draw_color(205, 183, 151)
    pdf.set_line_width(0.7)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(8)
    # KPIs em blocos
    pdf.set_font("Arial", 'B', 13)
    pdf.set_fill_color(243, 231, 215)
    pdf.set_text_color(61, 41, 28)
    pdf.cell(65, 18, f"Geração: {format_num(df['Geração (kWh)'].sum(), 0)} kWh", border=0, ln=0, align="C", fill=True)
    pdf.cell(65, 18, f"Receita: {format_real(df['Receita (R$)'].sum())}", border=0, ln=0, align="C", fill=True)
    if 'Redução GEE (tCO2)' in df.columns:
        pdf.cell(65, 18, f"GEE: {format_num(df['Redução GEE (tCO2)'].sum(), 2)} tCO2", border=0, ln=1, align="C", fill=True)
    else:
        pdf.cell(65, 18, "", border=0, ln=1, align="C", fill=True)
    pdf.ln(6)
    pdf.set_draw_color(205, 183, 151)
    pdf.set_line_width(0.5)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(6)
    # Resumo por mês
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(71, 50, 40)
    pdf.cell(0, 10, "Resumo por mês:", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.set_text_color(61, 41, 28)
    meses = df.groupby(['Ano', 'MesNum']).agg({
        'Geração (kWh)': 'sum',
        'Receita (R$)': 'sum',
        'Redução GEE (tCO2)': 'sum'
    }).reset_index()
    for _, row in meses.iterrows():
        mes_num = int(row['MesNum']) if not pd.isnull(row['MesNum']) else 0
        pdf.cell(0, 8, f"{row['Ano']}/{mes_num:02d} - Energia: {format_num(row['Geração (kWh)'], 0)}, Receita: {format_real(row['Receita (R$)'])}, GEE: {format_num(row['Redução GEE (tCO2)'], 2)}", ln=True)
    pdf.ln(8)
    # Gráficos com borda e melhorias visuais
    def add_graph(data, col, color, title, ylabel):
        import calendar
        meses_labels = [calendar.month_abbr[m].capitalize() for m in data['MesNum']]
        fig, ax = plt.subplots(figsize=(7, 4.2))
        bars = ax.bar(meses_labels, data[col], color=color, edgecolor='#473228', linewidth=1.2)
        ax.set_title(title, fontsize=12, color='#473228', pad=12)
        ax.set_xlabel('Mês', fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.grid(axis='y', linestyle='--', alpha=0.25)
        ax.tick_params(axis='x', labelsize=10)
        ax.tick_params(axis='y', labelsize=10)
        # Adiciona rótulos de valor em cada barra
        for bar, value in zip(bars, data[col]):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{int(value):,}'.replace(",", "."),
                    ha='center', va='bottom', fontsize=10, color='#473228', fontweight='bold')
        # Legenda fora do gráfico, canto superior esquerdo
        ax.legend(["Sistemas Fotovoltaicos Prefeitura"], loc='upper left', bbox_to_anchor=(0, 1.08), fontsize=10, frameon=False)
        # Ajusta margens para alinhamento perfeito
        fig.subplots_adjust(left=0.15, right=0.97, top=0.85, bottom=0.22)
        ax.set_position([0.15, 0.22, 0.75, 0.63])
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            fig.savefig(tmp.name, dpi=180)
            plt.close(fig)
            pdf.image(tmp.name, x=25, w=160)
    add_graph(meses, 'Geração (kWh)', '#FFC93C', 'Geração de Energia (kWh) por Mês', 'kWh')
    add_graph(meses, 'Receita (R$)', '#8d6052', 'Receita (R$) por Mês', 'R$')
    if 'Redução GEE (tCO2)' in meses.columns:
        add_graph(meses, 'Redução GEE (tCO2)', '#3A9425', 'Redução GEE (tCO2) por Mês', 'tCO2')
    pdf.set_y(-30)
    pdf.set_font("Arial", size=9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 10, "© Sistemas Fotovoltaicos e Mobilidade Elétrica - CEAMAZON - 2025", align="C")
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return pdf_bytes
