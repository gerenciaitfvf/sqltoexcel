"""Envío de correos por SMTP con el enlace de descarga del informe."""
import html
import smtplib
import ssl
from datetime import timezone
from email.message import EmailMessage

from web import settings


def _require_config():
    faltan = [
        nombre for nombre, valor in {
            'SMTP_HOST': settings.SMTP_HOST,
            'SMTP_USER': settings.SMTP_USER,
            'SMTP_PASSWORD': settings.SMTP_PASSWORD,
            'MAIL_FROM': settings.MAIL_FROM,
        }.items() if not valor
    ]
    if faltan:
        raise RuntimeError('Falta configuración SMTP: ' + ', '.join(faltan))


def _connect():
    ctx = ssl.create_default_context()
    if settings.SMTP_PORT == 465:
        return smtplib.SMTP_SSL(
            settings.SMTP_HOST, settings.SMTP_PORT, timeout=30, context=ctx
        )
    server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30)
    server.ehlo()
    if server.has_extn('starttls'):
        server.starttls(context=ctx)
        server.ehlo()
    return server


def _redact(texto):
    if settings.SMTP_PASSWORD:
        return texto.replace(settings.SMTP_PASSWORD, '***')
    return texto


def _cuerpo(nombre, rango, url, expires_at):
    hasta = expires_at.astimezone(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')
    texto = (
        f'El informe "{nombre}" está listo.\n\n'
        f'Rango: {rango}\n'
        f'Descarga: {url}\n\n'
        f'El enlace estará disponible hasta el {hasta}.\n'
        'Si no solicitaste este correo, puedes ignorarlo.\n'
    )
    nombre_html = html.escape(nombre)
    rango_html = html.escape(rango)
    url_html = html.escape(url)
    html_cuerpo = f"""\
<html><body style="font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;color:#1d2330">
  <p>El informe <strong>{nombre_html}</strong> está listo.</p>
  <p>Rango: {rango_html}</p>
  <p><a href="{url_html}" style="display:inline-block;background:#1f6f50;color:#fff;
     padding:10px 18px;border-radius:6px;text-decoration:none">Descargar Excel</a></p>
  <p style="color:#6b7280;font-size:13px">El enlace estará disponible hasta el {hasta}.</p>
</body></html>
"""
    return texto, html_cuerpo


def send_report_email(to, nombre, rango, url, expires_at):
    """Envía un correo a un único destinatario. Reintenta una vez si falla."""
    _require_config()
    texto, html_cuerpo = _cuerpo(nombre, rango, url, expires_at)

    msg = EmailMessage()
    msg['From'] = settings.MAIL_FROM
    msg['To'] = to
    msg['Subject'] = f'Informe {nombre} listo'
    msg.set_content(texto)
    msg.add_alternative(html_cuerpo, subtype='html')

    ultimo_error = None
    for _ in range(2):
        try:
            with _connect() as server:
                if settings.SMTP_USER:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            return
        except Exception as exc:  # noqa: BLE001 - se reintenta y se reporta
            ultimo_error = exc
    raise RuntimeError(f'No se pudo enviar el correo a {to}: {_redact(str(ultimo_error))}')
