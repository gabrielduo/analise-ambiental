# utils/adiciona_ao_database_met.py
# -------------------------------------------------------------------
# MESCLA MET:
#  - Lê dados-coletados/<ano>/<mês>/met.csv (sem header)
#  - Normaliza 1ª coluna (timestamp) -> '%Y-%m-%d %H:%M:%S'
#  - Concatena em tratamento-dos-dados/database_met.csv
#  - Dedup estrito por timestamp, ordena, grava (utf-8-sig, sem header)
#  - NÃO altera número/ordem de colunas originais, só padroniza a 1ª
#  - Valida pós-gravação
#  - Caminhos agora alinhados ao config.py (DATA_ROOT, METEOROLOGY_PATH)
# -------------------------------------------------------------------

from __future__ import annotations
import os
from typing import Optional, List, Dict, Tuple

import pandas as pd
import numpy as np

# ====== CAMINHOS ALINHADOS AO APP/CONFIG ======
try:
    from config import DATA_ROOT as DATA_ROOT_FROM_CFG, METEOROLOGY_PATH as DB_MET_PATH_FROM_CFG
    DATA_ROOT = DATA_ROOT_FROM_CFG
    DB_MET_PATH = DB_MET_PATH_FROM_CFG
except Exception:
    # Fallback sensato para execução isolada
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    DATA_ROOT = os.path.join(ROOT_DIR, "dados-coletados")
    DB_MET_PATH = os.path.join(ROOT_DIR, "tratamento-dos-dados", "database_met.csv")
# ==============================================

PT_MONTHS = [
    "janeiro","fevereiro","marco","abril","maio","junho",
    "julho","agosto","setembro","outubro","novembro","dezembro"
]

def _month_name_pt(n: int) -> str:
    if not (1 <= n <= 12):
        raise ValueError(f"Mês inválido: {n}")
    return PT_MONTHS[n-1]

def _resolve_month_paths(year: int, month: int) -> List[str]:
    """
    Resolve todos os caminhos possíveis para o met.csv do mês:
    - .../<ano>/<marco>/met.csv
    - .../<ano>/<março>/met.csv (variante com acento)
    - .../<ano>/met.csv (fallback)
    """
    base_year = os.path.join(DATA_ROOT, str(year))

    names = [_month_name_pt(month)]
    # março pode existir com acento ou sem
    if month == 3 and "março" not in names:
        names.append("março")

    candidates = [os.path.join(base_year, nm, "met.csv") for nm in names]
    candidates.append(os.path.join(base_year, "met.csv"))  # fallback
    return candidates

def _safe_read_csv_noheader(path: str) -> Optional[pd.DataFrame]:
    """
    Lê CSV sem header de forma tolerante:
    - tenta múltiplas codificações (utf-8-sig, utf-8, latin-1)
    - tenta separador vírgula, ponto-e-vírgula e autodetecção (sep=None)
    - ignora linhas ruins (on_bad_lines='skip')
    Retorna DataFrame ou None se todas as tentativas falharem/ficarem vazias.
    """
    if not os.path.isfile(path):
        return None

    attempts = []
    encs = ["utf-8-sig", "utf-8", "latin-1"]
    seps = [",", ";", None]  # None => sniff do engine='python'
    engines = ["python", "c"]  # tenta os dois

    for enc in encs:
        for sep in seps:
            for eng in engines:
                kw = dict(header=None, encoding=enc, low_memory=False,
                          on_bad_lines="skip")
                if sep is not None:
                    kw["sep"] = sep
                kw["engine"] = eng
                attempts.append(kw)

    for kw in attempts:
        try:
            df = pd.read_csv(path, **kw)
            if df is not None and not df.empty:
                return df
        except Exception:
            continue

    return None


