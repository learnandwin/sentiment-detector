import snscrape.modules.twitter as sntwitter
import pandas as pd
import yfinance as yf
import datetime
from textblob import TextBlob
import streamlit as st
import plotly.express as px

# Configuración inicial
assets = {
    'Stocks': ['$TSLA', '$AAPL', '$NVDA'],
    'Crypto': ['$BTC', '$ETH', '$SOL']
}
query_keywords = ["moon", "panic", "bullish", "bearish", "pump", "dump", "FOMO", "rug"]
lookback_minutes = 15
sentiment_threshold = 0.3

st.set_page_config(page_title="Sentiment Spike Detector", layout="wide")
st.title("📊 Real-Time Sentiment Spike Detector (X / Twitter)")

# Función para scrapear tweets
@st.cache_data(show_spinner=False)
def scrape_tweets(symbol, minutes):
    query = f'{symbol} {" OR ".join(query_keywords)} lang:en'
    tweets = []
    since_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=minutes)
    for tweet in sntwitter.TwitterSearchScraper(query).get_items():
        if tweet.date < since_time:
            break
        tweets.append({
            "date": tweet.date,
            "content": tweet.content,
            "username": tweet.user.username
        })
    return tweets

# Función de análisis de sentimiento
def analyze_sentiment(tweets):
    sentiments = [TextBlob(t["content"]).sentiment.polarity for t in tweets]
    return sum(sentiments) / len(sentiments) if sentiments else 0

# Obtener precios actuales desde Yahoo Finance
@st.cache_data(show_spinner=False)
def get_current_price(symbol):
    ticker = yf.Ticker(symbol.replace("$", ""))
    hist = ticke
