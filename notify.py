"""
notify.py — Her sabah 08:30 (Türkiye) çalışır.
Piyasa verilerini çeker, AI raporu oluşturur, Telegram'a gönderir.
"""

import os, re, requests
import yfinance as yf
import pandas as pd
from openai import OpenAI

# ── API ANAHTARLARI (GitHub Secrets'tan gelir) ────────────
TELEGRAM_TOKEN     = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
FRED_API_KEY       = os.environ.get("FRED_API_KEY", "")

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


# =========================================================
# VERİ ÇEKME
# =========================================================
def veri_cek():
    v = {}

    # ── BTC + tüm altcoinler (Coinpaprika) ───────────────
    alt_ids = {
        "BTC":"btc-bitcoin","ETH":"eth-ethereum","SOL":"sol-solana",
        "BNB":"bnb-binance-coin","XRP":"xrp-xrp","ADA":"ada-cardano",
        "AVAX":"avax-avalanche","LINK":"link-chainlink","DOT":"dot-polkadot"
    }
    for sym, cid in alt_ids.items():
        try:
            r = requests.get(f"https://api.coinpaprika.com/v1/tickers/{cid}",
                             headers=HEADERS, timeout=8).json()["quotes"]["USD"]
            v[f"{sym}_P"] = f"${r['price']:,.2f}"
            v[f"{sym}_C"] = f"{r['percent_change_24h']:.2f}%"
            v[f"{sym}_7D"] = f"{r['percent_change_7d']:.2f}%"
            if sym=="BTC":
                v["BTC_P"]    = f"${r['price']:,.0f}"
                v["Vol_24h"]  = f"${r['volume_24h']:,.0f}"
                v["MCap_BTC"] = f"${r['market_cap']:,.0f}"
        except:
            v[f"{sym}_P"]="—"; v[f"{sym}_C"]="—"; v[f"{sym}_7D"]="—"

    # ── Global piyasa dominance (Coinpaprika) ─────────────
    try:
        g = requests.get("https://api.coinpaprika.com/v1/global",
                         headers=HEADERS, timeout=6).json()
        v["Dom"]        = f"%{g['bitcoin_dominance_percentage']:.2f}"
        v["Total_MCap"] = f"${g['market_cap_usd']/1e12:.2f}T"
        v["Total_Vol"]  = f"${g['volume_24h_usd']/1e9:.1f}B"
    except:
        v["Dom"]="—"; v["Total_MCap"]="—"; v["Total_Vol"]="—"

    # ── Hisse endeksleri + emtialar + forex (yFinance) ────
    yf_data = {
        "SP500":"^GSPC","NASDAQ":"^IXIC","DOW":"^DJI",
        "DAX":"^GDAXI","NIKKEI":"^N225","BIST100":"XU100.IS",
        "VIX":"^VIX","DXY":"DX-Y.NYB","US10Y":"^TNX",
        "GOLD":"GC=F","SILVER":"SI=F","OIL":"CL=F","NATGAS":"NG=F",
        "USDTRY":"TRY=X","EURUSD":"EURUSD=X","USDJPY":"JPY=X",
    }
    for key, sym in yf_data.items():
        try:
            df   = yf.Ticker(sym).history(period="5d")
            curr = df["Close"].iloc[-1]; prev = df["Close"].iloc[-2]
            v[key]        = f"{curr:,.3f}"
            v[f"{key}_C"] = f"{(curr-prev)/prev*100:.2f}%"
        except:
            v[key]="—"; v[f"{key}_C"]="—"

    # ── ETF (yFinance — son kapanış) ──────────────────────
    for sym in ["IBIT","FBTC","BITB","ARKB"]:
        try:
            df   = yf.Ticker(sym).history(period="10d")
            curr = df["Close"].iloc[-1]; prev = df["Close"].iloc[-2]
            v[f"{sym}_P"]   = f"${curr:.2f}"
            v[f"{sym}_C"]   = f"{(curr-prev)/prev*100:.2f}%"
            v[f"{sym}_Vol"] = f"{int(df['Volume'].iloc[-1]):,}"
            if sym=="IBIT":
                flow = int(df["Volume"].iloc[-1])*(curr-prev)
                v["IBIT_Flow"] = f"{'📈 +' if flow>0 else '📉 '}{abs(flow/1e6):.1f}M $"
        except:
            v[f"{sym}_P"]="—"; v[f"{sym}_C"]="—"
    if "IBIT_Flow" not in v: v["IBIT_Flow"]="—"

    # ── Korku/Açgözlülük ─────────────────────────────────
    try:
        fng = requests.get("https://api.alternative.me/fng/?limit=2",timeout=5).json()["data"]
        v["FNG"]      = f"{fng[0]['value']} ({fng[0]['value_classification']})"
        v["FNG_PREV"] = f"{fng[1]['value']} ({fng[1]['value_classification']})"
    except:
        v["FNG"]="—"; v["FNG_PREV"]="—"

    # ── Balina duvarları (Kraken) ─────────────────────────
    try:
        ob  = requests.get("https://api.kraken.com/0/public/Depth?pair=XBTUSD&count=500",timeout=8).json()
        pk  = list(ob["result"].keys())[0]
        bids= [(float(p),float(q)) for p,q,_ in ob["result"][pk]["bids"]]
        asks= [(float(p),float(q)) for p,q,_ in ob["result"][pk]["asks"]]
        cur = bids[0][0]; noise=250; bs=100
        fb  = [(p,q) for p,q in bids if p<cur-noise] or bids[len(bids)//2:]
        fa  = [(p,q) for p,q in asks if p>cur+noise] or asks[len(asks)//2:]
        def bkt(data,fn):
            d={}
            for p,q in data: k=fn(p); d[k]=d.get(k,0)+q
            return max(d.items(),key=lambda x:x[1])
        sw,sv = bkt(fb,lambda p:int(p/bs)*bs)
        rw,rv = bkt(fa,lambda p:int((p/bs)+1)*bs)
        v["Sup_Wall"]=f"${sw:,}"; v["Sup_Vol"]=f"{int(sv):,}"
        v["Res_Wall"]=f"${rw:,}"; v["Res_Vol"]=f"{int(rv):,}"
        v["BTC_Now"]  = f"${cur:,.0f}"
    except:
        v["Sup_Wall"]="—"; v["Sup_Vol"]="—"
        v["Res_Wall"]="—"; v["Res_Vol"]="—"; v["BTC_Now"]="—"

    # ── OI & Funding — OKX ───────────────────────────────
    try:
        okx_fr = requests.get(
            "https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP",
            headers=HEADERS, timeout=6).json()
        fr = float(okx_fr["data"][0]["fundingRate"])
        v["FR"] = f"%{fr*100:.4f}"
    except:
        v["FR"] = "—"

    try:
        okx_oi = requests.get(
            "https://www.okx.com/api/v5/public/open-interest?instType=SWAP&instId=BTC-USDT-SWAP",
            headers=HEADERS, timeout=6).json()
        oi = float(okx_oi["data"][0]["oi"])
        v["OI"] = f"{oi:,.0f} BTC"
    except:
        v["OI"] = "—"

    # ── Taker B/S — OKX ──────────────────────────────────
    try:
        tk = requests.get(
            "https://www.okx.com/api/v5/rubik/stat/taker-volume"
            "?ccy=BTC&instType=contracts&period=1H",
            headers=HEADERS, timeout=6).json()
        buy_vol  = float(tk["data"][0][1])
        sell_vol = float(tk["data"][0][2])
        v["Taker"] = f"{buy_vol/sell_vol:.3f}" if sell_vol > 0 else "1.000"
    except:
        v["Taker"] = "1.000"

    # ── Long/Short — OKX (çoklu kaynak fallback) ─────────
    ls_done = False

    # Kaynak 1: OKX top trader long/short ratio
    if not ls_done:
        try:
            okx_ls = requests.get(
                "https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio-contract-top-trader"
                "?instId=BTC-USDT-SWAP&period=1H",
                headers=HEADERS, timeout=6).json()
            if okx_ls.get("data") and len(okx_ls["data"]) > 0:
                d     = okx_ls["data"][0]
                lp    = float(d["longRatio"]) * 100
                sp    = float(d["shortRatio"]) * 100
                ratio = lp / sp if sp > 0 else 1
                v["LS_Ratio"] = f"{ratio:.3f}"
                v["Long_Pct"] = f"%{lp:.1f}"
                v["Short_Pct"]= f"%{sp:.1f}"
                v["LS_Signal"]= "🟢 Long Ağırlıklı" if ratio > 1 else "🔴 Short Ağırlıklı"
                ls_done = True
        except: pass

    # Kaynak 2: OKX genel hesap L/S
    if not ls_done:
        try:
            okx_ls2 = requests.get(
                "https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio"
                "?ccy=BTC&period=1H",
                headers=HEADERS, timeout=6).json()
            if okx_ls2.get("data") and len(okx_ls2["data"]) > 0:
                d     = okx_ls2["data"][0]
                ratio = float(d[1]) if isinstance(d, list) else float(d.get("longShortRatio", 1))
                lp    = ratio / (1 + ratio) * 100
                v["LS_Ratio"] = f"{ratio:.3f}"
                v["Long_Pct"] = f"%{lp:.1f}"
                v["Short_Pct"]= f"%{100-lp:.1f}"
                v["LS_Signal"]= "🟢 Long Ağırlıklı" if ratio > 1 else "🔴 Short Ağırlıklı"
                ls_done = True
        except: pass

    # Kaynak 3: Gate.io yedek
    if not ls_done:
        try:
            gate = requests.get(
                "https://api.gateio.ws/api/v4/futures/usdt/contract_stats"
                "?contract=BTC_USDT&interval=1h&limit=1",
                headers=HEADERS, timeout=6).json()
            d  = gate[0]
            lp = float(d.get("lsr_taker", 1))
            v["LS_Ratio"] = f"{lp:.3f}"
            lp_pct = lp / (1 + lp) * 100
            v["Long_Pct"] = f"%{lp_pct:.1f}"
            v["Short_Pct"]= f"%{100-lp_pct:.1f}"
            v["LS_Signal"]= "🟢 Long Ağırlıklı" if lp > 1 else "🔴 Short Ağırlıklı"
            ls_done = True
        except: pass

    if not ls_done:
        v["LS_Ratio"]="—"; v["Long_Pct"]="—"
        v["Short_Pct"]="—"; v["LS_Signal"]="—"

    # ── Stablecoin (DeFiLlama) ────────────────────────────
    try:
        sc    = requests.get("https://stablecoins.llama.fi/stablecoins?includePrices=true",
                             headers=HEADERS, timeout=8).json()["peggedAssets"]
        total = sum(c.get("circulating",{}).get("peggedUSD",0) for c in sc)
        def gcap(sym):
            c=next((x for x in sc if x["symbol"].upper()==sym),None)
            return f"${c['circulating']['peggedUSD']/1e9:.1f}B" if c else "—"
        v["Total_Stable"] = f"${total/1e9:.1f}B"
        v["USDT_MCap"]    = gcap("USDT")
        v["USDC_MCap"]    = gcap("USDC")
    except:
        v["Total_Stable"]="—"; v["USDT_MCap"]="—"; v["USDC_MCap"]="—"

    # ── BTC Korelasyonları (30 günlük) ────────────────────
    try:
        cd = yf.download(["BTC-USD","^GSPC","GC=F"],period="30d",progress=False)["Close"]
        cm = cd.corr()
        v["Corr_SP500"] = f"{cm.loc['BTC-USD','^GSPC']:.2f}"
        v["Corr_Gold"]  = f"{cm.loc['BTC-USD','GC=F']:.2f}"
    except:
        v["Corr_SP500"]="—"; v["Corr_Gold"]="—"

    # ── On-chain (Blockchain.info) ────────────────────────
    try:
        s = requests.get("https://api.blockchain.info/stats",timeout=5).json()
        v["Hash"]      = f"{s['hash_rate']/1e9:.2f} EH/s"
        v["BTC_Active"]= f"{s['n_blocks_mined']*2100:,}"
    except:
        v["Hash"]="—"; v["BTC_Active"]="—"

    # ── M2 & FED (FRED) ───────────────────────────────────
    try:
        m2 = requests.get(
            f"https://api.stlouisfed.org/fred/series/observations?series_id=M2SL"
            f"&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=13",
            timeout=6).json()["observations"]
        v["M2"]=f"{(float(m2[0]['value'])-float(m2[12]['value']))/float(m2[12]['value'])*100:.2f}%"
    except: v["M2"]="—"
    try:
        fed = requests.get(
            f"https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS"
            f"&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=1",
            timeout=6).json()["observations"]
        v["FED"]=f"%{fed[0]['value']}"
    except: v["FED"]="—"

    return v


# =========================================================
# EKONOMİK TAKVİM (Trading Economics — ücretsiz RSS)
# =========================================================
def takvim_cek():
    sonuclar = []

    # Kaynak 1: Trading Economics RSS
    try:
        rss    = requests.get("https://tradingeconomics.com/rss/calendar.aspx",
                              headers=HEADERS, timeout=8).text
        titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", rss)[1:15]
        kritik = [t for t in titles if any(k in t for k in
                  ["USD","EUR","Fed","CPI","NFP","GDP","PMI","FOMC","Powell",
                   "Interest Rate","Inflation","Unemployment","Retail","ISM"])]
        sonuclar = kritik[:5] if kritik else titles[:4]
    except:
        pass

    # Kaynak 2: ForexFactory RSS (yedek)
    if not sonuclar:
        try:
            rss2   = requests.get("https://nfs.faireconomy.media/ff_calendar_thisweek.xml",
                                  headers=HEADERS, timeout=8).text
            titles2= re.findall(r"<title>(.*?)</title>", rss2)[1:10]
            sonuclar = titles2[:5]
        except:
            pass

    # Bugünün gün ve tarihini ekle
    bugun_str = pd.Timestamp.now(tz="Europe/Istanbul").strftime("%A, %d %B %Y")
    if sonuclar:
        return sonuclar
    else:
        # Boş bile olsa AI'a bilgi ver
        return [
            f"📅 Bugün ({bugun_str}) için yüksek etkili veri takvimde tespit edilemedi.",
            "Bu tür günlerde piyasa fiyat hareketi haber akışı ve teknik seviyelere duyarlı olur.",
            "Özellikle BTC'de büyük bir balinanın hamlesi veya ETF akış verisi yön belirleyici olabilir.",
        ]


# =========================================================
# HABERLER (CoinDesk RSS)
# =========================================================
def haber_cek():
    try:
        rss    = requests.get("https://www.coindesk.com/arc/outboundfeeds/rss/",
                              headers=HEADERS, timeout=8).text
        titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", rss)[1:6]
        return titles
    except:
        return []


# =========================================================
# AI RAPORU
# =========================================================
def ai_raporu(v, takvim, haberler):
    takvim_str = "\n".join(f"• {t}" for t in takvim) if takvim else "Önemli veri yok"
    haber_str  = "\n".join(f"• {h}" for h in haberler) if haberler else "Haber alınamadı"

    bugun = pd.Timestamp.now(tz="Europe/Istanbul").strftime("%d %B %Y, %A")

    prompt = f"""
Sen 20 yıllık deneyime sahip bir makro-kripto fon yöneticisisin.
Aşağıdaki TÜM gerçek verileri kullanarak Serhat için derinlikli, rakamsal ve eyleme dönüşebilir 
bir sabah bülteni yaz. Türkçe yaz. Telegram Markdown formatı (**kalın**, _italik_).

TEMEL KURALLAR:
- Her iddiayı rakamla destekle. "VIX yüksek" değil, "VIX {v['VIX']} ({v.get('VIX_C','—')})" yaz.
- Seviyeleri kesin yaz: "$70,200 kırılırsa" gibi.
- Her bölüm derinlikli olsun, yüzeysel geçme.
- Tüm veri kategorilerini mutlaka kullan.

━━━━━━━━ DASHBOARD VERİLERİ ({bugun}) ━━━━━━━━

🔶 KRİPTO FİYATLAR:
BTC: {v['BTC_P']} | 24s: {v['BTC_C']} | 7g: {v.get('BTC_7D','—')} | Hacim: {v['Vol_24h']}
ETH: {v['ETH_P']} (24s:{v['ETH_C']} 7g:{v.get('ETH_7D','—')})
SOL: {v['SOL_P']} (24s:{v['SOL_C']} 7g:{v.get('SOL_7D','—')})
BNB: {v['BNB_P']} (24s:{v['BNB_C']}) | XRP: {v['XRP_P']} (24s:{v['XRP_C']})
ADA: {v['ADA_P']} | AVAX: {v['AVAX_P']} | LINK: {v['LINK_P']} | DOT: {v['DOT_P']}
Korku/Açgözlülük: {v['FNG']} (dün: {v.get('FNG_PREV','—')})
BTC Dominance: {v['Dom']} | Total MCap: {v['Total_MCap']} | 24s Hacim: {v['Total_Vol']}

🔶 BITCOIN ETF:
IBIT: {v['IBIT_P']} ({v['IBIT_C']}) | Hacim: {v.get('IBIT_Vol','—')} | Akış: {v['IBIT_Flow']}
FBTC: {v['FBTC_P']} ({v['FBTC_C']}) | BITB: {v['BITB_P']} ({v['BITB_C']}) | ARKB: {v['ARKB_P']} ({v['ARKB_C']})

🔶 STABLECOİN LİKİDİTESİ:
Toplam: {v['Total_Stable']} | USDT: {v['USDT_MCap']} | USDC: {v['USDC_MCap']}

🔶 TÜREV PİYASALAR:
Long/Short: {v['LS_Ratio']} → {v['LS_Signal']}
Long: {v['Long_Pct']} | Short: {v['Short_Pct']}
Open Interest: {v['OI']} | Funding Rate: {v['FR']} | Taker B/S: {v.get('Taker','—')}

🔶 BALİNA DUVARLARI (Kraken):
🟢 Destek: {v['Sup_Wall']} ({v['Sup_Vol']} BTC bekliyor)
🔴 Direnç: {v['Res_Wall']} ({v['Res_Vol']} BTC bekliyor)

🔶 GLOBAL HİSSE ENDEKSLERİ:
SP500: {v['SP500']} ({v['SP500_C']}) | NASDAQ: {v['NASDAQ']} ({v['NASDAQ_C']})
DAX: {v['DAX']} ({v['DAX_C']}) | NIKKEI: {v['NIKKEI']} ({v['NIKKEI_C']})
BIST100: {v['BIST100']} ({v['BIST100_C']}) | VIX: {v['VIX']} ({v['VIX_C']})

🔶 FOREX & TAHVİL:
DXY: {v['DXY']} ({v['DXY_C']}) | EUR/USD: {v['EURUSD']} ({v['EURUSD_C']})
USD/TRY: {v['USDTRY']} ({v['USDTRY_C']}) | USD/JPY: {v['USDJPY']} ({v['USDJPY_C']})
ABD 10Y: {v['US10Y']} ({v['US10Y_C']})

🔶 EMTİALAR:
Altın: {v['GOLD']} ({v['GOLD_C']}) | Gümüş: {v['SILVER']} ({v['SILVER_C']})
Ham Petrol: {v['OIL']} ({v['OIL_C']}) | Doğalgaz: {v['NATGAS']} ({v['NATGAS_C']})

🔶 MAKRO & ON-CHAIN:
FED Faizi: {v['FED']} | M2 Büyümesi: {v['M2']}
BTC Hashrate: {v['Hash']} | BTC Korelasyon SP500: {v['Corr_SP500']} | Altın: {v['Corr_Gold']}

📅 EKONOMİK TAKVİM:
{takvim_str}

📰 KRİPTO HABERLERİ:
{haber_str}

━━━━━━━━ RAPOR YAPISI ━━━━━━━━

**🌅 Sabah Bülteni — {bugun}**

**1️⃣ Makro Ortam & Korelasyon**
SP500, VIX, DXY, tahvil faizi rakamlarını ver.
BTC'nin bu makro ortamla {v['Corr_SP500']} korelasyonunu yorumla.
Altın {v['GOLD']} ve petrol {v['OIL']} ne söylüyor?
USD/TRY {v['USDTRY']} TL bazlı yatırımcıyı nasıl etkiliyor?
M2 {v['M2']} ve FED {v['FED']} likidite mesajı ne?

**2️⃣ BTC Teknik & Türev Analizi**
Fiyat {v['BTC_P']}, 24s değişim, hacim {v['Vol_24h']}, 7 günlük trend.
Balina duvarı analizi — {v['Sup_Wall']}'deki {v['Sup_Vol']} BTC ne anlama gelir?
{v['Res_Wall']}'deki {v['Res_Vol']} BTC direnç ne kadar güçlü?
Funding {v['FR']} pozitif mi negatif mi, short squeeze/long liquidation riski var mı?
OI {v['OI']} — pozisyon birikimi tehlikeli mi?
L/S {v['LS_Ratio']} ({v['LS_Signal']}) — kalabalık taraf neresi, squeeze ihtimali?

**3️⃣ ETF & Likidite Akışları**
IBIT akış {v['IBIT_Flow']} — kurumsal para giriyor mu çıkıyor mu?
Stablecoin toplam {v['Total_Stable']} — piyasaya hazır para var mı?
USDT {v['USDT_MCap']} + USDC {v['USDC_MCap']} — likidite trendini yorumla.

**4️⃣ Altcoin Sinyalleri**
ETH {v['ETH_P']} ({v['ETH_C']}), SOL {v['SOL_P']} ({v['SOL_C']}), BNB {v['BNB_P']} rakamsal karşılaştır.
BTC dominance {v['Dom']} — altcoin sezonu yaklaşıyor mu uzaklaşıyor mu?
7 günlük performans farkını yorumla.

**5️⃣ Ekonomik Takvim**
Takvim varsa: hangi veri, saat, beklenti, piyasaya etkisi.
Takvim boşsa: bu hafta yaklaşan kritik veriler var mı? 
Takvim boş günlerde hangi faktörler yön belirler (ETF akış, balina, teknik)?

**6️⃣ Öne Çıkan Haberler**
En kritik 2 haberi seç, BTC/kripto üzerindeki olası etkisini açıkla.

**7️⃣ Günlük Aksiyon Planı**
📗 LONG: seviye, hedef, stop-loss (hepsi rakamsal)
📕 SHORT: seviye, hedef, stop-loss (hepsi rakamsal)
📒 BEKLE: hangi koşulda beklemek mantıklı

**⚠️ Bugünün En Kritik Riski** — tek cümle, rakamsal.
"""

    resp = client.chat.completions.create(
        model="google/gemini-2.0-flash-001",
        messages=[{"role":"user","content":prompt}],
        max_tokens=3000
    )
    return resp.choices[0].message.content


# =========================================================
# TELEGRAM GÖNDER
# =========================================================
def telegram_gonder(mesaj):
    max_len = 4000
    parcalar = [mesaj[i:i+max_len] for i in range(0, len(mesaj), max_len)]

    for parca in parcalar:
        # Önce Markdown ile dene
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": parca, "parse_mode": "Markdown"},
            timeout=10
        )
        # Markdown parse hatası → parse_mode olmadan düz metin gönder
        if not r.ok:
            print("⚠️ Markdown hatası, düz metin olarak yeniden deneniyor...")
            r2 = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": parca},
                timeout=10
            )
            if not r2.ok:
                raise Exception(f"Telegram gönderim başarısız: {r2.text}")

    print("✅ Rapor Telegram\'a gönderildi.")


# =========================================================
# ANA FONKSİYON
# =========================================================
if __name__ == "__main__":
    print("📡 Veriler çekiliyor...")
    v        = veri_cek()
    takvim   = takvim_cek()
    haberler = haber_cek()

    print("🤖 AI raporu oluşturuluyor...")
    rapor = ai_raporu(v, takvim, haberler)

    print("📨 Telegram'a gönderiliyor...")
    telegram_gonder(rapor)
