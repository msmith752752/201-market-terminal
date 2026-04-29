from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CACHE = {}
CACHE_TIME = 60

MARKET_PULSE = {
    "SPY": "SPY",
    "QQQ": "QQQ",
    "DIA": "DIA",
    "IWM": "IWM",
    "VIX": "^VIX",
    "TNX": "^TNX",
    "NVDA": "NVDA",
}

FUTURES = {
    "S&P Futures": "ES=F",
    "Nasdaq Futures": "NQ=F",
    "Dow Futures": "YM=F",
    "Russell Futures": "RTY=F",
}

MOVER_TICKERS = [
    "NVDA", "AAPL", "MSFT", "TSLA", "AMZN",
    "META", "GOOGL", "AMD", "AVGO", "PLTR"
]

SECTORS = {
    "Technology": "XLK",
    "Financials": "XLF",
    "Energy": "XLE",
    "Health Care": "XLV",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Industrials": "XLI",
    "Utilities": "XLU",
    "Materials": "XLB",
    "Real Estate": "XLRE",
    "Communication Services": "XLC",
}

def get_quote(symbol):
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="5d", interval="1d")

    if hist.empty or len(hist) < 2:
        raise ValueError("Not enough price history")

    price = float(hist["Close"].iloc[-1])
    previous_close = float(hist["Close"].iloc[-2])
    change_percent = ((price - previous_close) / previous_close) * 100

    return {
        "price": round(price, 2),
        "changePercent": round(change_percent, 2),
    }

@app.get("/")
def home():
    return {"status": "201 Market Terminal backend running"}

@app.get("/dashboard")
def dashboard():
    now = time.time()

    if "dashboard" in CACHE and now - CACHE["dashboard"]["time"] < CACHE_TIME:
        return CACHE["dashboard"]["data"]

    market_pulse = {}
    futures = {}
    movers = []
    sectors = []

    for display_symbol, yf_symbol in MARKET_PULSE.items():
        try:
            market_pulse[display_symbol] = get_quote(yf_symbol)
        except Exception as e:
            market_pulse[display_symbol] = {
                "price": None,
                "changePercent": None,
                "error": str(e),
            }

    for display_name, yf_symbol in FUTURES.items():
        try:
            futures[display_name] = get_quote(yf_symbol)
        except Exception as e:
            futures[display_name] = {
                "price": None,
                "changePercent": None,
                "error": str(e),
            }

    for symbol in MOVER_TICKERS:
        try:
            quote = get_quote(symbol)
            movers.append({
                "symbol": symbol,
                "price": quote["price"],
                "changePercent": quote["changePercent"],
            })
        except:
            pass

    movers = sorted(movers, key=lambda x: abs(x["changePercent"]), reverse=True)[:5]

    for sector_name, etf in SECTORS.items():
        try:
            quote = get_quote(etf)
            sectors.append({
                "sector": sector_name,
                "etf": etf,
                "changePercent": quote["changePercent"],
            })
        except:
            pass

    sectors = sorted(sectors, key=lambda x: x["changePercent"], reverse=True)

    data = {
        "marketPulse": market_pulse,
        "futures": futures,
        "biggestMovers": movers,
        "sectorStrength": sectors,
    }

    CACHE["dashboard"] = {
        "time": now,
        "data": data,
    }

    return data