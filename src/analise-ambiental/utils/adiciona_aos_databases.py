# utils/adiciona_aos_databases.py
# -------------------------------------------------------------------
# Após o upload (qar.xls) já validado e salvo em dados-coletados,
# atualiza automaticamente o database_resumido.csv do QAR.
#  - QAR: gera as linhas do database_resumido.csv a partir do mês adicionado
#         e mescla no arquivo mestre PRESERVANDO cabeçalho e ordem de colunas.
#         Também faz BACKFILL dos campos de "mais detalhes" quando faltarem.
# -------------------------------------------------------------------

from __future__ import annotations
import os, re
from typing import Dict, Tuple, Optional, List
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

# Raiz do projeto (…/analise-ambiental/utils -> sobe 2 níveis)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Caminhos padrões
TRAT_DIR  = os.path.join(ROOT_DIR, "tratamento-dos-dados")
DATA_ROOT = os.path.join(ROOT_DIR, "dados-coletados")

DB_QAR_RESUMO_PATH = os.path.join(TRAT_DIR, "database_resumido.csv")

STATIONS = ["EAMA11", "EAMA21", "EAMA31", "EAMA41"]
POLS     = ["MP10", "MP2.5"]  # PTS não entra no resumido (PTS é tratado à parte)

# ---------------- utilidades comuns ----------------
def _month_name_pt(n: int) -> str:
    return [
        "janeiro","fevereiro","marco","abril","maio","junho",
        "julho","agosto","setembro","outubro","novembro","dezembro"
    ][n-1]

def _month_dir(year: int, month: int) -> str:
    return os.path.join(DATA_ROOT, str(year), _month_name_pt(month))

def _safe_read_csv_noheader(path: str) -> Optional[pd.DataFrame]:
    if not os.path.isfile(path):
        return None
    try:
        return pd.read_csv(path, header=None, encoding="utf-8", engine="python", low_memory=False)
    except Exception:
        return pd.read_csv(path, header=None, encoding="utf-8-sig", engine="python", low_memory=False)

# Gerador da ordem oficial de colunas do database_resumido.csv
def RESUMIDO_COLUMNS() -> List[str]:
    cols = ["timestamp"]
    for st in STATIONS:
        for pol in POLS:
            cols += [f"{st}_{pol}_media", f"{st}_{pol}_IQAr", f"{st}_{pol}_class"]
    for st in STATIONS:
        for pol in POLS:
            cols += [
                f"{st}_{pol}_idx_ini", f"{st}_{pol}_idx_fin",
                f"{st}_{pol}_conc_ini", f"{st}_{pol}_conc_fin",
            ]
    return cols

# ---------------- QAR: gerar "resumido" direto do mês ----------------
def col_index(station: str, pol: str) -> int:
    """
    Mapa de colunas no QAR bruto (skiprows=8).
    timestamp = col 0. Para cada estação há um bloco de 3 poluentes:
      PTS (base), MP10 (base+4), MP2.5 (base+8),
    cada um com 4 colunas (valor, n, n, n).
    """
    base_by_station = {
        "EAMA11": 1,   # PTS -> B
        "EAMA21": 13,  # PTS -> N
        "EAMA31": 25,  # PTS -> Z
        "EAMA41": 37,  # PTS -> AL
    }
    base = base_by_station[station]
    if pol == "PTS":   return base
    if pol == "MP10":  return base + 4
    if pol == "MP2.5": return base + 8
    raise KeyError(pol)

def _linear_scale(x, x0, x1, y0, y1):
    if x <= x0: return y0
    if x >= x1: return y1
    if x1 == x0: return y0
    return y0 + (x - x0) * (y1 - y0) / (x1 - x0)

def _calculate_IQAr(media: float, pollutant: str):
    v = float(media)
    if pollutant == "MP10":
        table = [(0,50,0,40),(51,100,41,80),(101,150,81,120),(151,250,121,200),(251,600,201,400)]
    else:  # MP2.5
        table = [(0,25,0,40),(26,50,41,80),(51,75,81,120),(76,125,121,200),(126,300,201,400)]
    for (c0,c1,i0,i1) in table:
        if v <= c1:
            iqar = _linear_scale(v, c0, c1, i0, i1)
            return (iqar, i0, i1, c0, c1)
    (c0,c1,i0,i1) = table[-1]
    iqar = _linear_scale(v, c0, c1, i0, i1)
    return (iqar, i0, i1, c0, c1)

