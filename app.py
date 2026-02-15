import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import time

st.set_page_config(page_title="Stock Earnings Tracker", layout="wide")
st.title("Stock Earnings Tracker")
st.markdown("Tracks upcoming earnings dates and recent EPS data from Yahoo Finance.")


DEFAULT_TICKERS = [
    {"Symbol": "AAPL", "Name": "Apple Inc.", "Sector": "Information Technology"},
    {"Symbol": "MSFT", "Name": "Microsoft Corp.", "Sector": "Information Technology"},
    {"Symbol": "AMZN", "Name": "Amazon.com Inc.", "Sector": "Consumer Discretionary"},
    {"Symbol": "NVDA", "Name": "NVIDIA Corp.", "Sector": "Information Technology"},
    {"Symbol": "GOOGL", "Name": "Alphabet Inc. (A)", "Sector": "Communication Services"},
    {"Symbol": "META", "Name": "Meta Platforms Inc.", "Sector": "Communication Services"},
    {"Symbol": "TSLA", "Name": "Tesla Inc.", "Sector": "Consumer Discretionary"},
    {"Symbol": "BRK-B", "Name": "Berkshire Hathaway (B)", "Sector": "Financials"},
    {"Symbol": "JPM", "Name": "JPMorgan Chase & Co.", "Sector": "Financials"},
    {"Symbol": "V", "Name": "Visa Inc.", "Sector": "Financials"},
    {"Symbol": "JNJ", "Name": "Johnson & Johnson", "Sector": "Health Care"},
    {"Symbol": "UNH", "Name": "UnitedHealth Group", "Sector": "Health Care"},
    {"Symbol": "XOM", "Name": "Exxon Mobil Corp.", "Sector": "Energy"},
    {"Symbol": "WMT", "Name": "Walmart Inc.", "Sector": "Consumer Staples"},
    {"Symbol": "MA", "Name": "Mastercard Inc.", "Sector": "Financials"},
    {"Symbol": "PG", "Name": "Procter & Gamble Co.", "Sector": "Consumer Staples"},
    {"Symbol": "HD", "Name": "Home Depot Inc.", "Sector": "Consumer Discretionary"},
    {"Symbol": "COST", "Name": "Costco Wholesale", "Sector": "Consumer Staples"},
    {"Symbol": "ABBV", "Name": "AbbVie Inc.", "Sector": "Health Care"},
    {"Symbol": "CRM", "Name": "Salesforce Inc.", "Sector": "Information Technology"},
    {"Symbol": "BAC", "Name": "Bank of America Corp.", "Sector": "Financials"},
    {"Symbol": "MRK", "Name": "Merck & Co. Inc.", "Sector": "Health Care"},
    {"Symbol": "CVX", "Name": "Chevron Corp.", "Sector": "Energy"},
    {"Symbol": "NFLX", "Name": "Netflix Inc.", "Sector": "Communication Services"},
    {"Symbol": "AMD", "Name": "Advanced Micro Devices", "Sector": "Information Technology"},
    {"Symbol": "LIN", "Name": "Linde plc", "Sector": "Materials"},
    {"Symbol": "TMO", "Name": "Thermo Fisher Scientific", "Sector": "Health Care"},
    {"Symbol": "PEP", "Name": "PepsiCo Inc.", "Sector": "Consumer Staples"},
    {"Symbol": "ADBE", "Name": "Adobe Inc.", "Sector": "Information Technology"},
    {"Symbol": "DIS", "Name": "Walt Disney Co.", "Sector": "Communication Services"},
    {"Symbol": "CSCO", "Name": "Cisco Systems Inc.", "Sector": "Information Technology"},
    {"Symbol": "ABT", "Name": "Abbott Laboratories", "Sector": "Health Care"},
    {"Symbol": "ACN", "Name": "Accenture plc", "Sector": "Information Technology"},
    {"Symbol": "INTC", "Name": "Intel Corp.", "Sector": "Information Technology"},
    {"Symbol": "WFC", "Name": "Wells Fargo & Co.", "Sector": "Financials"},
    {"Symbol": "QCOM", "Name": "Qualcomm Inc.", "Sector": "Information Technology"},
    {"Symbol": "CMCSA", "Name": "Comcast Corp.", "Sector": "Communication Services"},
    {"Symbol": "IBM", "Name": "IBM Corp.", "Sector": "Information Technology"},
    {"Symbol": "INTU", "Name": "Intuit Inc.", "Sector": "Information Technology"},
    {"Symbol": "GE", "Name": "GE Aerospace", "Sector": "Industrials"},
    {"Symbol": "AMAT", "Name": "Applied Materials", "Sector": "Information Technology"},
    {"Symbol": "CAT", "Name": "Caterpillar Inc.", "Sector": "Industrials"},
    {"Symbol": "NOW", "Name": "ServiceNow Inc.", "Sector": "Information Technology"},
    {"Symbol": "TXN", "Name": "Texas Instruments", "Sector": "Information Technology"},
    {"Symbol": "GS", "Name": "Goldman Sachs Group", "Sector": "Financials"},
    {"Symbol": "BKNG", "Name": "Booking Holdings", "Sector": "Consumer Discretionary"},
    {"Symbol": "ISRG", "Name": "Intuitive Surgical", "Sector": "Health Care"},
    {"Symbol": "SPGI", "Name": "S&P Global Inc.", "Sector": "Financials"},
    {"Symbol": "PFE", "Name": "Pfizer Inc.", "Sector": "Health Care"},
    {"Symbol": "T", "Name": "AT&T Inc.", "Sector": "Communication Services"},
]


