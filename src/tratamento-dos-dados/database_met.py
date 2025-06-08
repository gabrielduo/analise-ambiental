import os
import pandas as pd

# Diretório onde o script está localizado
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Caminho relativo para a pasta 'dados-coletados'
OUTPUT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'tratamento-dos-dados'))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "database_met.csv")

# Mapeamento dos nomes dos meses em português para números
months_map = {
    'janeiro': 1,
    'fevereiro': 2,
    'março': 3,
    'marco': 3,  
    'abril': 4,
    'maio': 5,
    'junho': 6,
    'julho': 7,
    'agosto': 8,
    'setembro': 9,
    'outubro': 10,
    'novembro': 11,
    'dezembro': 12,
}

files_list = []

# Percorre as pastas de ano dentro do BASE_DIR
for year_folder in os.listdir(BASE_DIR):
    year_path = os.path.join(BASE_DIR, year_folder)
    if not os.path.isdir(year_path):
        continue
    try:
        year_int = int(year_folder)
    except ValueError:
        continue
    if year_int < 2022:
        continue

    # Percorre as pastas de mês dentro do ano
    for month_folder in os.listdir(year_path):
        month_path = os.path.join(year_path, month_folder)
        if not os.path.isdir(month_path):
            continue
        month_name = month_folder.lower()
        if month_name not in months_map:
            continue
        month_number = months_map[month_name]
        # Verifica se o arquivo "met.csv" existe na pasta do mês
        met_csv_path = os.path.join(month_path, "met.csv")
        if os.path.isfile(met_csv_path):
            files_list.append((year_int, month_number, met_csv_path))

# Ordena os arquivos por ano e mês
files_list.sort(key=lambda x: (x[0], x[1]))

# Lê e acumula os arquivos CSV
dfs = []
for year, month, file_path in files_list:
    try:
        df = pd.read_csv(file_path, header=None, encoding="utf-8-sig")
        dfs.append(df)
        print(f"Processado: {file_path}")
    except Exception as e:
        print(f"Erro ao ler {file_path}: {e}")

if dfs:
    # Concatena todos os DataFrames ignorando os índices
    combined_df = pd.concat(dfs, ignore_index=True)
    # Salva o database final sem cabeçalho
    combined_df.to_csv(OUTPUT_FILE, index=False, header=False, encoding="utf-8-sig")
    print(f"Database criado com sucesso em: {OUTPUT_FILE}")
else:
    print("Nenhum arquivo CSV encontrado para a criação do database.")
