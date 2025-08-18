import os
import pandas as pd
import argparse

# -------------------------------
# Utilidades de IO
# -------------------------------
def _ext(path: str) -> str:
    return os.path.splitext(path)[1].lower()

def _read_excel_any(path: str, header=None) -> pd.DataFrame:
    """
    Lê Excel em DataFrame:
      - .xls  -> engine='xlrd'   (xlrd==1.2.0)
      - .xlsx -> engine='openpyxl'
    """
    ext = _ext(path)
    if ext == ".xls":
        return pd.read_excel(path, header=header, engine="xlrd")
    elif ext == ".xlsx":
        return pd.read_excel(path, header=header, engine="openpyxl")
    else:
        raise ValueError(f"Extensão não suportada: {ext}")

def padronizar_csv(filepath_input: str) -> None:
    """Padroniza o CSV: trim; vazios -> 'n'."""
    with open(filepath_input, "r", encoding="utf-8") as f:
        linhas = f.readlines()

    linhas_corrigidas = []
    for linha in linhas:
        valores = [v.strip() if v.strip() != "" else "n" for v in linha.rstrip("\n").split(",")]
        linhas_corrigidas.append(",".join(valores))

    with open(filepath_input, "w", encoding="utf-8-sig") as f:
        for linha in linhas_corrigidas:
            f.write(linha + "\n")

    print(f"CSV padronizado salvo em: {filepath_input}")

def remover_coluna_b_se_vazia(df: pd.DataFrame) -> pd.DataFrame:
    """Remove a coluna B (índice 1) se estiver completamente vazia."""
    if df.shape[1] > 1 and df.iloc[:, 1].isnull().all():
        df = df.drop(columns=[1])
        print("Coluna B removida por estar completamente vazia.")
    return df

# -------------------------------
# Validadores de formato
# -------------------------------
def validar_e_carregar_qar(filepath: str) -> pd.DataFrame:
    df = _read_excel_any(filepath, header=None)
    if df.shape[0] < 9 or df.shape[1] < 15:
        raise ValueError("A planilha não parece ter linhas/colunas suficientes para o padrão esperado.")

    # C2 (índices base 0 -> linha 1, coluna 2)
    estacao_eama11 = df.iloc[1, 2]
    if "EAMA11" not in str(estacao_eama11):
        raise ValueError("A estação EAMA11 não foi encontrada na célula esperada (C2).")
    return df

def validar_cenario_maior(filepath: str) -> pd.DataFrame:
    df = _read_excel_any(filepath, header=None)
    if df.shape[0] < 9 or df.shape[1] < 82:
        raise ValueError("A planilha não parece ter dimensões suficientes para o cenário maior.")

    texto_c2 = str(df.iloc[1, 2])  # C2
    if "EAMA11" not in texto_c2:
        if "EAMA41" in texto_c2:
            raise ValueError("Planilha invertida detectada: EAMA41 encontrada onde deveria estar EAMA11.")
        else:
            raise ValueError("Nem EAMA11 nem EAMA41 encontrados na posição esperada (C2). Formato desconhecido.")
    return df

def corrigir_inversao_colunas(filepath: str) -> str:
    df = _read_excel_any(filepath, header=None)

    # Faixas (0-based): C..V (2..21), W..AP (22..41), AQ..BJ (42..61), BK..CD (62..81)
    eama11_slice = slice(2, 22)   # C..V
    eama41_slice = slice(62, 82)  # BK..CD
    eama31_slice = slice(22, 42)  # W..AP
    eama21_slice = slice(42, 62)  # AQ..BJ

    df_corrigido = df.copy()

    # Troca EAMA11 <-> EAMA41
    eama11_data = df.iloc[:, eama11_slice].values
    eama41_data = df.iloc[:, eama41_slice].values
    df_corrigido.iloc[:, eama11_slice] = eama41_data
    df_corrigido.iloc[:, eama41_slice] = eama11_data

    # Troca EAMA31 <-> EAMA21
    eama31_data = df_corrigido.iloc[:, eama31_slice].values
    eama21_data = df_corrigido.iloc[:, eama21_slice].values
    df_corrigido.iloc[:, eama31_slice] = eama21_data
    df_corrigido.iloc[:, eama21_slice] = eama31_data

    base, _ = os.path.splitext(filepath)
    novo_arquivo = base + "_corrigido.xlsx"
    # Salva sem cabeçalho/index para preservar layout
    with pd.ExcelWriter(novo_arquivo, engine="openpyxl") as writer:
        df_corrigido.to_excel(writer, index=False, header=False)
    return novo_arquivo

