import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def send_email(message_text):
    gmail_user     = os.environ['GMAIL_USER']
    gmail_password = os.environ['GMAIL_APP_PASSWORD']
    to_email       = os.environ['EMAIL_TO']

    date_str = datetime.now().strftime("%d/%m/%Y")

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"📊 Bourse FR — Top 3 actions du {date_str}"
    msg['From']    = gmail_user
    msg['To']      = to_email

    # Version texte
    part_text = MIMEText(message_text, 'plain', 'utf-8')

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

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, Arial, sans-serif; max-width: 620px;
             margin: 0 auto; padding: 24px; background: #f5f7fa;">
  <div style="background: white; border-radius: 12px; padding: 28px;
              box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
    {html_body}
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
