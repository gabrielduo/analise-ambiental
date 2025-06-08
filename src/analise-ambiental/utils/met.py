"""
============================================
Arquivo: met.py
--------------------------------------------
Fornece função get_meteorologia para leitura de dados meteorológicos:
- Converte strings de data e hora em datetime (minuto fixo :30:00).
- Lê CSV de meteorologia (tolerância a encoding e parsing de datas).
- Filtra registro exato de data/hora e formata saída.
- Retorna dicionário com vento, precipitação, temperatura, umidade e pressão.
============================================
"""

import pandas as pd
from datetime import datetime
from config import METEOROLOGY_PATH

def get_meteorologia(input_date_str,
                     input_hour_str,
                     database_path: str = METEOROLOGY_PATH):
    """
    Retorna um dicionário com as informações meteorológicas para a data e hora especificadas.
    O horário é considerado com ":30:00" (exemplo: se input_hour_str = "00", assume 00:30:00).
    """
    try:
        # Converte a data e hora para um objeto datetime
        target_datetime = datetime.strptime(f"{input_date_str} {input_hour_str}:30:00", "%Y-%m-%d %H:%M:%S")
    except Exception:
        return {"error": "Formato de data ou hora inválido."}
    
    try:
        # Lê o CSV de meteorologia
        df = pd.read_csv(
            database_path,
            header=None,
            encoding="utf-8-sig",
            sep=",",
            decimal=",",
            parse_dates=[0]  # Converte a primeira coluna em datetime
        )
    except Exception as e:
        return {"error": f"Erro ao ler o arquivo CSV: {e}"}
    
    # Filtra o registro com a data/hora exatas
    registro = df[df[0] == target_datetime]
    if registro.empty:
        return {"error": "Não foram encontrados registros meteorológicos para esse período."}
    
    registro = registro.iloc[0]

    # Formata a data/hora (por exemplo, dd/mm/yyyy HH:MM)
    dt_value = registro[0]
    # Se vier como pd.Timestamp, convertemos para datetime nativo
    if isinstance(dt_value, pd.Timestamp):
        dt_value = dt_value.to_pydatetime()
    data_formatada = dt_value.strftime("%d/%m/%Y %H:%M")

    # Retorna os valores meteorológicos (sem unidades ainda)
    return {
        "Data e Hora": data_formatada,
        "Velocidade Escalar do Vento": registro[1],
        "Direção Escalar do Vento": registro[2],
        "Precipitação Pluviométrica": registro[3],
        "Temperatura": registro[4],
        "Umidade Relativa": registro[5],
        "Pressão Atmosférica": registro[6]
    }

if __name__ == "__main__":
    # Teste rápido no terminal
    input_date = input("Digite a data (YYYY-MM-DD): ").strip()
    input_hour = input("Digite a hora (HH): ").strip()
    resultado = get_meteorologia(input_date, input_hour)
    print(resultado)
