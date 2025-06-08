"""
============================================
Arquivo: visualization_gradient.py
--------------------------------------------
Geração de imagens de gradiente (heatmaps) para indicadores de qualidade do ar:
- Define cores base e colormaps (_CMAP_MEAN, _CMAP_MAX, _CMAP_MIN).
- _encode_figure_to_datauri: converte figura Matplotlib em data URI Base64.
- _style_axes e _style_colorbar: aplicam tema escuro e estilo consistente.
- _make_heatmap: desenha heatmap mensal×anual de um poluente.
- generate_gradient_image: heatmaps de médias mensais × anuais para MP2.5, MP10 e PTS.
- generate_max_gradient_image: mesmos heatmaps, mas de valores máximos.
- generate_min_gradient_image: mesmos heatmaps, mas de valores mínimos.
- Cada função retorna URI para uso inline em templates HTML.
============================================
"""

import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # usa backend 'Agg' para renderizar figuras em background (sem display)
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO
from matplotlib.colors import LinearSegmentedColormap

# -----------------------------------------------------------------------------
# Constantes de cores para os gradientes de classificação de qualidade do ar
# -----------------------------------------------------------------------------
_COLORS = [
    "#006b3d",  # verde escuro (boa qualidade)
    "#069c56",  # verde claro (moderada)
    "#ff980e",  # laranja (ruim)
    "#ff681e",  # laranja escuro (muito ruim)
    "#d3212c"   # vermelho (péssima)
]
_DARK_BG = "#272727"  # cor de fundo escuro para gráficos
_WHITE   = "white"    # cor branca para textos e ticks

# -----------------------------------------------------------------------------
# Criação de colormaps personalizados a partir da lista de cores base
# -----------------------------------------------------------------------------
_CMAP_MEAN = LinearSegmentedColormap.from_list("mean", _COLORS)
_CMAP_MAX  = LinearSegmentedColormap.from_list("max",  _COLORS[1:])   # exclui o primeiro verde escuro
_CMAP_MIN  = LinearSegmentedColormap.from_list("min",  _COLORS[:-1])  # exclui o vermelho intenso

def _encode_figure_to_datauri(fig):
    """
    Converte uma figura Matplotlib em uma URI de dados Base64 PNG.
    - Salva a figura em um buffer em memória.
    - Fecha a figura para liberar recursos.
    - Retorna string 'data:image/png;base64,...' pronta para uso em <img src="...">.
    """
    buf = BytesIO()
    fig.savefig(
        buf,
        format='png',
        bbox_inches='tight',               # elimina margens em branco
        facecolor=fig.get_facecolor()      # preserva cor de fundo da figura
    )
    plt.close(fig)                         # fecha a figura para não acumular na memória
    buf.seek(0)
    # codifica o conteúdo do buffer em Base64
    data = base64.b64encode(buf.read()).decode('utf-8')
    return f"data:image/png;base64,{data}"

def _style_axes(ax):
    """
    Aplica estilo consistente ao eixo de um gráfico:
    - Fundo escuro
    - Título e labels em branco
    - Tamanhos de fonte ajustados para legibilidade
    """
    ax.set_facecolor(_DARK_BG)
    # Estilo do título do eixo
    ax.title.set_color(_WHITE)
    ax.title.set_fontsize(16)
    # Estilo dos rótulos dos eixos X e Y
    ax.xaxis.label.set_color(_WHITE)
    ax.xaxis.label.set_fontsize(14)
    ax.yaxis.label.set_color(_WHITE)
    ax.yaxis.label.set_fontsize(14)
    # Estilo dos ticks
    ax.tick_params(colors=_WHITE, labelsize=12)

def _style_colorbar(cbar):
    """
    Ajusta estilo da barra de cores (colorbar):
    - Contorno branco
    - Fundo escuro
    - Ticks em branco
    """
    cbar.outline.set_edgecolor(_WHITE)
    cbar.ax.yaxis.set_tick_params(labelcolor=_WHITE, labelsize=12)
    cbar.ax.set_facecolor(_DARK_BG)

