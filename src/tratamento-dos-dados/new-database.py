import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import multiprocessing as mp
from config import DATABASE_PATH, NEW_DATABASE_PATH

# Adiciona o caminho onde está o classifica.py
from classifica import calculate_IQAr, classify_air_quality, columns_mapping            

def extrair_valores(series):
    """Converte os valores de uma série para float, ignorando erros."""
    valores = []
    for v in series:
        try:
            valores.append(float(v))
        except:
            continue
    return valores

# Variável global para compartilhar o DataFrame com os workers
global_df = None

def init_worker(df):
    global global_df
    global_df = df

def process_timestamp(target):
    """
    Processa um único timestamp (target) e para cada estação calcula os parâmetros.
    Retorna um dicionário com uma linha de saída com os resultados agrupados.
    """
    global global_df
    mmss = target.strftime("%M:%S")
    start_time = target - timedelta(hours=23)
    
    # Filtra os registros do intervalo que tenham os mesmos mm:ss (usando a coluna auxiliar)
    subset = global_df[(global_df[0] >= start_time) & 
                       (global_df[0] <= target) & 
                       (global_df["mmss"] == mmss)]
    if subset.empty:
        return None

    row_data = {"timestamp": target.strftime("%Y-%m-%d %H:%M:%S")}
    # Define o row_type: se o target for "12:00:00", é do tipo "12:00:00"; caso contrário, "normal".
    row_type = "12:00:00" if target.strftime("%H:%M:%S") == "12:00:00" else "normal"
    row_data["row_type"] = row_type

    # Para cada estação, calcula os valores e adiciona com prefixo
    for station in ["EAMA11", "EAMA21", "EAMA31", "EAMA41"]:
        prefix = station + "_"
        try:
            mapping = columns_mapping[station][row_type]
            col_mp10 = mapping["MP10"]
            col_mp25 = mapping["MP2.5"]
            col_pts  = mapping["PTS"]
        except KeyError:
            row_data[prefix + "MP10_media"] = "dados insuficientes"
            row_data[prefix + "MP2.5_media"] = "dados insuficientes"
            row_data[prefix + "PTS_media"] = "dados insuficientes"
            continue

        vals_mp10 = extrair_valores(subset[col_mp10])
        vals_mp25 = extrair_valores(subset[col_mp25])
        vals_pts  = extrair_valores(subset[col_pts])

        # Processamento para MP10
        if len(vals_mp10) < 16:
            row_data[prefix + "MP10_media"] = "dados insuficientes"
            row_data[prefix + "MP10_I_ini"] = "dados insuficientes"
            row_data[prefix + "MP10_I_fin"] = "dados insuficientes"
            row_data[prefix + "MP10_C_ini"] = "dados insuficientes"
            row_data[prefix + "MP10_C_fin"] = "dados insuficientes"
            row_data[prefix + "MP10_IQAr"]  = "dados insuficientes"
            row_data[prefix + "MP10_class"] = "dados insuficientes"
        else:
            media_mp10 = np.mean(vals_mp10)
            iqar_mp10, I_ini_mp10, I_fin_mp10, C_ini_mp10, C_fin_mp10 = calculate_IQAr(media_mp10, "MP10")
            classificacao_mp10 = classify_air_quality(iqar_mp10)
            row_data[prefix + "MP10_media"] = media_mp10
            row_data[prefix + "MP10_I_ini"] = I_ini_mp10
            row_data[prefix + "MP10_I_fin"] = I_fin_mp10
            row_data[prefix + "MP10_C_ini"] = C_ini_mp10
            row_data[prefix + "MP10_C_fin"] = C_fin_mp10
            row_data[prefix + "MP10_IQAr"]  = iqar_mp10
            row_data[prefix + "MP10_class"] = classificacao_mp10

        # Processamento para MP2.5
        if len(vals_mp25) < 16:
            row_data[prefix + "MP2.5_media"] = "dados insuficientes"
            row_data[prefix + "MP2.5_I_ini"] = "dados insuficientes"
            row_data[prefix + "MP2.5_I_fin"] = "dados insuficientes"
            row_data[prefix + "MP2.5_C_ini"] = "dados insuficientes"
            row_data[prefix + "MP2.5_C_fin"] = "dados insuficientes"
            row_data[prefix + "MP2.5_IQAr"]  = "dados insuficientes"
            row_data[prefix + "MP2.5_class"] = "dados insuficientes"
        else:
            media_mp25 = np.mean(vals_mp25)
            iqar_mp25, I_ini_mp25, I_fin_mp25, C_ini_mp25, C_fin_mp25 = calculate_IQAr(media_mp25, "MP2.5")
            classificacao_mp25 = classify_air_quality(iqar_mp25)
            row_data[prefix + "MP2.5_media"] = media_mp25
            row_data[prefix + "MP2.5_I_ini"] = I_ini_mp25
            row_data[prefix + "MP2.5_I_fin"] = I_fin_mp25
            row_data[prefix + "MP2.5_C_ini"] = C_ini_mp25
            row_data[prefix + "MP2.5_C_fin"] = C_fin_mp25
            row_data[prefix + "MP2.5_IQAr"]  = iqar_mp25
            row_data[prefix + "MP2.5_class"] = classificacao_mp25

        # Processamento para PTS (apenas média horária)
        if len(vals_pts) < 16:
            row_data[prefix + "PTS_media"] = "dados insuficientes"
        else:
            media_pts = np.mean(vals_pts)
            row_data[prefix + "PTS_media"] = media_pts

    return row_data

def process_database_grouped_parallel(database_path, output_path):
    try:
        df = pd.read_csv(database_path, header=None, skiprows=1, low_memory=False)
    except Exception as e:
        print(f"Erro ao ler o CSV: {e}")
        return
    try:
        df[0] = pd.to_datetime(df[0], format="%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"Erro na conversão dos timestamps: {e}")
        return

    # Cria a coluna auxiliar "mmss" com os minutos e segundos
    df["mmss"] = df[0].dt.strftime("%M:%S")
    df = df.sort_values(by=0)
    unique_timestamps = df[0].drop_duplicates().sort_values()

    tasks = list(unique_timestamps)
    with mp.Pool(initializer=init_worker, initargs=(df,)) as pool:
        results = pool.map(process_timestamp, tasks)
    rows = [r for r in results if r is not None]
    if rows:
        new_df = pd.DataFrame(rows)
        new_df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"New database saved to {output_path}")
    else:
        print("Nenhum dado foi processado.")

if __name__ == "__main__":
    process_database_grouped_parallel(DATABASE_PATH, NEW_DATABASE_PATH)