def _classify_air_quality(iqar) -> str:
    try:
        v = float(iqar)
    except Exception:
        return "dados insuficientes"
    if v <= 40:  return "BOA"
    if v <= 80:  return "MODERADA"
    if v <= 120: return "RUIM"
    if v <= 200: return "MUITO RUIM"
    return "PÉSSIMA"

_NUM_RE = re.compile(r"-?\d+(?:[.,]\d+)?")

def _extrair_valores_num(series: pd.Series) -> List[float]:
    """Extrai floats, tolerando strings como '17.5 VM', 'n', vírgula decimal etc."""
    vals: List[float] = []
    for v in series:
        if v is None:
            continue
        if isinstance(v, (int, float)):
            try:
                f = float(v)
                if not (isinstance(f, float) and np.isnan(f)):
                    vals.append(f)
            except Exception:
                pass
            continue
        s = str(v).strip().lower()
        if not s or s in {"n", "nan", "null", "none"}:
            continue
        m = _NUM_RE.search(s)
        if not m:
            continue
        num = m.group(0).replace(",", ".")
        try:
            vals.append(float(num))
        except Exception:
            pass
    return vals

def _extrair_valores_validos(series_val: pd.Series, series_flag: pd.Series) -> List[float]:
    """
    Extrai números de `series_val` **somente** onde a flag correspondente em `series_flag` é 'n'.
    Aceita valores numéricos ou strings (com vírgula decimal etc.).
    Ignora qualquer flag diferente de 'n' (ex.: IE, IR, IU...).
    """
    vals: List[float] = []
    for v, f in zip(series_val, series_flag):
        # valida flag
        sf = ("" if f is None else str(f)).strip().lower()
        if sf != "n":
            continue

        # extrai número do valor
        if v is None:
            continue
        if isinstance(v, (int, float)):
            try:
                fval = float(v)
                if not (isinstance(fval, float) and np.isnan(fval)):
                    vals.append(fval)
            except Exception:
                pass
            continue

        s = str(v).strip().lower()
        if not s or s in {"n", "nan", "null", "none"}:
            continue
        m = _NUM_RE.search(s)
        if not m:
            continue
        num = m.group(0).replace(",", ".")
        try:
            vals.append(float(num))
        except Exception:
            pass

    return vals


