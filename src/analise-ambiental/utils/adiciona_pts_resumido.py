# utils/adiciona_pts_resumido.py
from __future__ import annotations
import os, re
from typing import Dict, Tuple, Optional, List, Iterable
from datetime import timedelta
import pandas as pd
import numpy as np

# --------------------------------------------------------------------
# Pastas do projeto (…/analise-ambiental/utils -> sobe 2 níveis)
# --------------------------------------------------------------------
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

TRAT_DIR   = os.path.join(ROOT_DIR, "tratamento-dos-dados")
DATA_ROOT  = os.path.join(ROOT_DIR, "dados-coletados")
RESUMO_CSV = os.path.join(TRAT_DIR, "database_resumido.csv")

STATIONS = ["EAMA11", "EAMA21", "EAMA31", "EAMA41"]
MESES_PT = [
    "janeiro","fevereiro","marco","abril","maio","junho",
    "julho","agosto","setembro","outubro","novembro","dezembro"
]

# --------------------------------------------------------------------
# Regras de FLAGS:
# - Usar TODAS as leituras, EXCETO as flags que começam com "I" (I, I1, I2, IM…)
# - "VG" (validado pelo gerente) **entra** no cálculo
# - Flags vazias também entram
# --------------------------------------------------------------------
def _flag_is_valid(f) -> bool:
    if f is None or (isinstance(f, float) and pd.isna(f)):
        return True
    s = str(f).strip().lower()
    if not s:
        return True
    return not s.startswith("i")  # exclui apenas I*

# --------------------------------------------------------------------
# Limites de sanidade para PTS (µg/m³). Ajuste conforme necessário.
# --------------------------------------------------------------------
SANE_MIN = 0.0
SANE_MAX = 5000.0   # descarta absurdos muito altos (ex.: leituras corrompidas)

# --------------------------------------------------------------------
# MAPEAMENTO FIXO PARA PTS (valor) nas planilhas QAR válidas (pós-validação):
#   EAMA11 -> B  (índice 1)
#   EAMA21 -> N  (índice 13)
#   EAMA31 -> Z  (índice 25)
#   EAMA41 -> AL (índice 37)
# Cada poluente ocupa 4 colunas: (valor, flag1, flag2, flag3).
# Aqui usaremos a PRIMEIRA flag (flag1) para validar.
# --------------------------------------------------------------------
PTS_COL_BY_STATION = {"EAMA11": 1, "EAMA21": 13, "EAMA31": 25, "EAMA41": 37}

# regex para extrair número tolerante a "123,45 VM", "  78.9  ", etc.
_NUM_RE = re.compile(r"-?\d+(?:[.,]\d+)?")

# --------------------------------------------------------------------
# Utilidades de caminhos/meses
# --------------------------------------------------------------------
def _month_dir(year: int, month: int) -> str:
    return os.path.join(DATA_ROOT, str(year), MESES_PT[month-1])

def _iter_all_month_paths() -> Iterable[Tuple[int,int,str]]:
    if not os.path.isdir(DATA_ROOT):
        return
    for a in sorted([d for d in os.listdir(DATA_ROOT) if d.isdigit()], key=int):
        year = int(a)
        for m_idx, mes in enumerate(MESES_PT, start=1):
            p = os.path.join(DATA_ROOT, a, mes)
            if os.path.isdir(p):
                yield year, m_idx, p

def _pick_qar_path(month_dir: str) -> Optional[str]:
    for name in ("qar.csv", "qar_novo.csv"):
        p = os.path.join(month_dir, name)
        if os.path.isfile(p):
            return p
    return None

