# utils/auth_upload.py
# -----------------------------------------------------------------------------
# Autenticação de upload com senha -> token de curta duração (Bearer).
# - POST /api/upload-auth  : recebe {"password": "..."} e retorna {ok, token, ttl}
# - require_upload_token   : decorator que valida Authorization: Bearer <token>
# -----------------------------------------------------------------------------

from __future__ import annotations
from functools import wraps

from flask import Blueprint, request, jsonify
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import bcrypt

# >>> Leia SEMPRE do config.py (que já carrega o .env)
from config import SECRET_KEY, UPLOAD_PASSWORD_HASH, UPLOAD_TOKEN_TTL_SECONDS

auth_bp = Blueprint("auth_upload", __name__)
serializer = URLSafeTimedSerializer(SECRET_KEY)

# ---------- Helpers ----------
def verify_password(plain: str) -> bool:
    """Valida a senha informada contra o hash configurado (bcrypt)."""
    if not UPLOAD_PASSWORD_HASH:
        # hash não configurado -> falha explícita
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), UPLOAD_PASSWORD_HASH.encode("utf-8"))
    except Exception:
        return False

def make_upload_token() -> str:
    """Gera token assinado com escopo 'upload'."""
    return serializer.dumps({"scope": "upload"})

def verify_upload_token(token: str) -> bool:
    try:
        data = serializer.loads(token, max_age=UPLOAD_TOKEN_TTL_SECONDS)
        return data.get("scope") == "upload"
    except (BadSignature, SignatureExpired):
        return False

def require_upload_token(fn):
    """Decorator para proteger endpoints de upload."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        parts = auth.split()
        if len(parts) == 2 and parts[0].lower() == "bearer" and verify_upload_token(parts[1]):
            return fn(*args, **kwargs)
        return jsonify({"ok": False, "message": "Unauthorized"}), 401
    return wrapper

# ---------- Rotas ----------
@auth_bp.post("/api/upload-auth")
def upload_auth():
    """Recebe {"password":"..."} e retorna token curto."""
    if not UPLOAD_PASSWORD_HASH:
        # Ajuda a diagnosticar ambiente mal configurado, sem vazar segredo
        return jsonify({"ok": False, "message": "Servidor sem UPLOAD_PASSWORD_HASH configurado."}), 500

    data = request.get_json(silent=True) or {}
    password = data.get("password", "")

    if verify_password(password):
        token = make_upload_token()
        return jsonify({"ok": True, "token": token, "ttl": UPLOAD_TOKEN_TTL_SECONDS})
    return jsonify({"ok": False, "message": "Senha inválida"}), 401
