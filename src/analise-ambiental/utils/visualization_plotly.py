"""
============================================
Arquivo: visualization_plotly.py
--------------------------------------------
Preparação e geração de gráficos 3D interativos Plotly:
- _load_data: carrega CSV resumido, parseia timestamp, extrai ano/mês,
  calcula médias mensais de MP10 e MP2.5 por estação.
- _DATA: cache global dos dados processados.
- generate_plotly_html: decora e retorna HTML embed de gráfico 3D Plotly
  com superfícies por estação e ano, configura layout, cores e hovertemplate.
- Usa lru_cache para evitar recálculo ao mudar apenas a métrica.
============================================
"""

import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from functools import lru_cache

def _load_data():
    """
    Carrega e prepara os dados do arquivo CSV 'database_resumido.csv' para geração de gráficos Plotly.
    
    - Lê o CSV, converte a coluna 'timestamp' em índice datetime.
    - Extrai ano e mês como colunas separadas.
    - Para cada estação, agrupa médias mensais de MP10 e MP2.5.
    - Retorna um dicionário contendo:
        * "mp10": DataFrame com médias mensais de MP10 por estação/ano/mês
        * "mp2.5": DataFrame com médias mensais de MP2.5 por estação/ano/mês
        * "stations": lista de estações processadas
        * "years": lista de anos encontrados no índice
    """
    # Caminho absoluto até este arquivo
    base_dir = os.path.dirname(__file__)
    # Constrói o caminho até o CSV de dados resumidos
    csv_path = os.path.abspath(
        os.path.join(base_dir, '..', '..', 'tratamento-dos-dados', 'database_resumido.csv')
    )

    # Lê o CSV em DataFrame, parsing da coluna 'timestamp' como datetime
    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    # Define 'timestamp' como índice do DataFrame
    df.set_index("timestamp", inplace=True)
    # Adiciona colunas auxiliares para ano e mês
    df["year"]  = df.index.year
    df["month"] = df.index.month

    # Lista fixa de estações a serem incluídas na análise
    stations = ["EAMA11","EAMA21","EAMA31","EAMA41"]

    def prepare(suffix):
        """
        Preparação de dados para um indicador (suffix):
        
        - Itera sobre cada estação em 'stations'.
        - Converte a coluna específica (e.g. 'EAMA11_MP10_media') para numérico.
        - Monta um DataFrame temporário com colunas: value, year, month, station.
        - Concatena todos os DataFrames e calcula média por (year, station, month).
        """
        recs = []
        for st in stations:
            # Tenta converter valores para numérico, valores inválidos viram NaN
            ser = pd.to_numeric(df[f"{st}_{suffix}"], errors="coerce")
            # Cria DataFrame temporário com colunas padronizadas
            recs.append(pd.DataFrame({
                "value":   ser,
                "year":    df["year"],
                "month":   df["month"],
                "station": st
            }))
        # Concatena todos e agrupa por ano, estação e mês, calculando média
        return (
            pd.concat(recs, ignore_index=True)
              .groupby(["year", "station", "month"], as_index=False)
              .mean()
        )

    # Chama 'prepare' para MP10 e MP2.5 e retorna dicionário com resultados
    return {
        "mp10":     prepare("MP10_media"),
        "mp2.5":    prepare("MP2.5_media"),
        "stations": stations,
        "years":    sorted(df.index.year.unique())
    }

# Carrega uma vez os dados preparados para uso nas gerações de gráficos
_DATA = _load_data()

