"""
============================================
Arquivo: config.py
--------------------------------------------
Configura caminhos e variáveis de ambiente para a aplicação:
- BASE_DIR, SRC_DIR: determinação de diretórios base do projeto.
- DATABASE_PATH: CSV original de medições de qualidade do ar.
- NEW_DATABASE_PATH: CSV resumido para geração de gradientes.
- METEOROLOGY_PATH: CSV de dados meteorológicos.
- SQLALCHEMY_DATABASE_URI: string de conexão (SQLite por default).
============================================
"""

import os

# pasta atual (analise-ambiental)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# subindo uma pasta até src
SRC_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))

# Caminho relativo para o diretório 'dados-coletados'
DADOS_COLETADOS_DIR = os.path.join(BASE_DIR, 'dados-coletados')

# CSV de medições de qualidade do ar — serve tanto ao app Flask quanto ao "adiciona ao database"
DATABASE_PATH         = os.path.join(SRC_DIR, "tratamento-dos-dados", "database.csv")
NEW_DATABASE_PATH     = os.path.join(SRC_DIR, "tratamento-dos-dados", "new_database.csv")
METEOROLOGY_PATH      = os.path.join(SRC_DIR, "tratamento-dos-dados", "database_met.csv")
INFO_DATABASE_MESES_PATH = os.path.join(SRC_DIR, "tratamento-dos-dados", "info-database-meses.txt")

# Mantém o SQLite para erros
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///error_reports.db')