def _atomic_write_csv_noheader(df: pd.DataFrame, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    df.to_csv(tmp, index=False, header=False, encoding="utf-8-sig")
    os.replace(tmp, path)

def _normalize_timestamp_col(series: pd.Series) -> pd.Series:
    raw = series.astype(str).str.replace("\ufeff", "", regex=False).str.strip()
    # tenta canônico e depois dayfirst tolerante
    dt = pd.to_datetime(raw, format="%Y-%m-%d %H:%M:%S", errors="coerce")
    dt = dt.fillna(pd.to_datetime(raw, dayfirst=True, errors="coerce"))
    return dt.dt.strftime("%Y-%m-%d %H:%M:%S")

def _ensure_same_width(df_a: pd.DataFrame, df_b: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Garante mesma largura de colunas antes de concatenar (não altera dados existentes)."""
    w = max(df_a.shape[1], df_b.shape[1])
    def pad(df):
        if df.shape[1] >= w:
            return df
        for _ in range(w - df.shape[1]):
            df[f"__pad{df.shape[1]}__"] = np.nan
        return df
    return pad(df_a.copy()), pad(df_b.copy())

def add_met_month_to_database(year: int, month: int) -> Dict:
    month_candidates = _resolve_month_paths(year, month)
    month_path = next((p for p in month_candidates if os.path.isfile(p)), None)
    if month_path is None:
        return {
            "ok": False, "target": DB_MET_PATH,
            "message": "met.csv não encontrado. Procurei em: " + ", ".join(os.path.abspath(p) for p in month_candidates)
        }

    df_new = _safe_read_csv_noheader(month_path)
    if df_new is None or df_new.empty:
        return {"ok": False, "target": DB_MET_PATH, "message": f"met.csv vazio/ilegível em {os.path.abspath(month_path)}"}

    # normaliza apenas a 1ª coluna (timestamp)
    df_new = df_new.copy()
    df_new["_ts"] = _normalize_timestamp_col(df_new.iloc[:, 0])
    df_new = df_new.dropna(subset=["_ts"])
    if df_new.empty:
        return {"ok": False, "target": DB_MET_PATH, "message": "Todas as datas do met.csv são inválidas."}

    new_keys = set(df_new["_ts"].tolist())
    new_min, new_max = min(new_keys), max(new_keys)

    # lê database atual
    db = _safe_read_csv_noheader(DB_MET_PATH)
    rows_before = 0
    last_before = None
    prev_keys: set = set()

    if db is not None and not db.empty:
        rows_before = len(db)
        db = db.copy()
        db["_ts"] = _normalize_timestamp_col(db.iloc[:, 0])
        db = db.dropna(subset=["_ts"])
        if not db.empty:
            last_before = db["_ts"].max()
            prev_keys = set(db["_ts"].tolist())
    else:
        db = pd.DataFrame(columns=df_new.columns)

    # garante mesma largura, concatena, dedup estrito por timestamp, ordena
    db, df_new = _ensure_same_width(db, df_new)
    combined = pd.concat([db, df_new], ignore_index=True)
    combined = combined.dropna(subset=["_ts"]).drop_duplicates(subset=["_ts"], keep="last").sort_values("_ts")

    # padroniza 1ª coluna como timestamp canônico e remove auxiliar
    combined = combined.copy()
    combined.iloc[:, 0] = combined["_ts"]
    combined = combined.drop(columns=["_ts"])

    rows_after = len(combined)
    added_keys = len(new_keys - prev_keys)
    added_rows = rows_after - rows_before

    # grava final
    _atomic_write_csv_noheader(combined, DB_MET_PATH)

    # valida pós-gravação
    re_db = _safe_read_csv_noheader(DB_MET_PATH)
    if re_db is None or re_db.empty:
        return {"ok": False, "target": DB_MET_PATH, "message": "Validação falhou: database salvo ficou vazio."}
    re_db = re_db.copy()
    re_db["_ts"] = _normalize_timestamp_col(re_db.iloc[:, 0])
    re_db = re_db.dropna(subset=["_ts"])
    re_keys = set(re_db["_ts"].tolist())
    re_last = re_db["_ts"].max() if not re_db.empty else None

    if new_keys.isdisjoint(re_keys):
        return {
            "ok": False, "target": DB_MET_PATH,
            "message": (
                "Validação falhou: nenhum timestamp do mês apareceu no database salvo.\n"
                f"db_path={os.path.abspath(DB_MET_PATH)}\n"
                f"month_path={os.path.abspath(month_path)}\n"
                f"intervalo_mes=[{new_min}→{new_max}]"
            )
        }

    return {
        "ok": True, "target": DB_MET_PATH,
        "message": (
            "database_met.csv atualizado. "
            f"added_keys={added_keys}, added_rows={added_rows}. "
            f"intervalo_mes=[{new_min}→{new_max}]. "
            f"ultimo_antes={last_before}, ultimo_depois={re_last}. "
            f"db_path={os.path.abspath(DB_MET_PATH)}, month_path={os.path.abspath(month_path)}"
        )
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("uso: python -m utils.adiciona_ao_database_met <ano> <mes_num>")
        raise SystemExit(2)
    y = int(sys.argv[1]); m = int(sys.argv[2])
    print(add_met_month_to_database(y, m))