@st.cache_data(ttl=3600)
def get_sp500_tickers():
    """Scrape S&P 500 tickers from Wikipedia, with fallback to a curated list."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; StockEarningsTracker/1.0)"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", {"id": "constituents"})
        rows = table.find("tbody").find_all("tr")[1:]
        tickers = []
        for row in rows:
            cols = row.find_all("td")
            if cols:
                symbol = cols[0].text.strip().replace(".", "-")
                name = cols[1].text.strip()
                sector = cols[3].text.strip()
                tickers.append({"Symbol": symbol, "Name": name, "Sector": sector})
        if tickers:
            return pd.DataFrame(tickers)
    except Exception:
        pass
    # Fallback to curated top-50 S&P 500 stocks
    return pd.DataFrame(DEFAULT_TICKERS)


@st.cache_data(ttl=3600)
def get_most_active_tickers():
    """Scrape Yahoo Finance most active stocks page."""
    url = "https://finance.yahoo.com/most-active/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        symbols = []
        for link in soup.find_all("a", {"data-testid": "table-cell-ticker"}):
            symbols.append(link.text.strip())
        if not symbols:
            for link in soup.select("a[href*='/quote/']"):
                txt = link.text.strip()
                if txt.isupper() and 1 <= len(txt) <= 5:
                    symbols.append(txt)
        return list(dict.fromkeys(symbols))[:50]
    except Exception:
        return []


@st.cache_data(ttl=1800)
def fetch_earnings_data(symbol):
    """Fetch earnings dates and EPS history for a single ticker."""
    try:
        ticker = yf.Ticker(symbol)

        # Get upcoming earnings date
        next_earnings = None
        try:
            cal = ticker.calendar
            if cal is not None:
                if isinstance(cal, dict):
                    if "Earnings Date" in cal:
                        dates = cal["Earnings Date"]
                        if isinstance(dates, list) and len(dates) > 0:
                            next_earnings = pd.Timestamp(dates[0])
                        elif not isinstance(dates, list):
                            next_earnings = pd.Timestamp(dates)
                elif isinstance(cal, pd.DataFrame) and not cal.empty:
                    if "Earnings Date" in cal.index:
                        val = cal.loc["Earnings Date"].iloc[0]
                        next_earnings = pd.Timestamp(val)
        except Exception:
            pass

        # Get EPS history from earnings_history or quarterly_earnings
        eps_records = []
        try:
            eh = ticker.earnings_history
            if eh is not None and isinstance(eh, pd.DataFrame) and not eh.empty:
                for _, row in eh.iterrows():
                    record = {}
                    # Try to get the date
                    if hasattr(row, "name") and row.name is not None:
                        record["Date"] = str(row.name)
                    for col in eh.columns:
                        if "date" in col.lower():
                            record["Date"] = str(row[col])
                    # Get EPS values
                    for col in eh.columns:
                        if "eps" in col.lower() and "actual" in col.lower():
                            record["EPS Actual"] = row[col]
                        elif "eps" in col.lower() and "estimate" in col.lower():
                            record["EPS Estimate"] = row[col]
                        elif "eps" in col.lower() and "surprise" in col.lower():
                            record["EPS Surprise (%)"] = row[col]
                    if record:
                        eps_records.append(record)
        except Exception:
            pass

        # Fallback: use quarterly earnings
        if not eps_records:
            try:
                qe = ticker.quarterly_earnings
                if qe is not None and isinstance(qe, pd.DataFrame) and not qe.empty:
                    for idx, row in qe.iterrows():
                        record = {"Date": str(idx)}
                        if "Earnings" in qe.columns:
                            record["EPS Actual"] = row["Earnings"]
                        if "Revenue" in qe.columns:
                            record["Revenue"] = row["Revenue"]
                        eps_records.append(record)
            except Exception:
                pass

        # Fallback: use earnings_dates
        if not eps_records:
            try:
                ed = ticker.earnings_dates
                if ed is not None and isinstance(ed, pd.DataFrame) and not ed.empty:
                    past = ed[ed.index <= pd.Timestamp.now(tz=ed.index.tz)]
                    for idx, row in past.head(4).iterrows():
                        record = {"Date": idx.strftime("%Y-%m-%d")}
                        for col in ed.columns:
                            if "eps" in col.lower() and "actual" in col.lower():
                                record["EPS Actual"] = row[col]
                            elif "eps" in col.lower() and "estimate" in col.lower():
                                record["EPS Estimate"] = row[col]
                            elif "surprise" in col.lower():
                                record["EPS Surprise (%)"] = row[col]
                        eps_records.append(record)

                    # Also try to get next earnings from future dates
                    if next_earnings is None:
                        future = ed[ed.index > pd.Timestamp.now(tz=ed.index.tz)]
                        if not future.empty:
                            next_earnings = future.index[0]
            except Exception:
                pass

        return {
            "next_earnings": next_earnings,
            "eps_history": eps_records,
        }

    except Exception as e:
        return {"next_earnings": None, "eps_history": [], "error": str(e)}


@st.cache_data(ttl=300)
def fetch_last_trading_data(symbol):
    """Fetch last trading day close price and total volume for a single ticker."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d")
        if hist is not None and not hist.empty:
            last_row = hist.iloc[-1]
            trade_date = hist.index[-1]
            return {
                "Last Price": round(last_row["Close"], 2),
                "Volume": int(last_row["Volume"]),
                "Trade Date": trade_date.strftime("%Y-%m-%d"),
            }
    except Exception:
        pass
    return {"Last Price": None, "Volume": None, "Trade Date": None}


