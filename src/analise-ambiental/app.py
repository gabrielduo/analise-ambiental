# app.py
"""
============================================
Arquivo: app.py
--------------------------------------------
- Rotas principais da UI
- API JSON de classificação e meteorologia
- /api/upload-model: recebe planilha e chama utils/model_uploader.handle_uploaded_model
- DatePicker: min fixo 2022-01-01; max = max(última data do CSV, 2026-12-31)
- Upload QAR: além do merge padrão, injeta/atualiza colunas *_PTS_media (auto bootstrap/incremental)
============================================
"""
import os
from datetime import datetime, date
import pandas as pd
import sqlite3, time
from flask import Flask, render_template, request, jsonify, send_file, make_response
from flask_compress import Compress
from werkzeug.utils import secure_filename
from utils.mailer import send_error_email

from config import (
    DATABASE_PATH,             # caminho do database_resumido.csv (qualidade do ar)
    NEW_DATABASE_PATH,         # caminho do new_database.csv (para gradientes)
    METEOROLOGY_PATH,          # caminho do database_met.csv
    SQLALCHEMY_DATABASE_URI,   
)

from utils.classifica import classify_air
from utils.met import get_meteorologia
from utils.visualization_plotly import generate_plotly_html
from utils.visualization_gradient import (
    generate_gradient_image,
    generate_max_gradient_image,
    generate_min_gradient_image,
)

# --- uploader e utilitários de atualização ---
try:
    from utils.model_uploader import handle_uploaded_model
except Exception:
    handle_uploaded_model = None

try:
    from utils.adiciona_aos_databases import add_to_databases
except Exception:
    add_to_databases = None

# utilitário NOVO para PTS (auto: bootstrap ou incremental)
try:
    from utils.adiciona_pts_resumido import add_pts_update
except Exception:
    add_pts_update = None

from utils.adiciona_ao_database_met import add_met_month_to_database  
from utils.auth_upload import auth_bp, require_upload_token


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
MIN_AVAILABLE_DATE = "2022-01-01"
HARD_MAX_DATE = "2026-12-31"  # teto mínimo desejado no datepicker

def _compute_max_date_from_resumo(csv_path: str) -> str:
    """
    Lê o database_resumido.csv e retorna a maior data (YYYY-MM-DD) presente em 'timestamp'.
    Em caso de falha, retorna a data de hoje.
    """
    try:
        if not os.path.isfile(csv_path):
            return datetime.today().strftime("%Y-%m-%d")
        df = pd.read_csv(csv_path, encoding="utf-8-sig", low_memory=False)
        # normaliza coluna de tempo
        if "timestamp" not in df.columns:
            for cand in ("datahora", "datetime", "date_time"):
                if cand in df.columns:
                    df = df.rename(columns={cand: "timestamp"})
                    break
        if "timestamp" not in df.columns:
            return datetime.today().strftime("%Y-%m-%d")
        ts = pd.to_datetime(df["timestamp"], errors="coerce").dropna()
        if ts.empty:
            return datetime.today().strftime("%Y-%m-%d")
        return ts.max().date().strftime("%Y-%m-%d")
    except Exception:
        return datetime.today().strftime("%Y-%m-%d")

def _picker_max_date() -> str:
    """
    Garante que o datepicker tenha ao menos 2026-12-31 como máximo.
    Se a base tiver algo mais novo, usa o mais novo.
    """
    data_max = _compute_max_date_from_resumo(DATABASE_PATH)
    return max(data_max, HARD_MAX_DATE)

def _gradient_bundle():
    return (
        generate_gradient_image(csv_path=NEW_DATABASE_PATH),
        generate_max_gradient_image(csv_path=NEW_DATABASE_PATH),
        generate_min_gradient_image(csv_path=NEW_DATABASE_PATH),
    )

