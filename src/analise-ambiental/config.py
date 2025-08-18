"""
============================================
Arquivo: config.py
--------------------------------------------
Resolve caminhos para CSVs e pastas de dados.
Inclui:
- DATABASE_PATH  : CSV resumido (com "Mais detalhes")
- NEW_DATABASE_PATH, METEOROLOGY_PATH, etc.
- DATA_ROOT      : raiz dos dados-coletados/<ano>/<mes>
- UPLOAD_TMP     : pasta temporária para uploads
============================================
"""
import os

# pasta atual (analise-ambiental)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# sobe para a raiz do src
SRC_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))

def _first_existing(*paths):
    for p in paths:
        if p and os.path.exists(p):
            return os.path.abspath(p)
    return None

# --- CSV resumido usado na classificação ---
ENV_OVERRIDE      = os.environ.get("DATABASE_PATH")
RESUMIDO_TRAT     = os.path.join(SRC_DIR, "tratamento-dos-dados", "database_resumido.csv")
RESUMIDO_DADOS    = os.path.join(SRC_DIR, "dados-coletados", "database_resumido.csv")
DATABASE_PATH     = _first_existing(ENV_OVERRIDE, RESUMIDO_TRAT, RESUMIDO_DADOS)

if DATABASE_PATH is None:
    raise FileNotFoundError(
        "Não encontrei 'database_resumido.csv'. Gere-o em:\n"
        f" - {RESUMIDO_TRAT}\n"
        f"ou copie para:\n"
        f" - {RESUMIDO_DADOS}\n"
        "Ou defina a variável de ambiente DATABASE_PATH apontando para o arquivo."
    )

# --- Outros CSVs usados em telas distintas ---
NEW_DATABASE_PATH        = os.path.join(SRC_DIR, "tratamento-dos-dados", "new_database.csv")
METEOROLOGY_PATH         = os.path.join(SRC_DIR, "tratamento-dos-dados", "database_met.csv")
INFO_DATABASE_MESES_PATH = os.path.join(SRC_DIR, "tratamento-dos-dados", "info-database-meses.txt")

# --- Pastas para uploader/modelos ---
DATA_ROOT  = os.path.join(SRC_DIR, "dados-coletados")   # onde criamos <ano>/<mes>
UPLOAD_TMP = os.path.join(SRC_DIR, "uploads_tmp")       # staging de upload

os.makedirs(DATA_ROOT, exist_ok=True)
os.makedirs(UPLOAD_TMP, exist_ok=True)

# Banco local para relatórios de erro
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///error_reports.db")
