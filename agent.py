# v3
import anthropic
import json
import os
import sys
import traceback
from datetime import datetime
from technical import get_technical_analysis, TICKERS_FR
from news import get_news_for_ticker, get_market_context
from email_sender import send_email
from tracker import parse_claude_recommendations, add_recommendation, update_prices, get_tracking_table

# Bloquer les week-ends
if datetime.now().weekday() >= 5:
    print("Weekend — marchés fermés, pas d'analyse.")
    sys.exit(0)

def collect_all_data():
    print("📊 Collecte des données techniques...")
    results = []
    for ticker in TICKERS_FR:
        data = get_technical_analysis(ticker)
        if data:
            news = get_news_for_ticker(ticker, data['nom'])
            data['actualites'] = [n['titre'] for n in news]
            results.append(data)
            print(f"  ✓ {ticker:10s} | score={data['score_technique']:3d} | RSI={data['rsi']:5.1f} | {data['tendance']}")
    results.sort(key=lambda x: x['score_technique'], reverse=True)
    return results[:8]

def analyze_with_claude(data, market_context):
    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
    date_str = datetime.now().strftime("%A %d %B %Y")
    data_str = json.dumps(data, ensure_ascii=False, indent=2)
    prompt = f"""Tu es un analyste financier senior spécialisé sur les marchés boursiers français (Euronext Paris).

Date d'analyse : {date_str}
Contexte de marché : {market_context}

Voici les données techniques et fondamentales des actions pré-sélectionnées par scoring :
{data_str}

MISSION : Sélectionne les 3 meilleures opportunités d'achat avec un potentiel de +10% minimum à 3 mois.

Pour chaque action, fournis EXACTEMENT ce format (respect strict des tirets et emojis) :
1️⃣ / 2️⃣ / 3️⃣ NOM (TICKER.PA) — Prix actuel : XXX€
🎯 Objectif 3 mois : XXX€ (+XX%)
📈 Technique : RSI XX | MACD [signal] | Tendance [tendance]
✅ Catalyseur 1 : [raison concrète]
✅ Catalyseur 2 : [raison concrète]
⚠️ Risque : [Faible/Modéré/Élevé] — Stop-loss suggéré : XXX€

FORMAT GLOBAL :
- Commence par "📊 Analyse du {date_str}"
- Une ligne vide entre chaque action
- Termine par "⚠️ Pas un conseil financier. DYOR."
- Sois concis mais précis — max 600 mots
"""
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def run():
    print(f"\n{'='*55}")
    print(f"  🚀 AGENT BOURSE — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'='*55}\n")

    market_context = get_market_context()
    print(f"📈 Marché : {market_context}\n")

    top_stocks = collect_all_data()
    print(f"\n🔍 {len(top_stocks)} actions sélectionnées pour analyse Claude\n")

    print("🤖 Analyse Claude en cours...")
    analysis = analyze_with_claude(top_stocks, market_context)

    print("\n📋 Mise à jour du tracker...")
    try:
        update_prices()
    except Exception as e:
        print(f"  ❌ Erreur mise à jour tracker: {e}")
        print(traceback.format_exc())

    print("\n💾 Enregistrement des recommandations...")
    try:
        recos = parse_claude_recommendations(analysis)
        print(f"  🔍 {len(recos)} recommandation(s) parsée(s)")
        for reco in recos:
            print(f"  → {reco['ticker']} | achat={reco['prix_achat']} | target={reco['target']}")
            add_recommendation(
                ticker=reco['ticker'],
                nom=reco['nom'],
                prix_achat=reco['prix_achat'],
                target=reco['target'],
                stop_loss=reco['stop_loss'],
            )
    except Exception as e:
        print(f"  ❌ Erreur enregistrement recommandations: {e}")
        print(traceback.format_exc())

    tracking_table = []
    try:
        tracking_table = get_tracking_table()
        print(f"  📊 {len(tracking_table)} ligne(s) dans le tracker")
    except Exception as e:
        print(f"  ❌ Erreur lecture tracker: {e}")
        print(traceback.format_exc())

    print("\n📧 Envoi de l'email...")
    send_email(analysis, tracking_table)

    print(f"\n{'='*55}")
    print("  ✅ ANALYSE DU JOUR")
    print(f"{'='*55}")
    print(analysis)
    print(f"{'='*55}\n")


if __name__ == "__main__":
    run()
    