# --- Sidebar controls ---
st.sidebar.header("Settings")

ticker_source = st.sidebar.radio(
    "Ticker Source",
    ["S&P 500 (Wikipedia)", "Yahoo Finance Most Active", "Custom List"],
)

custom_tickers = []
if ticker_source == "Custom List":
    raw = st.sidebar.text_area(
        "Enter tickers (comma-separated)",
        value="AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA, META, JPM, V, JNJ",
    )
    custom_tickers = [t.strip().upper() for t in raw.split(",") if t.strip()]

batch_size = st.sidebar.slider("Tickers to fetch", min_value=5, max_value=100, value=20, step=5)
show_only_upcoming = st.sidebar.checkbox("Show only stocks with upcoming earnings", value=False)

# --- Load tickers ---
if ticker_source == "S&P 500 (Wikipedia)":
    with st.spinner("Loading S&P 500 tickers from Wikipedia..."):
        sp500_df = get_sp500_tickers()
    symbols = sp500_df["Symbol"].tolist()[:batch_size]
    st.sidebar.success(f"Loaded {len(sp500_df)} S&P 500 tickers. Showing first {batch_size}.")

    with st.expander("S&P 500 Ticker List"):
        sector_filter = st.multiselect("Filter by sector", sp500_df["Sector"].unique().tolist())
        if sector_filter:
            filtered = sp500_df[sp500_df["Sector"].isin(sector_filter)]
            symbols = filtered["Symbol"].tolist()[:batch_size]
            st.dataframe(filtered, use_container_width=True)
        else:
            st.dataframe(sp500_df.head(batch_size), use_container_width=True)

elif ticker_source == "Yahoo Finance Most Active":
    with st.spinner("Loading most active tickers from Yahoo Finance..."):
        active = get_most_active_tickers()
    if active:
        symbols = active[:batch_size]
        st.sidebar.success(f"Loaded {len(active)} most active tickers.")
    else:
        st.sidebar.warning("Could not scrape Yahoo Finance. Using default list.")
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "JPM", "V", "JNJ"]
else:
    symbols = custom_tickers[:batch_size]

# --- Fetch buttons ---
btn_col1, btn_col2, _ = st.columns([1, 1, 2])
with btn_col1:
    st.button("Fetch Earnings Data", type="primary",
              on_click=lambda: st.session_state.update({"do_fetch_earnings": True}))
with btn_col2:
    st.button("Fetch Last Price & Volume", type="secondary",
              on_click=lambda: st.session_state.update({"do_fetch_price": True}))

# --- Fetch last price & volume ---
if st.session_state.pop("do_fetch_price", False):
    progress = st.progress(0, text="Fetching price & volume data...")
    price_results = []
    for i, sym in enumerate(symbols):
        progress.progress((i + 1) / len(symbols), text=f"Fetching {sym} ({i+1}/{len(symbols)})...")
        data = fetch_last_trading_data(sym)
        price_results.append({"Symbol": sym, **data})
        if (i + 1) % 5 == 0:
            time.sleep(0.3)
    progress.empty()
    st.session_state["price_results"] = price_results

