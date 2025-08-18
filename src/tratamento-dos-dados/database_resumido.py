#!/usr/bin/env python3
# database_resumido.py
# Gera database_resumido.csv a partir de new_database.csv
# Agora inclui colunas de "Mais detalhes":
#   _idx_ini, _idx_fin, _conc_ini, _conc_fin  para cada estação/poluente

import os
import math
import pandas as pd

# ---------- Parâmetros do IQAr (mesmos de classifica.py) ----------
PARAMS = {
    "MP2.5": {
        "concentration_ranges": [
            (25, (0, 25)),
            (50, (26, 50)),
            (75, (51, 75)),
            (125, (76, 125)),
            (float("inf"), (126, 300)),
        ],
        "indices": [
            (25, (0, 40)),
            (50, (41, 80)),
            (75, (81, 120)),
            (125, (121, 200)),
            (float("inf"), (201, 400)),
        ],
    },
    "MP10": {
        "concentration_ranges": [
            (50, (0, 50)),
            (100, (51, 100)),
            (150, (101, 150)),
            (250, (151, 250)),
            (float("inf"), (251, 600)),
        ],
        "indices": [
            (50, (0, 40)),
            (100, (41, 80)),
            (150, (81, 120)),
            (250, (121, 200)),
            (float("inf"), (201, 400)),
        ],
    },
}

def _range_for(value: float, pollutant: str, key: str):
    for limit, r in PARAMS[pollutant][key]:
        if value <= limit:
            return r
    return PARAMS[pollutant][key][-1][1]

def _calc_details_from_media(media_val, pollutant: str):
    """
    Recebe a média (pode vir como string/NaN) e retorna:
    (idx_ini, idx_fin, conc_ini, conc_fin) ou (None, None, None, None)
    """
    try:
        v = float(str(media_val).replace(",", "."))
    except Exception:
        return (None, None, None, None)
    if math.isnan(v):
        return (None, None, None, None)

    c_ini, c_fin = _range_for(v, pollutant, "concentration_ranges")
    i_ini, i_fin = _range_for(v, pollutant, "indices")
    return (i_ini, i_fin, c_ini, c_fin)

def main():
    script_dir  = os.path.dirname(os.path.abspath(__file__))
    input_file  = os.path.join(script_dir, "new_database.csv")
    output_file = os.path.join(script_dir, "database_resumido.csv")

    stations   = ["EAMA11", "EAMA21", "EAMA31", "EAMA41"]
    pollutants = ["MP10", "MP2.5"]  # nomes como estão nas colunas do CSV

    try:
        df = pd.read_csv(input_file, parse_dates=["timestamp"])
    except Exception as e:
        print(f"Erro ao ler '{input_file}': {e}")
        return

    # Checagem de colunas mínimas
    required = ["timestamp"]
    for st in stations:
        for pol in pollutants:
            required += [
                f"{st}_{pol}_media",
                f"{st}_{pol}_IQAr",
                f"{st}_{pol}_class",
            ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print("Colunas não encontradas:", missing)
        return

    # Vamos começar só com as colunas originais do resumido
    out_cols = list(required)  # inclui timestamp + media/IQAr/class
    out_df = df[required].copy()

    # Para cada estação/poluente, calcular e anexar detalhes
    for st in stations:
        for pol in pollutants:
            media_col = f"{st}_{pol}_media"

            # nomes das novas colunas
            idx_ini_col  = f"{st}_{pol}_idx_ini"
            idx_fin_col  = f"{st}_{pol}_idx_fin"
            conc_ini_col = f"{st}_{pol}_conc_ini"
            conc_fin_col = f"{st}_{pol}_conc_fin"

            # aplica linha-a-linha (rápido o suficiente; se preferir, dá para vetorizá-lo)
            details = out_df[media_col].apply(lambda v: _calc_details_from_media(v, pol))
            out_df[idx_ini_col]  = details.apply(lambda t: t[0])
            out_df[idx_fin_col]  = details.apply(lambda t: t[1])
            out_df[conc_ini_col] = details.apply(lambda t: t[2])
            out_df[conc_fin_col] = details.apply(lambda t: t[3])

            # guardar ordem
            out_cols += [idx_ini_col, idx_fin_col, conc_ini_col, conc_fin_col]

    # salvar no disco
    out_df[out_cols].to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"Arquivo resumido salvo em '{output_file}'.")

if __name__ == "__main__":
    main()
