import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date

# App Title
st.title("Stock Market Visualizer with Enhanced Analytics")
st.sidebar.title("Options")

# Helper Functions
import time
from pathlib import Path

import pandas as pd
import streamlit as st
import yfinance as yf
from yfinance.exceptions import YFRateLimitError


# Optional but helpful on Streamlit Cloud
CACHE_DIR = Path(".cache/yfinance")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

try:
    yf.set_tz_cache_location(str(CACHE_DIR))
except Exception:
    pass


@st.cache_data(ttl=60 * 30, show_spinner=False)
def with st.spinner(f"Loading data for {ticker}..."):
    data = fetch_stock_data(ticker, start_date, end_date)

if data.empty:
    st.stop() max_retries=3):
    """
    Fetch historical stock data with caching and basic retry handling.

    ttl=30 minutes prevents the app from calling Yahoo Finance on every rerun.
    """
    ticker = ticker.upper().strip()

    if not ticker:
        return pd.DataFrame()

    for attempt in range(max_retries):
        try:
            data = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                progress=False,
                auto_adjust=False,
                threads=False,
            )

            if data.empty:
                return pd.DataFrame()

            # yfinance sometimes returns multi-index columns
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            return data

        except YFRateLimitError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                st.warning(
                    "Yahoo Finance is temporarily rate-limiting requests. "
                    "Please wait a bit, try a shorter date range, or use cached data if available."
                )
                return pd.DataFrame()

        except Exception as e:
            st.error(f"Could not fetch data for {ticker}: {e}")
            return pd.DataFrame()

    return pd.DataFrame()

def plot_candlestick(data):
    """Plot a candlestick chart."""
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name="Candlestick"
    ))
    fig.update_layout(title="Candlestick Chart", xaxis_title="Date", yaxis_title="Price", template="plotly_dark")
    st.plotly_chart(fig)

def plot_volume(data):
    """Plot a volume chart."""
    fig = px.bar(data, x=data.index, y='Volume', title="Trading Volume", template="plotly_dark")
    st.plotly_chart(fig)

def plot_daily_returns(data):
    """Plot daily returns."""
    data['Daily Return'] = data['Close'].pct_change() * 100
    fig = px.line(data, x=data.index, y='Daily Return', title="Daily Returns (%)", template="plotly_dark")
    st.plotly_chart(fig)

def plot_cumulative_returns(data):
    """Plot cumulative returns."""
    data['Cumulative Return'] = (1 + data['Close'].pct_change()).cumprod() - 1
    fig = px.line(data, x=data.index, y='Cumulative Return', title="Cumulative Returns", template="plotly_dark")
    st.plotly_chart(fig)

def plot_moving_averages(data, windows):
    """Plot moving averages."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name="Close Price"))
    for window in windows:
        data[f"MA{window}"] = data['Close'].rolling(window=window).mean()
        fig.add_trace(go.Scatter(x=data.index, y=data[f"MA{window}"], mode='lines', name=f"MA {window}"))
    fig.update_layout(title="Moving Averages", xaxis_title="Date", yaxis_title="Price", template="plotly_dark")
    st.plotly_chart(fig)

def plot_correlation_matrix(data):
    """Plot correlation matrix for stock portfolio."""
    corr = data.corr()
    fig = px.imshow(corr, title="Correlation Matrix", template="plotly_dark", text_auto=True, color_continuous_scale='RdBu_r')
    st.plotly_chart(fig)

# Inputs
st.sidebar.header("Stock Selection")
ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL)", value="AAPL")
start_date = st.sidebar.date_input("Start Date", value=date(2020, 1, 1))
end_date = st.sidebar.date_input("End Date", value=date.today())

data = fetch_stock_data(ticker, start_date, end_date)

# Visualizations
if not data.empty:
    st.subheader(f"Stock Data for {ticker}")
    st.write(data.tail())

    # Candlestick Chart
    st.subheader("Candlestick Chart")
    plot_candlestick(data)

    # Volume Chart
    st.subheader("Volume Chart")
    plot_volume(data)

    # Daily Returns
    st.subheader("Daily Returns")
    plot_daily_returns(data)

    # Cumulative Returns
    st.subheader("Cumulative Returns")
    plot_cumulative_returns(data)

    # Moving Averages
    st.sidebar.header("Moving Averages")
    moving_averages = st.sidebar.multiselect("Select Moving Averages (days)", options=[10, 20, 50, 100, 200], default=[20, 50])
    if moving_averages:
        st.subheader("Moving Averages")
        plot_moving_averages(data, moving_averages)

# Portfolio Correlation
st.sidebar.header("Portfolio Analysis")
portfolio_file = st.sidebar.file_uploader("Upload Portfolio (CSV or Excel)")
if portfolio_file:
    portfolio = pd.read_csv(portfolio_file) if portfolio_file.name.endswith("csv") else pd.read_excel(portfolio_file)
    tickers = portfolio['Ticker'].tolist()
    st.subheader("Portfolio Data")
    st.write(portfolio)

    portfolio_data = {t: fetch_stock_data(t, start_date, end_date)['Close'] for t in tickers}
    portfolio_df = pd.DataFrame(portfolio_data)
    st.subheader("Correlation Matrix")
    plot_correlation_matrix(portfolio_df)
