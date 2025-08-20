"""
============================================
Arquivo: visualization_gradient.py (AJUSTADO p/ database_resumido.csv)
--------------------------------------------
Geração de imagens de gradiente (heatmaps) para indicadores de qualidade do ar:
- Usa 'database_resumido.csv' (irmão do 'new_database.csv').
- Mantém as funções públicas: generate_gradient_image, generate_max_gradient_image,
  generate_min_gradient_image — cada uma retorna uma data-URI PNG.
- Compatível com a chamada existente no app.py:
    generate_gradient_image(csv_path=NEW_DATABASE_PATH)  # se vier new_database.csv,
                                                         # o código troca p/ database_resumido.csv
============================================
"""

import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # backend sem display
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO
from matplotlib.colors import LinearSegmentedColormap
from typing import List, Tuple


# ---------------------------------------------------------------------
# Cores e colormaps (mantidos)
# ---------------------------------------------------------------------
_COLORS = [
    "#006b3d",  # verde escuro (boa qualidade)
    "#069c56",  # verde claro (moderada)
    "#ff980e",  # laranja (ruim)
    "#ff681e",  # laranja escuro (muito ruim)
    "#d3212c"   # vermelho (péssima)
]
_DARK_BG = "#111111"
_WHITE   = "white"

_CMAP_MEAN = LinearSegmentedColormap.from_list("mean", _COLORS)
_CMAP_MAX  = LinearSegmentedColormap.from_list("max",  _COLORS[1:])
_CMAP_MIN  = LinearSegmentedColormap.from_list("min",  _COLORS[:-1])


# ---------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------
def _encode_figure_to_datauri(fig) -> str:
    buf = BytesIO()
    fig.savefig(
        buf,
        format='png',
        bbox_inches='tight',
        facecolor=fig.get_facecolor()
    )
    plt.close(fig)
    buf.seek(0)
    data = base64.b64encode(buf.read()).decode('utf-8')
    return f"data:image/png;base64,{data}"


def _style_axes(ax):
    ax.set_facecolor(_DARK_BG)
    ax.title.set_color(_WHITE)
    ax.title.set_fontsize(20)
    ax.xaxis.label.set_color(_WHITE)
    ax.xaxis.label.set_fontsize(18)
    ax.yaxis.label.set_color(_WHITE)
    ax.yaxis.label.set_fontsize(18)
    ax.tick_params(colors=_WHITE, labelsize=13)


def _style_colorbar(cbar):
    cbar.outline.set_edgecolor(_WHITE)
    cbar.ax.yaxis.set_tick_params(labelcolor=_WHITE, labelsize=13)
    cbar.ax.set_facecolor(_DARK_BG)


def _resolve_resumido_path(csv_path: str | None) -> str:
    """
    Resolve o caminho final do CSV a ser lido.

    Regras:
    1) Se 'csv_path' apontar para 'database_resumido.csv' existente -> usa.
    2) Se 'csv_path' apontar para 'new_database.csv', tenta trocar para
       'database_resumido.csv' na mesma pasta -> se existir, usa.
    3) Se existir a env var DATABASE_RESUMIDO_PATH, usa.
    4) Caminho padrão relativo: .../tratamento-dos-dados/database_resumido.csv
    5) Fallback: varredura na árvore do projeto para encontrar 'database_resumido.csv'.
    """
    # 1) chamado diretamente com database_resumido.csv
    if csv_path and os.path.basename(csv_path) == "database_resumido.csv" and os.path.exists(csv_path):
        return csv_path

    # 2) se veio new_database.csv, troca pelo irmão database_resumido.csv
    if csv_path and os.path.basename(csv_path) == "new_database.csv" and os.path.exists(csv_path):
        brother = os.path.join(os.path.dirname(csv_path), "database_resumido.csv")
        if os.path.exists(brother):
            return brother

    # 3) env var
    env = os.environ.get("DATABASE_RESUMIDO_PATH")
    if env and os.path.exists(env):
        return env

    # 4) caminho padrão relativo à estrutura do projeto
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src_dir  = os.path.abspath(os.path.join(base_dir, ".."))
    candidate = os.path.join(src_dir, "tratamento-dos-dados", "database_resumido.csv")
    if os.path.exists(candidate):
        return candidate

    # 5) fallback: varre
    for root, _, files in os.walk(src_dir):
        if "database_resumido.csv" in files:
            return os.path.join(root, "database_resumido.csv")

    raise FileNotFoundError(
        "Não foi possível localizar 'database_resumido.csv'. "
        "Defina DATABASE_RESUMIDO_PATH ou confira a árvore do projeto."
    )


def _collect_pollutants_columns(df: pd.DataFrame) -> List[Tuple[str, List[str]]]:
    """
    Retorna lista [(pollutant, cols_media), ...] apenas para poluentes existentes.
    Espera colunas no padrão: <ESTACAO>_<POLUENTE>_media
      Ex.: EAMA11_MP10_media, EAMA21_MP2.5_media, ...
    """
    pollutants = ["MP2.5", "MP10", "PTS"]
    result: List[Tuple[str, List[str]]] = []
    for pol in pollutants:
        cols = [c for c in df.columns if c.endswith("_media") and f"_{pol}_" in c]
        if cols:
            result.append((pol, cols))
    return result


