#!/usr/bin/env python3
# database_resumido.py

import os
import pandas as pd

def main():
    # pasta onde está este script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file  = os.path.join(script_dir, "new_database.csv")
    output_file = os.path.join(script_dir, "database_resumido.csv")

    cols = [
        "timestamp",
        "EAMA11_MP10_media","EAMA11_MP10_IQAr","EAMA11_MP10_class",
        "EAMA11_MP2.5_media","EAMA11_MP2.5_IQAr","EAMA11_MP2.5_class",
        "EAMA21_MP10_media","EAMA21_MP10_IQAr","EAMA21_MP10_class",
        "EAMA21_MP2.5_media","EAMA21_MP2.5_IQAr","EAMA21_MP2.5_class",
        "EAMA31_MP10_media","EAMA31_MP10_IQAr","EAMA31_MP10_class",
        "EAMA31_MP2.5_media","EAMA31_MP2.5_IQAr","EAMA31_MP2.5_class",
        "EAMA41_MP10_media","EAMA41_MP10_IQAr","EAMA41_MP10_class",
        "EAMA41_MP2.5_media","EAMA41_MP2.5_IQAr","EAMA41_MP2.5_class",
    ]

    try:
        df = pd.read_csv(input_file, parse_dates=["timestamp"])
    except Exception as e:
        print(f"Erro ao ler '{input_file}': {e}")
        return

    missing = [c for c in cols if c not in df.columns]
    if missing:
        print("Colunas não encontradas:", missing)
        return

    df[cols].to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"Arquivo resumido salvo em '{output_file}'.")

if __name__ == "__main__":
    main()
