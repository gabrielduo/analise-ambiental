import os
import pandas as pd
import pyexcel as p
from config import DADOS_COLETADOS_DIR as BASE_DIR

def converter_xls_para_xlsx(filepath):
    base, ext = os.path.splitext(filepath)
    if ext.lower() == '.xls':
        new_filepath = base + '.xlsx'
        p.save_book_as(file_name=filepath, dest_file_name=new_filepath)
        return new_filepath
    else:
        return filepath

def padronizar_csv(filepath_input):
    """Padroniza o CSV ajustando as vírgulas e preenchendo valores vazios com 'n'."""
    with open(filepath_input, 'r', encoding='utf-8') as file:
        linhas = file.readlines()

    linhas_corrigidas = []
    for linha in linhas:
        valores = [valor.strip() if valor.strip() != "" else "n" for valor in linha.split(',')]
        linha_corrigida = ','.join(valores)
        linhas_corrigidas.append(linha_corrigida)

    with open(filepath_input, 'w', encoding='utf-8-sig') as file:
        for linha in linhas_corrigidas:
            file.write(linha + '\n')

    print(f"CSV padronizado salvo em: {filepath_input}")

def remover_coluna_b_se_vazia(df):
    """Remove a coluna B se estiver completamente vazia."""
    if df.iloc[:, 1].isnull().all():
        df = df.drop(columns=[1])
        print("Coluna B removida por estar completamente vazia.")
    return df

def validar_e_carregar_qar(filepath):
    df = pd.read_excel(filepath, header=None)

    if df.shape[0] < 9 or df.shape[1] < 15:
        raise ValueError("A planilha não parece ter linhas/colunas suficientes para o padrão esperado.")
    
    estacao_eama11 = df.iloc[1, 2]
    if "EAMA11" not in str(estacao_eama11):
        raise ValueError("A estação EAMA11 não foi encontrada na célula esperada (C2).")
    return df

def validar_cenario_maior(filepath):
    df = pd.read_excel(filepath, header=None)

    if df.shape[0] < 9 or df.shape[1] < 82:
        raise ValueError("A planilha não parece ter dimensões suficientes para o cenário maior.")

    texto_c2 = str(df.iloc[1, 2])
    if "EAMA11" not in texto_c2:
        if "EAMA41" in texto_c2:
            raise ValueError("Planilha invertida detectada: EAMA41 encontrada onde deveria estar EAMA11.")
        else:
            raise ValueError("Nem EAMA11 nem EAMA41 encontrados na posição esperada (C2). Formato desconhecido.")
    return df

def corrigir_inversao_colunas(filepath):
    df = pd.read_excel(filepath, header=None)
    
    eama11_slice = slice(2, 22)   # Colunas C..V
    eama41_slice = slice(62, 82)  # Colunas BK..CD
    eama31_slice = slice(22, 42)  # Colunas W..AP
    eama21_slice = slice(42, 62)  # Colunas AQ..BJ

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

    base, ext = os.path.splitext(filepath)
    novo_arquivo = base + "_corrigido.xlsx"
    df_corrigido.to_excel(novo_arquivo, index=False, header=False)
    return novo_arquivo

def validar_novo_formato(filepath):
    df = pd.read_excel(filepath, header=None)
    
    eama11 = df.iloc[1, 1]  # Célula B2
    eama21 = df.iloc[1, 13] # Célula N2
    eama31 = df.iloc[1, 25] # Célula Z2
    eama41 = df.iloc[1, 37] # Célula AL2

    if "EAMA11" not in str(eama11) or "EAMA21" not in str(eama21):
        raise ValueError("Novo formato inválido: EAMA11 ou EAMA21 não encontrados nas células esperadas.")
    if "EAMA31" not in str(eama31) or "EAMA41" not in str(eama41):
        raise ValueError("Novo formato inválido: EAMA31 ou EAMA41 não encontrados nas células esperadas.")
    
    print("Sucesso: Planilha validada no novo formato.")
    return df

def processar_qar(filepath):
    try:
        caminho_arquivo_convertido = converter_xls_para_xlsx(filepath)
        df = validar_e_carregar_qar(caminho_arquivo_convertido)
        print(f"Sucesso: {filepath} validada no cenário original!")
        df = remover_coluna_b_se_vazia(df)
        base, ext = os.path.splitext(caminho_arquivo_convertido)
        output_csv = base + ".csv"
        df.to_csv(output_csv, index=False, header=False)
        padronizar_csv(output_csv)
    except Exception as e:
        erro_msg = str(e)
        if "A estação EAMA11 não foi encontrada na célula esperada (C2)." in erro_msg:
            try:
                df_maior = validar_cenario_maior(caminho_arquivo_convertido)
                print(f"Sucesso: {filepath} validada no cenário maior sem inversão!")
                df_maior = remover_coluna_b_se_vazia(df_maior)
                base, ext = os.path.splitext(caminho_arquivo_convertido)
                output_csv = base + "_maior.csv"
                df_maior.to_csv(output_csv, index=False, header=False)
                padronizar_csv(output_csv)
            except Exception as e2:
                if "Planilha invertida detectada" in str(e2):
                    caminho_corrigido = corrigir_inversao_colunas(caminho_arquivo_convertido)
                    df_corrigido = validar_cenario_maior(caminho_corrigido)
                    print(f"Sucesso: {filepath} estava invertida, foi corrigida e validada com sucesso!")
                    df_corrigido = remover_coluna_b_se_vazia(df_corrigido)
                    base, ext = os.path.splitext(caminho_corrigido)
                    output_csv = base + ".csv"
                    df_corrigido.to_csv(output_csv, index=False, header=False)
                    padronizar_csv(output_csv)
                else:
                    df_novo = validar_novo_formato(caminho_arquivo_convertido)
                    print(f"Sucesso: {filepath} validada no novo formato!")
                    df_novo = remover_coluna_b_se_vazia(df_novo)
                    base, ext = os.path.splitext(caminho_arquivo_convertido)
                    output_csv = base + "_novo.csv"
                    df_novo.to_csv(output_csv, index=False, header=False)
                    padronizar_csv(output_csv)
        else:
            print(f"Erro de Validação em {filepath}: {e}")

def main():
    # Itera sobre os diretórios dentro de BASE_DIR que representam os anos
    for ano in os.listdir(BASE_DIR):
        caminho_ano = os.path.join(BASE_DIR, ano)
        if os.path.isdir(caminho_ano) and ano.isdigit():
            # Itera sobre os subdiretórios do ano, que representam os meses
            for mes in os.listdir(caminho_ano):
                caminho_mes = os.path.join(caminho_ano, mes)
                if os.path.isdir(caminho_mes):
                    arquivos = [
                        arq for arq in os.listdir(caminho_mes)
                        if arq.lower().startswith("qar.") and (arq.lower().endswith(".xls") or arq.lower().endswith(".xlsx"))
                    ]
                    for arq in arquivos:
                        caminho_arquivo = os.path.join(caminho_mes, arq)
                        print(f"Processando {caminho_arquivo}...")
                        try:
                            processar_qar(caminho_arquivo)
                        except Exception as e:
                            print(f"Erro ao processar {caminho_arquivo}: {e}")

if __name__ == "__main__":
    main()
