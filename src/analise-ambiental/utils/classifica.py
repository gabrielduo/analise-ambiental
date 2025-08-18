# analise-ambiental/utils/classifica.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional
import pandas as pd
from datetime import datetime
import os
import math

# Caminho padrão vem do config.py (aponta para database_resumido.csv)
try:
    from config import DATABASE_PATH
except Exception:
    DATABASE_PATH = os.path.join(
        os.path.dirname(__file__), "..", "tratamento-dos-dados", "database_resumido.csv"
    )

# ---------------- utils data/hora ----------------
def _parse_date_time(date_str: str, time_str: str) -> datetime:
    """
    Recebe data "YYYY-MM-DD" ou "DD-MM-YYYY" (ou com /) e hora "HH" ou "HH:MM[:SS]".
    No resumo os timestamps são HH:30:00, então forçamos mm=30.
    """
    date_str = date_str.strip().replace("/", "-")
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        d = datetime.strptime(date_str, "%d-%m-%Y")

    t = time_str.strip()
    if len(t) == 2 and t.isdigit():
        hh, mm, ss = int(t), 30, 0
    else:
        parts = t.split(":")
        hh = int(parts[0]) if parts and parts[0] else 0
        mm, ss = 30, 0

    return datetime(d.year, d.month, d.day, hh, mm, ss)

# ---------------- conversões seguras ----------------
_INVALID_STRINGS = {
    "", "nan", "none", "null", "NULL", "NaN",
    "indisponivel", "indisponível", "sem dado", "sem dados",
    "dados insuficientes", "insuficiente", "n/a", "na"
}

def _to_float_or_none(x) -> Optional[float]:
    """Converte valores diversos para float, devolvendo None quando não-dado."""
    if x is None:
        return None
    if isinstance(x, (float, int)):
        if isinstance(x, float) and math.isnan(x):
            return None
        return float(x)
    if isinstance(x, str):
        s = x.strip()
        if not s or s.lower() in _INVALID_STRINGS:
            return None
        s = s.replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None
    return None

# ---------------- leitura CSV resumo ----------------
def _load_resumo_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8", low_memory=False)
    if "timestamp" not in df.columns:
        for cand in ("datahora", "datetime", "date_time"):
            if cand in df.columns:
                df = df.rename(columns={cand: "timestamp"})
                break
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

# ---------------- helpers ----------------
_STATIONS = {"EAMA11", "EAMA21", "EAMA31", "EAMA41"}
_POLLUTANTS = ("MP10", "MP2.5", "PTS")

def _colname(station: str, pol: str, kind: str) -> str:
    # ex.: EAMA11_MP10_media | _IQAr | _class | _idx_ini | _idx_fin | _conc_ini | _conc_fin
    return f"{station}_{pol}_{kind}"

@dataclass
class PollutantOutput:
    value: Optional[float]
    iqar: Optional[float]
    quality_class: str
    I_ini: Optional[float] = None
    I_fin: Optional[float] = None
    C_ini: Optional[float] = None
    C_fin: Optional[float] = None

    def as_dict(self) -> Dict:
        """
        Publica chaves novas e legadas (compatível com o template).
        Para o Jinja não quebrar no %.2f, valores ausentes viram 0.0.
        """
        def nf(x):  # normalize float
            return x if x is not None else 0.0

        return {
            # formato “novo”
            "value": self.value,
            "iqar": self.iqar,
            "class": self.quality_class,
            "I_ini": self.I_ini,
            "I_fin": self.I_fin,
            "C_ini": self.C_ini,
            "C_fin": self.C_fin,
            # chaves esperadas pelo template
            "Média Horária": nf(self.value),
            "IQAr": nf(self.iqar),
            "Classificação": self.quality_class,
            "Índice Inicial": nf(self.I_ini),
            "Índice Final": nf(self.I_fin),
            "Concentração Inicial": nf(self.C_ini),
            "Concentração Final": nf(self.C_fin),
        }

# ---------------- API principal ----------------
def classify_air(
    input_date: str,
    input_time: str,
    station: str,
    database_path: Optional[str] = None,
) -> Dict[str, Dict]:
    if station not in _STATIONS:
        raise ValueError(f"Estação inválida: {station}. Use uma de {_STATIONS}.")

    path = database_path or DATABASE_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {path}")

    target_dt = _parse_date_time(input_date, input_time)
    df = _load_resumo_csv(path)

    # pega a linha exata ou a mais próxima
    row = df.loc[df["timestamp"] == target_dt]
    if row.empty:
        nearest_idx = (df["timestamp"] - target_dt).abs().idxmin()
        row = df.iloc[[nearest_idx]]
    row = row.iloc[0]

    def pick(pol: str) -> PollutantOutput:
        media_col = _colname(station, pol, "media")
        iqar_col  = _colname(station, pol, "IQAr")
        class_col = _colname(station, pol, "class")

        v  = _to_float_or_none(row.get(media_col)) if media_col in df.columns else None
        iq = _to_float_or_none(row.get(iqar_col))  if iqar_col  in df.columns else None
        cl = (str(row[class_col]) if class_col in df.columns and pd.notna(row[class_col])
              else "Indisponível")

        # Para PTS não existem colunas de detalhes/IQAr
        if pol == "PTS":
            return PollutantOutput(value=v, iqar=None, quality_class=cl)

        # Detalhes (existem no resumo: _idx_ini/_idx_fin/_conc_ini/_conc_fin)
        idx_i_col  = _colname(station, pol, "idx_ini")
        idx_f_col  = _colname(station, pol, "idx_fin")
        conc_i_col = _colname(station, pol, "conc_ini")
        conc_f_col = _colname(station, pol, "conc_fin")

        I_ini = _to_float_or_none(row.get(idx_i_col))  if idx_i_col  in df.columns else None
        I_fin = _to_float_or_none(row.get(idx_f_col))  if idx_f_col  in df.columns else None
        C_ini = _to_float_or_none(row.get(conc_i_col)) if conc_i_col in df.columns else None
        C_fin = _to_float_or_none(row.get(conc_f_col)) if conc_f_col in df.columns else None

        return PollutantOutput(
            value=v, iqar=iq, quality_class=cl,
            I_ini=I_ini, I_fin=I_fin, C_ini=C_ini, C_fin=C_fin
        )

    out = {
        "timestamp": row["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
        "station": station,
    }
    for pol in _POLLUTANTS:
        out[pol] = pick(pol).as_dict()
    return out


if __name__ == "__main__":
    date = input("Data (dd-mm-aaaa ou yyyy-mm-dd): ").strip()
    hour = input("Hora (HH ou HH:MM[:SS]): ").strip()
    st   = input("Estação (EAMA11, EAMA21, EAMA31, EAMA41): ").strip().upper()
    print(classify_air(date, hour, st))
