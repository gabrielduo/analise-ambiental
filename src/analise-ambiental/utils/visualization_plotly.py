"""
============================================
Arquivo: visualization_plotly.py
--------------------------------------------
Visual 3D com Plotly:
- _load_data: lê CSV resumido e monta médias mensais por estação/ano.
- generate_plotly_html:
    * 1 trace Scatter3d por estação/ano (linha grossa).
    * Overlays (JS) para filtrar ESTAÇÕES e ANOS sem deslocar layout.
    * Sem legenda nativa do Plotly.
============================================
"""

import os
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from functools import lru_cache


def _load_data():
    base_dir = os.path.dirname(__file__)
    csv_path = os.path.abspath(
        os.path.join(base_dir, '..', '..', 'tratamento-dos-dados', 'database_resumido.csv')
    )

    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    df["year"]  = df.index.year
    df["month"] = df.index.month

    stations = ["EAMA11", "EAMA21", "EAMA31", "EAMA41"]

    def prepare(suffix):
        recs = []
        for st in stations:
            ser = pd.to_numeric(df[f"{st}_{suffix}"], errors="coerce")
            recs.append(pd.DataFrame({
                "value":   ser,
                "year":    df["year"],
                "month":   df["month"],
                "station": st
            }))
        return (
            pd.concat(recs, ignore_index=True)
              .groupby(["year", "station", "month"], as_index=False)
              .mean()
        )

    return {
        "mp10":     prepare("MP10_media"),
        "mp2.5":    prepare("MP2.5_media"),
        "stations": stations,
        "years":    sorted(df.index.year.unique())
    }


_DATA = _load_data()


def _upsample_line(x_pos, z_vals, factor: int):
    """
    Densifica a linha entre os pontos (x_pos) para suavizar no Scatter3d.
    x_pos: lista de posições X (em float) de cada mês após aplicar x_spacing.
    """
    if factor <= 1:
        return x_pos, z_vals
    x = np.array(x_pos, dtype=float)
    z = np.array(z_vals, dtype=float)
    x_dense = np.linspace(x.min(), x.max(), num=(len(x) - 1) * factor + 1)
    z_dense = np.interp(x_dense, x, z)
    return x_dense.tolist(), z_dense.tolist()