@lru_cache(maxsize=32)
def generate_plotly_html(metric: str) -> str:
    """
    Gera o HTML embutido de um gráfico Plotly 3D para o indicador especificado.
    
    Parâmetros:
    - metric: "mp10" ou "mp2.5", define qual conjunto de dados usar.

    Retorna:
    - String HTML com a figura Plotly pronta para ser inserida em template.
    """
    # Obtém o DataFrame agrupado conforme o indicador escolhido
    grouped  = _DATA[metric]
    # Meses do ano (1 a 12) e listas de estações e anos disponíveis
    months   = list(range(1, 13))
    stations = _DATA["stations"]
    years    = _DATA["years"]

    # Espaçamento e espessura das camadas no eixo Y
    spacing   = 1.2
    thickness = 1.0

    # Nomes de meses para exibir nos ticks do eixo X
    month_names = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]

    # Cores customizadas por ano (fallback para paleta Plotly se o ano não estiver no dicionário)
    CUSTOM_YEAR_COLORS = {
        2024: "#ee363b",  # vermelho
        2023: "#13b9d3",  # verde
        2022: "#ffda27",  # amarelo
    }
    palette = px.colors.qualitative.Plotly
    colors = {}
    for i, yr in enumerate(years):
        # Usa cor custom se disponível, caso contrário paleta padrão
        if yr in CUSTOM_YEAR_COLORS:
            colors[yr] = CUSTOM_YEAR_COLORS[yr]
        else:
            colors[yr] = palette[i % len(palette)]

    # Inicializa a figura Plotly vazia
    fig = go.Figure()

    # Para cada ano, cria uma superfície 3D de linhas representando cada estação
    for yr in years:
        # Filtra dados do ano atual e rearranja em formato de matriz mês x estação
        sub = grouped[grouped["year"] == yr]
        pivot = (
            sub
            .pivot(index="station", columns="month", values="value")
            .reindex(stations)           # garante ordem das estações
            .reindex(columns=months)    # garante ordem dos meses
        )
        Z = pivot.values  # matriz de valores
        c = colors[yr]    # cor atribuída a este ano

        # Para cada estação, plota uma faixa no gráfico de superfície
        for i, st in enumerate(stations):
            # Extrai a linha correspondente à estação
            row = Z[i:i+1, :]
            # Duplica para formar uma pequena faixa (espessura)
            Z2 = [list(row[0]), list(row[0])]
            # Calcula posição vertical da faixa
            y0     = i * spacing
            y_vals = [y0, y0 + thickness]

            # Adiciona o trace Surface ao gráfico
            fig.add_trace(go.Surface(
                x=months,                       # coordenadas X: meses
                y=y_vals,                       # coordenadas Y: faixa fina por estação
                z=Z2,                           # valores Z: média mensal
                name=str(yr),                   # etiqueta de legenda para o ano
                legendgroup=str(yr),            # agrupa legendas por ano
                showlegend=(i == 0),            # mostra legenda apenas na primeira estação
                colorscale=[[0, c], [1, c]],    # cor fixa para toda a superfície
                showscale=False,                # não exibe barra de cores
                opacity=0.8,                    # transparência da superfície
                hovertemplate=(                # template do hover
                    f"Ano: {yr}<br>"
                    "Mês: %{x}<br>"
                    f"Estação: {st}<br>"
                    "Valor Médio de MP (µg/m³): %{z:.1f}<extra></extra>"
                )
            ))

    # Define o título do gráfico conforme o indicador selecionado
    title = "MP10 Média" if metric == "mp10" else "MP2.5 Média"

    # Atualiza layout geral da figura
    fig.update_layout(
        # Configurações do título do gráfico
        title=dict(
            text=title,
            font=dict(
                family="Inter, sans-serif",  # Fonte do título
                size=22,                     # Tamanho da fonte
                color="white"                # Cor do texto
            ),
            x=0.15,    # Posição horizontal (0=esquerda, 1=direita)
            y=0.91,    # Posição vertical (0=embaixo, 1=topo)
            xanchor="right",  # Alinhamento horizontal em relação ao x
            yanchor="top"     # Alinhamento vertical em relação ao y
        ),
        # Cores de fundo transparentes para integrar ao tema escuro
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        # Cor padrão do texto no gráfico
        font=dict(color="white"),
        # Dimensões da figura em pixels
        width=1200,
        height=800,
        # Configuração do sistema de eixos 3D (scene)
        scene=dict(
            aspectmode='cube',  # Mantém proporção cúbica nos eixos
            camera=dict(
                eye   = dict(x=-1.9, y=1.9, z=1.0),    # Posição da "câmera"
                center= dict(x=-0.15, y=0.0, z=-0.6),  # Centro focal da cena
                up    = dict(x=0, y=0, z=1)            # Vetor "up" da câmera
            ),
            dragmode='turntable',  # Modo de interação de rotação
            # Eixo X: Meses
            xaxis=dict(
                title=dict(text="Mês", font=dict(color="white")),
                tickmode="array",
                tickvals=months,               # Valores dos ticks (1–12)
                ticktext=month_names,          # Nomes dos meses
                showbackground=False,
                gridcolor="white",
                zerolinecolor="white",
                tickfont=dict(color="white")
            ),
            # Eixo Y: Estações
            yaxis=dict(
                title=dict(text="Estação de Qualidade do Ar", font=dict(color="white")),
                tickmode="array",
                # Calcula posições dos ticks centralizados nas faixas
                tickvals=[i * spacing + thickness / 2 for i in range(len(stations))],
                ticktext=stations,  # Rótulos das estações
                # Define limites do eixo Y para abranger todas as faixas
                range=[-thickness / 2,
                       (len(stations) - 1) * spacing + thickness + thickness / 2],
                showbackground=False,
                gridcolor="white",
                zerolinecolor="white",
                tickfont=dict(color="white")
            ),
            # Eixo Z: Valor médio
            zaxis=dict(
                title=dict(text="Valor Médio de MP", font=dict(color="white")),
                showbackground=False,
                gridcolor="white",
                zerolinecolor="white",
                tickfont=dict(color="white")
            )
        ),
        # Margens externas do gráfico para ajustar espaçamentos
        margin=dict(l=0, r=10, t=100, b=0),
        # Configurações da legenda
        legend=dict(
            title=dict(text="Selecione o Ano:", font=dict(color="white")),
            orientation='h',        # Legenda horizontal
            x=0.95, y=1.0,          # Posição da legenda
            xanchor='right',        # Alinhamento horizontal da legenda
            yanchor='bottom',       # Alinhamento vertical da legenda
            bgcolor="rgba(39,39,39,0.5)",  # Fundo semi-transparente
            bordercolor="white",    # Cor da borda
            borderwidth=0,
            font=dict(color='white')
        )
    )

    # Converte a figura para HTML embutido (sem <html> completo),
    # incluindo Plotly.js via CDN e configura opções de interação.
    return fig.to_html(
        full_html=False,             # não inclui tags <html>/<body>
        include_plotlyjs="cdn",      # carrega Plotly.js de CDN
        config={
            'scrollZoom': False,      # desativa zoom via scroll
            'plotGlPixelRatio': 1.1   # ajusta densidade de pixels WebGL
        }
    )

