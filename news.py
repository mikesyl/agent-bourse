import feedparser
import yfinance as yf
from datetime import datetime

def get_news_for_ticker(ticker, company_name):
    """Récupère les actualités récentes via Google News RSS (gratuit)"""
    news_items = []
    # On simplifie le nom pour la recherche
    short_name = company_name.split(' ')[0] if company_name else ticker.replace('.PA', '')
    query = f"{short_name} bourse résultats".replace(' ', '+')
    rss_url = f"https://news.google.com/rss/search?q={query}&hl=fr&gl=FR&ceid=FR:fr"

    try:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:4]:
            news_items.append({
                "titre": entry.get('title', ''),
                "date": entry.get('published', ''),
            })
    except Exception as e:
        print(f"  ✗ News {ticker}: {e}")

    return news_items

def get_market_context():
    """Contexte macro : CAC 40 + secteurs"""
    lines = []
    try:
        cac = yf.Ticker("^FCHI")
        hist = cac.history(period="5d")
        if len(hist) >= 2:
            close = hist['Close'].iloc[-1]
            prev  = hist['Close'].iloc[-2]
            var   = ((close / prev) - 1) * 100
            lines.append(f"CAC 40 : {close:.0f} pts ({var:+.2f}%)")
    except:
        lines.append("CAC 40 : données indisponibles")

    try:
        dax = yf.Ticker("^GDAXI")
        hist = dax.history(period="2d")
        if len(hist) >= 2:
            var = ((hist['Close'].iloc[-1] / hist['Close'].iloc[-2]) - 1) * 100
            lines.append(f"DAX : {var:+.2f}%")
    except:
        pass

    return " | ".join(lines)
