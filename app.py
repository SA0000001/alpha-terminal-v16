import os
import streamlit as st
import requests
import yfinance as yf
from openai import OpenAI
import pandas as pd
import streamlit.components.v1 as components
from dotenv import load_dotenv

# --- ORTAM DEĞİŞKENLERİ ---
load_dotenv()
ALPHA_VANTAGE_KEY  = os.getenv("ALPHA_VANTAGE_KEY", "")
FRED_API_KEY       = os.getenv("FRED_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

if not OPENROUTER_API_KEY:
    st.error("❌ .env dosyasında OPENROUTER_API_KEY eksik!")
    st.stop()

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)

# --- SAYFA YAPISI ---
st.set_page_config(
    page_title="Serhat Alpha Terminal v16.0",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS ---
st.markdown("""
<style>
body { background-color: #020617; }
.card-green  { background:#0f172a; padding:15px; border-radius:12px; border-bottom:4px solid #00ff88; margin-bottom:12px; }
.card-yellow { background:#1e1e2f; padding:15px; border-radius:12px; border-left:4px solid #facc15;  margin-bottom:12px; }
.card-purple { background:#170f2a; padding:15px; border-radius:12px; border-right:4px solid #a855f7; margin-bottom:12px; }
.card-blue   { background:#0f1f3a; padding:15px; border-radius:12px; border-top:4px solid #38bdf8;   margin-bottom:12px; }
.news-item { background:#0f172a; padding:12px 15px; border-radius:10px; border-left:3px solid #00ff88; margin-bottom:8px; font-size:0.88em; line-height:1.5; }
.news-item a { color:#38bdf8; text-decoration:none; }
.news-item .meta { color:#64748b; font-size:0.8em; margin-top:4px; }
.report-box { background:#020617; padding:25px; border-radius:15px; border:1px solid #1e293b; line-height:1.7; font-size:0.95em; }
.stButton button { background-color:#00ff88 !important; color:#000 !important; font-weight:bold; border-radius:8px; height:3.5em; width:100%; }
.section-title { font-size:1.05em; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:1px; margin:18px 0 8px 0; }
</style>
""", unsafe_allow_html=True)


# =========================================================
# VERİ MOTORU
# =========================================================
@st.cache_data(ttl=300)
def veri_motoru():
    v = {}

    # 1. BTC (CoinGecko)
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=bitcoin&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true",
            timeout=8).json()["bitcoin"]
        v["BTC_P"]   = f"${r['usd']:,.0f}"
        v["BTC_C"]   = f"{r['usd_24h_change']:.2f}%"
        v["Vol_24h"] = f"${r['usd_24h_vol']:,.0f}"
    except:
        v["BTC_P"] = "—"; v["BTC_C"] = "—"; v["Vol_24h"] = "—"

    # 2. ALTCOİNLER (CoinGecko)
    try:
        coins = requests.get(
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=ethereum,solana,binancecoin,ripple,cardano,avalanche-2,polkadot,chainlink"
            "&vs_currencies=usd&include_24hr_change=true",
            timeout=8).json()
        alts = {
            "ETH": "ethereum", "SOL": "solana", "BNB": "binancecoin",
            "XRP": "ripple",   "ADA": "cardano","AVAX": "avalanche-2",
            "DOT": "polkadot", "LINK": "chainlink"
        }
        for sym, cid in alts.items():
            v[f"{sym}_P"] = f"${coins[cid]['usd']:,.2f}"
            v[f"{sym}_C"] = f"{coins[cid]['usd_24h_change']:.2f}%"
    except:
        for sym in ["ETH","SOL","BNB","XRP","ADA","AVAX","DOT","LINK"]:
            v[f"{sym}_P"] = "—"; v[f"{sym}_C"] = "—"

    # 3. IBIT + DİĞER ETF'LER
    try:
        ibit = yf.Ticker("IBIT").history(period="5d")
        last = ibit["Close"].iloc[-1]; prev = ibit["Close"].iloc[-2]
        v["IBIT_P"]   = f"${last:.2f}"
        v["IBIT_C"]   = f"{(last-prev)/prev*100:.2f}%"
        v["IBIT_Vol"] = f"{int(ibit['Volume'].iloc[-1]):,}"
        flow = int(ibit['Volume'].iloc[-1]) * (last - prev)
        v["IBIT_Flow"] = f"{'📈 +' if flow>0 else '📉 '}{abs(flow/1e6):.1f}M $"
    except:
        v["IBIT_P"]="Kapalı"; v["IBIT_C"]="0%"; v["IBIT_Vol"]="—"; v["IBIT_Flow"]="—"

    for sym in ["FBTC","BITB","ARKB"]:
        try:
            t = yf.Ticker(sym).history(period="5d")
            last=t["Close"].iloc[-1]; prev=t["Close"].iloc[-2]
            v[f"{sym}_P"] = f"${last:.2f}"
            v[f"{sym}_C"] = f"{(last-prev)/prev*100:.2f}%"
        except:
            v[f"{sym}_P"]="—"; v[f"{sym}_C"]="—"

    # 4. GLOBAL HİSSE ENDEKSLERİ
    endeksler = {
        "SP500":   "^GSPC",   "NASDAQ":  "^IXIC",  "DOW":   "^DJI",
        "DAX":     "^GDAXI",  "FTSE":    "^FTSE",  "NIKKEI":"^N225",
        "HSI":     "^HSI",    "BIST100": "XU100.IS","VIX":   "^VIX",
    }
    for key, sym in endeksler.items():
        try:
            df = yf.Ticker(sym).history(period="5d")
            curr = df["Close"].iloc[-1]; prev = df["Close"].iloc[-2]
            v[key]          = f"{curr:,.2f}"
            v[f"{key}_C"]   = f"{(curr-prev)/prev*100:.2f}%"
        except:
            v[key]="—"; v[f"{key}_C"]="—"

    # 5. EMTİALAR
    emtialar = {
        "GOLD":"GC=F","SILVER":"SI=F","OIL":"CL=F",
        "NATGAS":"NG=F","COPPER":"HG=F","WHEAT":"ZW=F"
    }
    for key, sym in emtialar.items():
        try:
            df = yf.Ticker(sym).history(period="5d")
            curr = df["Close"].iloc[-1]; prev = df["Close"].iloc[-2]
            v[key]        = f"{curr:,.3f}"
            v[f"{key}_C"] = f"{(curr-prev)/prev*100:.2f}%"
        except:
            v[key]="—"; v[f"{key}_C"]="—"

    # 6. FOREX
    forex = {
        "DXY":"DX-Y.NYB","EURUSD":"EURUSD=X","GBPUSD":"GBPUSD=X",
        "USDJPY":"JPY=X","USDTRY":"TRY=X","USDCHF":"CHF=X",
        "AUDUSD":"AUDUSD=X","US10Y":"^TNX"
    }
    for key, sym in forex.items():
        try:
            df = yf.Ticker(sym).history(period="5d")
            curr = df["Close"].iloc[-1]; prev = df["Close"].iloc[-2]
            v[key]        = round(curr, 4)
            v[f"{key}_C"] = f"{(curr-prev)/prev*100:.2f}%"
        except:
            v[key]="—"; v[f"{key}_C"]="—"

    # 7. KORELASYONLAR
    try:
        cd = yf.download(["BTC-USD","^GSPC","GC=F"],period="30d",progress=False)["Close"]
        cm = cd.corr()
        v["Corr_SP500"] = round(cm.loc["BTC-USD","^GSPC"],2)
        v["Corr_Gold"]  = round(cm.loc["BTC-USD","GC=F"],2)
    except:
        v["Corr_SP500"]="—"; v["Corr_Gold"]="—"

    # 8. BALİNA DUVARI (Kraken)
    try:
        ob  = requests.get("https://api.kraken.com/0/public/Depth?pair=XBTUSD&count=500",timeout=8).json()
        pk  = list(ob["result"].keys())[0]
        bids= [(float(p),float(q)) for p,q,_ in ob["result"][pk]["bids"]]
        asks= [(float(p),float(q)) for p,q,_ in ob["result"][pk]["asks"]]
        cur = bids[0][0]; noise=250; bs=100
        fb  = [(p,q) for p,q in bids if p < cur-noise] or bids[len(bids)//2:]
        fa  = [(p,q) for p,q in asks if p > cur+noise] or asks[len(asks)//2:]
        def bkt(data,fn):
            d={}
            for p,q in data:
                k=fn(p); d[k]=d.get(k,0)+q
            return max(d.items(),key=lambda x:x[1])
        sw,sv = bkt(fb,lambda p: int(p/bs)*bs)
        rw,rv = bkt(fa,lambda p: int((p/bs)+1)*bs)
        v["Sup_Wall"]=f"${sw:,}"; v["Sup_Vol"]=f"{int(sv):,} BTC"
        v["Res_Wall"]=f"${rw:,}"; v["Res_Vol"]=f"{int(rv):,} BTC"
        ds=cur-sw; dr=rw-cur
        v["Wall_Status"]= "🔴 Makro Dirence Yakın" if dr<ds else ("🟢 Makro Desteğe Yakın" if ds<dr else "⚖️ Kanal Ortasında")
    except:
        v["Sup_Wall"]="—"; v["Sup_Vol"]="—"; v["Res_Wall"]="—"; v["Res_Vol"]="—"; v["Wall_Status"]="Veri Yok"

    # 9. STABLECOİN
    try:
        sc = requests.get(
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=tether,usd-coin,dai&vs_currencies=usd&include_market_cap=true",
            timeout=6).json()
        v["USDT_MCap"]   = f"${sc['tether']['usd_market_cap']/1e9:.1f}B"
        v["USDC_MCap"]   = f"${sc['usd-coin']['usd_market_cap']/1e9:.1f}B"
        v["DAI_MCap"]    = f"${sc['dai']['usd_market_cap']/1e9:.1f}B"
        total = sc['tether']['usd_market_cap']+sc['usd-coin']['usd_market_cap']+sc['dai']['usd_market_cap']
        v["Total_Stable"]= f"${total/1e9:.1f}B"
    except:
        v["USDT_MCap"]="—"; v["USDC_MCap"]="—"; v["DAI_MCap"]="—"; v["Total_Stable"]="—"

    # 10. LONG/SHORT ORANI
    try:
        ls = requests.get(
            "https://fapi.binance.com/futures/data/globalLongShortAccountRatio"
            "?symbol=BTCUSDT&period=1h&limit=1",timeout=5).json()
        ratio = float(ls[0]["longShortRatio"])
        v["LS_Ratio"] = f"{ratio:.3f}"
        v["Long_Pct"] = f"%{float(ls[0]['longAccount'])*100:.1f}"
        v["Short_Pct"]= f"%{float(ls[0]['shortAccount'])*100:.1f}"
        v["LS_Signal"]= "🟢 Long Ağırlıklı" if ratio>1 else "🔴 Short Ağırlıklı"
    except:
        v["LS_Ratio"]="—"; v["Long_Pct"]="—"; v["Short_Pct"]="—"; v["LS_Signal"]="—"

    # 11. TAKER / OI / FUNDING
    try:
        tr = requests.get("https://fapi.binance.com/futures/data/takerbuySellVol?symbol=BTCUSDT&period=1h&limit=1",timeout=5).json()
        v["Taker"] = f"{float(tr[0]['buySellRatio']):.3f}"
    except: v["Taker"]="1.000"
    try:
        oi = requests.get("https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT",timeout=5).json()
        v["OI"] = f"{int(float(oi['openInterest'])):,} BTC"
    except: v["OI"]="—"
    try:
        fr = requests.get("https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT",timeout=5).json()
        v["FR"] = f"%{float(fr['lastFundingRate'])*100:.4f}"
    except: v["FR"]="—"

    # 12. FRED
    try:
        m2 = requests.get(
            f"https://api.stlouisfed.org/fred/series/observations?series_id=M2SL&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=13",
            timeout=6).json()["observations"]
        v["M2"] = f"{(float(m2[0]['value'])-float(m2[12]['value']))/float(m2[12]['value'])*100:.2f}"
    except: v["M2"]="—"
    try:
        fed = requests.get(
            f"https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=1",
            timeout=6).json()["observations"]
        v["FED"] = f"%{fed[0]['value']}"
    except: v["FED"]="—"

    # 13. ON-CHAIN
    try:
        s = requests.get("https://api.blockchain.info/stats",timeout=5).json()
        v["Active"] = f"{s['n_blocks_mined']*2100:,}"
        v["Hash"]   = f"{s['hash_rate']/1e9:.2f} EH/s"
    except: v["Active"]="—"; v["Hash"]="—"

    # 14. KORKU / MARKET CAP
    try:
        fng = requests.get("https://api.alternative.me/fng/",timeout=5).json()["data"][0]
        v["FNG"] = f"{fng['value']} ({fng['value_classification']})"
    except: v["FNG"]="—"
    try:
        cg = requests.get("https://api.coingecko.com/api/v3/global",timeout=5).json()["data"]
        v["Dom"]        = f"%{cg['market_cap_percentage']['btc']:.2f}"
        v["ETH_Dom"]    = f"%{cg['market_cap_percentage']['eth']:.2f}"
        v["Total_MCap"] = f"${cg['total_market_cap']['usd']/1e12:.2f}T"
    except: v["Dom"]="—"; v["ETH_Dom"]="—"; v["Total_MCap"]="—"

    # 15. HABERLER (CryptoCompare)
    try:
        nr = requests.get(
            "https://min-api.cryptocompare.com/data/v2/news/?lang=EN&sortOrder=latest&limit=10",
            timeout=6).json()
        v["NEWS"] = [
            {"title": n["title"], "url": n["url"],
             "source": n["source_info"]["name"],
             "time": pd.Timestamp(n["published_on"],unit="s").strftime("%H:%M")}
            for n in nr["Data"][:10]
        ]
    except: v["NEWS"] = []

    return v


# =========================================================
# ARAYÜZ
# =========================================================
st.title("🛡️ Serhat's Alpha Terminal v16.0")
st.caption("Kripto · Makro · Forex · Emtia · Haber | Her 5 dakikada güncellenir")

with st.spinner("Tüm piyasa verileri yükleniyor..."):
    data = veri_motoru()

# SIDEBAR
st.sidebar.title("📥 Veri Arşivi")
df_exp = pd.DataFrame([(k,v) for k,v in data.items() if k!="NEWS"],columns=["Metrik","Değer"])
csv = df_exp.to_csv(index=False,sep=";").encode("utf-8-sig")
st.sidebar.download_button("💾 CSV İndir", csv,
    file_name=f"SerhatTerminal_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
    mime="text/csv")
st.sidebar.divider()
st.sidebar.markdown("**Model:** Gemini 2.0 Flash\n\n**Kaynak:** 16 Bağımsız API\n\n**Güncelleme:** Her 5 dk")

# TABS
tab1,tab2,tab3,tab4,tab5 = st.tabs(["₿ Kripto","🌍 Makro & Forex","📊 Grafik & Rapor","📰 Haberler","⚙️ Detay"])


# ── TAB 1: KRİPTO ─────────────────────────────────────────
with tab1:
    st.markdown("<div class='section-title'>₿ Bitcoin & Temel Göstergeler</div>",unsafe_allow_html=True)
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("BTC Fiyatı",       data.get("BTC_P"),    data.get("BTC_C"))
    c2.metric("Korku/Açgözlülük", data.get("FNG"))
    c3.metric("BTC Dominance",    data.get("Dom"))
    c4.metric("Total Market Cap", data.get("Total_MCap"))
    c5.metric("M2 Likidite(YoY)", f"%{data.get('M2')}")
    c6.metric("FED Faizi",        data.get("FED"))

    st.divider()
    st.markdown("<div class='section-title'>🪙 Altcoin Fiyatları</div>",unsafe_allow_html=True)
    a1,a2,a3,a4 = st.columns(4)
    a1.metric("Ethereum (ETH)",  data.get("ETH_P"),  data.get("ETH_C"))
    a2.metric("Solana (SOL)",    data.get("SOL_P"),  data.get("SOL_C"))
    a3.metric("BNB",             data.get("BNB_P"),  data.get("BNB_C"))
    a4.metric("XRP",             data.get("XRP_P"),  data.get("XRP_C"))
    a5,a6,a7,a8 = st.columns(4)
    a5.metric("Cardano (ADA)",   data.get("ADA_P"),  data.get("ADA_C"))
    a6.metric("Avalanche (AVAX)",data.get("AVAX_P"), data.get("AVAX_C"))
    a7.metric("Polkadot (DOT)",  data.get("DOT_P"),  data.get("DOT_C"))
    a8.metric("Chainlink (LINK)",data.get("LINK_P"), data.get("LINK_C"))

    st.divider()
    col_etf,col_stable,col_ls = st.columns(3)

    with col_etf:
        st.markdown("<div class='section-title'>🏦 Bitcoin ETF Akışları</div>",unsafe_allow_html=True)
        st.metric("IBIT Fiyatı",      data.get("IBIT_P"),  data.get("IBIT_C"))
        st.metric("IBIT Günlük Akış", data.get("IBIT_Flow"))
        st.metric("IBIT Hacim",       data.get("IBIT_Vol"))
        st.metric("FBTC (Fidelity)",  data.get("FBTC_P"),  data.get("FBTC_C"))
        st.metric("BITB (Bitwise)",   data.get("BITB_P"),  data.get("BITB_C"))
        st.metric("ARKB (ARK)",       data.get("ARKB_P"),  data.get("ARKB_C"))

    with col_stable:
        st.markdown("<div class='section-title'>💵 Stablecoin Akışları</div>",unsafe_allow_html=True)
        st.metric("Toplam Stablecoin",data.get("Total_Stable"))
        st.metric("USDT Market Cap",  data.get("USDT_MCap"))
        st.metric("USDC Market Cap",  data.get("USDC_MCap"))
        st.metric("DAI Market Cap",   data.get("DAI_MCap"))
        st.metric("ETH Dominance",    data.get("ETH_Dom"))
        st.metric("24s BTC Hacim",    data.get("Vol_24h"))

    with col_ls:
        st.markdown("<div class='section-title'>📊 Türev & Pozisyon</div>",unsafe_allow_html=True)
        st.metric("L/S Sinyal",       data.get("LS_Signal"))
        st.metric("Long/Short Oranı", data.get("LS_Ratio"))
        st.metric("Long Pozisyonlar", data.get("Long_Pct"))
        st.metric("Short Pozisyonlar",data.get("Short_Pct"))
        st.metric("Taker B/S Oranı",  data.get("Taker"))
        st.metric("Open Interest",    data.get("OI"))
        st.metric("Funding Rate",     data.get("FR"))

    st.divider()
    st.markdown("<div class='section-title'>🐋 Balina Duvarları (Kraken)</div>",unsafe_allow_html=True)
    w1,w2,w3 = st.columns(3)
    w1.metric("Tahta Durumu",         data.get("Wall_Status"))
    w2.metric("🟢 Ana Destek Duvarı", data.get("Sup_Wall"),f"{data.get('Sup_Vol')} Bekliyor")
    w3.metric("🔴 Ana Direnç Duvarı", data.get("Res_Wall"),f"−{data.get('Res_Vol')} Bekliyor")


# ── TAB 2: MAKRO & FOREX ──────────────────────────────────
with tab2:
    col_idx,col_forex,col_com = st.columns(3)

    with col_idx:
        st.markdown("<div class='section-title'>📈 Global Hisse Endeksleri</div>",unsafe_allow_html=True)
        for label,key in [("S&P 500","SP500"),("NASDAQ","NASDAQ"),("DOW JONES","DOW"),
                           ("DAX","DAX"),("FTSE 100","FTSE"),("Nikkei 225","NIKKEI"),
                           ("Hang Seng","HSI"),("BIST 100","BIST100"),("VIX","VIX")]:
            st.metric(label, data.get(key), data.get(f"{key}_C"))

    with col_forex:
        st.markdown("<div class='section-title'>💱 Döviz Kurları</div>",unsafe_allow_html=True)
        for label,key in [("DXY (Dolar Endeksi)","DXY"),("EUR/USD","EURUSD"),
                           ("GBP/USD","GBPUSD"),("USD/JPY","USDJPY"),("USD/TRY","USDTRY"),
                           ("USD/CHF","USDCHF"),("AUD/USD","AUDUSD"),("ABD 10Y Tahvil","US10Y")]:
            st.metric(label, data.get(key), data.get(f"{key}_C"))

    with col_com:
        st.markdown("<div class='section-title'>🏭 Emtialar</div>",unsafe_allow_html=True)
        for label,key in [("Altın (XAU/USD)","GOLD"),("Gümüş (XAG/USD)","SILVER"),
                           ("Ham Petrol (WTI)","OIL"),("Doğalgaz","NATGAS"),
                           ("Bakır","COPPER"),("Buğday","WHEAT")]:
            st.metric(label, data.get(key), data.get(f"{key}_C"))
        st.divider()
        st.markdown("<div class='section-title'>🔗 BTC Korelasyonları (30g)</div>",unsafe_allow_html=True)
        st.metric("BTC ↔ S&P500", data.get("Corr_SP500"))
        st.metric("BTC ↔ Altın",  data.get("Corr_Gold"))


# ── TAB 3: GRAFİK & RAPOR ────────────────────────────────
with tab3:
    col_chart,col_side = st.columns([2.2,1.2])

    with col_chart:
        st.subheader("📊 Canlı BTC/USDT Grafiği")
        components.html("""
        <div style="height:520px;">
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>new TradingView.widget({autosize:true,symbol:"BINANCE:BTCUSDT",
        interval:"D",theme:"dark",style:"1",locale:"tr",toolbar_bg:"#020617",
        container_id:"tv_main"});</script>
        <div id="tv_main" style="height:100%;"></div></div>""", height=540)

    with col_side:
        st.subheader("📅 Ekonomik Takvim")
        components.html("""
        <div class="tradingview-widget-container">
        <div class="tradingview-widget-container__widget"></div>
        <script src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
        {"colorTheme":"dark","isTransparent":true,"width":"100%","height":"480",
        "locale":"tr","importanceFilter":"0,1","currencyFilter":"USD,EUR"}
        </script></div>""", height=500)

        st.divider()
        st.subheader("📄 God Mode Strateji Raporu")
        st.caption("Gemini 2.0 Flash · Tüm veriler dahil")

        if st.button("🚀 RAPOR OLUŞTUR", use_container_width=True):
            with st.spinner("AI analiz ediyor..."):
                clean = {k:v for k,v in data.items() if k!="NEWS"}
                prompt = f"""
Sen deneyimli bir makro-kripto fon yöneticisisin.
Aşağıdaki GERÇEK piyasa verilerini kullanarak Serhat için strateji raporu yaz. Türkçe.

VERİLER: {str(clean)}

## 1. Makro Durum
Global endeksler, Forex (DXY, TRY), emtialar ve BTC korelasyonlarını yorumla.

## 2. Kripto Piyasa Yapısı
Long/Short: {data.get('LS_Ratio')} ({data.get('LS_Signal')})
Funding: {data.get('FR')}, OI: {data.get('OI')}
Stablecoin: {data.get('Total_Stable')}, ETF Akış: {data.get('IBIT_Flow')}

## 3. Balina Duvarı Analizi
Destek: {data.get('Sup_Wall')} ({data.get('Sup_Vol')})
Direnç: {data.get('Res_Wall')} ({data.get('Res_Vol')})

## 4. Altcoin Sinyalleri
ETH, SOL, BNB performanslarını BTC dominance ile ilişkilendir.

## 5. Aksiyon Planı (1-3 Gün)
Kesin fiyat seviyeleri, Long/Short/Bekle kararı, stop-loss ve hedefler.
"""
                try:
                    resp = client.chat.completions.create(
                        model="google/gemini-2.0-flash-001",
                        messages=[{"role":"user","content":prompt}],
                        max_tokens=2000)
                    st.markdown(f'<div class="report-box">{resp.choices[0].message.content}</div>',unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"AI hatası: {e}")


# ── TAB 4: HABERLER ──────────────────────────────────────
with tab4:
    st.subheader("📰 Son Kripto Haberleri")
    st.caption("CryptoCompare · Otomatik güncellenir")

    news = data.get("NEWS",[])
    if news:
        for item in news:
            st.markdown(f"""
            <div class="news-item">
                <a href="{item['url']}" target="_blank">{item['title']}</a>
                <div class="meta">🕐 {item['time']} · {item['source']}</div>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("Haber verisi yüklenemedi. Birkaç dakika sonra tekrar deneyin.")

    st.divider()
    st.subheader("📡 Canlı Haber Bandı (TradingView)")
    components.html("""
    <div class="tradingview-widget-container">
    <div class="tradingview-widget-container__widget"></div>
    <script src="https://s3.tradingview.com/external-embedding/embed-widget-timeline.js" async>
    {"feedMode":"all_symbols","isTransparent":true,"displayMode":"regular",
    "width":"100%","height":"600","colorTheme":"dark","locale":"tr"}
    </script></div>""", height=620)


# ── TAB 5: DETAY ─────────────────────────────────────────
with tab5:
    st.subheader("⚙️ Tüm Metrikler")
    sections = {
        "Kripto Türevler": [
            ("Open Interest","OI"),("Funding Rate","FR"),("Taker B/S","Taker"),
            ("L/S Oranı","LS_Ratio"),("Long %","Long_Pct"),("Short %","Short_Pct"),
        ],
        "On-Chain & Ağ": [
            ("Aktif Adres","Active"),("Hashrate","Hash"),("BTC Dom","Dom"),
            ("ETH Dom","ETH_Dom"),("Total MCap","Total_MCap"),("24s Hacim","Vol_24h"),
        ],
        "Stablecoin & ETF": [
            ("Toplam Stable","Total_Stable"),("USDT MCap","USDT_MCap"),
            ("USDC MCap","USDC_MCap"),("DAI MCap","DAI_MCap"),
            ("IBIT Hacim","IBIT_Vol"),("IBIT Akış","IBIT_Flow"),
        ],
        "Makro": [
            ("M2 (YoY)","M2"),("FED Faizi","FED"),("VIX","VIX"),
            ("DXY","DXY"),("ABD 10Y","US10Y"),("BTC↔SP500","Corr_SP500"),("BTC↔Altın","Corr_Gold"),
        ],
    }
    d1,d2,d3,d4 = st.columns(4)
    for col_ui,(section,items) in zip([d1,d2,d3,d4],sections.items()):
        with col_ui:
            st.markdown(f"**{section}**")
            df = pd.DataFrame([(lbl,data.get(key,"—")) for lbl,key in items],columns=["Metrik","Değer"])
            st.dataframe(df,use_container_width=True,hide_index=True)
