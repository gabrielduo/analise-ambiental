import os
import shutil
import pandas as pd
import pyexcel as p
import tkinter as tk
from tkinter import filedialog, messagebox
from openpyxl import load_workbook
from datetime import datetime

def converter_xls_para_xlsx(filepath):
    """Se o arquivo for .xls, converte para .xlsx usando pyexcel."""
    base, ext = os.path.splitext(filepath)
    if ext.lower() == '.xls':
        new_filepath = base + '.xlsx'
        p.save_book_as(file_name=filepath, dest_file_name=new_filepath)
        return new_filepath
    return filepath

def detect_version(filepath):
    """
    Detecta a versão da planilha verificando o conteúdo das células:
      - Versão 3: se a célula B2 contém "EM11" (novo formato com coluna B preenchida).
      - Versão 1: se a célula C2 contém "EM11".
      - Versão 2: se a célula AA2 contém "EM11".
    Retorna 3, 1, 2 ou None se não encontrar.
    """
    wb = load_workbook(filepath, data_only=True)
    ws = wb.active
    # Novo formato: coluna B preenchida, EM11 em B2
    if ws['B2'].value and "EM11" in str(ws['B2'].value):
        return 3
    if ws['C2'].value and "EM11" in str(ws['C2'].value):
        return 1
    if ws['AA2'].value and "EM11" in str(ws['AA2'].value):
        return 2
    return None

def processar_met(filepath):
    """
    Processa o arquivo met (met.xls ou met.xlsx) conforme:
      - Se existir somente met.xlsx na pasta, cria uma cópia (met_corrigido.xlsx) e trabalha sobre ela.
      - Converte .xls para .xlsx se necessário.
      - Detecta a versão do formato e extrai as colunas de interesse (os dados começam na linha 9).
      - Converte a data para "YYYY-MM-DD HH:MM:SS" e formata os demais valores (troca ponto por vírgula e preenche vazios com "n").
      - Salva os resultados em met_corrigido.xlsx e met.csv (sem cabeçalho) na mesma pasta.
    """
    basename = os.path.basename(filepath).lower()
    dirpath = os.path.dirname(filepath)
    
    if basename not in ["met.xls", "met.xlsx"]:
        print(f"Arquivo {filepath} não possui o nome esperado 'met.xls' ou 'met.xlsx'.")
        return

    # Verifica quantos arquivos existem na pasta (em minúsculas)
    files_in_dir = [f.lower() for f in os.listdir(dirpath) if os.path.isfile(os.path.join(dirpath, f))]
    
    # Se existir somente met.xlsx (sem met.xls), cria uma cópia para met_corrigido.xlsx e trabalha sobre ela
    if files_in_dir.count("met.xlsx") == 1 and "met.xls" not in files_in_dir:
        corr_path = os.path.join(dirpath, "met_corrigido.xlsx")
        shutil.copy2(filepath, corr_path)
        filepath = corr_path
        print("Somente met.xlsx encontrado. Usando met_corrigido.xlsx como base para criação do CSV.")
    else:
        filepath = converter_xls_para_xlsx(filepath)

    # Detecta o formato (versão)
    version = detect_version(filepath)
    if not version:
        print(f"Formato diferente encontrado em {filepath}. Verifique a formatação da planilha.")
        return

    # Lê a planilha inteira (os dados começam na linha 9 – índice 8)
    df = pd.read_excel(filepath, header=None, engine='openpyxl')

    # Define os índices das colunas conforme o formato detectado
    if version == 1:
        # Versão 1 (antigo formato sem dados em coluna B)
        col_data = 0   # Data em A
        col_vel  = 2   # Velocidade Escalar do Vento em C
        col_dir  = 4   # Direção Escalar do Vento em E
        col_prec = 6   # Precipitação Pluviométrica em G
        col_temp = 8   # Temperatura em I
        col_umid = 12  # Umidade Relativa em M
        col_pres = 14  # Pressão Atmosférica em O
    elif version == 2:
        # Versão 2 (formato deslocado, EM11 em AA2)
        col_data = 0    # Data em A
        col_vel  = 26   # Velocidade Escalar do Vento em AA
        col_dir  = 28   # Direção Escalar do Vento em AC
        col_prec = 30   # Precipitação Pluviométrica em AE
        col_temp = 32   # Temperatura em AG
        col_umid = 36   # Umidade Relativa em AK
        col_pres = 38   # Pressão Atmosférica em AM
    elif version == 3:
        # Versão 3 (novo formato com coluna B preenchida, EM11 de B até O)
        col_data = 0   # Data em A
        col_vel  = 1   # Velocidade Escalar do Vento agora começa em B
        col_dir  = 3   # Direção Escalar do Vento em D (anteriormente em E)
        col_prec = 5   # Precipitação Pluviométrica em F (anteriormente em G)
        col_temp = 7   # Temperatura em H (anteriormente em I)
        col_umid = 11  # Umidade Relativa em L (anteriormente em M)
        col_pres = 13  # Pressão Atmosférica em N (anteriormente em O)
    else:
        print("Formato de planilha não reconhecido.")
        return

    # Seleciona os dados a partir da linha 9 (índice 8)
    df_measure = df.iloc[8:, [col_data, col_vel, col_dir, col_prec, col_temp, col_umid, col_pres]].copy()
    df_measure = df_measure[df_measure.iloc[:, 0].notna()]  # Remove linhas sem data

    # Converte a coluna de data para o formato "YYYY-MM-DD HH:MM:SS"
    def parse_date(x):
        try:
            dt = pd.to_datetime(x, dayfirst=True, errors='raise')
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print(f"Erro ao converter data '{x}': {e}")
            return "n"

    df_measure.iloc[:, 0] = df_measure.iloc[:, 0].apply(parse_date)

    # Formata os demais valores: se ausente, preenche com "n"; caso contrário, converte para float e troca ponto por vírgula
    def format_val(x):
        if pd.isna(x):
            return "n"
        try:
            val = float(x)
            return str(val).replace('.', ',')
        except:
            return str(x)

    for col_idx in range(1, 7):
        df_measure.iloc[:, col_idx] = df_measure.iloc[:, col_idx].apply(format_val)

    # Salva o arquivo XLSX corrigido (met_corrigido.xlsx) – sobrescrevendo, se já existir
    out_xlsx_path = os.path.join(dirpath, "met_corrigido.xlsx")
    df_measure.to_excel(out_xlsx_path, index=False, header=True)
    print(f"Arquivo XLSX criado/atualizado: {out_xlsx_path}")

    # Salva o arquivo CSV (sem cabeçalho)
    out_csv_path = os.path.join(dirpath, "met.csv")
    df_measure.to_csv(out_csv_path, index=False, header=False, encoding='utf-8-sig')
    print(f"Arquivo CSV criado: {out_csv_path}")

def selecionar_e_processar():
    root = tk.Tk()
    root.withdraw()
    try:
        filepath = filedialog.askopenfilename(
            title="Selecione a planilha met.xls ou met.xlsx",
            filetypes=[("Excel Files", "*.xls *.xlsx")]
        )
        if not filepath:
            messagebox.showinfo("Informação", "Nenhum arquivo selecionado.")
            return

        processar_met(filepath)
        messagebox.showinfo("Sucesso", "Arquivo processado com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao processar o arquivo:\n{e}")
    finally:
        root.destroy()

if __name__ == "__main__":
    selecionar_e_processar()
