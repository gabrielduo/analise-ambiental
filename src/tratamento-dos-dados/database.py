import os
import pandas as pd
from datetime import datetime
from config import DADOS_COLETADOS_DIR as BASE_DIR

# CONFIGURAÇÕES
# Diretório onde o script está localizado (usado para salvar os arquivos gerados)
CUR_DIR = os.path.dirname(os.path.abspath(__file__))

# Arquivos de saída serão gerados na mesma pasta do código
OUTPUT_CSV = os.path.join(CUR_DIR, "database.csv")
INFO_TXT = os.path.join(CUR_DIR, "info-database-meses.txt")

# Lista de meses em ordem
meses = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho", 
         "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

def corrigir_timestamp(ts, mes_info):
    """
    Corrige o timestamp, especialmente para linhas referentes a fevereiro,
    onde pode haver inversão de dia/mês.
    """
    mes_info = str(mes_info).strip().lower()
    if mes_info == "fevereiro":
        try:
            dt = pd.to_datetime(ts, errors='coerce', infer_datetime_format=True)
            if pd.isna(dt):
                return ts
            if dt.month != 2:
                # Corrige a inversão: o mês original vira o dia e fevereiro se torna o mês
                novo_dt = datetime(dt.year, 2, dt.month, dt.hour, dt.minute, dt.second)
                return novo_dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return ts
    else:
        try:
            dt = pd.to_datetime(ts, errors='coerce', infer_datetime_format=True)
            if pd.isna(dt):
                return ts
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return ts

def combinar_csvs(base_dir, output_csv):
    """
    Percorre a estrutura de pastas (anos e meses), lê os arquivos 'qar.csv' ou 'qar_novo.csv'
    (ignorando as 7 primeiras linhas) e os combina em um único CSV. 
    Adiciona as colunas 'Ano' e 'Mes' e corrige os timestamps.
    """
    lista_dfs = []

    # Percorre as pastas de anos
    for ano in os.listdir(base_dir):
        caminho_ano = os.path.join(base_dir, ano)
        if not os.path.isdir(caminho_ano):
            continue

        # Percorre os meses na ordem definida
        for mes in meses:
            caminho_mes = os.path.join(caminho_ano, mes)
            if not os.path.isdir(caminho_mes):
                continue

            # Busca arquivos 'qar.csv' ou 'qar_novo.csv'
            for arquivo in os.listdir(caminho_mes):
                if arquivo.lower() in ["qar.csv", "qar_novo.csv"]:
                    filepath = os.path.join(caminho_mes, arquivo)
                    try:
                        # Carrega o CSV ignorando as 7 primeiras linhas
                        df = pd.read_csv(filepath, header=None, skiprows=8)
                        df['Ano'] = ano
                        df['Mes'] = mes
                        lista_dfs.append(df)
                    except Exception as e:
                        print(f"Erro ao processar {filepath}: {e}")

    # Combina os DataFrames e corrige os timestamps
    if lista_dfs:
        df_final = pd.concat(lista_dfs, ignore_index=True)
        df_final[0] = df_final.apply(lambda row: corrigir_timestamp(row[0], row['Mes']), axis=1)
        df_final.to_csv(output_csv, index=False, encoding='utf-8-sig', header=False)
        print(f"Dados combinados e corrigidos salvos em '{output_csv}'.")
    else:
        print("Nenhum arquivo válido encontrado.")

def validar_consistencia_colunas(filepath):
    """
    Valida se, para cada ano presente no CSV, todas as linhas possuem a mesma quantidade
    de elementos (não nulos). Exibe no terminal eventuais inconsistências.
    """
    df = pd.read_csv(filepath, header=None)
    # Assume que a penúltima coluna contém o ano
    anos = df.iloc[:, -2].unique()
    inconsistencias = []

    for ano in anos:
        df_ano = df[df.iloc[:, -2] == ano]
        # Conta os elementos não nulos de cada linha
        colunas_unicas = df_ano.apply(lambda row: len(row.dropna()), axis=1).unique()
        if len(colunas_unicas) > 1:
            inconsistencias.append((ano, colunas_unicas))

    if inconsistencias:
        print("Inconsistências encontradas:")
        for ano, colunas in inconsistencias:
            print(f"Ano: {ano}, Quantidades de colunas encontradas: {colunas}")
    else:
        print("Todos os anos possuem a mesma quantidade de elementos separados por vírgulas.")

def encontrar_intervalos(lista_de_linhas):
    """
    Agrupa números de linhas contínuos em intervalos.
    Exemplo: [1,2,3,5,6] gera [(1,3), (5,6)]
    """
    intervalos = []
    inicio = lista_de_linhas[0]
    atual = inicio

    for linha in lista_de_linhas[1:]:
        if linha == atual + 1:
            atual = linha
        else:
            intervalos.append((inicio, atual))
            inicio = linha
            atual = inicio
    intervalos.append((inicio, atual))
    return intervalos

def gerar_info_database(filepath, output_txt):
    """
    Lê o CSV unificado e agrupa os índices (linhas) de cada combinação "ano-mes".
    Em seguida, gera um arquivo de texto com os intervalos (convertendo de 0-indexado para 1-indexado).
    """
    df = pd.read_csv(filepath, header=None)
    # Define nomes de colunas para facilitar a referência: as últimas duas são 'ano' e 'mes'
    n_cols = df.shape[1]
    df.columns = [f'col{i}' for i in range(n_cols - 2)] + ['ano', 'mes']

    resultado = {}
    for index, row in df.iterrows():
        chave = f"{row['ano']}-{row['mes']}"
        resultado.setdefault(chave, []).append(index)

    with open(output_txt, 'w') as f:
        for chave, linhas in resultado.items():
            intervalos = encontrar_intervalos(linhas)
            # Converte para 1-indexado e formata os intervalos
            intervalos_str = ', '.join(f"linhas {inicio+1}-{fim+1}" for inicio, fim in intervalos)
            f.write(f"{chave}: {intervalos_str}\n")
    
    print(f"Arquivo '{output_txt}' criado com sucesso com intervalos de linhas.")

if __name__ == "__main__":
    # 1. Combina os CSVs e gera o arquivo unificado na mesma pasta do script
    combinar_csvs(BASE_DIR, OUTPUT_CSV)
    
    # 2. Valida a consistência das colunas e imprime as informações no terminal
    validar_consistencia_colunas(OUTPUT_CSV)
    
    # 3. Gera o arquivo .txt com os intervalos de linhas por ano e mês na mesma pasta do script
    gerar_info_database(OUTPUT_CSV, INFO_TXT)
