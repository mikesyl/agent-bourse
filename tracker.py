import os
import json
import re
from datetime import datetime
import yfinance as yf

# Google Sheets via gspread
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_NAME = "Agent Bourse — Suivi Recommandations"
HEADERS = ["Date", "Ticker", "Nom", "Prix Achat (€)", "Target (€)", "Potentiel %", "Prix Actuel (€)", "Perf % actuelle", "Stop-Loss (€)", "Statut", "Jours"]


# ─────────────────────────────────────────────
#  Connexion Google Sheets
# ─────────────────────────────────────────────

def get_sheet():
    """Retourne la worksheet principale, crée la feuille si nécessaire."""
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if not creds_json:
        raise EnvironmentError("Variable GOOGLE_CREDENTIALS_JSON manquante.")

    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)

    try:
        spreadsheet = client.open(SHEET_NAME)
    except gspread.SpreadsheetNotFound:
        spreadsheet = client.create(SHEET_NAME)
        # Partager en lecture avec l'email owner si fourni
        owner = os.environ.get("GMAIL_USER")
        if owner:
            spreadsheet.share(owner, perm_type="user", role="writer")

    worksheets = [ws.title for ws in spreadsheet.worksheets()]

    if "Recommandations" not in worksheets:
        ws = spreadsheet.add_worksheet(title="Recommandations", rows=500, cols=len(HEADERS))
        ws.append_row(HEADERS)
        _format_header(ws)
    else:
        ws = spreadsheet.worksheet("Recommandations")

    return ws


def _format_header(ws):
    """Met en gras la ligne d'en-tête."""
    try:
        ws.format("A1:K1", {
            "textFormat": {"bold": True},
            "backgroundColor": {"red": 0.1, "green": 0.2, "blue": 0.4},
        })
    except Exception:
        pass  # Formatage optionnel


# ─────────────────────────────────────────────
#  Ajout d'une recommandation
# ─────────────────────────────────────────────

def add_recommendation(ticker: str, nom: str, prix_achat: float,
                        target: float, stop_loss: float):
    """
    Ajoute une nouvelle ligne de recommandation dans la Google Sheet.
    Vérifie d'abord qu'elle n'existe pas déjà pour aujourd'hui.
    """
    ws = get_sheet()
    today = datetime.now().strftime("%d/%m/%Y")

    # Eviter les doublons (même ticker, même date)
    existing = ws.get_all_values()
    for row in existing[1:]:  # Skip header
        if len(row) >= 2 and row[0] == today and row[1] == ticker:
            print(f"  ⏩ {ticker} déjà enregistré aujourd'hui, skip.")
            return

    potentiel = round((target / prix_achat - 1) * 100, 2) if prix_achat else 0

    new_row = [
        today,           # Date
        ticker,          # Ticker
        nom,             # Nom
        prix_achat,      # Prix Achat
        target,          # Target
        f"{potentiel}%", # Potentiel %
        prix_achat,      # Prix Actuel (= prix achat au moment de l'ajout)
        "0.00%",         # Perf % actuelle
        stop_loss,       # Stop-Loss
        "🟡 En cours",   # Statut
        "0",             # Jours
    ]
    ws.append_row(new_row)
    print(f"  ✅ {ticker} ajouté au tracker ({today}, achat={prix_achat}€, target={target}€)")


# ─────────────────────────────────────────────
#  Mise à jour des prix actuels
# ─────────────────────────────────────────────