def _build_metric_series(df: pd.DataFrame, cols: List[str], how: str) -> pd.Series:
    """
    A partir das colunas de estações (string -> numérico), calcula por timestamp:
    - 'mean': média entre estações
    - 'max' : máximo entre estações
    - 'min' : mínimo entre estações
    Retorna uma Series indexada por timestamp.
    """
    # empilha -> numérico -> volta para colunas -> aplica agregação por linha
    wide = (
        pd.to_numeric(df[cols].stack(), errors="coerce")
          .unstack()
    )
    if how == "mean":
        return wide.mean(axis=1)
    if how == "max":
        return wide.max(axis=1)
    if how == "min":
        return wide.min(axis=1)
    raise ValueError("how deve ser 'mean', 'max' ou 'min'")


def _make_heatmap(df: pd.DataFrame, values_col: str, title: str, cmap):
    """
    Desenha um heatmap (mês × ano) de uma coluna numérica.
    df precisa ter colunas: ['year','month', values_col]
    """
    pivot = (
        df.pivot_table(index="month", columns="year", values=values_col, aggfunc="mean")
          .sort_index()
    )

    ax = plt.gca()
    im = ax.imshow(
        pivot.values,
        aspect='auto',
        origin='lower',
        cmap=cmap
    )

    ax.set_title(title)
    ax.set_ylabel('Mês')
    ax.set_xlabel('Ano')

    ax.set_yticks(np.arange(pivot.shape[0]))
    ax.set_yticklabels(pivot.index)

    ax.set_xticks(np.arange(pivot.shape[1]))
    ax.set_xticklabels(pivot.columns, rotation=45)

    _style_axes(ax)

    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    _style_colorbar(cbar)


def _generate_any_gradient(csv_path: str | None, how: str, cmap) -> str:
    """
    Implementa o núcleo das três funções públicas.
    - how: 'mean' | 'max' | 'min'
    - cmap: colormap a utilizar
    Retorna data-URI PNG.
    """
    # Resolve o caminho real do database_resumido.csv
    resumido_path = _resolve_resumido_path(csv_path)

    # Lê e prepara
    df = pd.read_csv(resumido_path, parse_dates=['timestamp']).set_index('timestamp')
    # Descobre quais poluentes existem no resumido
    pol_cols = _collect_pollutants_columns(df)
    if not pol_cols:
        raise ValueError("Nenhum poluente com colunas '*_media' encontrado no database_resumido.csv.")

    # Para cada poluente disponível, gera uma série por timestamp conforme 'how'
    series_by_pol = {}
    for pol, cols in pol_cols:
        series_by_pol[pol] = _build_metric_series(df, cols, how=how)

    # Monta DF único com year/month + colunas por poluente
    out = pd.DataFrame(index=df.index)
    out["year"] = out.index.year
    out["month"] = out.index.month
    for pol, ser in series_by_pol.items():
        out[f"{pol}_{how}"] = ser

    # Cria figura com N subplots (um por poluente disponível, na ordem MP2.5, MP10, PTS)
    order = [p for p in ["MP2.5", "MP10", "PTS"] if f"{p}_{how}" in out.columns]
    n = len(order)
    fig, axes = plt.subplots(
        1, n,
        figsize=(6*n, 6),
        constrained_layout=True
    )
    fig.patch.set_facecolor(_DARK_BG)

    if n == 1:
        axes = [axes]  # normaliza para iterar

    for ax, pol in zip(axes, order):
        plt.sca(ax)
        _make_heatmap(out, f"{pol}_{how}", f"{pol} {how.capitalize()}", cmap)

    return _encode_figure_to_datauri(fig)


# ---------------------------------------------------------------------
# API pública (nomes mantidos p/ compatibilidade com app.py)
# ---------------------------------------------------------------------
def generate_gradient_image(csv_path: str | None = None) -> str:
    """
    Gera heatmaps (mês × ano) das MÉDIAS para os poluentes disponíveis no
    'database_resumido.csv' (MP2.5, MP10 e/ou PTS), retornando uma data-URI PNG.
    Se 'csv_path' vier apontando para 'new_database.csv', será automaticamente
    trocado para 'database_resumido.csv' na mesma pasta.
    """
    return _generate_any_gradient(csv_path, how="mean", cmap=_CMAP_MEAN)


def generate_max_gradient_image(csv_path: str | None = None) -> str:
    """
    Gera heatmaps (mês × ano) dos MÁXIMOS para os poluentes disponíveis.
    """
    return _generate_any_gradient(csv_path, how="max", cmap=_CMAP_MAX)


def generate_min_gradient_image(csv_path: str | None = None) -> str:
    """
    Gera heatmaps (mês × ano) dos MÍNIMOS para os poluentes disponíveis.
    """
    return _generate_any_gradient(csv_path, how="min", cmap=_CMAP_MIN)
