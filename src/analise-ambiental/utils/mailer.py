# utils/mailer.py
from __future__ import annotations
import smtplib, ssl, mimetypes
from email.message import EmailMessage
from config import (
    SMTP_HOST, SMTP_PORT, SMTP_USE_TLS, SMTP_USER, SMTP_PASS,
    ERROR_REPORT_TO, ERROR_REPORT_FROM,
)

def send_error_email(
    subject: str,
    body: str,
    attachments: list[dict] | None = None,
):
    """
    Envia e-mail com corpo texto e anexos em memória.
    attachments: lista de dicts com:
      - filename: nome do arquivo (str, obrigatório)
      - data: bytes do arquivo (bytes, obrigatório)
      - content_type: MIME type (str, opcional; será inferido se ausente)
    """
    if not (SMTP_HOST and SMTP_PORT and ERROR_REPORT_TO):
        raise RuntimeError("SMTP não configurado (veja .env).")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = ERROR_REPORT_FROM or (SMTP_USER or "noreply@localhost")
    msg["To"] = ERROR_REPORT_TO
    msg.set_content(body)

    for att in (attachments or []):
        if not att or "data" not in att or "filename" not in att:
            continue
        filename = att["filename"]
        data = att["data"]
        ctype = att.get("content_type")
        if not ctype:
            guess, _ = mimetypes.guess_type(filename)
            ctype = guess or "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)

    if SMTP_USE_TLS:
        # STARTTLS (porta 587)
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls(context=context)
            if SMTP_USER and SMTP_PASS:
                s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
    else:
        # SSL direto (porta 465)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as s:
            if SMTP_USER and SMTP_PASS:
                s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
