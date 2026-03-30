import os, re
import streamlit as st
import requests
import yfinance as yf
from openai import OpenAI
import pandas as pd
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()
FRED_API_KEY       = os.getenv("FRED_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

if not OPENROUTER_API_KEY:
    st.error("❌ OPENROUTER_API_KEY eksik!")
    st.stop()

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)

st.set_page_config(
    page_title="Serhat Alpha Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&display=swap');

:root {
    --bg:        #070d1a;
    --bg2:       #0b1425;
    --bg3:       #0f1e35;
    --border:    #1a2d4a;
    --accent:    #00e5ff;
    --accent2:   #ff6b35;
    --green:     #00ff88;
    --red:       #ff3b5c;
    --yellow:    #ffd600;
    --text:      #c8d8e8;
    --muted:     #4a6080;
    --mono:      'Space Mono', monospace;
    --sans:      'Syne', sans-serif;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    font-family: var(--sans) !important;
    color: var(--text) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #070d1a 0%, #0b1425 100%) !important;
    border-right: 1px solid var(--border) !important;
}

/* Hide streamlit default header */
#MainMenu, footer, header { visibility: hidden; }

/* Custom title */
.terminal-header {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px 0 8px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 20px;
}
.terminal-header h1 {
    font-family: var(--sans);
    font-size: 1.6em;
    font-weight: 800;
    color: #fff;
    margin: 0;
    letter-spacing: -0.5px;
}
.terminal-header .badge {
    font-family: var(--mono);
    font-size: 0.65em;
    background: var(--accent);
    color: #000;
    padding: 3px 8px;
    border-radius: 4px;
    font-weight: 700;
}
.status-dot {
    width: 8px; height: 8px;
    background: var(--green);
    border-radius: 50%;
    display: inline-block;
    animation: blink 2s infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* ── KATEGORİ BAŞLIKLARI ───────────────────────────────── */
.cat-header {
    font-family: var(--mono);
    font-size: 0.68em;
    font-weight: 700;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 2.5px;
    padding: 6px 0 10px 0;
    border-bottom: 1px solid var(--border);
    margin: 16px 0 12px 0;
}

/* ── METRİK KARTLARI ───────────────────────────────────── */
.metric-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 16px;
    transition: border-color 0.2s, transform 0.15s;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), transparent);
}
.metric-card:hover {
    border-color: var(--accent);
    transform: translateY(-1px);
}
.metric-label {
    font-family: var(--mono);
    font-size: 0.62em;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 4px;
}
.metric-value {
    font-family: var(--mono);
    font-size: 1.15em;
    font-weight: 700;
    color: #fff;
    line-height: 1.2;
}
.metric-delta-pos { color: var(--green); font-size: 0.75em; font-family: var(--mono); margin-top: 2px; }
.metric-delta-neg { color: var(--red);   font-size: 0.75em; font-family: var(--mono); margin-top: 2px; }
.metric-delta-neu { color: var(--muted); font-size: 0.75em; font-family: var(--mono); margin-top: 2px; }

