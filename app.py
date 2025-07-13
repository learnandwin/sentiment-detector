import pandas as pd
import yfinance as yf
import datetime
from textblob import TextBlob
import subprocess
import json
import streamlit as st
import plotly.express as px

# Configuración
assets = {
    'Stocks': ['$TSLA', '$AAPL', '$NVDA'],
    'Crypto': ['$BTC', '$ETH', '$SOL']
}
query_keywords = ["moon", "panic", "bullish", "bearish", "pump", "dump", "FOMO", "rug"]
lookback_minutes = 15
sentiment_threshold = 0.3

st.set_page_config(page_title="Sentiment Spike Detector", layout="wide")
st.title("📊 Real-Time Sentiment Spike Detector (X / Twitter)")

# Función para scrapear tweets usando subprocess
@st.cache_data(show_spinner=False)
def scrape_tweets(symbol, minutes):
    since_time = (datetime.datetime.utcnow() - datetime.timedelta(minutes=minutes)).isoformat(timespec='seconds') + "Z"
    query = f'{symbol} {" OR ".join(query_keywords)} since:{since_time} lang:en'
    cmd = f"snscrape --jsonl --max-results 100 'twitter-search \"{query}\"'"

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        tweets_raw = result.stdout.strip().split("\n")
        tweets = []

        for line in tweets_raw:
            tweet_data = json.loads(line)
            tweets.append({
                "date": tweet_data["date"],
                "content": tweet_data["content"],
                "username": tweet_data["user"]["username"]
            })

        return tweets

    except subprocess.CalledProcessError as e:
        st.error(f"❌ Error ejecutando snscrape: {e}")
        return []

# Función de análisis de sentimiento
def analyze_sentiment(tweets):
    sentiments = [TextBlob(t["content"]).sentiment.polarity for t in tweets]
    return sum(sentiments) / len(sentiments) if sentiments else 0

# Obtener precios desde Yahoo Finance
@st.cache_data(show_spinner=False)
def get_current_price(symbol):
    ticker = yf.Ticker(symbol.replace("$", ""))
    hist = ticker.history(period="1d", interval="5m")
    if not hist.empty:
        return hist.iloc[-1]["Close"], hist
    return None, None

# Estrategia principal
def run_strategy():
    results = []
    for group, symbols in assets.items():
        for symbol in symbols:
            with st.spinner(f"🔍 Analizando {symbol}..."):
                tweets = scrape_tweets(symbol, lookback_minutes)
                sentiment = analyze_sentiment(tweets)
                tweet_count = len(tweets)
                price, hist = get_current_price(symbol)
                if tweet_count > 20 and abs(sentiment) > sentiment_threshold:
                    results.append({
                        "Symbol": symbol,
                        "Type": group,
                        "Sentiment": "Positive" if sentiment > 0 else "Negative",
                        "Score": round(sentiment, 3),
                        "Tweets": tweet_count,
                        "Price": round(price, 2) if price else "-",
                        "Time": datetime.datetime.utcnow().strftime("%H:%M UTC"),
                        "Hist": hist
                    })
    return results

# Mostrar resultados
signals = run_strategy()
if signals:
    st.success(f"🚨 {len(signals)} señales detectadas!")
    df = pd.DataFrame(signals)
    st.dataframe(df.drop(columns=["Hist"]))

    for signal in signals:
        st.subheader(f"{signal['Symbol']} - {signal['Sentiment']} Sentiment 📈")
        hist = signal["Hist"]
        fig = px.line(hist, x=hist.index, y="Close", title=f"Precio de {signal['Symbol']} (últimas horas)")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("🔄 No se detectaron picos de sentimiento en este momento.")