def _make_heatmap(df, values_col, title, cmap):
    """
    Desenha um heatmap para os valores médios mensais de um poluente ao longo dos anos.
    
    Parâmetros:
    - df: DataFrame com colunas 'year', 'month' e a coluna de valores.
    - values_col (str): nome da coluna no df que contém os valores a serem plotados.
    - title (str): título do heatmap.
    - cmap: colormap Matplotlib a ser usado.
    """
    # monta tabela pivot com meses nas linhas, anos nas colunas e média dos valores
    pivot = df.pivot_table(
        index='month',
        columns='year',
        values=values_col,
        aggfunc='mean'
    ).sort_index()

    ax = plt.gca()  # pega o eixo atual para plotagem
    # plota matriz de valores como imagem, com origem "lower" para mês 1 embaixo
    im = ax.imshow(
        pivot.values,
        aspect='auto',
        origin='lower',
        cmap=cmap
    )

    # configurações de rótulos e títulos
    ax.set_title(title)
    ax.set_ylabel('Mês')
    ax.set_xlabel('Ano')

    # ajusta ticks de mês (eixo Y)
    ax.set_yticks(np.arange(pivot.shape[0]))
    ax.set_yticklabels(pivot.index)

    # ajusta ticks de ano (eixo X), rotacionando para melhor leitura
    ax.set_xticks(np.arange(pivot.shape[1]))
    ax.set_xticklabels(pivot.columns, rotation=45)

    _style_axes(ax)  # aplica tema escuro e estilo consistente aos eixos

    # adiciona barra de cores ao lado do heatmap
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    _style_colorbar(cbar)  # aplica estilo ao colorbar

def generate_gradient_image(csv_path):
    """
    Gera um colormap em gradiente para IQAr (MP2.5, MP10) e PTS.
    - Lê arquivo CSV com timestamp e valores médios por estação.
    - Calcula média mensal × anual para cada poluente.
    - Plota três heatmaps lado a lado com tema escuro.
    - Retorna imagem codificada em data URI (Base64 PNG).
    """
    # carrega dados e define timestamp como índice
    df = pd.read_csv(csv_path, parse_dates=['timestamp']).set_index('timestamp')

    # calcula, para cada poluente, a média diária média de todas as estações
    for pollutant, suffix in [
        ("MP2.5", "_MP2.5_media"),
        ("MP10",  "_MP10_media"),
        ("PTS",   "_PTS_media")
    ]:
        # seleciona colunas que terminam com o sufixo
        cols = [c for c in df.columns if c.endswith(suffix)]
        # empilha por estação, converte em numérico e calcula a média diária
        df[f"{pollutant}_mean"] = (
            pd.to_numeric(df[cols].stack(), errors='coerce')
              .unstack()
              .mean(axis=1)
        )

    # extrai ano e mês a partir do índice de datas
    df['year'], df['month'] = df.index.year, df.index.month

    # cria figura com 3 subplots (um para cada poluente)
    fig, axes = plt.subplots(
        1, 3,
        figsize=(18, 6),
        constrained_layout=True
    )
    fig.patch.set_facecolor(_DARK_BG)  # fundo escuro para toda a figura

    # desenha cada heatmap em seu eixo correspondente
    plt.sca(axes[0])
    _make_heatmap(df, "MP2.5_mean", "MP2.5 IQAr Média", _CMAP_MEAN)

    plt.sca(axes[1])
    _make_heatmap(df, "MP10_mean",  "MP10 IQAr Média",  _CMAP_MEAN)

    plt.sca(axes[2])
    _make_heatmap(df, "PTS_mean",   "PTS Média",        _CMAP_MEAN)

    # converte figura para data URI e retorna para uso inline em HTML
    return _encode_figure_to_datauri(fig)