def _infer_year_month_from_dest_dir(dest_dir: str):
    """
    Fallback: se o uploader devolveu 'duplicate' sem tipo/ano/mês,
    tenta inferir a partir de .../<ano>/<mês>/ .
    Aceita 'marco' e 'março'.
    """
    if not dest_dir:
        return None, None
    try:
        month_name = os.path.basename(dest_dir)
        year_name = os.path.basename(os.path.dirname(dest_dir))
        year = int(year_name)
        # mapa PT -> número
        pt_to_num = {
            "janeiro": 1, "fevereiro": 2, "marco": 3, "março": 3,
            "abril": 4, "maio": 5, "junho": 6, "julho": 7,
            "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
        }
        month = pt_to_num.get(month_name.lower())
        return year, month
    except Exception:
        return None, None


# ----------------------------------------------------------------------
# App
# ----------------------------------------------------------------------
app = Flask(__name__)
Compress(app)


# arquivo sqlite para contar envios por IP/dia
RATE_DB = os.path.join(app.root_path, "rate_limit.db")

def _rate_init():
    """Cria a tabela de controle de envios por IP/dia (se não existir)."""
    conn = sqlite3.connect(RATE_DB)
    try:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS errors_per_ip (
                ip TEXT NOT NULL,
                ymd TEXT NOT NULL,
                count INTEGER NOT NULL DEFAULT 0,
                last_ts REAL NOT NULL,
                PRIMARY KEY (ip, ymd)
            )
        """)
        # índice opcional por data (não é obrigatório)
        c.execute("CREATE INDEX IF NOT EXISTS idx_errors_per_ip_ymd ON errors_per_ip(ymd)")
        conn.commit()
    finally:
        conn.close()

def _rate_allow(ip: str, limit: int = 2) -> bool:
    """
    Incrementa e verifica o contador de hoje para o IP.
    Retorna True se ainda estiver dentro do limite; False se estourou.
    """
    ymd = date.today().isoformat()
    now = time.time()
    conn = sqlite3.connect(RATE_DB)
    try:
        c = conn.cursor()
        c.execute("SELECT count FROM errors_per_ip WHERE ip=? AND ymd=?", (ip, ymd))
        row = c.fetchone()
        if row is None:
            c.execute(
                "INSERT INTO errors_per_ip (ip, ymd, count, last_ts) VALUES (?, ?, 1, ?)",
                (ip, ymd, now)
            )
            conn.commit()
            return True
        cnt = row[0]
        if cnt >= limit:
            return False
        c.execute(
            "UPDATE errors_per_ip SET count = count + 1, last_ts=? WHERE ip=? AND ymd=?",
            (now, ip, ymd)
        )
        conn.commit()
        return True
    finally:
        conn.close()

# inicializa a tabelinha na subida do app
_rate_init()
# ---------------------------------------------------------------------------

app.register_blueprint(auth_bp)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

# evita cache só na rota de upload
@app.after_request
def _no_store_for_upload(resp):
    try:
        if request.path == "/api/upload-model":
            resp.headers["Cache-Control"] = "no-store"
    except Exception:
        pass
    return resp


# ----------------------------------------------------------------------
# Rotas principais
# ----------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    # limites do DatePicker
    min_available_date = MIN_AVAILABLE_DATE
    max_available_date = _picker_max_date()

    # defaults (mantidos)
    default_date = "2022-07-22"
    default_hour = "09"
    default_station = "EAMA21"
    default_time = f"{default_hour}:30:00"

    result = classify_air(default_date, default_time, default_station, database_path=DATABASE_PATH)

    graph_html = None
    metric = None

    gradient_url, gradient_max_url, gradient_min_url = _gradient_bundle()

    if request.method == "POST" and "metric" in request.form:
        m = request.form.get("metric", "").lower()
        if m in ("mp10", "mp2.5"):
            metric = m
            graph_html = generate_plotly_html(metric)

    return render_template(
        "index.html",
        result=result,
        selected_date=default_date,
        selected_hour=default_hour,
        selected_station=default_station,
        graph_html=graph_html,
        metric=metric,
        gradient_url=gradient_url,
        gradient_max_url=gradient_max_url,
        gradient_min_url=gradient_min_url,
        min_available_date=min_available_date,
        max_available_date=max_available_date,
    )


@app.route("/classificar", methods=["POST"])
def classificar():
    # limites do DatePicker
    min_available_date = MIN_AVAILABLE_DATE
    max_available_date = _picker_max_date()

    input_date = request.form.get("input_date")
    input_hour = request.form.get("input_hour")
    station = request.form.get("station")
    input_time = f"{input_hour}:30:00" if input_hour else "23:30:00"

    grad_med, grad_max, grad_min = _gradient_bundle()

    if not input_date or not input_hour or not station:
        return render_template(
            "index.html",
            result={"error": "Preencha data, hora e estação para classificar."},
            selected_date=input_date,
            selected_hour=input_hour,
            selected_station=station,
            graph_html=None,
            metric=None,
            gradient_url=grad_med,
            gradient_max_url=grad_max,
            gradient_min_url=grad_min,
            min_available_date=min_available_date,
            max_available_date=max_available_date,
        )

    result = classify_air(input_date, input_time, station, database_path=DATABASE_PATH)
    return render_template(
        "index.html",
        result=result,
        selected_date=input_date,
        selected_hour=input_hour,
        selected_station=station,
        graph_html=None,
        metric=None,
        gradient_url=grad_med,
        gradient_max_url=grad_max,
        gradient_min_url=grad_min,
        min_available_date=min_available_date,
        max_available_date=max_available_date,
    )


@app.route("/classificar/json", methods=["POST"])
def classificar_json():
    input_date = request.form.get("input_date")
    input_hour = request.form.get("input_hour")
    station = request.form.get("station")

    if not input_date or not input_hour or not station:
        return jsonify({"error": "Data, hora e estação são obrigatórios."}), 400

    result = classify_air(input_date, f"{input_hour}:30:00", station, database_path=DATABASE_PATH)
    return jsonify(result)


@app.route("/meteorologia", methods=["POST"])
def meteorologia():
    input_date = request.form.get("input_date")
    input_hour = request.form.get("input_hour")

    if not input_date or not input_hour:
        return jsonify({"error": "Data e hora são obrigatórias."}), 400

    result = get_meteorologia(input_date, input_hour, database_path=METEOROLOGY_PATH)
    return jsonify(result)


@app.route("/sobre-iqar")
def sobre_iqar():
    grad_med, grad_max, grad_min = _gradient_bundle()
    min_available_date = MIN_AVAILABLE_DATE
    max_available_date = _picker_max_date()

    return render_template(
        "index.html",
        explicacao=True,
        graph_html=None,
        metric=None,
        gradient_url=grad_med,
        gradient_max_url=grad_max,
        gradient_min_url=grad_min,
        min_available_date=min_available_date,
        max_available_date=max_available_date,
    )


# ----------------------------------------------------------------------
# API do uploader
# ----------------------------------------------------------------------
@app.route("/api/upload-model", methods=["POST"])
@require_upload_token
def api_upload_model():
    # Garantir que o uploader existe
    if handle_uploaded_model is None:
        return jsonify(
            {"ok": False, "message": "Uploader não está disponível no servidor (import falhou)."}
        ), 500

    """
    Recebe 'file' (qar.xls/.xlsx | met.xls/.xlsx), valida e salva CSV mensal no destino.
    Após sucesso, atualiza automaticamente os databases consolidados:
      - MET -> mescla em database_met.csv (ordem cronológica) usando add_met_month_to_database
      - QAR -> rotina padrão (add_to_databases)
             -> e, adicionalmente, injeta/atualiza colunas *_PTS_media (add_pts_update)
    """
    file = request.files.get("file")
    result = handle_uploaded_model(file)

    # Se falhou por motivo diferente de "duplicate", devolve como antes
    if not result.get("ok") and result.get("code") != "duplicate":
        return jsonify(result), 400

    payload = dict(result)

    # Preparar parâmetros do mês (tente do retorno; senão, infira do dest_dir)
    tipo = (result.get("tipo") or "").lower().strip()   # "met" ou "qar"
    year = result.get("year")
    month_pt = (result.get("month") or "").lower()

    # mapa PT -> número (aceita 'março' e 'marco')
    pt_to_num = {
        "janeiro": 1, "fevereiro": 2, "marco": 3, "março": 3, "abril": 4,
        "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
        "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
    }
    month_num = pt_to_num.get(month_pt)

    if not (tipo and year and month_num):
        # fallback: tentar inferir do dest_dir (em caso de duplicate antigo sem enrich)
        dest_dir = result.get("dest_dir")
        y_fallback, m_fallback = _infer_year_month_from_dest_dir(dest_dir or "")
        if not year and y_fallback:
            year = y_fallback
        if not month_num and m_fallback:
            month_num = m_fallback

    # Parâmetros obrigatórios para qualquer merge
    if not (tipo and year and month_num):
        payload["database_update"] = {
            "ok": False,
            "message": "Faltam informações de tipo/ano/mês para atualizar databases."
        }
        payload["pts_update"] = {
            "ok": False,
            "message": "Sem tipo/ano/mês não dá para atualizar PTS."
        }
        return jsonify(payload), 200

    # --- MERGE ---
    try:
        if tipo == "met":
            # usa o mesclador NOVO específico do MET
            merge_info = add_met_month_to_database(int(year), int(month_num))
        else:
            # QAR continua pela rotina existente (se disponível)
            if add_to_databases is None:
                merge_info = {"ok": False, "message": "add_to_databases indisponível para QAR."}
            else:
                merge_info = add_to_databases(tipo="qar", year=int(year), month=int(month_num))
    except Exception as e:
        merge_info = {"ok": False, "message": f"Falha ao atualizar databases: {e}"}

    payload["database_update"] = merge_info

    # --- PTS: só tentar para QAR, como já era ---
    if tipo == "qar" and add_pts_update is not None:
        try:
            pts_info = add_pts_update(int(year), int(month_num))
        except Exception as e:
            pts_info = {"ok": False, "message": f"Falha ao atualizar PTS no resumido: {e}"}
    else:
        pts_info = {
            "ok": False,
            "message": "Atualização de PTS indisponível (tipo != 'qar' ou import falhou).",
        }
    payload["pts_update"] = pts_info

    return jsonify(payload), 200

@app.route("/report_error", methods=["POST"])
def report_error():
    error_text = request.form.get("error_text")
    error_file = request.files.get("error_file")

    if not error_text:
        return jsonify({"error": "O texto do erro é obrigatório."}), 400

    # Rate limit: no máx. 2 envios por IP/dia
    client_ip = (request.headers.get("X-Forwarded-For") or request.remote_addr or "").split(",")[0].strip()
    if not _rate_allow(client_ip, limit=2):
        return jsonify({"error": "Limite diário atingido para este IP (2 envios). Tente amanhã."}), 429

    # Monta assunto/corpo
    subject = "[IQAR] Report de erro"
    body = f"Novo report de erro recebido.\n\nTexto do erro:\n{error_text}\n"

    # Anexo (somente em memória; nada é salvo em disco)
    attachments = []
    if error_file and error_file.filename:
        filename = secure_filename(error_file.filename)
        file_bytes = error_file.read()  # <- lê em memória
        if file_bytes:
            # (opcional) proteção de tamanho, ex.: 10MB
            if len(file_bytes) > 10 * 1024 * 1024:
                return jsonify({"error": "Anexo maior que 10MB."}), 400
            attachments.append({
                "filename": filename,
                "data": file_bytes,
                "content_type": error_file.mimetype or "application/octet-stream",
            })

    # Envia
    try:
        send_error_email(subject, body, attachments)
        return jsonify({
            "message": "Erro reportado e enviado por e-mail com sucesso!",
            "email": {"ok": True}
        }), 200
    except Exception as e:
        return jsonify({
            "message": "Falha ao enviar o e-mail de erro.",
            "email": {"ok": False, "message": str(e)}
        }), 500

@app.get("/database_resumido.csv")
def serve_database_resumido():
    """
    Expõe o database_resumido.csv para o frontend (somente leitura).
    Lê exatamente o caminho configurado em config.DATABASE_PATH.
    """
    path = DATABASE_PATH  
    if not os.path.isfile(path):
        return jsonify({"ok": False, "message": f"Arquivo não encontrado: {path}"}), 404
    resp = make_response(send_file(path, mimetype="text/csv"))
    # evita cache para o guard ver atualizações imediatamente
    resp.headers["Cache-Control"] = "no-store"
    return resp


# ----------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
