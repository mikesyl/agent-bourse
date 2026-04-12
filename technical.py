import yfinance as yf
import pandas as pd
import numpy as np

# Universe d'actions françaises SBF 120
TICKERS_FR = [
    "AI.PA",    # Air Liquide
    "MC.PA",    # LVMH
    "TTE.PA",   # TotalEnergies
    "SAN.PA",   # Sanofi
    "BNP.PA",   # BNP Paribas
    "DG.PA",    # Vinci
    "CAP.PA",   # Capgemini
    "DSY.PA",   # Dassault Systèmes
    "VIE.PA",   # Veolia
    "ORA.PA",   # Orange
    "HO.PA",    # Thales
    "ALO.PA",   # Alstom
    "ERF.PA",   # Eurofins
    "RMS.PA",   # Hermès
    "STM.PA",   # STMicroelectronics
    "SGO.PA",   # Saint-Gobain
    "ACA.PA",   # Crédit Agricole
    "GLE.PA",   # Société Générale
    "ML.PA",    # Michelin
    "PUB.PA",   # Publicis
]

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(prices):
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    return macd.iloc[-1], signal.iloc[-1], histogram.iloc[-1]

def calculate_bollinger(prices, period=20):
    ma = prices.rolling(period).mean()
    std = prices.rolling(period).std()
    upper = ma + (2 * std)
    lower = ma - (2 * std)
    current = prices.iloc[-1]
    denom = upper.iloc[-1] - lower.iloc[-1]
    pct_b = (current - lower.iloc[-1]) / denom if denom != 0 else 0.5
    return upper.iloc[-1], ma.iloc[-1], lower.iloc[-1], pct_b

def get_technical_analysis(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")
        info = stock.info

        if len(hist) < 30:
            return None

        prices = hist['Close']
        volumes = hist['Volume']

        # RSI
        rsi = calculate_rsi(prices).iloc[-1]

        # MACD
        macd, signal, histogram = calculate_macd(prices)
        macd_signal = "ACHAT" if histogram > 0 else "VENTE"

        # Bollinger Bands
        bb_upper, bb_mid, bb_lower, pct_b = calculate_bollinger(prices)
        bb_signal = "SURVENDU" if pct_b < 0.2 else "SURACHETÉ" if pct_b > 0.8 else "NEUTRE"

        # Moyennes mobiles
        ma20 = prices.rolling(20).mean().iloc[-1]
        ma50 = prices.rolling(50).mean().iloc[-1]
        trend = "HAUSSIER" if prices.iloc[-1] > ma20 > ma50 else \
                "BAISSIER" if prices.iloc[-1] < ma20 < ma50 else "LATÉRAL"

        # Volume
        vol_10d = volumes.tail(10).mean()
        vol_3m = volumes.mean()
        vol_signal = "FORT" if vol_10d > vol_3m * 1.3 else \
                     "FAIBLE" if vol_10d < vol_3m * 0.7 else "NORMAL"

        # Momentum
        momentum_1m = ((prices.iloc[-1] / prices.iloc[-22]) - 1) * 100
        momentum_3m = ((prices.iloc[-1] / prices.iloc[-66]) - 1) * 100 \
                      if len(prices) >= 66 else None

        # Support / Résistance
        high = hist['High'].tail(20).max()
        low = hist['Low'].tail(20).min()
        pivot = (high + low + prices.iloc[-1]) / 3
        support = round(2 * pivot - high, 2)
        resistance = round(2 * pivot - low, 2)

        # Score technique (0-100)
        score = 0
        if 30 < rsi < 50:  score += 25   # Zone d'achat idéale
        elif 50 <= rsi < 65: score += 15
        if macd_signal == "ACHAT":  score += 20
        if trend == "HAUSSIER":     score += 20
        if vol_signal == "FORT":    score += 10
        if pct_b < 0.35:            score += 15  # Proche bande basse
        if momentum_1m and momentum_1m > 0: score += 10

        return {
            "ticker": ticker,
            "nom": info.get('longName', ticker),
            "secteur": info.get('sector', 'N/A'),
            "prix": round(float(prices.iloc[-1]), 2),
            "variation_1m": round(momentum_1m, 2),
            "variation_3m": round(momentum_3m, 2) if momentum_3m else "N/A",
            "rsi": round(rsi, 1),
            "macd_signal": macd_signal,
            "bb_signal": bb_signal,
            "tendance": trend,
            "volume_signal": vol_signal,
            "support": support,
            "resistance": resistance,
            "ma20": round(ma20, 2),
            "ma50": round(ma50, 2),
            "per": info.get('trailingPE', 'N/A'),
            "capitalisation_M": round(info.get('marketCap', 0) / 1e6) if info.get('marketCap') else 'N/A',
            "score_technique": score,
        }
    except Exception as e:
        print(f"  ✗ Erreur {ticker}: {e}")
        return None
