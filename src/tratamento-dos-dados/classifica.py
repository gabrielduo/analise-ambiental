"""
============================================
Arquivo: classifica.py
--------------------------------------------
Define funções para cálculo do Índice de Qualidade do Ar (IQAr):
- Dicionário de parâmetros (faixas de concentração e índices) para MP2.5 e MP10.
- get_parameter_range: busca faixas de concentração/índice.
- calculate_IQAr: calcula IQAr e retorna parâmetros de interpolação.
- classify_air_quality: mapeia valor de IQAr para categoria qualitativa.
- parse_date_time: converte strings de data/hora para datetime.
- extract_valid_values: filtra valores numéricos de série.
- classify_air: orquestra leitura de CSV, seleção de dados por horário,
  cálculo de médias, IQAr e classificação final para MP10, MP2.5 e PTS.
- Permite execução standalone via CLI para testes rápidos.
============================================
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Dicionário de parâmetros: limites de concentração e índices para cada poluente.
PARAMS = {
    "MP2.5": {
        "concentration_ranges": [
            (25, (0, 25)),
            (50, (26, 50)),
            (75, (51, 75)),
            (125, (76, 125)),
            (float("inf"), (126, 300))
        ],
        "indices": [
            (25, (0, 40)),
            (50, (41, 80)),
            (75, (81, 120)),
            (125, (121, 200)),
            (float("inf"), (201, 400))
        ]
    },
    "MP10": {
        "concentration_ranges": [
            (50, (0, 50)),
            (100, (51, 100)),
            (150, (101, 150)),
            (250, (151, 250)),
            (float("inf"), (251, 600))
        ],
        "indices": [
            (50, (0, 40)),
            (100, (41, 80)),
            (150, (81, 120)),
            (250, (121, 200)),
            (float("inf"), (201, 400))
        ]
    }
}

def get_parameter_range(value, pollutant_type, key):
    """
    Busca a faixa (concentração ou índice) para o valor informado, 
    baseado no dicionário de parâmetros.
    
    Parâmetros:
      - value: valor medido.
      - pollutant_type: tipo de poluente (e.g., "MP2.5" ou "MP10").
      - key: "concentration_ranges" ou "indices".
    
    Retorna a tupla com os limites da faixa.
    """
    for limit, range_tuple in PARAMS[pollutant_type][key]:
        if value <= limit:
            return range_tuple
    # Caso não encontre, pode retornar o último ou lançar erro.
    return PARAMS[pollutant_type][key][-1][1]

def calculate_IQAr(value, pollutant_type):
    """
    Calcula o IQAr com base no valor médio de concentração e no poluente.
    Caso o valor seja NaN, retorna "Não Representa" e os demais parâmetros como None.
    """
    if pd.isna(value):
        return "Não Representa", None, None, None, None
    C_ini, C_fin = get_parameter_range(value, pollutant_type, "concentration_ranges")
    I_ini, I_fin = get_parameter_range(value, pollutant_type, "indices")
    iqar = I_ini + ((I_fin - I_ini) / (C_fin - C_ini)) * (value - C_ini)
    return iqar, I_ini, I_fin, C_ini, C_fin

#def classify_air_quality(iqar):
#    """
#    Classifica a qualidade do ar com base no valor do IQAr.
#    """
#    if iqar == "Não Representa":
#        return iqar
#    if iqar < 41:
#        return "BOA"
#    if iqar < 81:
#        return "MODERADA"
#    if iqar < 121:
#        return "RUIM"
#    if iqar < 201:
#        return "MUITO RUIM"
#    return "PÉSSIMA"
# Complexidade O(n) em ambos os casos, e pra ser sincero, o de cima é até mais legível.
def classify_air_quality(iqar): 
    """
    Classifica a qualidade do ar com base no valor numérico do IQAr.
    """
    if iqar == "Não Representa":
        return iqar

    thresholds = [
        (40, "BOA"),
        (80, "MODERADA"),
        (120, "RUIM"),
        (200, "MUITO RUIM")
    ]

    for limit, category in thresholds:
        if iqar <= limit:
            return category
    return "PÉSSIMA"

