import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def _statut_color(statut):
    s = (statut or "").lower()
    if "objectif" in s:
        return "#2d6a4f"  # vert
    if "stop" in s:
        return "#c0392b"  # rouge
    return "#2c3e50"      # neutre


def _perf_color(perf_str):
    try:
        val = float(str(perf_str).replace('%', '').replace('+', '').replace(',', '.'))
        return "#2d6a4f" if val >= 0 else "#c0392b"
    except (ValueError, TypeError):
        return "#2c3e50"


def _build_tracker_html(tracking_table):
    if not tracking_table:
        return ""

    rows_html = []
    for row in tracking_table:
        perf = row.get("Perf %", "")
        statut = row.get("Statut", "")
        rows_html.append(f"""
          <tr>
            <td style="padding:6px 8px;border-bottom:1px solid #eee;font-size:12px;">{row.get("Date", "")}</td>
            <td style="padding:6px 8px;border-bottom:1px solid #eee;font-weight:bold;">{row.get("Ticker", "")}</td>
            <td style="padding:6px 8px;border-bottom:1px solid #eee;">{row.get("Nom", "")}</td>
            <td style="padding:6px 8px;border-bottom:1px solid #eee;text-align:right;">{row.get("Prix Achat (€)", "")}</td>
            <td style="padding:6px 8px;border-bottom:1px solid #eee;text-align:right;">{row.get("Prix Actuel (€)", "")}</td>
            <td style="padding:6px 8px;border-bottom:1px solid #eee;text-align:right;">{row.get("Target (€)", "")}</td>
            <td style="padding:6px 8px;border-bottom:1px solid #eee;text-align:right;color:{_perf_color(perf)};font-weight:bold;">{perf}</td>
            <td style="padding:6px 8px;border-bottom:1px solid #eee;color:{_statut_color(statut)};">{statut}</td>
            <td style="padding:6px 8px;border-bottom:1px solid #eee;text-align:right;color:#888;">{row.get("Jours", "")}</td>
          </tr>""")

    return f"""
    <h2 style="color:#1a1a2e;border-bottom:2px solid #e8f4f8;padding-bottom:8px;margin-top:32px;">
      📋 Suivi des positions ({len(tracking_table)})
    </h2>
    <div style="overflow-x:auto;">
      <table style="width:100%;border-collapse:collapse;font-size:12px;margin-top:12px;">
        <thead>
          <tr style="background:#f5f7fa;color:#1a1a2e;">
            <th style="padding:8px;text-align:left;">Date</th>
            <th style="padding:8px;text-align:left;">Ticker</th>
            <th style="padding:8px;text-align:left;">Nom</th>
            <th style="padding:8px;text-align:right;">Achat €</th>
            <th style="padding:8px;text-align:right;">Actuel €</th>
            <th style="padding:8px;text-align:right;">Target €</th>
            <th style="padding:8px;text-align:right;">Perf</th>
            <th style="padding:8px;text-align:left;">Statut</th>
            <th style="padding:8px;text-align:right;">Jours</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows_html)}
        </tbody>
      </table>
    </div>
    """


def _build_tracker_text(tracking_table):
    if not tracking_table:
        return ""
    lines = ["", "=" * 60, f"📋 SUIVI DES POSITIONS ({len(tracking_table)})", "=" * 60]
    for row in tracking_table:
        lines.append(
            f"  {row.get('Date',''):10s} | {row.get('Ticker',''):10s} | "
            f"achat: {row.get('Prix Achat (€)','')}€ | actuel: {row.get('Prix Actuel (€)','')}€ | "
            f"target: {row.get('Target (€)','')}€ | {row.get('Perf %','')} | {row.get('Statut','')}"
        )
    return '\n'.join(lines)


def send_email(message_text, tracking_table=None):
    gmail_user     = os.environ['GMAIL_USER']
    gmail_password = os.environ['GMAIL_APP_PASSWORD']
    to_email       = os.environ['EMAIL_TO']
    date_str = datetime.now().strftime("%d/%m/%Y")

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"📊 Bourse FR — Top 3 actions du {date_str}"
    msg['From']    = gmail_user
    msg['To']      = to_email

    # Version texte
    text_full = message_text + _build_tracker_text(tracking_table)
    part_text = MIMEText(text_full, 'plain', 'utf-8')

    # Version HTML lisible
    lines = message_text.split('\n')
    html_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            html_lines.append('<br>')
        elif line.startswith('1️⃣') or line.startswith('2️⃣') or line.startswith('3️⃣'):
            html_lines.append(f'<h3 style="color:#1a1a2e;margin:20px 0 8px;">{line}</h3>')
        elif line.startswith('🎯'):
            html_lines.append(f'<p style="font-size:16px;font-weight:bold;color:#2d6a4f;margin:4px 0;">{line}</p>')
        elif line.startswith('⚠️'):
            html_lines.append(f'<p style="color:#c0392b;margin:4px 0;">{line}</p>')
        elif line.startswith('📊'):
            html_lines.append(f'<h2 style="color:#1a1a2e;border-bottom:2px solid #e8f4f8;padding-bottom:8px;">{line}</h2>')
        else:
            html_lines.append(f'<p style="margin:4px 0;color:#2c3e50;">{line}</p>')
    html_body = '\n'.join(html_lines)

    tracker_html = _build_tracker_html(tracking_table)

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, Arial, sans-serif; max-width: 760px;
             margin: 0 auto; padding: 24px; background: #f5f7fa;">
  <div style="background: white; border-radius: 12px; padding: 28px;
              box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
    {html_body}
    {tracker_html}
    <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
    <p style="color:#aaa;font-size:11px;text-align:center;">
      Généré automatiquement par votre Agent Bourse IA — {date_str}<br>
      Ceci n'est pas un conseil en investissement financier.
    </p>
  </div>
</body>
</html>"""

    part_html = MIMEText(html, 'html', 'utf-8')
    msg.attach(part_text)
    msg.attach(part_html)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, to_email, msg.as_string())
    print(f"  ✓ Email envoyé à {to_email}")