def generate_max_gradient_image(csv_path):
    """
    Gera mapa de calor com os valores MÁXIMOS mensais × anuais para MP2.5, MP10 e PTS.
    Utiliza o colormap _CMAP_MAX (sem o verde mais escuro).
    
    Parâmetros:
    - csv_path (str): caminho para o CSV de dados com timestamp e valores por estação.
    
    Retorna:
    - data URI contendo uma imagem PNG Base64 do gráfico gerado.
    """
    # carrega dados e define timestamp como índice
    df = pd.read_csv(csv_path, parse_dates=['timestamp']).set_index('timestamp')

    # para cada poluente, calcula o valor máximo diário entre todas as estações
    for pollutant, suffix in [
        ("MP2.5", "_MP2.5_media"),
        ("MP10",  "_MP10_media"),
        ("PTS",   "_PTS_media")
    ]:
        # seleciona as colunas daquele poluente
        cols = [c for c in df.columns if c.endswith(suffix)]
        # empilha por estação, converte em numérico e extrai o máximo ao longo das colunas
        df[f"{pollutant}_max"] = (
            pd.to_numeric(df[cols].stack(), errors='coerce')
              .unstack()
              .max(axis=1)
        )

    # extrai ano e mês para agrupamento no heatmap
    df['year'], df['month'] = df.index.year, df.index.month

    # cria figura com 3 subplots (um para cada poluente) e tema escuro
    fig, axes = plt.subplots(
        1, 3,
        figsize=(18, 6),
        constrained_layout=True
    )
    fig.patch.set_facecolor(_DARK_BG)

    # plota cada heatmap no subplot correspondente
    plt.sca(axes[0])
    _make_heatmap(df, "MP2.5_max", "MP2.5 IQAr Máximo", _CMAP_MAX)

    plt.sca(axes[1])
    _make_heatmap(df, "MP10_max",  "MP10 IQAr Máximo",  _CMAP_MAX)

    plt.sca(axes[2])
    _make_heatmap(df, "PTS_max",   "PTS Máximo",        _CMAP_MAX)

    # retorna a figura codificada como data URI para uso inline
    return _encode_figure_to_datauri(fig)

def generate_min_gradient_image(csv_path):
    """
    Gera mapa de calor com os valores MÍNIMOS mensais × anuais para MP2.5, MP10 e PTS.
    Utiliza o colormap _CMAP_MIN (sem o vermelho mais intenso).
    
    Parâmetros:
    - csv_path (str): caminho para o CSV de dados com timestamp e valores por estação.
    
    Retorna:
    - data URI contendo uma imagem PNG Base64 do gráfico gerado.
    """
    # carrega dados e define timestamp como índice
    df = pd.read_csv(csv_path, parse_dates=['timestamp']).set_index('timestamp')

    # para cada poluente, calcula o valor mínimo diário entre todas as estações
    for pollutant, suffix in [
        ("MP2.5", "_MP2.5_media"),
        ("MP10",  "_MP10_media"),
        ("PTS",   "_PTS_media")
    ]:
        # seleciona as colunas daquele poluente
        cols = [c for c in df.columns if c.endswith(suffix)]
        # empilha por estação, converte em numérico e extrai o mínimo ao longo das colunas
        df[f"{pollutant}_min"] = (
            pd.to_numeric(df[cols].stack(), errors='coerce')
              .unstack()
              .min(axis=1)
        )

    # extrai ano e mês para agrupamento no heatmap
    df['year'], df['month'] = df.index.year, df.index.month

    # cria figura com 3 subplots (um para cada poluente) e tema escuro
    fig, axes = plt.subplots(
        1, 3,
        figsize=(18, 6),
        constrained_layout=True
    )
    fig.patch.set_facecolor(_DARK_BG)

    # plota cada heatmap no subplot correspondente
    plt.sca(axes[0])
    _make_heatmap(df, "MP2.5_min", "MP2.5 IQAr Mínimo", _CMAP_MIN)

    plt.sca(axes[1])
    _make_heatmap(df, "MP10_min",  "MP10 IQAr Mínimo",  _CMAP_MIN)

    plt.sca(axes[2])
    _make_heatmap(df, "PTS_min",   "PTS Mínimo",        _CMAP_MIN)

    # retorna a figura codificada como data URI para uso inline
    return _encode_figure_to_datauri(fig)