def update_prices():
    """
    Parcourt toutes les lignes 'En cours' et met à jour
    le prix actuel, la performance et le statut.
    """
    ws = get_sheet()
    rows = ws.get_all_values()
    if len(rows) <= 1:
        return  # Que le header

    headers = rows[0]
    col = {h: i for i, h in enumerate(headers)}

    updates = []
    today = datetime.now().strftime("%d/%m/%Y")

    for i, row in enumerate(rows[1:], start=2):  # start=2 car ligne 1 = header
        if len(row) < len(HEADERS):
            continue
        statut = row[col["Statut"]]
        if "En cours" not in statut:
            continue  # On ne touche pas aux lignes clôturées

        ticker = row[col["Ticker"]]
        try:
            prix_achat = float(str(row[col["Prix Achat (€)"]]).replace(",", "."))
            target = float(str(row[col["Target (€)"]]).replace(",", "."))
            stop_loss = float(str(row[col["Stop-Loss (€)"]]).replace(",", "."))
            date_achat = datetime.strptime(row[col["Date"]], "%d/%m/%Y")
        except (ValueError, IndexError):
            continue

        # Récupérer le prix actuel via yfinance
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            if hist.empty:
                continue
            prix_actuel = round(float(hist['Close'].iloc[-1]), 2)
        except Exception as e:
            print(f"  ✗ Impossible de récupérer {ticker}: {e}")
            continue

        perf = round((prix_actuel / prix_achat - 1) * 100, 2)
        jours = (datetime.now() - date_achat).days

        # Déterminer le statut
        if prix_actuel >= target:
            nouveau_statut = "🎯 Objectif atteint"
        elif prix_actuel <= stop_loss:
            nouveau_statut = "❌ Stop-loss touché"
        else:
            nouveau_statut = "🟡 En cours"

        perf_str = f"{'+' if perf >= 0 else ''}{perf}%"

        # Préparer les cellules à mettre à jour (row i, colonnes 0-indexed)
        row_updates = {
            col["Prix Actuel (€)"] + 1: prix_actuel,   # gspread = 1-indexed
            col["Perf % actuelle"] + 1: perf_str,
            col["Statut"] + 1: nouveau_statut,
            col["Jours"] + 1: str(jours),
        }
        for col_num, value in row_updates.items():
            updates.append({
                "range": gspread.utils.rowcol_to_a1(i, col_num),
                "values": [[value]],
            })

        print(f"  🔄 {ticker}: {prix_actuel}€ ({perf_str}) — {nouveau_statut}")

    if updates:
        ws.spreadsheet.values_batch_update({
            "valueInputOption": "USER_ENTERED",
            "data": updates,
        })
        print(f"  ✅ {len(updates) // 4} position(s) mise(s) à jour")


# ─────────────────────────────────────────────
#  Lecture du tableau pour l'email
# ─────────────────────────────────────────────

def get_tracking_table() -> list[dict]:
    """
    Retourne toutes les recommandations sous forme de liste de dicts,
    triées par date décroissante, pour inclusion dans l'email.
    """
    try:
        ws = get_sheet()
        rows = ws.get_all_values()
        if len(rows) <= 1:
            return []

        headers = rows[0]
        result = []
        for row in rows[1:]:
            if len(row) >= len(HEADERS):
                result.append(dict(zip(headers, row)))

        # Trier par date décroissante
        def parse_date(d):
            try:
                return datetime.strptime(d.get("Date", "01/01/2000"), "%d/%m/%Y")
            except ValueError:
                return datetime.min

        result.sort(key=parse_date, reverse=True)
        return result

    except Exception as e:
        print(f"  ⚠️ Impossible de lire le tracker: {e}")
        return []


# ─────────────────────────────────────────────
#  Parser les recommandations Claude
# ─────────────────────────────────────────────

def parse_claude_recommendations(analysis_text: str) -> list[dict]:
    """
    Extrait les recommandations structurées du texte produit par Claude.
    Retourne une liste de dicts avec ticker, nom, prix, target, stop_loss.
    """
    recommendations = []

    # Pattern : "NOM (TICKER.PA) — Prix actuel : XXX€"
    stock_pattern = re.compile(
        r'[1-3]️⃣\s+(.+?)\s*\(([A-Z]+\.PA)\)\s*[—-]\s*Prix actuel\s*:\s*([\d,\.]+)\s*€',
        re.IGNORECASE
    )
    # Pattern : "Objectif 3 mois : XXX€"
    target_pattern = re.compile(
        r'Objectif\s+\d\s+mois\s*:\s*([\d,\.]+)\s*€',
        re.IGNORECASE
    )
    # Pattern : "Stop-loss suggéré : XXX€"
    stop_pattern = re.compile(
        r'Stop-loss\s+sugg[eé]r[eé]\s*:\s*([\d,\.]+)\s*€',
        re.IGNORECASE
    )

    # Diviser par bloc action (1️⃣, 2️⃣, 3️⃣)
    blocks = re.split(r'(?=[1-3]️⃣)', analysis_text)

    for block in blocks:
        stock_match = stock_pattern.search(block)
        if not stock_match:
            continue

        nom = stock_match.group(1).strip()
        ticker = stock_match.group(2).strip()
        prix_str = stock_match.group(3).replace(",", ".")

        target_match = target_pattern.search(block)
        stop_match = stop_pattern.search(block)

        try:
            prix = float(prix_str)
            target = float(target_match.group(1).replace(",", ".")) if target_match else round(prix * 1.10, 2)
            stop = float(stop_match.group(1).replace(",", ".")) if stop_match else round(prix * 0.93, 2)

            recommendations.append({
                "ticker": ticker,
                "nom": nom,
                "prix_achat": prix,
                "target": target,
                "stop_loss": stop,
            })
        except ValueError:
            continue

    return recommendations