/* ── BTC HEROCard ──────────────────────────────────────── */
.btc-hero {
    background: linear-gradient(135deg, #0b1e38 0%, #0d2848 100%);
    border: 1px solid #1e3d6b;
    border-radius: 14px;
    padding: 24px 28px;
    position: relative;
    overflow: hidden;
}
.btc-hero::after {
    content: '₿';
    position: absolute;
    right: 20px; top: 10px;
    font-size: 6em;
    color: rgba(0,229,255,0.05);
    font-weight: 700;
}
.btc-hero .price {
    font-family: var(--mono);
    font-size: 2.6em;
    font-weight: 700;
    color: #fff;
    line-height: 1;
}
.btc-hero .sub { color: var(--muted); font-size: 0.8em; margin-top: 4px; font-family: var(--mono); }

/* ── SINYAL BADGE'LERİ ─────────────────────────────────── */
.signal-long {
    background: rgba(0,255,136,0.12);
    border: 1px solid var(--green);
    color: var(--green);
    font-family: var(--mono);
    font-size: 0.72em;
    padding: 4px 10px;
    border-radius: 6px;
    display: inline-block;
    font-weight: 700;
}
.signal-short {
    background: rgba(255,59,92,0.12);
    border: 1px solid var(--red);
    color: var(--red);
    font-family: var(--mono);
    font-size: 0.72em;
    padding: 4px 10px;
    border-radius: 6px;
    display: inline-block;
    font-weight: 700;
}
.signal-neutral {
    background: rgba(255,214,0,0.10);
    border: 1px solid var(--yellow);
    color: var(--yellow);
    font-family: var(--mono);
    font-size: 0.72em;
    padding: 4px 10px;
    border-radius: 6px;
    display: inline-block;
    font-weight: 700;
}

/* ── DUVAR GÖSTERGESİ ──────────────────────────────────── */
.wall-bar-container {
    background: var(--bg3);
    border-radius: 8px;
    padding: 14px 16px;
    border: 1px solid var(--border);
    margin-top: 8px;
}
.wall-label { font-family: var(--mono); font-size: 0.65em; color: var(--muted); letter-spacing: 1px; }
.wall-price { font-family: var(--mono); font-size: 1.05em; font-weight: 700; }

/* ── HABER KARTI ───────────────────────────────────────── */
.news-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    transition: border-color 0.2s;
}
.news-card:hover { border-color: var(--accent2); }
.news-card a { color: #e0eef8; text-decoration: none; font-size: 0.88em; font-family: var(--sans); font-weight: 600; }
.news-card a:hover { color: var(--accent); }
.news-meta { color: var(--muted); font-size: 0.72em; margin-top: 5px; font-family: var(--mono); }

/* ── RAPOR KUTUSU ──────────────────────────────────────── */
.report-box {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px 28px;
    line-height: 1.8;
    font-size: 0.9em;
    font-family: var(--sans);
}

/* ── TABS ──────────────────────────────────────────────── */
[data-testid="stTab"] {
    font-family: var(--mono) !important;
    font-size: 0.78em !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
}

/* ── BUTON ─────────────────────────────────────────────── */
.stButton button {
    background: linear-gradient(135deg, var(--accent), #0099bb) !important;
    color: #000 !important;
    font-family: var(--mono) !important;
    font-weight: 700 !important;
    font-size: 0.8em !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 12px 20px !important;
    letter-spacing: 1px !important;
    transition: opacity 0.2s !important;
    width: 100% !important;
}
.stButton button:hover { opacity: 0.85 !important; }

/* Metric override — Streamlit'in kendi metric bileşeni */
[data-testid="metric-container"] {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 12px 14px !important;
}
[data-testid="stMetricLabel"] { 
    font-family: var(--mono) !important;
    font-size: 0.62em !important;
    color: var(--muted) !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
}
[data-testid="stMetricValue"] {
    font-family: var(--mono) !important;
    font-size: 1.05em !important;
    color: #fff !important;
}
[data-testid="stMetricDelta"] { font-family: var(--mono) !important; font-size: 0.78em !important; }

/* Sidebar text */
[data-testid="stSidebar"] * { font-family: var(--sans) !important; }
[data-testid="stSidebar"] .stMarkdown p { font-size: 0.82em !important; color: var(--muted) !important; }

/* Divider */
hr { border-color: var(--border) !important; margin: 16px 0 !important; }
</style>
""", unsafe_allow_html=True)

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


# ============================================================
#  YARDIMCI: HTML METRİK KARTI
# ============================================================
def mcard(label: str, value: str, delta: str = "", accent_color: str = "--accent"):
    if delta and delta not in ("—", ""):
        try:
            raw = float(delta.replace("%", "").replace(",", ".").strip())
            cls = "metric-delta-pos" if raw >= 0 else "metric-delta-neg"
            arrow = "▲" if raw >= 0 else "▼"
            delta_html = f'<div class="{cls}">{arrow} {delta}</div>'
        except Exception:
            delta_html = f'<div class="metric-delta-neu">{delta}</div>'
    elif delta:
        delta_html = f'<div class="metric-delta-neu">{delta}</div>'
    else:
        delta_html = ""

    return f"""
    <div class="metric-card" style="--card-accent: var({accent_color});">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """


def render_cards(items, cols=4, accent="--accent"):
    """items = [(label, value, delta), ...]"""
    columns = st.columns(cols)
    for i, item in enumerate(items):
        label = item[0]
        value = item[1] if len(item) > 1 else "—"
        delta = item[2] if len(item) > 2 else ""
        with columns[i % cols]:
            st.markdown(mcard(label, value, delta, accent), unsafe_allow_html=True)


def cat(title: str, icon: str = ""):
    st.markdown(f'<div class="cat-header">{icon}&nbsp; {title}</div>', unsafe_allow_html=True)


# ============================================================
#  VERİ MOTORU — cache'li (3dk)
# ============================================================
@st.cache_data(ttl=180)
def veri_motoru():
    v = {}

    # 1. BTC
    try:
        r = requests.get("https://api.coinpaprika.com/v1/tickers/btc-bitcoin",
                         headers=HEADERS, timeout=8).json()
        q = r["quotes"]["USD"]
        v["BTC_P"]   = f"${q['price']:,.0f}"
        v["BTC_C"]   = f"{q['percent_change_24h']:.2f}%"
        v["BTC_7D"]  = f"{q['percent_change_7d']:.2f}%"
        v["Vol_24h"] = f"${q['volume_24h']:,.0f}"
        v["BTC_MCap"]= f"${q['market_cap']/1e9:.0f}B"
    except:
        v["BTC_P"]="—"; v["BTC_C"]="—"; v["BTC_7D"]="—"; v["Vol_24h"]="—"; v["BTC_MCap"]="—"

    # 2. Altcoinler
    alt_ids = {
        "ETH":"eth-ethereum","SOL":"sol-solana","BNB":"bnb-binance-coin",
        "XRP":"xrp-xrp","ADA":"ada-cardano","AVAX":"avax-avalanche",
        "DOT":"dot-polkadot","LINK":"link-chainlink"
    }
    for sym, cid in alt_ids.items():
        try:
            r = requests.get(f"https://api.coinpaprika.com/v1/tickers/{cid}",
                             headers=HEADERS, timeout=6).json()
            q = r["quotes"]["USD"]
            v[f"{sym}_P"]  = f"${q['price']:,.2f}"
            v[f"{sym}_C"]  = f"{q['percent_change_24h']:.2f}%"
            v[f"{sym}_7D"] = f"{q['percent_change_7d']:.2f}%"
        except:
            v[f"{sym}_P"]="—"; v[f"{sym}_C"]="—"; v[f"{sym}_7D"]="—"

    # 3. Global piyasa (Coinpaprika)
    try:
        g = requests.get("https://api.coinpaprika.com/v1/global", headers=HEADERS, timeout=6).json()
        v["Dom"]        = f"%{g['bitcoin_dominance_percentage']:.2f}"
        v["Total_MCap"] = f"${g['market_cap_usd']/1e12:.2f}T"
        v["Total_Vol"]  = f"${g['volume_24h_usd']/1e9:.1f}B"
    except:
        v["Dom"]="—"; v["Total_MCap"]="—"; v["Total_Vol"]="—"

    # ETH dominance
    try:
        eth = requests.get("https://api.coinpaprika.com/v1/tickers/eth-ethereum",
                           headers=HEADERS, timeout=5).json()
        dom_val = float(v["Dom"].replace("%","")) if v["Dom"] != "—" else 0
        btc_mc  = float(v["BTC_MCap"].replace("$","").replace("B",""))*1e9 if v["BTC_MCap"] != "—" else 0
        total_mc= btc_mc / (dom_val/100) if dom_val > 0 else 0
        if total_mc > 0:
            v["ETH_Dom"] = f"%{float(eth['quotes']['USD']['market_cap'])/total_mc*100:.2f}"
        else:
            v["ETH_Dom"] = "—"
    except:
        v["ETH_Dom"] = "—"

    # 4. BTC ETF (yFinance)
    for sym in ["IBIT","FBTC","BITB","ARKB"]:
        try:
            df   = yf.Ticker(sym).history(period="10d")
            if df.empty: raise ValueError
            curr = df["Close"].iloc[-1]; prev = df["Close"].iloc[-2]
            v[f"{sym}_P"]   = f"${curr:.2f}"
            v[f"{sym}_C"]   = f"{(curr-prev)/prev*100:.2f}%"
            v[f"{sym}_Vol"] = f"{int(df['Volume'].iloc[-1]):,}"
            if sym == "IBIT":
                flow = int(df["Volume"].iloc[-1]) * (curr - prev)
                v["IBIT_Flow"] = f"{'📈 +' if flow>0 else '📉 '}{abs(flow/1e6):.1f}M $"
        except:
            v[f"{sym}_P"]="—"; v[f"{sym}_C"]="—"; v[f"{sym}_Vol"]="—"
    if "IBIT_Flow" not in v: v["IBIT_Flow"]="—"

    # 5. Hisse endeksleri
    endeksler = {
        "SP500":"^GSPC","NASDAQ":"^IXIC","DOW":"^DJI","DAX":"^GDAXI",
        "FTSE":"^FTSE","NIKKEI":"^N225","HSI":"^HSI","BIST100":"XU100.IS","VIX":"^VIX"
    }
    for key, sym in endeksler.items():
        try:
            df   = yf.Ticker(sym).history(period="5d")
            curr = df["Close"].iloc[-1]; prev = df["Close"].iloc[-2]
            v[key]          = f"{curr:,.2f}"
            v[f"{key}_C"]   = f"{(curr-prev)/prev*100:.2f}%"
        except:
            v[key]="—"; v[f"{key}_C"]="—"

    # 6. Emtialar
    emtialar = {"GOLD":"GC=F","SILVER":"SI=F","OIL":"CL=F","NATGAS":"NG=F","COPPER":"HG=F","WHEAT":"ZW=F"}
    for key, sym in emtialar.items():
        try:
            df   = yf.Ticker(sym).history(period="5d")
            curr = df["Close"].iloc[-1]; prev = df["Close"].iloc[-2]
            v[key]        = f"${curr:,.2f}"
            v[f"{key}_C"] = f"{(curr-prev)/prev*100:.2f}%"
        except:
            v[key]="—"; v[f"{key}_C"]="—"

    # 7. Forex + makro faiz
    forex = {
        "DXY":"DX-Y.NYB","EURUSD":"EURUSD=X","GBPUSD":"GBPUSD=X",
        "USDJPY":"JPY=X","USDTRY":"TRY=X","USDCHF":"CHF=X",
        "AUDUSD":"AUDUSD=X","US10Y":"^TNX"
    }
    for key, sym in forex.items():
        try:
            df   = yf.Ticker(sym).history(period="5d")
            curr = df["Close"].iloc[-1]; prev = df["Close"].iloc[-2]
            v[key]        = f"{curr:.4f}"
            v[f"{key}_C"] = f"{(curr-prev)/prev*100:.2f}%"
        except:
            v[key]="—"; v[f"{key}_C"]="—"

    # 8. BTC Korelasyon (30 gün)
    try:
        cd = yf.download(["BTC-USD","^GSPC","GC=F"], period="30d", progress=False)["Close"]
        cm = cd.corr()
        v["Corr_SP500"] = round(cm.loc["BTC-USD","^GSPC"], 2)
        v["Corr_Gold"]  = round(cm.loc["BTC-USD","GC=F"],  2)
    except:
        v["Corr_SP500"]="—"; v["Corr_Gold"]="—"

    # 9. Balina duvarları (Kraken)
    try:
        ob  = requests.get("https://api.kraken.com/0/public/Depth?pair=XBTUSD&count=500", timeout=8).json()
        pk  = list(ob["result"].keys())[0]
        bids= [(float(p),float(q)) for p,q,_ in ob["result"][pk]["bids"]]
        asks= [(float(p),float(q)) for p,q,_ in ob["result"][pk]["asks"]]
        cur = bids[0][0]; noise=250; bs=100
        fb  = [(p,q) for p,q in bids if p<cur-noise] or bids[len(bids)//2:]
        fa  = [(p,q) for p,q in asks if p>cur+noise] or asks[len(asks)//2:]
        def bkt(data, fn):
            d={}
            for p,q in data: k=fn(p); d[k]=d.get(k,0)+q
            return max(d.items(), key=lambda x: x[1])
        sw,sv = bkt(fb, lambda p: int(p/bs)*bs)
        rw,rv = bkt(fa, lambda p: int((p/bs)+1)*bs)
        v["Sup_Wall"]    = f"${sw:,}"
        v["Sup_Vol"]     = f"{int(sv):,} BTC"
        v["Res_Wall"]    = f"${rw:,}"
        v["Res_Vol"]     = f"{int(rv):,} BTC"
        ds = cur - sw; dr = rw - cur
        v["Wall_Status"] = ("🔴 Dirence Yakın" if dr < ds else
                            ("🟢 Desteğe Yakın" if ds < dr else "⚖️ Kanal Ortası"))
        v["BTC_Now"]     = f"${cur:,.0f}"
    except:
        v["Sup_Wall"]="—"; v["Sup_Vol"]="—"; v["Res_Wall"]="—"; v["Res_Vol"]="—"
        v["Wall_Status"]="—"; v["BTC_Now"]="—"

    # 10. Stablecoin (DeFiLlama)
    try:
        sc    = requests.get("https://stablecoins.llama.fi/stablecoins?includePrices=true",
                             headers=HEADERS, timeout=8).json()["peggedAssets"]
        total = sum(c.get("circulating",{}).get("peggedUSD",0) for c in sc)
        def gcap(sym):
            c = next((x for x in sc if x["symbol"].upper()==sym), None)
            return c["circulating"]["peggedUSD"] if c else 0
        usdt_c = gcap("USDT"); usdc_c = gcap("USDC"); dai_c = gcap("DAI")
        v["Total_Stable"]   = f"${total/1e9:.1f}B"
        v["USDT_MCap"]      = f"${usdt_c/1e9:.1f}B"
        v["USDC_MCap"]      = f"${usdc_c/1e9:.1f}B"
        v["DAI_MCap"]       = f"${dai_c/1e9:.1f}B"
        v["USDT_Dom_Stable"]= f"%{usdt_c/total*100:.1f}" if total > 0 else "—"
    except:
        v["Total_Stable"]="—"; v["USDT_MCap"]="—"; v["USDC_MCap"]="—"
        v["DAI_MCap"]="—"; v["USDT_Dom_Stable"]="—"

    # USDT.D — CoinGecko
    try:
        cg_g = requests.get("https://api.coingecko.com/api/v3/global",
                            headers=HEADERS, timeout=6).json()["data"]
        v["USDT_D"] = f"%{cg_g['market_cap_percentage']['usdt']:.2f}"
    except:
        try:
            cg2 = requests.get("https://api.coinpaprika.com/v1/global",
                               headers=HEADERS, timeout=6).json()
            total_mc = cg2["market_cap_usd"]
            ur = requests.get("https://api.coinpaprika.com/v1/tickers/usdt-tether",
                              headers=HEADERS, timeout=6).json()
            v["USDT_D"] = f"%{ur['quotes']['USD']['market_cap']/total_mc*100:.2f}"
        except:
            v["USDT_D"] = "—"

    # OI + FR + L/S (placeholder — turev_cek() ile doldurulacak)
    v["OI"]="—"; v["FR"]="—"; v["Taker"]="—"
    v["LS_Ratio"]="—"; v["Long_Pct"]="—"; v["Short_Pct"]="—"; v["LS_Signal"]="—"

    # 11. FRED (M2, FED)
    try:
        m2 = requests.get(
            f"https://api.stlouisfed.org/fred/series/observations?series_id=M2SL"
            f"&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=13",
            timeout=6).json()["observations"]
        v["M2"] = f"%{(float(m2[0]['value'])-float(m2[12]['value']))/float(m2[12]['value'])*100:.2f}"
    except:
        v["M2"] = "—"
    try:
        fed = requests.get(
            f"https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS"
            f"&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=1",
            timeout=6).json()["observations"]
        v["FED"] = f"%{fed[0]['value']}"
    except:
        v["FED"] = "—"

    # 12. On-chain (Blockchain.info)
    try:
        s = requests.get("https://api.blockchain.info/stats", timeout=5).json()
        v["Hash"] = f"{s['hash_rate']/1e9:.2f} EH/s"
        v["Active"] = f"{s['n_blocks_mined']*2100:,}"
    except:
        v["Hash"]="—"; v["Active"]="—"

    # 13. Korku/Açgözlülük
    try:
        fng = requests.get("https://api.alternative.me/fng/?limit=2", timeout=5).json()["data"]
        v["FNG"]      = f"{fng[0]['value']} ({fng[0]['value_classification']})"
        v["FNG_PREV"] = f"{fng[1]['value']} ({fng[1]['value_classification']})"
        v["FNG_NUM"]  = int(fng[0]["value"])
    except:
        v["FNG"]="—"; v["FNG_PREV"]="—"; v["FNG_NUM"]=0

    # 14. Haberler (CoinDesk RSS)
    try:
        rss    = requests.get("https://www.coindesk.com/arc/outboundfeeds/rss/",
                              headers=HEADERS, timeout=8).text
        titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", rss)[1:11]
        links  = re.findall(r"<link>(https://www\.coindesk\.com.*?)</link>", rss)[:10]
        dates  = re.findall(r"<pubDate>(.*?)</pubDate>", rss)[:10]
        v["NEWS"] = [
            {"title": t, "url": links[i] if i<len(links) else "#",
             "source": "CoinDesk", "time": dates[i][:16] if i<len(dates) else ""}
            for i, t in enumerate(titles)
        ]
    except:
        try:
            nr = requests.get(
                "https://min-api.cryptocompare.com/data/v2/news/?lang=EN&sortOrder=latest&limit=10",
                headers=HEADERS, timeout=6).json()
            v["NEWS"] = [
                {"title": n["title"], "url": n["url"], "source": n["source_info"]["name"],
                 "time": pd.Timestamp(n["published_on"], unit="s").strftime("%d %b %H:%M")}
                for n in nr["Data"][:10]
            ]
        except:
            v["NEWS"] = []

    return v


# ============================================================
#  TÜREV VERİLERİ — cache'siz, her yüklemede taze
# ============================================================
def turev_cek():
    t = {}

    # OI + FR (OKX)
    try:
        fr_r = requests.get(
            "https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP",
            headers=HEADERS, timeout=6).json()
        t["FR"] = f"%{float(fr_r['data'][0]['fundingRate'])*100:.4f}"
    except:
        t["FR"] = "—"
    try:
        oi_r = requests.get(
            "https://www.okx.com/api/v5/public/open-interest?instType=SWAP&instId=BTC-USDT-SWAP",
            headers=HEADERS, timeout=6).json()
        t["OI"] = f"{float(oi_r['data'][0]['oi']):,.0f} BTC"
    except:
        t["OI"] = "—"

    # Taker B/S (OKX)
    try:
        tk = requests.get(
            "https://www.okx.com/api/v5/rubik/stat/taker-volume?ccy=BTC&instType=contracts&period=1H",
            headers=HEADERS, timeout=6).json()
        bv = float(tk["data"][0][1]); sv = float(tk["data"][0][2])
        t["Taker"] = f"{bv/sv:.3f}" if sv > 0 else "1.000"
    except:
        t["Taker"] = "1.000"

    # L/S Oranı
    ls_done = False
    for url in [
        "https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio-contract-top-trader?instId=BTC-USDT-SWAP&period=1H",
        "https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio?ccy=BTC&period=1H"
    ]:
        if ls_done: break
        try:
            r = requests.get(url, headers=HEADERS, timeout=6).json()
            d = r.get("data", [])
            if not d: continue
            d0  = d[0]
            if isinstance(d0, dict) and "longRatio" in d0:
                lp    = float(d0["longRatio"])*100
                sp    = float(d0["shortRatio"])*100
                ratio = lp/sp if sp > 0 else 1
            else:
                ratio = float(d0[1]) if isinstance(d0, list) else 1
                lp    = ratio/(1+ratio)*100
                sp    = 100-lp
            t["LS_Ratio"]  = f"{ratio:.3f}"
            t["Long_Pct"]  = f"%{lp:.1f}"
            t["Short_Pct"] = f"%{sp:.1f}"
            t["LS_Signal"] = "🟢 Long Ağırlıklı" if ratio > 1 else "🔴 Short Ağırlıklı"
            ls_done = True
        except: pass

    if not ls_done:
        try:
            gate = requests.get(
                "https://api.gateio.ws/api/v4/futures/usdt/contract_stats?contract=BTC_USDT&interval=1h&limit=1",
                headers=HEADERS, timeout=6).json()
            lp    = float(gate[0].get("lsr_taker",1))
            lp_pct= lp/(1+lp)*100
            t["LS_Ratio"]  = f"{lp:.3f}"
            t["Long_Pct"]  = f"%{lp_pct:.1f}"
            t["Short_Pct"] = f"%{100-lp_pct:.1f}"
            t["LS_Signal"] = "🟢 Long Ağırlıklı" if lp > 1 else "🔴 Short Ağırlıklı"
            ls_done = True
        except: pass

    if not ls_done:
        t["LS_Ratio"]="—"; t["Long_Pct"]="—"; t["Short_Pct"]="—"; t["LS_Signal"]="—"

    return t


# ============================================================
#  SAYFA YÜKLEMESİ
# ============================================================
# Header
st.markdown("""
<div class="terminal-header">
    <span class="status-dot"></span>
    <h1>⚡ Serhat Alpha Terminal</h1>
    <span class="badge">v17.0</span>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🛰️ Kontrol Merkezi")
    st.divider()

    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    son_guncelleme = pd.Timestamp.now(tz="Europe/Istanbul").strftime("%d.%m.%Y %H:%M:%S")
    st.caption(f"⏱️ **Son güncelleme:** {son_guncelleme}")
    st.divider()

    with st.spinner("Veriler yükleniyor..."):
        data  = veri_motoru()
        turev = turev_cek()
        data.update(turev)

    df_exp = pd.DataFrame([(k,v) for k,v in data.items() if k!="NEWS"], columns=["Metrik","Değer"])
    csv    = df_exp.to_csv(index=False, sep=";").encode("utf-8-sig")
    st.download_button(
        "💾 CSV İndir", csv,
        file_name=f"AlphaTerminal_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv", use_container_width=True
    )
    st.divider()
    st.markdown("""
**Veri Kaynakları:**  
`Coinpaprika` · `Kraken`  
`DeFiLlama` · `yFinance`  
`OKX` · `FRED` · `CoinDesk`

**Model:** `Gemini 2.0 Flash`  
**Cache:** 3 dk | Türev: Canlı
""")

# Tab yapısı
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "₿  BİTCOİN & KRİPTO",
    "🌍  MAKRO & PİYASALAR",
    "📊  GRAFİK & RAPOR",
    "📰  HABERLER",
    "⚙️  TÜM METRİKLER"
])


