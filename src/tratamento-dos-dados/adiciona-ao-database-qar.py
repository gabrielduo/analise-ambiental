"""
============================================
Arquivo: adiciona-ao-database.py
--------------------------------------------
Ferramenta de interface gráfica (Tkinter) para adicionar arquivos CSV ao database principal:

- Permite ao usuário selecionar um arquivo CSV (pulando cabeçalhos iniciais).
- Extrai ano e mês da primeira linha de dados para evitar duplicação.
- Mantém um registro de períodos já processados em 'info-database-meses.txt'.
- Em caso de nova chave (ano-mês), concatena o conteúdo do CSV selecionado ao 'database.csv'.
- Exibe mensagens ao usuário via dialogs (info, sucesso, erro).

Principais funções:
  - carregar_info_database_meses: lê e retorna períodos já registrados.
  - extrair_ano_mes_primeira_linha: obtém 'YYYY-mes' da primeira linha de dados.
  - adicionar_csv_no_database: concatena novos dados ao database existente.
  - selecionar_e_processar: orquestra todo o fluxo de seleção, verificação e adição.
  - main: cria janela principal com botão para iniciar o processo.

Dependências:
  - pandas, tkinter, os, shutil, datetime.

Uso:
  Execute este script diretamente para abrir a interface de seleção de CSV.
============================================
"""

import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
from config import INFO_DATABASE_MESES_PATH, DATABASE_PATH

# Dicionário para converter número do mês em nome por extenso (em português)
MESES_PT = {
    1: "janeiro", 2: "fevereiro", 3: "marco", 4: "abril", 5: "maio", 6: "junho",
    7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
}

def carregar_info_database_meses(info_path):
    """
    Lê o arquivo info-database-meses.txt e armazena cada 'ANO-MÊS' em um set,
    para verificar se já existe no database.
    Exemplo de linha no arquivo:
    2022-janeiro: linhas 1-775
    """
    if not os.path.isfile(info_path):
        # Se o arquivo não existir, retornamos um set vazio
        return set()

    with open(info_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    chaves_existentes = set()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Exemplo: "2022-janeiro: linhas 1-775"
        partes = line.split(":")
        if len(partes) > 1:
            chave = partes[0].strip()  # "2022-janeiro"
            chaves_existentes.add(chave.lower())  # Armazena em minúsculo para evitar diferenças
    return chaves_existentes

def extrair_ano_mes_primeira_linha(csv_path):
    """
    Lê apenas a primeira linha de dados úteis (pulando 8 linhas iniciais)
    e extrai o ano e o mês a partir do timestamp na primeira coluna.
    Retorna uma string no formato "2024-dezembro", por exemplo.
    """
    # Lê apenas a primeira linha de dados (nrows=1), ignorando as 8 primeiras linhas
    df_temp = pd.read_csv(csv_path, header=None, skiprows=8, nrows=1)
    if df_temp.empty:
        raise ValueError("O arquivo selecionado não possui dados após as 8 linhas iniciais.")

    # Extrai o timestamp (primeira coluna)
    timestamp_str = str(df_temp.iloc[0, 0]).strip()
    if not timestamp_str:
        raise ValueError("A primeira coluna da primeira linha de dados está vazia.")

    # Tenta converter para datetime
    try:
        dt = pd.to_datetime(timestamp_str, errors="raise", infer_datetime_format=True)
    except Exception:
        raise ValueError(f"Não foi possível converter '{timestamp_str}' em data/hora.")

    ano = dt.year
    mes_num = dt.month
    mes_nome = MESES_PT.get(mes_num, None)

    if not mes_nome:
        raise ValueError(f"Número de mês inválido ao interpretar o timestamp: {timestamp_str}")

    # Retorna no formato "2024-dezembro"
    return f"{ano}-{mes_nome}".lower()

def adicionar_csv_no_database(csv_path, database_path):
    """
    Lê o CSV (pulando as 8 primeiras linhas) e adiciona os dados ao final de database.csv,
    salvando diretamente nele (sem criar database2.csv).
    """
    # Lê o arquivo database.csv (sem cabeçalho)
    if not os.path.isfile(database_path):
        raise FileNotFoundError(f"O arquivo '{database_path}' não foi encontrado.")

    df_database = pd.read_csv(database_path, header=None)

    # Lê o novo CSV, pulando as 8 primeiras linhas
    df_novo = pd.read_csv(csv_path, header=None, skiprows=8)

    # Concatena os dois DataFrames
    df_concatenado = pd.concat([df_database, df_novo], ignore_index=True)

    # Salva em database.csv (sem cabeçalho, sem índice)
    df_concatenado.to_csv(database_path, header=False, index=False, encoding='utf-8-sig')

def selecionar_e_processar():
    """
    Função principal da interface:
      1) Pede ao usuário para selecionar um CSV.
      2) Verifica se o ano-mês do CSV já consta em info-database-meses.txt.
      3) Se não constar, adiciona as linhas no final de database.csv.
    """
    # Caminhos a partir do config.py
    info_database_meses = INFO_DATABASE_MESES_PATH
    database_csv = DATABASE_PATH

    # Janela de seleção de arquivo
    root = tk.Tk()
    root.withdraw()
    csv_selecionado = filedialog.askopenfilename(
        title="Selecione o arquivo QAR CSV (ou gerado a partir dele)",
        filetypes=[("CSV Files", "*.csv")]
    )
    if not csv_selecionado:
        messagebox.showinfo("Informação", "Nenhum arquivo selecionado.")
        return

    try:
        # Carrega chaves existentes no info-database-meses.txt
        chaves_existentes = carregar_info_database_meses(info_database_meses)

        # Extrai a chave (ano-mês) do arquivo selecionado
        chave_nova = extrair_ano_mes_primeira_linha(csv_selecionado)

        if chave_nova in chaves_existentes:
            # Se já existir, avisamos o usuário e não adicionamos
            messagebox.showinfo(
                "Informação",
                f"O período '{chave_nova}' já está presente no database.\n"
                "Não serão adicionadas linhas duplicadas."
            )
        else:
            # Se não existir, adicionamos ao final do database.csv
            adicionar_csv_no_database(csv_selecionado, database_csv)
            messagebox.showinfo(
                "Sucesso",
                f"As linhas de '{os.path.basename(csv_selecionado)}' foram adicionadas a '{database_csv}'."
            )
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao processar o arquivo:\n{e}")

def main():
    # Cria uma janela simples com um botão
    root = tk.Tk()
    root.title("Adicionar CSV ao Database")
    root.geometry("400x120")

    label = tk.Label(root, text="Clique no botão para selecionar o arquivo CSV:")
    label.pack(pady=10)

    botao = tk.Button(root, text="Selecionar CSV", command=selecionar_e_processar)
    botao.pack()

    root.mainloop()

if __name__ == "__main__":
    main()