# --------------------------------------------------------------------
# Leitura do QAR mensal
# --------------------------------------------------------------------
def _load_month_qar_df(year: int, month: int) -> Tuple[bool, str, Optional[pd.DataFrame], Optional[str]]:
    mdir = _month_dir(year, month)
    if not os.path.isdir(mdir):
        return False, f"Pasta do mês não encontrada: {mdir}", None, None

    fpath = _pick_qar_path(mdir)
    if not fpath:
        return False, f"qar.csv/qar_novo.csv não encontrado em {mdir}", None, None

    try:
        # As planilhas válidas têm 8 linhas de header; dados iniciam na linha 9
        df = pd.read_csv(fpath, header=None, skiprows=8, low_memory=False, encoding="utf-8-sig")
        df[0] = pd.to_datetime(df[0], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df = df.dropna(subset=[0]).sort_values(0)
        # chave para alinhar a janela de 24h no mesmo mm:ss (como no pipeline antigo)
        df["mmss"] = df[0].dt.strftime("%M:%S")
        return True, fpath, df, fpath
    except Exception as e:
        return False, f"Erro ao ler {fpath}: {e}", None, fpath

# --------------------------------------------------------------------
# Extração robusta: usa flag e pega apenas o número do texto
# --------------------------------------------------------------------
def _extrair_valores_validos(series_val: pd.Series, series_flag: pd.Series) -> List[float]:
    """
    Extrai números de 'series_val' **apenas** onde a flag correspondente em 'series_flag' é válida.
    Aceita vírgula decimal e sufixos (ex.: '123,45 VM').
    Aplica filtro de sanidade (SANE_MIN < v < SANE_MAX).
    """
    vals: List[float] = []
    for v, f in zip(series_val, series_flag):
        # ✅ nova regra de flag (usa tudo exceto I*)
        if not _flag_is_valid(f):
            continue

        # extrai número do campo de valor
        if v is None or (isinstance(v, float) and pd.isna(v)):
            continue
        if isinstance(v, (int, float)):
            try:
                fv = float(v)
            except Exception:
                continue
        else:
            s = str(v).strip().lower()
            m = _NUM_RE.search(s)
            if not m:
                continue
            try:
                fv = float(m.group(0).replace(",", "."))
            except Exception:
                continue

        # sanity check
        if not (SANE_MIN < fv < SANE_MAX):
            continue

        vals.append(fv)
    return vals

# --------------------------------------------------------------------
# Construção do PTS resumido (média de 24h, alinhada por mm:ss)
# --------------------------------------------------------------------
def _build_pts_resumido_for_df(df_month: pd.DataFrame, min_samples: int = 16) -> pd.DataFrame:
    """
    Para cada timestamp do mês, calcula a média de 24h (janela [t-23h, t]) no mesmo mm:ss,
    usando **apenas** leituras com flag válida (todas exceto as que começam com 'I') e valores
    numéricos extraídos de forma robusta.
    """
    uniq_ts = df_month[0].drop_duplicates().sort_values()
    out_rows: List[dict] = []

    for target_ts in uniq_ts:
        mmss  = target_ts.strftime("%M:%S")
        start = target_ts - timedelta(hours=23)      # janela [t-23h, t], mesmo mm:ss
        win   = df_month[(df_month[0] >= start) & (df_month[0] <= target_ts) & (df_month["mmss"] == mmss)]

        row = {"timestamp": target_ts}
        for st in STATIONS:
            val_col  = PTS_COL_BY_STATION[st]        # valor
            flag_col = val_col + 1                   # primeira flag logo após o valor

            if val_col in win.columns and flag_col in win.columns:
                pts_vals = _extrair_valores_validos(win[val_col], win[flag_col])
            else:
                pts_vals = []

            row[f"{st}_PTS_media"] = float(np.mean(pts_vals)) if len(pts_vals) >= min_samples else np.nan
        out_rows.append(row)

    out = pd.DataFrame(out_rows)
    return out.sort_values("timestamp") if not out.empty else out

# --------------------------------------------------------------------
# Leitura/merge do master (database_resumido.csv)
# --------------------------------------------------------------------
def _read_resumo_master() -> Optional[pd.DataFrame]:
    if not os.path.isfile(RESUMO_CSV):
        return None
    try:
        df = pd.read_csv(RESUMO_CSV, encoding="utf-8-sig", low_memory=False)
        if "timestamp" not in df.columns:
            for cand in ("datahora","datetime","date_time"):
                if cand in df.columns:
                    df = df.rename(columns={cand:"timestamp"})
                    break
        if "timestamp" not in df.columns:
            return None
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        return df.dropna(subset=["timestamp"]).sort_values("timestamp")
    except Exception:
        return None

def _ensure_pts_cols(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for st in STATIONS:
        col = f"{st}_PTS_media"
        if col not in out.columns:
            out[col] = np.nan
    return out

def _merge_pts_into_master(df_pts: pd.DataFrame) -> Tuple[bool, str]:
    if df_pts is None or df_pts.empty:
        return False, "DF de PTS vazio."

    df_pts = df_pts.copy()
    df_pts["timestamp"] = pd.to_datetime(df_pts["timestamp"], errors="coerce")
    df_pts = df_pts.dropna(subset=["timestamp"]).sort_values("timestamp")

    master = _read_resumo_master()
    if master is None or master.empty:
        out = df_pts.copy()
        out["timestamp"] = out["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
        out.to_csv(RESUMO_CSV, index=False, encoding="utf-8-sig")
        return True, "database_resumido.csv criado (timestamp + colunas *_PTS_media)."

    master = _ensure_pts_cols(master)

    merged = master.merge(df_pts, on="timestamp", how="outer", suffixes=("", "__new"))

    # Preferir valores novos (não-nulos) nas colunas *_PTS_media
    for st in STATIONS:
        base = f"{st}_PTS_media"
        newc = f"{base}__new"
        if newc in merged.columns:
            a = pd.to_numeric(merged[base], errors="coerce")
            b = pd.to_numeric(merged[newc], errors="coerce")
            merged[base] = np.where(b.notna(), b, a)
            merged.drop(columns=[newc], inplace=True)

    # Preserva ordem do master; extras (se houver) vão pro final
    core   = list(master.columns)
    extras = [c for c in merged.columns if c not in core]
    merged = merged[core + extras].sort_values("timestamp")

    merged["timestamp"] = merged["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    merged.to_csv(RESUMO_CSV, index=False, encoding="utf-8-sig")
    return True, "Colunas *_PTS_media mescladas/atualizadas no database_resumido.csv."

# --------------------------------------------------------------------
# APIs públicas
# --------------------------------------------------------------------
def add_pts_for_month(year: int, month: int, min_samples: int = 16) -> Dict:
    ok, msg, df_month, fpath = _load_month_qar_df(year, month)
    if not ok or df_month is None:
        return {"ok": False, "message": msg}

    pts_month = _build_pts_resumido_for_df(df_month, min_samples=min_samples)
    if pts_month.empty:
        return {"ok": False, "message": "Nenhuma linha válida de PTS neste mês."}

    ok2, msg2 = _merge_pts_into_master(pts_month)
    return {"ok": ok2, "message": msg2}

def add_pts_bootstrap_all(min_samples: int = 16) -> Dict:
    dfs: List[pd.DataFrame] = []
    total_meses = 0
    for year, month, mdir in _iter_all_month_paths():
        fpath = _pick_qar_path(mdir)
        if not fpath:
            continue
        ok, msg, dfm, _ = _load_month_qar_df(year, month)
        if not ok or dfm is None:
            continue
        pts_m = _build_pts_resumido_for_df(dfm, min_samples=min_samples)
        if not pts_m.empty:
            dfs.append(pts_m)
            total_meses += 1

    if not dfs:
        return {"ok": False, "message": "Nenhum mês válido com PTS encontrado para bootstrap."}

    big = (pd.concat(dfs, ignore_index=True)
             .drop_duplicates(subset=["timestamp"])
             .sort_values("timestamp"))
    ok2, msg2 = _merge_pts_into_master(big)
    return {"ok": ok2, "message": f"{msg2} (bootstrap em {total_meses} meses)"}

def add_pts_update(year: Optional[int] = None, month: Optional[int] = None, min_samples: int = 16) -> Dict:
    master = _read_resumo_master()
    has_pts = False
    if master is not None and not master.empty:
        for st in STATIONS:
            if f"{st}_PTS_media" in master.columns:
                has_pts = True
                break

    if not has_pts:
        return add_pts_bootstrap_all(min_samples=min_samples)

    if year and month:
        return add_pts_for_month(int(year), int(month), min_samples=min_samples)

    return {"ok": False, "message": "Nada a fazer: informe year e month para incremental, ou remova PTS para refazer bootstrap."}

# --------------------------------------------------------------------
if __name__ == "__main__":
    # Ex.: bootstrap geral
    # print(add_pts_bootstrap_all())
    # Ex.: incremental
    # print(add_pts_for_month(2025, 1))
    pass