# ── TAB 1: BİTCOİN & KRİPTO ─────────────────────────────────
with tab1:

    # BTC HERO
    btc_c = data.get("BTC_C","")
    try:
        btc_num = float(btc_c.replace("%",""))
        btc_color = "var(--green)" if btc_num >= 0 else "var(--red)"
        btc_arrow = "▲" if btc_num >= 0 else "▼"
    except:
        btc_color = "var(--muted)"; btc_arrow = ""

    st.markdown(f"""
    <div class="btc-hero">
        <div class="metric-label">BITCOIN / USD — CANLI FİYAT</div>
        <div class="price">{data.get('BTC_P','—')}</div>
        <div class="sub">
            <span style="color:{btc_color}; font-weight:700;">{btc_arrow} 24s: {btc_c}</span>
            &nbsp;·&nbsp; 7g: {data.get('BTC_7D','—')}
            &nbsp;·&nbsp; Hacim: {data.get('Vol_24h','—')}
            &nbsp;·&nbsp; MCap: {data.get('BTC_MCap','—')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── BÖLÜM A: Piyasa Genel Görünüm ─────────────────────
    cat("PIYASA GENEL GÖRÜNÜM", "📡")
    render_cards([
        ("Toplam Market Cap",  data.get("Total_MCap"), ""),
        ("BTC Dominance",      data.get("Dom"),        ""),
        ("ETH Dominance",      data.get("ETH_Dom"),    ""),
        ("Korku / Açgözlülük", data.get("FNG"),        ""),
        ("Total Piyasa Hacim", data.get("Total_Vol"),  ""),
        ("24s BTC Hacim",      data.get("Vol_24h"),    ""),
    ], cols=3)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── BÖLÜM B: Türev Piyasalar (Sentiment) ───────────────
    cat("TÜREV PİYASALAR & SENTİMENT", "📊")

    # L/S sinyali büyük göster
    ls_signal = data.get("LS_Signal","—")
    if "Long" in ls_signal:
        sig_cls = "signal-long"
    elif "Short" in ls_signal:
        sig_cls = "signal-short"
    else:
        sig_cls = "signal-neutral"

    fr_val = data.get("FR","—")
    try:
        fr_num = float(fr_val.replace("%",""))
        fr_badge = "signal-long" if fr_num > 0 else ("signal-short" if fr_num < 0 else "signal-neutral")
        fr_label = "Pozitif (Long favori)" if fr_num > 0 else ("Negatif (Short favori)" if fr_num < 0 else "Nötr")
    except:
        fr_badge = "signal-neutral"; fr_label = ""

    col_ls, col_fr, col_oi = st.columns(3)
    with col_ls:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Long / Short Sinyali</div>
            <div class="metric-value" style="margin-top:6px">
                <span class="{sig_cls}">{ls_signal}</span>
            </div>
            <div class="metric-delta-neu" style="margin-top:8px">
                Oran: {data.get('LS_Ratio','—')} &nbsp;|&nbsp;
                L: {data.get('Long_Pct','—')} &nbsp;S: {data.get('Short_Pct','—')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_fr:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Funding Rate (OKX)</div>
            <div class="metric-value" style="margin-top:6px">
                <span class="{fr_badge}">{fr_val}</span>
            </div>
            <div class="metric-delta-neu" style="margin-top:8px">{fr_label}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_oi:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Open Interest + Taker B/S</div>
            <div class="metric-value">{data.get('OI','—')}</div>
            <div class="metric-delta-neu" style="margin-top:4px">Taker B/S: {data.get('Taker','—')}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── BÖLÜM C: Balina Duvarları ──────────────────────────
    cat("BALİNA DUVARLARI — ORDER BOOK ANALİZİ (Kraken)", "🐋")

    wall_status = data.get("Wall_Status","—")
    ws_cls = "signal-long" if "Destek" in wall_status else ("signal-short" if "Direnç" in wall_status else "signal-neutral")

    col_ws, col_sup, col_res = st.columns(3)
    with col_ws:
        st.markdown(f"""
        <div class="metric-card" style="text-align:center; padding:20px;">
            <div class="metric-label">Tahta Durumu</div>
            <div style="margin-top:10px">
                <span class="{ws_cls}" style="font-size:0.9em;">{wall_status}</span>
            </div>
            <div class="metric-delta-neu" style="margin-top:8px">Mevcut: {data.get('BTC_Now','—')}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_sup:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🟢 Ana Destek Duvarı</div>
            <div class="metric-value" style="color:var(--green)">{data.get('Sup_Wall','—')}</div>
            <div class="metric-delta-neu" style="margin-top:4px">📦 {data.get('Sup_Vol','—')} bekliyor</div>
        </div>
        """, unsafe_allow_html=True)
    with col_res:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🔴 Ana Direnç Duvarı</div>
            <div class="metric-value" style="color:var(--red)">{data.get('Res_Wall','—')}</div>
            <div class="metric-delta-neu" style="margin-top:4px">📦 {data.get('Res_Vol','—')} bekliyor</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── BÖLÜM D: Bitcoin ETF & Kurumsal Akışlar ────────────
    cat("BİTCOİN ETF — KURUMSAL AKIŞ TAKIBI", "🏦")
    col_ibit, col_diğer = st.columns([1, 2])
    with col_ibit:
        st.markdown(f"""
        <div class="metric-card" style="border-color:#1e3d6b;">
            <div class="metric-label">IBIT — BlackRock (Lider ETF)</div>
            <div class="metric-value">{data.get('IBIT_P','—')} <span style="font-size:0.7em; color:{'var(--green)' if '+' in data.get('IBIT_C','') else 'var(--red)'};">{data.get('IBIT_C','')}</span></div>
            <div class="metric-delta-neu" style="margin-top:6px">Akış: {data.get('IBIT_Flow','—')}</div>
            <div class="metric-delta-neu">Hacim: {data.get('IBIT_Vol','—')}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_diğer:
        render_cards([
            ("FBTC — Fidelity", data.get("FBTC_P","—"), data.get("FBTC_C","")),
            ("BITB — Bitwise",  data.get("BITB_P","—"), data.get("BITB_C","")),
            ("ARKB — ARK Invest",data.get("ARKB_P","—"),data.get("ARKB_C","")),
        ], cols=3)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── BÖLÜM E: Stablecoin Likiditesi ────────────────────
    cat("STABLECOİN LİKİDİTESİ — DEFILLLAMA", "💵")
    render_cards([
        ("Toplam Stablecoin",    data.get("Total_Stable","—"), ""),
        ("USDT Market Cap",      data.get("USDT_MCap","—"),    ""),
        ("USDC Market Cap",      data.get("USDC_MCap","—"),    ""),
        ("DAI Market Cap",       data.get("DAI_MCap","—"),     ""),
        ("USDT.D (Piyasa %)",    data.get("USDT_D","—"),       ""),
        ("USDT Dom (Stable %)",  data.get("USDT_Dom_Stable","—"),""),
    ], cols=3)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── BÖLÜM F: Altcoinler ────────────────────────────────
    cat("ALTKOIN FİYATLARI & PERFORMANS", "🪙")
    render_cards([
        ("Ethereum (ETH)",    data.get("ETH_P","—"),  data.get("ETH_C","")),
        ("Solana (SOL)",      data.get("SOL_P","—"),  data.get("SOL_C","")),
        ("BNB Chain (BNB)",   data.get("BNB_P","—"),  data.get("BNB_C","")),
        ("Ripple (XRP)",      data.get("XRP_P","—"),  data.get("XRP_C","")),
        ("Cardano (ADA)",     data.get("ADA_P","—"),  data.get("ADA_C","")),
        ("Avalanche (AVAX)",  data.get("AVAX_P","—"), data.get("AVAX_C","")),
        ("Polkadot (DOT)",    data.get("DOT_P","—"),  data.get("DOT_C","")),
        ("Chainlink (LINK)",  data.get("LINK_P","—"), data.get("LINK_C","")),
    ], cols=4)

    # 7 günlük performans karşılaştırması
    st.markdown("<div style='margin-top:12px; margin-bottom:4px;'>", unsafe_allow_html=True)
    cat("7 GÜNLÜK PERFORMANS", "📅")
    render_cards([
        ("ETH 7g",  data.get("ETH_7D","—"),  ""),
        ("SOL 7g",  data.get("SOL_7D","—"),  ""),
        ("BNB 7g",  data.get("BNB_7D","—"),  ""),
        ("XRP 7g",  data.get("XRP_7D","—"),  ""),
        ("ADA 7g",  data.get("ADA_7D","—"),  ""),
        ("AVAX 7g", data.get("AVAX_7D","—"), ""),
        ("DOT 7g",  data.get("DOT_7D","—"),  ""),
        ("LINK 7g", data.get("LINK_7D","—"), ""),
    ], cols=4)
    st.markdown("</div>", unsafe_allow_html=True)


# ── TAB 2: MAKRO & PİYASALAR ─────────────────────────────────
with tab2:

    # ── BÖLÜM A: Makro Para Politikası ────────────────────
    cat("MAKRO PARA POLİTİKASI", "🏦")
    render_cards([
        ("FED Faiz Oranı",   data.get("FED","—"),       ""),
        ("M2 Büyümesi (YoY)",data.get("M2","—"),        ""),
        ("ABD 10Y Tahvil",   data.get("US10Y","—"),     data.get("US10Y_C","")),
        ("DXY Dolar Endeksi",data.get("DXY","—"),       data.get("DXY_C","")),
        ("VIX Volatilite",   data.get("VIX","—"),       data.get("VIX_C","")),
        ("BTC ↔ S&P500 Kor.",str(data.get("Corr_SP500","—")), ""),
        ("BTC ↔ Altın Kor.", str(data.get("Corr_Gold","—")),  ""),
    ], cols=4)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── BÖLÜM B: Global Hisse Endeksleri ──────────────────
    cat("GLOBAL HİSSE SENEDİ ENDEKSLERİ", "📈")
    col_us, col_eu, col_asia = st.columns(3)
    with col_us:
        st.markdown('<div class="metric-label" style="margin-bottom:8px;">🇺🇸 AMERİKA</div>', unsafe_allow_html=True)
        render_cards([
            ("S&P 500",  data.get("SP500","—"),  data.get("SP500_C","")),
            ("NASDAQ",   data.get("NASDAQ","—"), data.get("NASDAQ_C","")),
            ("Dow Jones",data.get("DOW","—"),    data.get("DOW_C","")),
        ], cols=1)
    with col_eu:
        st.markdown('<div class="metric-label" style="margin-bottom:8px;">🇪🇺 AVRUPA</div>', unsafe_allow_html=True)
        render_cards([
            ("DAX (Almanya)",   data.get("DAX","—"),    data.get("DAX_C","")),
            ("FTSE 100 (UK)",   data.get("FTSE","—"),   data.get("FTSE_C","")),
            ("BIST 100 (TÜRKİYE)", data.get("BIST100","—"),data.get("BIST100_C","")),
        ], cols=1)
    with col_asia:
        st.markdown('<div class="metric-label" style="margin-bottom:8px;">🌏 ASYA</div>', unsafe_allow_html=True)
        render_cards([
            ("Nikkei 225 (JP)", data.get("NIKKEI","—"), data.get("NIKKEI_C","")),
            ("Hang Seng (HK)",  data.get("HSI","—"),    data.get("HSI_C","")),
        ], cols=1)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── BÖLÜM C: Emtialar ─────────────────────────────────
    cat("EMTİALAR — GLOBAL HAM MADDE", "🏭")
    col_metal, col_enerji = st.columns(2)
    with col_metal:
        st.markdown('<div class="metric-label" style="margin-bottom:8px;">METALLER</div>', unsafe_allow_html=True)
        render_cards([
            ("Altın / oz",  data.get("GOLD","—"),   data.get("GOLD_C","")),
            ("Gümüş / oz",  data.get("SILVER","—"), data.get("SILVER_C","")),
            ("Bakır",       data.get("COPPER","—"),  data.get("COPPER_C","")),
        ], cols=1)
    with col_enerji:
        st.markdown('<div class="metric-label" style="margin-bottom:8px;">ENERJİ & TARIM</div>', unsafe_allow_html=True)
        render_cards([
            ("Ham Petrol (WTI)", data.get("OIL","—"),    data.get("OIL_C","")),
            ("Doğalgaz",         data.get("NATGAS","—"), data.get("NATGAS_C","")),
            ("Buğday",           data.get("WHEAT","—"),  data.get("WHEAT_C","")),
        ], cols=1)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── BÖLÜM D: Forex ────────────────────────────────────
    cat("DÖVİZ KURLARI", "💱")
    render_cards([
        ("EUR / USD",    data.get("EURUSD","—"),  data.get("EURUSD_C","")),
        ("GBP / USD",    data.get("GBPUSD","—"),  data.get("GBPUSD_C","")),
        ("USD / JPY",    data.get("USDJPY","—"),  data.get("USDJPY_C","")),
        ("USD / CHF",    data.get("USDCHF","—"),  data.get("USDCHF_C","")),
        ("AUD / USD",    data.get("AUDUSD","—"),  data.get("AUDUSD_C","")),
        ("USD / TRY",    data.get("USDTRY","—"),  data.get("USDTRY_C","")),
    ], cols=3)


# ── TAB 3: GRAFİK & RAPOR ────────────────────────────────────
with tab3:
    col_chart, col_side = st.columns([2.2, 1.2])
    with col_chart:
        st.subheader("📊 Canlı BTC/USDT Grafiği")
        components.html("""
        <div style="height:520px;">
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>new TradingView.widget({autosize:true,symbol:"BINANCE:BTCUSDT",
        interval:"D",theme:"dark",style:"1",locale:"tr",toolbar_bg:"#070d1a",
        container_id:"tv_main"});</script>
        <div id="tv_main" style="height:100%;"></div></div>""", height=540)

    with col_side:
        st.subheader("📅 Ekonomik Takvim")
        components.html("""
        <div class="tradingview-widget-container">
        <div class="tradingview-widget-container__widget"></div>
        <script src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
        {"colorTheme":"dark","isTransparent":true,"width":"100%","height":"480",
        "locale":"tr","importanceFilter":"0,1","currencyFilter":"USD,EUR"}</script></div>""", height=500)

        st.divider()
        st.subheader("🤖 God Mode Strateji Raporu")
        if st.button("🚀 AI RAPORU OLUŞTUR", use_container_width=True):
            with st.spinner("Gemini 2.5 Flash analiz ediyor — derin rapor hazırlanıyor..."):
                bugun = pd.Timestamp.now(tz="Europe/Istanbul").strftime("%d %B %Y, %A — %H:%M")
                news_str = "\n".join(f"• {n['title']} ({n['source']})" for n in data.get("NEWS",[])[:6])

                prompt = f"""Sen 20 yıllık deneyime sahip bir makro-kripto fon yöneticisi ve quant analistsin.
Aşağıdaki TÜM gerçek piyasa verilerini kullanarak Serhat için derinlikli, rakamsal ve eyleme dönüşebilir bir strateji raporu yaz.
Türkçe yaz. Rapor profesyonel, yapılandırılmış ve her iddia rakamla desteklenmiş olmalı.

TEMEL KURALLAR:
- Her iddiayı mutlaka rakamla destekle. "VIX yüksek" değil, "VIX {data.get('VIX','—')} seviyesinde" yaz.
- Seviyeleri kesin belirt: "$84,200 kırılırsa..." gibi somut eşikler ver.
- Yüzeysel geçme, her bölüm derinlikli analiz içersin.
- Tüm veri kategorilerini (makro, türev, on-chain, ETF, forex, emtia, altcoin) mutlaka kullan.
- "Dikkatli ol" gibi genel laflar yerine somut aksiyon ver.

YAZIM KURALLARI:
- Asla "bu rapor yatırım tavsiyesi değildir" veya benzeri yasal uyarı yazma.
- Asla LaTeX formatı ($65,000 yerine $65.000 gibi) kullanma, düz metin yaz.
- Markdown formatı kullan: **kalın**, başlıklar için ## kullan.
- Fiyatları her zaman düz yazı olarak yaz: 65000 dolar veya $65,000

━━━━━━━━ CANLI VERİLER ({bugun}) ━━━━━━━━

📌 BİTCOİN:
Fiyat: {data.get('BTC_P','—')} | 24s: {data.get('BTC_C','—')} | 7g: {data.get('BTC_7D','—')}
Hacim 24s: {data.get('Vol_24h','—')} | MCap: {data.get('BTC_MCap','—')}
BTC Dominance: {data.get('Dom','—')} | ETH Dominance: {data.get('ETH_Dom','—')}
Total MCap: {data.get('Total_MCap','—')} | Total Hacim: {data.get('Total_Vol','—')}

📌 TÜREV PİYASALAR:
Open Interest: {data.get('OI','—')}
Funding Rate: {data.get('FR','—')}
Taker Buy/Sell: {data.get('Taker','—')}
Long/Short Oranı: {data.get('LS_Ratio','—')} → {data.get('LS_Signal','—')}
Long %: {data.get('Long_Pct','—')} | Short %: {data.get('Short_Pct','—')}

📌 BALİNA DUVARLARI (Kraken Order Book):
🟢 Destek: {data.get('Sup_Wall','—')} — {data.get('Sup_Vol','—')} bekliyor
🔴 Direnç: {data.get('Res_Wall','—')} — {data.get('Res_Vol','—')} bekliyor
Tahta Durumu: {data.get('Wall_Status','—')}

📌 KORKU & DUYGU:
Fear & Greed Index: {data.get('FNG','—')} (dün: {data.get('FNG_PREV','—')})

📌 BİTCOİN ETF (Kurumsal Akış):
IBIT (BlackRock): {data.get('IBIT_P','—')} | {data.get('IBIT_C','—')} | Akış: {data.get('IBIT_Flow','—')} | Hacim: {data.get('IBIT_Vol','—')}
FBTC (Fidelity): {data.get('FBTC_P','—')} | {data.get('FBTC_C','—')}
BITB (Bitwise): {data.get('BITB_P','—')} | {data.get('BITB_C','—')}
ARKB (ARK): {data.get('ARKB_P','—')} | {data.get('ARKB_C','—')}

📌 STABLECOİN LİKİDİTESİ:
Toplam: {data.get('Total_Stable','—')} | USDT: {data.get('USDT_MCap','—')} | USDC: {data.get('USDC_MCap','—')} | DAI: {data.get('DAI_MCap','—')}
USDT.D (Piyasa %): {data.get('USDT_D','—')} | USDT Dom (Stable içi): {data.get('USDT_Dom_Stable','—')}

📌 ON-CHAIN:
Hashrate: {data.get('Hash','—')} | Aktif Adres (est): {data.get('Active','—')}
BTC ↔ S&P500 Korelasyon (30g): {data.get('Corr_SP500','—')}
BTC ↔ Altın Korelasyon (30g): {data.get('Corr_Gold','—')}

📌 MAKRO PARA POLİTİKASI:
FED Faizi: {data.get('FED','—')} | M2 Büyümesi (YoY): {data.get('M2','—')}
ABD 10Y Tahvil: {data.get('US10Y','—')} ({data.get('US10Y_C','—')})
DXY: {data.get('DXY','—')} ({data.get('DXY_C','—')})
VIX: {data.get('VIX','—')} ({data.get('VIX_C','—')})

📌 GLOBAL HİSSE ENDEKSLERİ:
S&P500: {data.get('SP500','—')} ({data.get('SP500_C','—')})
NASDAQ: {data.get('NASDAQ','—')} ({data.get('NASDAQ_C','—')})
DOW: {data.get('DOW','—')} ({data.get('DOW_C','—')})
DAX: {data.get('DAX','—')} ({data.get('DAX_C','—')})
FTSE: {data.get('FTSE','—')} ({data.get('FTSE_C','—')})
NIKKEI: {data.get('NIKKEI','—')} ({data.get('NIKKEI_C','—')})
BIST100: {data.get('BIST100','—')} ({data.get('BIST100_C','—')})

📌 FOREX:
DXY: {data.get('DXY','—')} | EUR/USD: {data.get('EURUSD','—')} ({data.get('EURUSD_C','—')})
GBP/USD: {data.get('GBPUSD','—')} | USD/JPY: {data.get('USDJPY','—')} ({data.get('USDJPY_C','—')})
USD/TRY: {data.get('USDTRY','—')} ({data.get('USDTRY_C','—')}) | USD/CHF: {data.get('USDCHF','—')}

📌 EMTİALAR:
Altın: {data.get('GOLD','—')} ({data.get('GOLD_C','—')})
Gümüş: {data.get('SILVER','—')} ({data.get('SILVER_C','—')})
Ham Petrol: {data.get('OIL','—')} ({data.get('OIL_C','—')})
Doğalgaz: {data.get('NATGAS','—')} ({data.get('NATGAS_C','—')})
Bakır: {data.get('COPPER','—')} ({data.get('COPPER_C','—')})
Buğday: {data.get('WHEAT','—')} ({data.get('WHEAT_C','—')})

📌 ALTCOİNLER:
ETH: {data.get('ETH_P','—')} | 24s: {data.get('ETH_C','—')} | 7g: {data.get('ETH_7D','—')}
SOL: {data.get('SOL_P','—')} | 24s: {data.get('SOL_C','—')} | 7g: {data.get('SOL_7D','—')}
BNB: {data.get('BNB_P','—')} | 24s: {data.get('BNB_C','—')}
XRP: {data.get('XRP_P','—')} | 24s: {data.get('XRP_C','—')}
ADA: {data.get('ADA_P','—')} | AVAX: {data.get('AVAX_P','—')}
DOT: {data.get('DOT_P','—')} | LINK: {data.get('LINK_P','—')}

📌 SON KRİPTO HABERLERİ:
{news_str if news_str else 'Haber alınamadı'}

━━━━━━━━ RAPOR YAPISI (her bölümü eksiksiz doldur) ━━━━━━━━

**🌍 1. MAKRO ORTAM ANALİZİ**
- SP500 {data.get('SP500_C','—')}, NASDAQ {data.get('NASDAQ_C','—')}, VIX {data.get('VIX','—')} — risk iştahı ne söylüyor?
- DXY {data.get('DXY','—')} ve tahvil faizi {data.get('US10Y','—')} BTC için ne anlam taşıyor?
- M2 {data.get('M2','—')} + FED {data.get('FED','—')}: likidite koşulları gevşiyor mu sıkışıyor mu?
- BTC↔SP500 korelasyon {data.get('Corr_SP500','—')}: hangi yönde kullanılabilir?
- Altın {data.get('GOLD','—')} ve petrol {data.get('OIL','—')} enflasyon/risk sinyali ne veriyor?
- USDTRY {data.get('USDTRY','—')}: TL bazlı yatırımcı için BTC avantajlı mı?

**₿ 2. BİTCOİN TEKNİK & TÜREV ANALİZİ**
- Fiyat {data.get('BTC_P','—')}, hacim {data.get('Vol_24h','—')}, 24s {data.get('BTC_C','—')}, 7g {data.get('BTC_7D','—')} trendini yorumla.
- OI {data.get('OI','—')}: pozisyon birikimi tehlikeli seviyede mi?
- Funding Rate {data.get('FR','—')}: short squeeze mu long liquidation mu daha olası?
- L/S {data.get('LS_Ratio','—')} ({data.get('LS_Signal','—')}): kalabalık taraf nerede, squeeze ihtimali?
- Taker B/S {data.get('Taker','—')}: piyasaya agresif alıcı mı satıcı mı hakim?
- Destek duvarı {data.get('Sup_Wall','—')} ({data.get('Sup_Vol','—')}): gerçekten güçlü mü?
- Direnç duvarı {data.get('Res_Wall','—')} ({data.get('Res_Vol','—')}): kırılabilir mi?

**🏦 3. KURUMSAL AKIŞ & LİKİDİTE ANALİZİ**
- IBIT akış {data.get('IBIT_Flow','—')}: kurumsal para girişi/çıkışı trendi ne?
- Toplam ETF hacmi ve yönü BTC fiyatıyla örtüşüyor mu?
- Stablecoin toplam {data.get('Total_Stable','—')}: piyasaya hazır "barut" var mı?
- USDT.D {data.get('USDT_D','—')}: yüksek mi alçak mı, altcoin sezonu sinyali veriyor mu?
- Likidite analizi: para kripto'ya mı giriyor, stablecoin'de mi bekliyor?

**🪙 4. ALTCOİN & DOMAİNANCE ANALİZİ**
- BTC dominance {data.get('Dom','—')}, ETH dominance {data.get('ETH_Dom','—')}: dominance trendi yükseliyor mu?
- ETH ({data.get('ETH_C','—')} / 7g: {data.get('ETH_7D','—')}), SOL ({data.get('SOL_C','—')} / 7g: {data.get('SOL_7D','—')}) BTC'ye göre güçlü mü zayıf mı?
- Hangi altcoin rölatif güç gösteriyor? Hangisi zayıf?
- Bu dominance seviyesinde altcoin pozisyonu mantıklı mı?

**📰 5. HABER & KATALIZÖR ANALİZİ**
- Yukarıdaki haberlerin BTC/kripto piyasasına olası etkisini değerlendir.
- Önümüzdeki 1-3 gün için izlenmesi gereken kritik gelişmeler neler?

**🎯 6. GÜNLÜK AKSİYON PLANI (1-3 Gün)**

📗 LONG (Alış) Senaryosu:
  - Giriş seviyesi: (kesin rakam)
  - Stop-Loss: (kesin rakam)
  - Hedef 1 / Hedef 2: (kesin rakamlar)
  - Gerekçe: (hangi koşul sağlanırsa giriş yapılır)

📕 SHORT (Satış) Senaryosu:
  - Giriş seviyesi: (kesin rakam)
  - Stop-Loss: (kesin rakam)
  - Hedef 1 / Hedef 2: (kesin rakamlar)
  - Gerekçe: (hangi koşul sağlanırsa giriş yapılır)

📒 BEKLE Senaryosu:
  - Hangi koşulda beklenmeli?
  - Beklerken izlenecek tetikleyici seviyeler neler?

**⚠️ 7. KRİTİK RİSK & ÖZET**
- Bugünün en kritik riski (tek cümle, rakamsal)
- Genel piyasa pozisyonu özeti (1-2 cümle)
- BTC için en olası senaryo (rakamsal eşiklerle)
"""
                try:
                    resp = client.chat.completions.create(
                        model="google/gemini-2.5-flash",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=8000
                    )
                    rapor_md = resp.choices[0].message.content
                    st.markdown(f'<div class="report-box">{rapor_md}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"AI hatası: {e}")


# ── TAB 4: HABERLER ──────────────────────────────────────────
with tab4:
    col_news, col_tv = st.columns([1, 1])
    with col_news:
        st.subheader("📰 Son Kripto Haberleri (CoinDesk)")
        news = data.get("NEWS", [])
        if news:
            for item in news:
                st.markdown(f"""
                <div class="news-card">
                    <a href="{item['url']}" target="_blank">{item['title']}</a>
                    <div class="news-meta">🕐 {item['time']} · {item['source']}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Haber yüklenemedi.")
    with col_tv:
        st.subheader("📡 Canlı Haber Bandı (TradingView)")
        components.html("""
        <div class="tradingview-widget-container">
        <div class="tradingview-widget-container__widget"></div>
        <script src="https://s3.tradingview.com/external-embedding/embed-widget-timeline.js" async>
        {"feedMode":"all_symbols","isTransparent":true,"displayMode":"regular",
        "width":"100%","height":"800","colorTheme":"dark","locale":"tr"}</script></div>""", height=820)


# ── TAB 5: TÜM METRİKLER ─────────────────────────────────────
with tab5:
    st.subheader("⚙️ Tüm Metrikler — Ham Veri")
    sections = {
        "₿ BTC & Kripto": [
            ("BTC Fiyatı","BTC_P"),("BTC 24s","BTC_C"),("BTC 7g","BTC_7D"),
            ("BTC MCap","BTC_MCap"),("24s Hacim","Vol_24h"),
            ("BTC Dominance","Dom"),("ETH Dominance","ETH_Dom"),
            ("Total MCap","Total_MCap"),("Total Hacim","Total_Vol"),
        ],
        "📊 Türev & Sentiment": [
            ("OI","OI"),("Funding Rate","FR"),("Taker B/S","Taker"),
            ("L/S Oranı","LS_Ratio"),("Long %","Long_Pct"),("Short %","Short_Pct"),
            ("L/S Sinyal","LS_Signal"),("Korku/Açgözlülük","FNG"),("FNG Dün","FNG_PREV"),
        ],
        "🐋 Order Book & ETF": [
            ("Destek Duvarı","Sup_Wall"),("Destek Hacim","Sup_Vol"),
            ("Direnç Duvarı","Res_Wall"),("Direnç Hacim","Res_Vol"),
            ("Tahta Durumu","Wall_Status"),
            ("IBIT","IBIT_P"),("IBIT 24s","IBIT_C"),("IBIT Akış","IBIT_Flow"),
            ("FBTC","FBTC_P"),("BITB","BITB_P"),("ARKB","ARKB_P"),
        ],
        "💵 Stablecoin & On-Chain": [
            ("Toplam Stable","Total_Stable"),("USDT","USDT_MCap"),
            ("USDC","USDC_MCap"),("DAI","DAI_MCap"),
            ("USDT.D","USDT_D"),("USDT Dom Stable","USDT_Dom_Stable"),
            ("Hashrate","Hash"),("Aktif Adres (est)","Active"),
        ],
        "🌍 Makro & Para Politikası": [
            ("FED Faizi","FED"),("M2 YoY","M2"),("ABD 10Y","US10Y"),
            ("DXY","DXY"),("VIX","VIX"),
            ("BTC↔SP500","Corr_SP500"),("BTC↔Altın","Corr_Gold"),
        ],
        "📈 Endeksler & Emtia": [
            ("S&P 500","SP500"),("NASDAQ","NASDAQ"),("DAX","DAX"),
            ("NIKKEI","NIKKEI"),("BIST100","BIST100"),
            ("Altın","GOLD"),("Gümüş","SILVER"),("Petrol","OIL"),
            ("Doğalgaz","NATGAS"),("Bakır","COPPER"),
        ],
        "💱 Forex": [
            ("EUR/USD","EURUSD"),("GBP/USD","GBPUSD"),("USD/JPY","USDJPY"),
            ("USD/TRY","USDTRY"),("USD/CHF","USDCHF"),("AUD/USD","AUDUSD"),
        ],
    }

    # 4 sütun grid
    sec_list = list(sections.items())
    for row_start in range(0, len(sec_list), 4):
        cols = st.columns(4)
        for i, (sec_name, items) in enumerate(sec_list[row_start:row_start+4]):
            with cols[i]:
                st.markdown(f"**{sec_name}**")
                df = pd.DataFrame(
                    [(lbl, data.get(key, "—")) for lbl, key in items],
                    columns=["Metrik", "Değer"]
                )
                st.dataframe(df, use_container_width=True, hide_index=True)