def validar_novo_formato(filepath: str) -> pd.DataFrame:
    df = _read_excel_any(filepath, header=None)

    # B2, N2, Z2, AL2  -> (1,1), (1,13), (1,25), (1,37)
    eama11 = df.iloc[1, 1]
    eama21 = df.iloc[1, 13]
    eama31 = df.iloc[1, 25]
    eama41 = df.iloc[1, 37]

    if "EAMA11" not in str(eama11) or "EAMA21" not in str(eama21):
        raise ValueError("Novo formato inválido: EAMA11 ou EAMA21 não encontrados nas células esperadas.")
    if "EAMA31" not in str(eama31) or "EAMA41" not in str(eama41):
        raise ValueError("Novo formato inválido: EAMA31 ou EAMA41 não encontrados nas células esperadas.")

    print("Sucesso: Planilha validada no novo formato.")
    return df

# -------------------------------
# Pipeline principal QAR
# -------------------------------
def processar_qar(filepath: str):
    """
    Pipeline headless para QAR:
      - Tenta validar cenário original (EAMA11 em C2).
      - Se falhar, tenta cenário maior; se "invertida", corrige e valida.
      - Senão, tenta novo formato (EAMAxx espalhadas) e gera *_novo.csv.
      - Em todos os casos, remove Coluna B se totalmente vazia e padroniza CSV.
    Gera um dos arquivos:
      - <base>.csv
      - <base>_maior.csv
      - <base>_corrigido.csv (se houve inversão)
      - <base>_novo.csv
    """
    try:
        # 1) Cenário original
        df = validar_e_carregar_qar(filepath)
        print(f"Sucesso: {filepath} validada no cenário original!")
        df = remover_coluna_b_se_vazia(df)
        base, _ = os.path.splitext(filepath)
        output_csv = base + ".csv"
        df.to_csv(output_csv, index=False, header=False)
        padronizar_csv(output_csv)
        return
    except Exception as e:
        erro_msg = str(e)

    # 2) Cenário maior (e possibilidade de inversão)
    try:
        df_maior = validar_cenario_maior(filepath)
        print(f"Sucesso: {filepath} validada no cenário maior sem inversão!")
        df_maior = remover_coluna_b_se_vazia(df_maior)
        base, _ = os.path.splitext(filepath)
        output_csv = base + "_maior.csv"
        df_maior.to_csv(output_csv, index=False, header=False)
        padronizar_csv(output_csv)
        return
    except Exception as e2:
        if "Planilha invertida detectada" in str(e2):
            # Corrige inversão e valida novamente como cenário maior
            caminho_corrigido = corrigir_inversao_colunas(filepath)
            df_corrigido = validar_cenario_maior(caminho_corrigido)
            print(f"Sucesso: {filepath} estava invertida, foi corrigida e validada com sucesso!")
            df_corrigido = remover_coluna_b_se_vazia(df_corrigido)
            base, _ = os.path.splitext(caminho_corrigido)
            output_csv = base + ".csv"
            df_corrigido.to_csv(output_csv, index=False, header=False)
            padronizar_csv(output_csv)
            return

    # 3) Novo formato
    try:
        df_novo = validar_novo_formato(filepath)
        print(f"Sucesso: {filepath} validada no novo formato!")
        df_novo = remover_coluna_b_se_vazia(df_novo)
        base, _ = os.path.splitext(filepath)
        output_csv = base + "_novo.csv"
        df_novo.to_csv(output_csv, index=False, header=False)
        padronizar_csv(output_csv)
        return
    except Exception as e3:
        print(f"Erro de Validação em {filepath}: {e3}")

# Execução via CLI (opcional)
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Valida QAR (diversos formatos) e gera CSVs headless.")
    ap.add_argument("arquivo", help="Caminho para qar.xls ou qar.xlsx")
    args = ap.parse_args()
    processar_qar(args.arquivo)
