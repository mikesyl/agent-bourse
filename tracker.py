import os
import csv
import re
from datetime import datetime
import yfinance as yf

CSV_FILE = "historique.csv"
HEADERS = ["Date", "Ticker", "Nom", "Prix Achat (€)", "Target (€)", "Potentiel %", "Prix Actuel (€)", "Perf %", "Stop-Loss (€)", "Statut", "Jours"]


def read_csv() -> list:
    if not os.path.exists(CSV_FILE):
        return []
    with open(CSV_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def write_csv(rows: list):
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def add_recommendation(ticker, nom, prix_achat, target, stop_loss):
    rows = read_csv()
    today = datetime.now().strftime("%d/%m/%Y")
    for row in rows:
        if row.get("Date") == today and row.get("Ticker") == ticker:
            print(f"  ⏩ {ticker} déjà enregistré aujourd'hui, skip.")
            return
    potentiel = round((target / prix_achat - 1) * 100, 2) if prix_achat else 0
    new_row = {
        "Date": today,
        "Ticker": ticker,
        "Nom": nom,
        "Prix Achat (€)": prix_achat,
        "Target (€)": target,
        "Potentiel %": f"{potentiel}%",
        "Prix Actuel (€)": prix_achat,
        "Perf %": "0.00%",
        "Stop-Loss (€)": stop_loss,
        "Statut": "En cours",
        "Jours": "0",
    }
    rows.append(new_row)
    write_csv(rows)
    print(f"  ✅ {ticker} ajouté au tracker ({today}, achat={prix_achat}€, target={target}€)")


def update_prices():
    rows = read_csv()
    if not rows:
        print("  ℹ️ Tracker vide, rien à mettre à jour.")
        return
    updated = 0
    for row in rows:
        if "En cours" not in row.get("Statut", ""):
            continue
        ticker = row.get("Ticker")
        try:
            prix_achat = float(str(row.get("Prix Achat (€)", "0")).replace(",", "."))
            target = float(str(row.get("Target (€)", "0")).replace(",", "."))
            stop_loss = float(str(row.get("Stop-Loss (€)", "0")).replace(",", "."))
            date_achat = datetime.strptime(row.get("Date", "01/01/2000"), "%d/%m/%Y")
        except (ValueError, TypeError):
            continue
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            if hist.empty:
                continue
            prix_actuel = round(float(hist['Close'].iloc[-1]), 2)
        except Exception as e:
            print(f"  ✗ Impossible de récupérer {ticker}: {e}")
            continue
        perf = round((prix_actuel / prix_achat - 1) * 100, 2) if prix_achat else 0
        jours = (datetime.now() - date_achat).days
        perf_str = f"{'+' if perf >= 0 else ''}{perf}%"
        if prix_actuel >= target:
            statut = "Objectif atteint"
        elif prix_actuel <= stop_loss:
            statut = "Stop-loss touché"
        else:
            statut = "En cours"
        row["Prix Actuel (€)"] = prix_actuel
        row["Perf %"] = perf_str
        row["Statut"] = statut
        row["Jours"] = str(jours)
        updated += 1
        print(f"  🔄 {ticker}: {prix_actuel}€ ({perf_str}) — {statut}")
    write_csv(rows)
    print(f"  ✅ {updated} position(s) mise(s) à jour")


def get_tracking_table() -> list:
    rows = read_csv()
    def parse_date(d):
        try:
            return datetime.strptime(d.get("Date", "01/01/2000"), "%d/%m/%Y")
        except ValueError:
            return datetime.min
    rows.sort(key=parse_date, reverse=True)
    return rows


def parse_claude_recommendations(analysis_text):
    recommendations = []
    stock_pattern = re.compile(
        r'[1-3️⃣\d]+[️⃣]?\s+\*{0,2}([^*\(]+?)\*{0,2}\s*\(([A-Z]+\.PA)\)\*{0,2}\s*[—-]\s*Prix actuel\s*:\s*([\d,\.]+)\s*€',
        re.IGNORECASE
    )
    target_pattern = re.compile(r'Objectif\s+\d\s+mois\s*:\s*([\d,\.]+)\s*€', re.IGNORECASE)
    stop_pattern = re.compile(r'Stop-loss\s+sugg[eé]r[eé]\s*:\s*([\d,\.]+)\s*€', re.IGNORECASE)
    blocks = re.split(r'(?=[1-3]️⃣|(?:^|\n)\s*[1-3]\s)', analysis_text)
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