# Mapeamento das colunas para cada estação e tipo de linha
columns_mapping = {
    "EAMA11": {
        "normal": {"PTS": 1, "MP10": 5, "MP2.5": 9},
        "12:00:00": {"PTS": 3, "MP10": 7, "MP2.5": 11}
    },
    "EAMA21": {
        "normal": {"PTS": 13, "MP10": 17, "MP2.5": 21},
        "12:00:00": {"PTS": 15, "MP10": 19, "MP2.5": 23}
    },
    "EAMA31": {
        "normal": {"PTS": 25, "MP10": 29, "MP2.5": 33},
        "12:00:00": {"PTS": 27, "MP10": 31, "MP2.5": 35}
    },
    "EAMA41": {
        "normal": {"PTS": 37, "MP10": 41, "MP2.5": 45},
        "12:00:00": {"PTS": 39, "MP10": 43, "MP2.5": 47}
    }
}

def parse_date_time(input_date_str, input_time_str):
    """
    Tenta converter as strings de data e hora para objetos datetime.
    Aceita formatos "dd-mm-YYYY" e "YYYY-mm-dd" para a data.
    """
    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            date_obj = datetime.strptime(input_date_str, fmt)
            break
        except ValueError:
            continue
    else:
        raise ValueError("Formato de data inválido.")
    
    try:
        time_obj = datetime.strptime(input_time_str, "%H:%M:%S").time()
    except ValueError:
        raise ValueError("Formato de hora inválido.")
        
    return datetime(date_obj.year, date_obj.month, date_obj.day,
                    time_obj.hour, time_obj.minute, time_obj.second)

def extract_valid_values(series):
    """
    Extrai valores numéricos válidos de uma série.
    """
    valores = []
    for v in series:
        try:
            valores.append(float(v))
        except (ValueError, TypeError):
            continue
    return valores

def classify_air(input_date_str, input_time_str, station, database_path="database.csv"):
    """
    Realiza a classificação da qualidade do ar para a data, horário e estação informados.
    Retorna um dicionário com os resultados para MP10, MP2.5 e a média horária de PTS,
    ou uma mensagem de erro.
    """
    try:
        target_datetime = parse_date_time(input_date_str, input_time_str)
    except ValueError as e:
        return {"error": str(e)}
    
    # Define se a linha é "12:00:00" ou "normal"
    row_type = "12:00:00" if input_time_str == "12:00:00" else "normal"
    
    if station not in columns_mapping:
        return {"error": "Estação inválida!"}
    
    try:
        df = pd.read_csv(database_path, header=None, skiprows=1, low_memory=False)
    except Exception as e:
        return {"error": f"Erro ao ler o arquivo CSV: {e}"}
    
    try:
        df[0] = pd.to_datetime(df[0], format="%Y-%m-%d %H:%M:%S")
    except Exception as e:
        return {"error": f"Erro ao converter a coluna de timestamp: {e}"}
    
    ms_str = target_datetime.strftime("%M:%S")
    start_datetime = target_datetime - timedelta(hours=23)
    
    selected_df = df[
        (df[0] >= start_datetime) &
        (df[0] <= target_datetime) &
        (df[0].dt.strftime("%M:%S") == ms_str)
    ].sort_values(by=0)
    
    if selected_df.empty:
        return {"error": "Nenhum registro encontrado no intervalo especificado."}
    
    result = {}
    
    # Função auxiliar para processamento geral dos dados
    def process_pollutant(col, pollutant, func):
        valores = extract_valid_values(selected_df[col])
        if len(valores) < 16:
            return { "error": f"Dados insuficientes para {pollutant} (apenas {len(valores)} valores válidos encontrados)." }
        media = np.mean(valores)
        if func:
            # Calcular IQAr e classificação
            iqar, I_ini, I_fin, C_ini, C_fin = calculate_IQAr(media, pollutant)
            return {
                "Média Horária": media,
                "Índice Inicial": I_ini,
                "Índice Final": I_fin,
                "Concentração Inicial": C_ini,
                "Concentração Final": C_fin,
                "IQAr": iqar,
                "Classificação": classify_air_quality(iqar)
            }
        return {"Média Horária": media}
    
    # Processamento para MP10, MP2.5 e PTS
    station_cols = columns_mapping[station][row_type]
    
    result["MP10"] = process_pollutant(station_cols["MP10"], "MP10", func=True)
    result["MP2.5"] = process_pollutant(station_cols["MP2.5"], "MP2.5", func=True)
    result["PTS"] = process_pollutant(station_cols["PTS"], "PTS", func=False)
    
    return result

if __name__ == "__main__":
    input_date_str = input("Digite a data (dd-mm-aaaa ou yyyy-mm-dd): ").strip()
    input_time_str = input("Digite o horário (HH:MM:SS): ").strip()
    station = input("Digite a estação (EAMA11, EAMA21, EAMA31 ou EAMA41): ").strip().upper()
    resultado = classify_air(input_date_str, input_time_str, station)
    print(resultado)
