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
- Vars de auth de upload lidas do .env (SECRET_KEY, UPLOAD_PASSWORD_HASH, TTL)
============================================
"""
import os
from dotenv import load_dotenv

# ------------------------------------------------------------
# Carrega .env localizado na MESMA PASTA deste arquivo
# (analise-ambiental/src/analise-ambiental/.env)
# ------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # pasta atual (analise-ambiental)
load_dotenv(os.path.join(BASE_DIR, ".env"))

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

# ------------------------------------------------------------
# Auth de upload (lidas do ambiente / .env) — NADA de segredo no código
# ------------------------------------------------------------
# Chave usada para assinar tokens de upload (obrigatório em prod)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")

# Hash bcrypt da senha de upload (obrigatório em prod)
UPLOAD_PASSWORD_HASH = os.getenv("UPLOAD_PASSWORD_HASH", "")

# Tempo de vida do token (segundos) — ex.: 600 = 10 min
UPLOAD_TOKEN_TTL_SECONDS = int(os.getenv("UPLOAD_TOKEN_TTL_SECONDS", "600"))

# ---------------- SMTP / Error Report ----------------
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").strip().lower() in ("1", "true", "yes", "on")
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
ERROR_REPORT_TO = os.getenv("ERROR_REPORT_TO", "")
ERROR_REPORT_FROM = os.getenv("ERROR_REPORT_FROM", SMTP_USER or "noreply@localhost")