@lru_cache(maxsize=32)
def generate_plotly_html(metric: str) -> str:
    grouped  = _DATA[metric]
    months   = list(range(1, 13))
    stations = _DATA["stations"]
    years    = _DATA["years"]

    # -------- Geometria --------
    # Eixo Y (estações)
    spacing   = 4.0   # distância entre estações (eixo Y)
    thickness = 0.7   # só para centralizar ticks/limites de Y

    # Eixo X (meses) – abre espaçamento visual
    x_spacing = 1.6   # >= 1.0 -> meses mais espaçados
    x_offset  = 0.0   # deslocamento opcional (normalmente 0.0)
    x_positions = [ (m - 1) * x_spacing + x_offset for m in months ]

    # Alongamento físico do eixo X no cubo 3D (efeito visual extra)
    x_scale = 2.0  # >=1.0; aumentar para “esticar” X

    # -------- Linha --------
    line_width_px      = 16
    upsample_per_month = 20

    month_names = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]

    CUSTOM_YEAR_COLORS = {
        2025: "#44AF69",
        2024: "#F8333C",
        2023: "#FCAB10",
        2022: "#2B9EB3",
    }
    palette = px.colors.qualitative.Plotly
    colors = {yr: CUSTOM_YEAR_COLORS.get(yr, palette[i % len(palette)])
              for i, yr in enumerate(years)}

    fig = go.Figure()

    # meta de traces para controlar visibilidade no JS
    traces_meta = []  # lista de dicts {idx, station, year}
    station_to_traceidxs = {st: [] for st in stations}
    year_to_traceidxs    = {yr: [] for yr in years}

    # 1 trace por estação/ano
    for yr in years:
        sub = grouped[grouped["year"] == yr]
        pivot = (
            sub.pivot(index="station", columns="month", values="value")
               .reindex(stations)
               .reindex(columns=months)
        )
        Z = pivot.values
        color = colors[yr]

        for i, st in enumerate(stations):
            y0 = i * spacing
            y_mid = y0 + thickness / 2.0
            z_vals = Z[i, :].tolist()

            # curva densa para suavizar a linha
            x_dense, z_dense = _upsample_line(x_positions, z_vals, upsample_per_month)

            # hover: nome do mês aproximado ao x_dense
            month_idx = np.clip(
                np.rint((np.array(x_dense) - x_positions[0]) / x_spacing).astype(int),
                0, 11
            )
            hover_months = [month_names[k] for k in month_idx]

            fig.add_trace(go.Scatter3d(
                x=x_dense,
                y=[y_mid] * len(x_dense),
                z=z_dense,
                mode="lines",
                name=f"{st} • {yr}",           # rótulo interno (sem legenda nativa)
                showlegend=False,              # legenda desativada
                line=dict(color=color, width=line_width_px),
                connectgaps=True,
                text=hover_months,
                hovertemplate=(
                    f"Ano: {yr}<br>"
                    "Mês: %{text}<br>"
                    f"Estação: {st}<br>"
                    "Valor Médio de MP (µg/m³): %{z:.1f}<extra></extra>"
                ),
                opacity=0.85,             
            ))
            idx = len(fig.data) - 1
            traces_meta.append({"idx": idx, "station": st, "year": int(yr)})
            station_to_traceidxs[st].append(idx)
            year_to_traceidxs[yr].append(idx)

    title = "Média de MP10" if metric == "mp10" else "Média de MP2,5"

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(family="Inter, sans-serif", size=24, color="white"),
            x=0.2, y=0.91, xanchor="right", yanchor="top"
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        width=1200, height=800,
        showlegend=False,  # <<< remove legenda nativa
        scene=dict(
            # manual para alongar o X
            aspectmode='manual',
            aspectratio=dict(x=x_scale, y=1.0, z=1.0),

            camera=dict(
                eye=dict(x=-2.1, y=-1.9, z=1.0),
                center=dict(x=-0.05, y=0.0, z=-0.8),
                up=dict(x=0, y=1, z=-1)
            ),
            dragmode='turntable',

            xaxis=dict(
                title=dict(text="Mês", font=dict(color="white")),
                tickmode="array",
                tickvals=x_positions,       # <<< posições espaçadas
                ticktext=month_names,
                showbackground=False, gridcolor="white", zerolinecolor="white",
                tickfont=dict(color="white")
            ),
            yaxis=dict(
                title=dict(text="Estação de Qualidade do Ar", font=dict(color="white")),
                tickmode="array",
                tickvals=[i * spacing + thickness / 2 for i in range(len(stations))],
                ticktext=stations,
                range=[-thickness / 2,
                       (len(stations) - 1) * spacing + thickness + thickness / 2],
                showbackground=False, gridcolor="white", zerolinecolor="white",
                tickfont=dict(color="white"),
                zeroline=False
            ),
            zaxis=dict(
                title=dict(text="Valor Médio de MP (µg/m³)", font=dict(color="white")),
                showbackground=False, gridcolor="white", zerolinecolor="white",
                tickfont=dict(color="white")
            )
        ),
        margin=dict(l=0, r=10, t=100, b=0),
    )

    # ---------- OVERLAYS (JS) ----------
    div_id = "plotly_3d_stats"
    traces_meta_js = json.dumps(traces_meta)
    stations_js    = json.dumps(stations)
    years_js       = json.dumps([int(y) for y in years])

    overlay_css = """
    <style>
      .plot-wrap { position: relative; }
      .overlay-panel {
        position: absolute;
        z-index: 10;
        display: flex; gap: 10px; flex-wrap: wrap;
        background: rgba(25,25,25,0.55);
        padding: 4px 8px; border-radius: 6px;
        backdrop-filter: blur(2px);
      }
      .overlay-panel label, .overlay-panel span, .overlay-panel button {
        color: #fff; font-family: Inter, sans-serif; font-size: 12px;
      }
      .overlay-panel input { vertical-align: middle; margin-right: 4px; }
      .overlay-panel button {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 5px; padding: 2px 8px; cursor: pointer;
      }
      .overlay-panel button:hover { background: rgba(255,255,255,0.16); }
      /* posicionadas à direita */
      #station-controls { top: 6px; right: 20px; }
      #year-controls    { top: 44px; right: 20px; }
      #stats-form       { top: 82px; right: 20px; }
      .color-box {
        display:inline-block;
        width:10px; height:10px;
        margin-right:4px;
        border-radius:2px;
      }
    </style>
    """

    stations_controls = """
<div class="overlay-panel" id="station-controls">
  <span>Estações:</span>
</div>
"""
    years_controls = """
<div class="overlay-panel" id="year-controls">
  <span>Anos:</span>
</div>
"""

    fig_html = fig.to_html(
        full_html=False,
        include_plotlyjs="cdn",
        div_id=div_id,
        config={'scrollZoom': False, 'plotGlPixelRatio': 1.1}
    )

    script = f"""
<script>
(function() {{
  var gd = document.getElementById("{div_id}");
  var tracesMeta = {traces_meta_js};  // list of {{idx, station, year}}
  var stations   = {stations_js};
  var years      = {years_js};

  // paleta de cores por ano (igual ao gráfico)
  var CUSTOM_YEAR_COLORS = {{2025:"#44AF69", 2024:"#F8333C", 2023:"#FCAB10", 2022:"#2B9EB3"}};

  // estados de visibilidade
  var stationVisible = {{}};
  var yearVisible    = {{}};
  stations.forEach(function(s) {{ stationVisible[s] = true; }});
  years.forEach(function(y)    {{ yearVisible[y]    = true; }});

  function applyVisibility() {{
    var vis = new Array(tracesMeta.length);
    for (var t = 0; t < tracesMeta.length; t++) {{
      var meta = tracesMeta[t];
      vis[t] = (stationVisible[meta.station] && yearVisible[meta.year]);
    }}
    Plotly.restyle(gd, {{visible: vis}});
  }}

  // posiciona overlays à DIREITA
  var stPanel = document.getElementById('station-controls');
  var yrPanel = document.getElementById('year-controls');
  [stPanel, yrPanel].forEach(function(p) {{
    if (!p) return;
    p.style.position = 'absolute';
    p.style.right = '20px';
  }});
  if (stPanel) stPanel.style.top = '6px';
  if (yrPanel) yrPanel.style.top = '44px';

  // monta checkboxes de ESTAÇÕES
  stations.forEach(function(st) {{
    var lbl = document.createElement('label');
    lbl.style.marginRight = '8px';
    lbl.innerHTML = '<input type="checkbox" data-st="' + st + '" checked> ' + st;
    stPanel.appendChild(lbl);
  }});
  var btnAllSt  = document.createElement('button'); btnAllSt.id  = 'st-all';  btnAllSt.textContent  = 'Todas';
  var btnNoneSt = document.createElement('button'); btnNoneSt.id = 'st-none'; btnNoneSt.textContent = 'Nenhuma';
  stPanel.appendChild(btnAllSt); stPanel.appendChild(btnNoneSt);

  // monta checkboxes de ANOS (com quadradinho de cor)
  years.forEach(function(yr) {{
    var lbl = document.createElement('label');
    lbl.style.marginRight = '8px';
    var color = CUSTOM_YEAR_COLORS[yr] || '#ccc';
    lbl.innerHTML =
      '<input type="checkbox" data-yr="' + yr + '" checked> ' +
      '<span style="display:inline-block;width:10px;height:10px;margin-right:4px;border-radius:2px;background:' + color + '"></span>' +
      yr;
    yrPanel.appendChild(lbl);
  }});
  var btnAllYr  = document.createElement('button'); btnAllYr.id  = 'yr-all';  btnAllYr.textContent  = 'Todos';
  var btnNoneYr = document.createElement('button'); btnNoneYr.id = 'yr-none'; btnNoneYr.textContent = 'Nenhum';
  yrPanel.appendChild(btnAllYr); yrPanel.appendChild(btnNoneYr);

  // listeners estações
  stPanel.addEventListener('change', function(ev) {{
    var el = ev.target;
    if (el && el.matches('input[type=checkbox][data-st]')) {{
      var st = el.getAttribute('data-st');
      stationVisible[st] = el.checked;
      applyVisibility();
    }}
  }});
  document.getElementById('st-all').addEventListener('click', function() {{
    Array.from(stPanel.querySelectorAll('input[data-st]')).forEach(function(chk) {{
      chk.checked = true; stationVisible[chk.getAttribute('data-st')] = true;
    }});
    applyVisibility();
  }});
  document.getElementById('st-none').addEventListener('click', function() {{
    Array.from(stPanel.querySelectorAll('input[data-st]')).forEach(function(chk) {{
      chk.checked = false; stationVisible[chk.getAttribute('data-st')] = false;
    }});
    applyVisibility();
  }});

  // listeners anos
  yrPanel.addEventListener('change', function(ev) {{
    var el = ev.target;
    if (el && el.matches('input[type=checkbox][data-yr]')) {{
      var yr = parseInt(el.getAttribute('data-yr'));
      yearVisible[yr] = el.checked;
      applyVisibility();
    }}
  }});
  document.getElementById('yr-all').addEventListener('click', function() {{
    Array.from(yrPanel.querySelectorAll('input[data-yr]')).forEach(function(chk) {{
      chk.checked = true; yearVisible[parseInt(chk.getAttribute('data-yr'))] = true;
    }});
    applyVisibility();
  }});
  document.getElementById('yr-none').addEventListener('click', function() {{
    Array.from(yrPanel.querySelectorAll('input[data-yr]')).forEach(function(chk) {{
      chk.checked = false; yearVisible[parseInt(chk.getAttribute('data-yr'))] = false;
    }});
    applyVisibility();
  }});
}})();
</script>
"""

    # wrapper relativo: gráfico + overlays absolutos
    return (
        overlay_css +
        '<div class="plot-wrap">'
        + fig_html +
        stations_controls +
        years_controls +
        script +
        '</div>'
    )