def _load_month_qar_df(year: int, month: int) -> Tuple[bool, str, Optional[pd.DataFrame]]:
    month_path = os.path.join(_month_dir(year, month), "")
    if not os.path.isdir(month_path):
        return False, f"Pasta do mês não encontrada: {month_path}", None

    candidates = ["qar.csv", "qar_novo.csv"]
    file_path = None
    for c in candidates:
        p = os.path.join(month_path, c)
        if os.path.isfile(p):
            file_path = p
            break
    if not file_path:
        return False, f"qar.csv/qar_novo.csv não encontrado em {month_path}", None

    try:
        df = pd.read_csv(file_path, header=None, skiprows=8, low_memory=False, encoding="utf-8-sig")
        df[0] = pd.to_datetime(df[0], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df = df.dropna(subset=[0])
        df["mmss"] = df[0].dt.strftime("%M:%S")
        df = df.sort_values(by=0)
        return True, file_path, df
    except Exception as e:
        return False, f"Erro ao ler {file_path}: {e}", None

def _build_resumido_for_month(df_month: pd.DataFrame) -> pd.DataFrame:
    uniq_ts = df_month[0].drop_duplicates().sort_values()
    out_rows: List[dict] = []

    for target_ts in uniq_ts:
        mmss = target_ts.strftime("%M:%S")
        start = target_ts - timedelta(hours=23)
        win = df_month[
            (df_month[0] >= start) &
            (df_month[0] <= target_ts) &
            (df_month["mmss"] == mmss)
        ]
        row = {"timestamp": target_ts.strftime("%Y-%m-%d %H:%M:%S")}

        for st in STATIONS:
            # -------- MP10 --------
            mp10_val_col  = col_index(st, "MP10")      # coluna do valor
            mp10_flag_col = mp10_val_col + 1           # primeira coluna de flag
            mp10_vals = _extrair_valores_validos(win[mp10_val_col], win[mp10_flag_col])

            if len(mp10_vals) < 16:
                row[f"{st}_MP10_media"] = "dados insuficientes"
                row[f"{st}_MP10_IQAr"]  = "dados insuficientes"
                row[f"{st}_MP10_class"] = "dados insuficientes"
                row[f"{st}_MP10_idx_ini"]  = np.nan
                row[f"{st}_MP10_idx_fin"]  = np.nan
                row[f"{st}_MP10_conc_ini"] = np.nan
                row[f"{st}_MP10_conc_fin"] = np.nan
            else:
                media = float(np.mean(mp10_vals))
                iqar, i_ini, i_fin, c_ini, c_fin = _calculate_IQAr(media, "MP10")
                row[f"{st}_MP10_media"] = media
                row[f"{st}_MP10_IQAr"]  = iqar
                row[f"{st}_MP10_class"] = _classify_air_quality(iqar)
                row[f"{st}_MP10_idx_ini"]  = i_ini
                row[f"{st}_MP10_idx_fin"]  = i_fin
                row[f"{st}_MP10_conc_ini"] = c_ini
                row[f"{st}_MP10_conc_fin"] = c_fin

            # -------- MP2.5 --------
            mp25_val_col  = col_index(st, "MP2.5")
            mp25_flag_col = mp25_val_col + 1
            mp25_vals = _extrair_valores_validos(win[mp25_val_col], win[mp25_flag_col])

            if len(mp25_vals) < 16:
                row[f"{st}_MP2.5_media"] = "dados insuficientes"
                row[f"{st}_MP2.5_IQAr"]  = "dados insuficientes"
                row[f"{st}_MP2.5_class"] = "dados insuficientes"
                row[f"{st}_MP2.5_idx_ini"]  = np.nan
                row[f"{st}_MP2.5_idx_fin"]  = np.nan
                row[f"{st}_MP2.5_conc_ini"] = np.nan
                row[f"{st}_MP2.5_conc_fin"] = np.nan
            else:
                media = float(np.mean(mp25_vals))
                iqar, i_ini, i_fin, c_ini, c_fin = _calculate_IQAr(media, "MP2.5")
                row[f"{st}_MP2.5_media"] = media
                row[f"{st}_MP2.5_IQAr"]  = iqar
                row[f"{st}_MP2.5_class"] = _classify_air_quality(iqar)
                row[f"{st}_MP2.5_idx_ini"]  = i_ini
                row[f"{st}_MP2.5_idx_fin"]  = i_fin
                row[f"{st}_MP2.5_conc_ini"] = c_ini
                row[f"{st}_MP2.5_conc_fin"] = c_fin

        out_rows.append(row)

    out = pd.DataFrame(out_rows)
    # garante exatamente a ordem/nomes esperados
    cols = RESUMIDO_COLUMNS()
    for c in cols:
        if c not in out.columns:
            out[c] = np.nan
    out = out[cols].sort_values(by="timestamp")
    return out

# ---------- leitura/mescla do resumido + BACKFILL ----------
def _read_resumido_master() -> Optional[pd.DataFrame]:
    if not os.path.isfile(DB_QAR_RESUMO_PATH):
        return None
    # 1) tenta com header (o que a UI espera)
    try:
        df = pd.read_csv(DB_QAR_RESUMO_PATH, encoding="utf-8-sig", low_memory=False)
        if "timestamp" not in df.columns:
            raise ValueError("arquivo sem coluna 'timestamp' no cabeçalho")
        return df
    except Exception:
        pass
    # 2) fallback para legado sem header
    try:
        df = pd.read_csv(DB_QAR_RESUMO_PATH, header=None, encoding="utf-8-sig", low_memory=False)
        expected = RESUMIDO_COLUMNS()
        if df.shape[1] >= len(expected):
            df = df.iloc[:, :len(expected)]
            df.columns = expected
        else:
            df.columns = [f"c{i}" for i in range(df.shape[1])]
            df = df.rename(columns={df.columns[0]: "timestamp"})
            for c in expected:
                if c not in df.columns:
                    df[c] = np.nan
            df = df[expected]
        return df
    except Exception:
        return None

def _is_number(x) -> bool:
    try:
        float(x)
        return not (isinstance(x, float) and np.isnan(x))
    except Exception:
        return False

def _compute_bounds_from_media(media: float, pol: str):
    """A partir da média (numérica), retorna (i_ini, i_fin, c_ini, c_fin)."""
    if media is None or not _is_number(media):
        return (np.nan, np.nan, np.nan, np.nan)
    _, i_ini, i_fin, c_ini, c_fin = _calculate_IQAr(float(media), pol)
    return (i_ini, i_fin, c_ini, c_fin)

def _backfill_resumido_details(df: pd.DataFrame) -> pd.DataFrame:
    """Preenche índices/conc limites via média; recalcula IQAr/class se faltarem."""
    out = df.copy()
    for st in STATIONS:
        for pol in POLS:
            mcol = f"{st}_{pol}_media"
            iqcol = f"{st}_{pol}_IQAr"
            ccol  = f"{st}_{pol}_class"
            i0col = f"{st}_{pol}_idx_ini"
            i1col = f"{st}_{pol}_idx_fin"
            c0col = f"{st}_{pol}_conc_ini"
            c1col = f"{st}_{pol}_conc_fin"

            for c in (i0col, i1col, c0col, c1col):
                if c not in out.columns:
                    out[c] = np.nan

            mvals = pd.to_numeric(out.get(mcol, np.nan), errors="coerce")
            ok = mvals.notna()

            if ok.any():
                if iqcol not in out.columns:
                    out[iqcol] = np.nan
                iq_series = pd.to_numeric(out[iqcol], errors="coerce")

                need_iqar = iq_series.isna() & ok
                if need_iqar.any():
                    new_iqar = mvals[need_iqar].apply(lambda v: _calculate_IQAr(float(v), pol)[0])
                    out.loc[need_iqar, iqcol] = new_iqar.values
                    out.loc[need_iqar, ccol]  = new_iqar.apply(_classify_air_quality).values

                need_details = (out[i0col].isna() | out[i1col].isna() |
                                out[c0col].isna() | out[c1col].isna()) & ok
                if need_details.any():
                    for idx in out.index[need_details]:
                        v = mvals.at[idx]
                        i_ini, i_fin, c_ini, c_fin = _compute_bounds_from_media(v, pol)
                        out.at[idx, i0col] = i_ini
                        out.at[idx, i1col] = i_fin
                        out.at[idx, c0col] = c_ini
                        out.at[idx, c1col] = c_fin
    return out

def _merge_resumido_month_into_master(df_month_resumido: pd.DataFrame) -> Tuple[bool, str]:
    df_month_resumido = df_month_resumido.copy()
    df_month_resumido["timestamp"] = pd.to_datetime(df_month_resumido["timestamp"])
    df_month_resumido = df_month_resumido.sort_values("timestamp")

    master = _read_resumido_master()
    if master is None or master.empty:
        out = _backfill_resumido_details(df_month_resumido.copy())
        out["timestamp"] = out["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
        out.to_csv(DB_QAR_RESUMO_PATH, index=False, encoding="utf-8-sig")
        return True, "database_resumido.csv criado a partir do mês recém-adicionado."

    expected = RESUMIDO_COLUMNS()
    for c in expected:
        if c not in master.columns:
            master[c] = np.nan
    master = master[expected]

    master["timestamp"] = pd.to_datetime(master["timestamp"], errors="coerce")
    master = master.dropna(subset=["timestamp"])

    combined = pd.concat([master, df_month_resumido], ignore_index=True)
    combined = combined.drop_duplicates(subset=["timestamp"]).sort_values("timestamp")

    combined = _backfill_resumido_details(combined)

    combined["timestamp"] = combined["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    combined.to_csv(DB_QAR_RESUMO_PATH, index=False, encoding="utf-8-sig")
    return True, f"database_resumido.csv mesclado/atualizado com {len(df_month_resumido)} linhas do mês."

def _append_qar_month_to_resumido(year: int, month: int) -> Tuple[bool, str]:
    ok, msg, df_month = _load_month_qar_df(year, month)
    if not ok or df_month is None:
        return False, msg

    resumido = _build_resumido_for_month(df_month)
    if resumido.empty:
        return False, "Nenhuma linha válida para gerar resumido a partir do mês."

    ok2, msg2 = _merge_resumido_month_into_master(resumido)
    return ok2, msg2

# ---------------- API pública ----------------
def add_to_databases(tipo: str, year: int, month: int) -> Dict:
    """
    - tipo 'qar' -> calcula e mescla diretamente no database_resumido.csv (com cabeçalho + backfill)
    (Observação: a parte MET foi movida para utils/adiciona_ao_database_met.py)
    """
    tipo = (tipo or "").lower().strip()
    if tipo != "qar":
        return {
            "ok": False,
            "message": "Tipo inválido aqui. Use 'qar' neste módulo. Para MET, chame utils.adiciona_ao_database_met.add_met_month_to_database(...)"
        }

    ok, msg = _append_qar_month_to_resumido(year, month)
    return {"ok": ok, "target": "database_resumido.csv", "message": msg}