if st.session_state.get("price_results"):
    price_df = pd.DataFrame(st.session_state["price_results"])
    st.subheader(f"Last Trading Day - Price & Volume ({len(price_df)} stocks)")
    st.dataframe(
        price_df,
        use_container_width=True,
        height=600,
        column_config={
            "Last Price": st.column_config.NumberColumn(format="$%.2f"),
            "Volume": st.column_config.NumberColumn(format="%d"),
        },
    )

# --- Fetch earnings data ---
if st.session_state.pop("do_fetch_earnings", False):
    progress = st.progress(0, text="Fetching earnings data...")
    results = []
    for i, sym in enumerate(symbols):
        progress.progress((i + 1) / len(symbols), text=f"Fetching {sym} ({i+1}/{len(symbols)})...")
        data = fetch_earnings_data(sym)
        results.append({"Symbol": sym, **data})
        if (i + 1) % 5 == 0:
            time.sleep(0.5)
    progress.empty()
    st.session_state["results"] = results
    st.session_state["symbols"] = symbols

if st.session_state.get("results"):
    results = st.session_state["results"]

    # --- Build summary table ---
    summary_rows = []
    for r in results:
        next_earn = r.get("next_earnings")
        if next_earn is not None:
            try:
                ts = pd.Timestamp(next_earn)
                next_earn_str = ts.strftime("%Y-%m-%d")
                ts_naive = ts.tz_localize(None) if ts.tzinfo else ts
                days_away = (ts_naive - pd.Timestamp.now()).days
            except Exception:
                next_earn_str = "N/A"
                days_away = None
        else:
            next_earn_str = "N/A"
            days_away = None

        last_eps = None
        last_eps_date = None
        eps_surprise = None
        eps_hist = r.get("eps_history", [])
        if eps_hist:
            latest = eps_hist[0]
            last_eps = latest.get("EPS Actual")
            last_eps_date = latest.get("Date")
            eps_surprise = latest.get("EPS Surprise (%)")

        summary_rows.append({
            "Symbol": r["Symbol"],
            "Next Earnings Date": next_earn_str,
            "Days Until Earnings": days_away,
            "Last EPS": last_eps,
            "Last EPS Date": last_eps_date,
            "EPS Surprise (%)": eps_surprise,
        })

    summary_df = pd.DataFrame(summary_rows)

    if show_only_upcoming:
        summary_df = summary_df[summary_df["Next Earnings Date"] != "N/A"]

    # Sort by days until earnings
    sort_col = "Days Until Earnings"
    if sort_col in summary_df.columns:
        summary_df = summary_df.sort_values(sort_col, ascending=True, na_position="last")

    st.subheader(f"Earnings Overview ({len(summary_df)} stocks)")

    # Highlight formatting
    def highlight_earnings(row):
        styles = [""] * len(row)
        days = row["Days Until Earnings"]
        if days is not None and not pd.isna(days):
            if days <= 7:
                styles[1] = "background-color: #ffcccc; font-weight: bold"
                styles[2] = "background-color: #ffcccc; font-weight: bold"
            elif days <= 30:
                styles[1] = "background-color: #fff3cd"
                styles[2] = "background-color: #fff3cd"
        return styles

    styled = summary_df.style.apply(highlight_earnings, axis=1).format({
        "Last EPS": lambda x: f"{x:.2f}" if pd.notna(x) else "N/A",
        "EPS Surprise (%)": lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A",
        "Days Until Earnings": lambda x: f"{int(x)}" if pd.notna(x) else "N/A",
    })
    st.dataframe(styled, use_container_width=True, height=600)

    # --- Detailed EPS history per stock ---
    st.subheader("Detailed EPS History")
    selected = st.multiselect(
        "Select stocks to view EPS history",
        summary_df["Symbol"].tolist(),
        default=summary_df["Symbol"].tolist()[:5],
    )

    for sym in selected:
        match = [r for r in results if r["Symbol"] == sym]
        if not match:
            continue
        r = match[0]
        eps_hist = r.get("eps_history", [])
        if eps_hist:
            st.markdown(f"**{sym}**")
            eps_df = pd.DataFrame(eps_hist)
            st.dataframe(eps_df, use_container_width=True)
        else:
            st.markdown(f"**{sym}** - No EPS history available.")

    # --- Download CSV ---
    st.subheader("Export")
    csv = summary_df.to_csv(index=False)
    st.download_button(
        label="Download earnings data as CSV",
        data=csv,
        file_name=f"earnings_tracker_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )
