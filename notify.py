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

    # BTC
    try:
        r = requests.get(
            "https://api.coinpaprika.com/v1/tickers/btc-bitcoin",
            headers=HEADERS, timeout=8).json()["quotes"]["USD"]
        v["BTC_P"]   = f"${r['price']:,.0f}"
        v["BTC_C"]   = f"{r['percent_change_24h']:.2f}%"
        v["Vol_24h"] = f"${r['volume_24h']:,.0f}"
    except:
        v["BTC_P"]="—"; v["BTC_C"]="—"; v["Vol_24h"]="—"

    # Altcoinler
    alt_ids = {"ETH":"eth-ethereum","SOL":"sol-solana","BNB":"bnb-binance-coin","XRP":"xrp-xrp"}
    for sym, cid in alt_ids.items():
        try:
            r = requests.get(f"https://api.coinpaprika.com/v1/tickers/{cid}",
                             headers=HEADERS, timeout=6).json()["quotes"]["USD"]
            v[f"{sym}_P"] = f"${r['price']:,.2f}"
            v[f"{sym}_C"] = f"{r['percent_change_24h']:.2f}%"
        except:
            v[f"{sym}_P"]="—"; v[f"{sym}_C"]="—"

    # Makro
    for key, sym in [("SP500","^GSPC"),("VIX","^VIX"),("DXY","DX-Y.NYB"),
                     ("GOLD","GC=F"),("US10Y","^TNX"),("USDTRY","TRY=X")]:
        try:
            df = yf.Ticker(sym).history(period="5d")
            curr=df["Close"].iloc[-1]; prev=df["Close"].iloc[-2]
            v[key]=f"{curr:,.2f}"; v[f"{key}_C"]=f"{(curr-prev)/prev*100:.2f}%"
        except:
            v[key]="—"; v[f"{key}_C"]="—"

    # Korku/Açgözlülük
    try:
        fng = requests.get("https://api.alternative.me/fng/",timeout=5).json()["data"][0]
        v["FNG"] = f"{fng['value']} ({fng['value_classification']})"
    except: v["FNG"]="—"

    # Balina duvarları (Kraken)
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
        sw,sv=bkt(fb,lambda p:int(p/bs)*bs)
        rw,rv=bkt(fa,lambda p:int((p/bs)+1)*bs)
        v["Sup_Wall"]=f"${sw:,}"; v["Sup_Vol"]=f"{int(sv):,} BTC"
        v["Res_Wall"]=f"${rw:,}"; v["Res_Vol"]=f"{int(rv):,} BTC"
    except:
        v["Sup_Wall"]="—"; v["Sup_Vol"]="—"; v["Res_Wall"]="—"; v["Res_Vol"]="—"

    # OI & Funding (Kraken Futures)
    try:
        kt = requests.get("https://futures.kraken.com/derivatives/api/v3/tickers",
                          headers=HEADERS, timeout=6).json()
        t  = next((x for x in kt["tickers"] if x["symbol"]=="PF_XBTUSD"), None)
        if t:
            v["OI"] = f"{t.get('openInterest','—'):,.0f} BTC"
            fr = t.get("fundingRate")
            v["FR"] = f"%{float(fr)*100:.4f}" if fr else "—"
    except: v["OI"]="—"; v["FR"]="—"

    # Long/Short (Bitfinex)
    try:
        lv = abs(float(requests.get(
            "https://api-pub.bitfinex.com/v2/stats1/pos.size:1m:tBTCUSD:long/hist?limit=1",
            headers=HEADERS, timeout=6).json()[0][1]))
        sv2= abs(float(requests.get(
            "https://api-pub.bitfinex.com/v2/stats1/pos.size:1m:tBTCUSD:short/hist?limit=1",
            headers=HEADERS, timeout=6).json()[0][1]))
        tot= lv+sv2; ratio=lv/sv2 if sv2>0 else 1
        v["LS_Ratio"]=f"{ratio:.3f}"
        v["Long_Pct"]=f"%{lv/tot*100:.1f}"
        v["Short_Pct"]=f"%{sv2/tot*100:.1f}"
        v["LS_Signal"]="🟢 Long Ağırlıklı" if ratio>1 else "🔴 Short Ağırlıklı"
    except:
        v["LS_Ratio"]="—"; v["Long_Pct"]="—"; v["Short_Pct"]="—"; v["LS_Signal"]="—"

    # Stablecoin (DeFiLlama)
    try:
        sc   = requests.get("https://stablecoins.llama.fi/stablecoins?includePrices=true",
                            headers=HEADERS, timeout=8).json()["peggedAssets"]
        total= sum(c.get("circulating",{}).get("peggedUSD",0) for c in sc)
        v["Total_Stable"] = f"${total/1e9:.1f}B"
    except: v["Total_Stable"]="—"

    # M2 & FED (FRED)
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
    try:
        rss = requests.get(
            "https://tradingeconomics.com/rss/calendar.aspx",
            headers=HEADERS, timeout=8).text
        titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", rss)[1:8]
        today  = pd.Timestamp.now(tz="Europe/Istanbul").strftime("%a, %d %b")
        bugun  = [t for t in titles if any(k in t for k in ["USD","EUR","Fed","CPI","NFP","GDP","PMI","FOMC","Powell"])]
        return bugun[:5] if bugun else titles[:4]
    except:
        return []


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

    prompt = f"""
Sen deneyimli bir makro-kripto fon yöneticisisin.
Aşağıdaki GERÇEK sabah verilerini analiz ederek Serhat için kısa, net ve eyleme dönüşebilir 
bir günlük strateji bülteni hazırla. Türkçe yaz. Telegram için uygun formatta, 
emoji kullan, başlıkları kalın yap (**başlık**).

📊 PİYASA VERİLERİ:
BTC: {v['BTC_P']} ({v['BTC_C']})
ETH: {v['ETH_P']} ({v['ETH_C']}) | SOL: {v['SOL_P']} ({v['SOL_C']})
SP500: {v['SP500']} ({v['SP500_C']}) | VIX: {v['VIX']} | DXY: {v['DXY']} ({v['DXY_C']})
Altın: {v['GOLD']} ({v['GOLD_C']}) | USD/TRY: {v['USDTRY']}
US10Y: {v['US10Y']} | FED: {v['FED']} | M2: {v['M2']}
Korku/Açgözlülük: {v['FNG']}
Destek Duvarı: {v['Sup_Wall']} ({v['Sup_Vol']})
Direnç Duvarı: {v['Res_Wall']} ({v['Res_Vol']})
Long/Short: {v['LS_Ratio']} ({v['LS_Signal']}) | Long: {v['Long_Pct']} | Short: {v['Short_Pct']}
OI: {v['OI']} | Funding: {v['FR']}
Stablecoin: {v['Total_Stable']}

📅 BUGÜNKÜ EKONOMİK TAKVİM:
{takvim_str}

📰 SON KRİPTO HABERLERİ:
{haber_str}

Rapor yapısı (kısa tut, Telegram'a sığsın):
**🌅 Sabah Bülteni — [TARİH]**
**📈 Makro Durum** — 2-3 cümle
**₿ BTC Analizi** — fiyat, duvarlar, yön tahmini
**📅 Bugünün Kritik Olayları** — takvimden önemli olanlar
**📰 Öne Çıkan Haber** — en kritik 1-2 haber
**🎯 Günlük Aksiyon** — Long/Short/Bekle + seviyeler
**⚠️ Risk** — bugün dikkat edilmesi gereken 1 şey
"""

    resp = client.chat.completions.create(
        model="google/gemini-2.0-flash-001",
        messages=[{"role":"user","content":prompt}],
        max_tokens=1200
    )
    return resp.choices[0].message.content


# =========================================================
# TELEGRAM GÖNDER
# =========================================================
def telegram_gonder(mesaj):
    # Mesajı 4000 karakterlik parçalara böl (Telegram limiti)
    max_len = 4000
    parcalar = [mesaj[i:i+max_len] for i in range(0, len(mesaj), max_len)]

    for parca in parcalar:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": parca,
                "parse_mode": "Markdown"
            },
            timeout=10
        )
        if not r.ok:
            print(f"Telegram hatası: {r.text}")
            raise Exception(f"Telegram gönderim başarısız: {r.text}")

    print("✅ Rapor Telegram'a gönderildi.")


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
