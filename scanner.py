#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
رادار الأسهم الحلال ومحرك إشارات ثاندر (EGX 33 Shariah & US Halal - Spot Only)
المصادر الموثقة:
- مؤشر الشريعة بالبورصة المصرية EGX 33: https://www.egx.com.eg/en/currentindexconstituntes.aspx?type=22&nav=22
- صندوق SPUS للأسهم الأمريكية الشرعية (AAOIFI): https://www.halalterminal.com/etf/spus
- منصة ثاندر للتداول الفوري (Thndr): https://thndr.app/
- مكتبة مؤشرات TradingView: https://pypi.org/project/tradingview-ta/
"""

import os
import urllib.parse
import xml.etree.ElementTree as ET
import requests
from tradingview_ta import TA_Handler, Interval

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# ==============================================================================
# 1. القائمة البيضاء المغلقة للأسهم المتوافقة مع الشريعة (Long / Spot Only)
# ==============================================================================
EGX33_SHARIAH_STOCKS = [
    {"symbol": "EGAS", "name": "غاز مصر", "query": "غاز مصر EGAS سهم"},
    {"symbol": "PHDC", "name": "بالم هيلز للتعمير", "query": "بالم هيلز PHDC سهم"},
    {"symbol": "AMOC", "name": "الإسكندرية للزيوت المعدنية أموك", "query": "أموك AMOC سهم"},
    {"symbol": "FAIT", "name": "بنك فيصل الإسلامي المصري", "query": "بنك فيصل الإسلامي FAIT"},
    {"symbol": "MPCO", "name": "المنصورة للدواجن", "query": "المنصورة للدواجن MPCO"},
    {"symbol": "ATQA", "name": "مصر الوطنية للصلب عتاقة", "query": "حديد عتاقة ATQA"},
    {"symbol": "ORWE", "name": "النساجون الشرقيون", "query": "النساجون الشرقيون ORWE"},
    {"symbol": "ETEL", "name": "المصرية للاتصالات", "query": "المصرية للاتصالات ETEL"},
    {"symbol": "EFIH", "name": "إي فاينانس", "query": "إي فاينانس EFIH سهم"},
    {"symbol": "EFID", "name": "إيديتا للصناعات الغذائية", "query": "إيديتا EFID سهم"},
    {"symbol": "ARCC", "name": "العربية للأسمنت", "query": "العربية للأسمنت ARCC"},
    {"symbol": "ORAS", "name": "أوراسكوم كونستراكشون", "query": "أوراسكوم كونستراكشون ORAS"},
    {"symbol": "ETRS", "name": "إيجيترانس", "query": "إيجيترانس ETRS سهم"},
    {"symbol": "ORHD", "name": "أوراسكوم للتنمية مصر", "query": "أوراسكوم للتنمية ORHD"},
    {"symbol": "MTIE", "name": "إم إم جروب MTI", "query": "إم إم جروب MTIE"},
    {"symbol": "ACGC", "name": "العربية لحليج الأقطان", "query": "العربية لحليج الأقطان ACGC"},
    {"symbol": "OCDI", "name": "سوديك", "query": "سوديك OCDI سهم"},
    {"symbol": "SKPC", "name": "سيدي كرير للبتروكيماويات", "query": "سيدي كرير SKPC سهم"},
]

US_HALAL_STOCKS = [
    {"symbol": "AVGO", "exchange": "NASDAQ", "name": "Broadcom Inc.", "query": "Broadcom AVGO stock AI"},
    {"symbol": "SPUS", "exchange": "AMEX",   "name": "SP Funds S&P 500 Sharia ETF", "query": "SPUS ETF S&P 500"},
    {"symbol": "LLY",  "exchange": "NYSE",   "name": "Eli Lilly & Co.", "query": "Eli Lilly LLY stock"},
    {"symbol": "TSLA", "exchange": "NASDAQ", "name": "Tesla Inc.", "query": "Tesla TSLA stock"},
    {"symbol": "AAPL", "exchange": "NASDAQ", "name": "Apple Inc.", "query": "Apple AAPL stock"},
    {"symbol": "NVDA", "exchange": "NASDAQ", "name": "NVIDIA Corp.", "query": "NVIDIA NVDA stock"},
]

# إعدادات المعادلة وإدارة المخاطر للمضاربة السريعة (Spot Cash Account)
TECH_WEIGHT = float(os.getenv("TECH_WEIGHT", "0.55"))
NEWS_WEIGHT = float(os.getenv("NEWS_WEIGHT", "0.45"))
TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", "4.5"))
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "2.0"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "").strip()
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "").strip()


# ==============================================================================
# 2. سحب الأخبار التلقائي من خلاصات Google News RSS (مجاني وبدون حظر)
# ==============================================================================
def fetch_latest_news_rss(search_query: str, lang: str = "ar", country: str = "EG", max_items: int = 3) -> list[str]:
    """يسحب أحدث عناوين الأخبار الخاصة بالسهم من Google News RSS."""
    encoded_q = urllib.parse.quote(search_query)
    hl = f"{lang}-{country}" if lang == "en" else "ar"
    ceid = f"{country}:{lang}"
    rss_url = f"https://news.google.com/rss/search?q={encoded_q}&hl={hl}&gl={country}&ceid={ceid}"

    headlines = []
    try:
        resp = requests.get(rss_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item")[:max_items]:
                title_el = item.find("title")
                if title_el is not None and title_el.text:
                    headlines.append(title_el.text.strip())
    except Exception as exc:
        print(f"[WARN] تعذر سحب أخبار RSS لـ {search_query}: {exc}")
    return headlines


# ==============================================================================
# 3. تحليل الأخبار بالذكاء الاصطناعي (Gemini API) مع بديل محلي فوري
# ==============================================================================
def local_keyword_sentiment(headlines: list[str]) -> tuple[int, str]:
    """محلل احتياطي للكلمات المفتاحية المالية في حال عدم توفر مفتاح Gemini أو انتهاء الكوتة."""
    if not headlines:
        return 50, "لا توجد أخبار طارئة اليوم؛ الاعتماد الأساسي على نقاط الدعم والمقاومة الفنية."

    joined = " ".join(headlines).lower()
    pos_words = [
        "ارتفاع", "نمو", "أرباح", "توزيعات", "توسع", "قفزة", "إيجابي", "عقود", "صعود",
        "surge", "growth", "beat", "bullish", "upgrade", "record", "rally", "gain"
    ]
    neg_words = [
        "تراجع", "انخفاض", "خسائر", "تحقيق", "هبوط", "ضغوط", "سلبي", "إيقاف",
        "drop", "fall", "investigation", "risk", "downgrade", "miss", "loss", "selloff"
    ]

    score = 50
    for w in pos_words:
        if w in joined:
            score += 12
    for w in neg_words:
        if w in joined:
            score -= 15

    score = max(-90, min(95, score))
    return score, headlines[0][:140]


def analyze_news_with_gemini(symbol: str, headlines: list[str]) -> tuple[int, str]:
    """يحلل عناوين الأخبار عبر Gemini 2.5 Flash ويعيد (درجة من -100 إلى 100، ملخص قصير)."""
    if not headlines:
        return 50, "لا توجد أخبار جديدة مؤثرة خلال الساعات الأخيرة."

    if not GEMINI_API_KEY or not HAS_GENAI:
        return local_keyword_sentiment(headlines)

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        news_bullet_list = "\n".join(f"- {h}" for h in headlines)
        prompt = (
            f"أنت محلل مالي للأسهم المتوافقة مع الشريعة (تداول فوري Spot بدون بيع على المكشوف). "
            f"قيّم أثر الأخبار التالية على سهم {symbol} في المضاربة القصيرة.\n"
            f"السطر الأول: اكتب رقماً صحيحاً فقط بين -100 و 100.\n"
            f"السطر الثاني: اكتب ملخصاً بالعربية في جملة واحدة قصيرة.\n\n"
            f"الأخبار:\n{news_bullet_list}"
        )
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        lines = [line.strip() for line in (resp.text or "").strip().splitlines() if line.strip()]
        if lines:
            num_str = "".join(c for c in lines[0] if c in "-0123456789")
            score = max(-100, min(100, int(num_str))) if num_str else 50
            summary = lines[1] if len(lines) > 1 else headlines[0][:140]
            return score, summary
    except Exception as exc:
        print(f"[WARN] تعذر تحليل Gemini لسهم {symbol}، سيتم استخدام المحلل المحلي: {exc}")

    return local_keyword_sentiment(headlines)


# ==============================================================================
# 4. سحب المؤشرات الفنية من TradingView وحساب الدرجة الفنية (0 إلى 100)
# ==============================================================================
def fetch_technical_score(symbol: str, screener: str, exchange: str) -> dict | None:
    """يسحب مؤشرات RSI وMACD والمتوسطات المتحركة ويحسب درجة فنية من 0 إلى 100."""
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener=screener,
            exchange=exchange,
            interval=Interval.INTERVAL_1_HOUR
        )
        analysis = handler.get_analysis()
        ind = analysis.indicators

        close_price = float(ind.get("close") or 0.0)
        if close_price <= 0:
            return None

        rsi = float(ind.get("RSI") or 50.0)
        macd = float(ind.get("MACD.macd") or 0.0)
        macd_sig = float(ind.get("MACD.signal") or 0.0)
        ema20 = float(ind.get("EMA20") or close_price)
        rec = analysis.summary.get("RECOMMENDATION", "NEUTRAL")

        base_map = {
            "STRONG_BUY": 85,
            "BUY": 74,
            "NEUTRAL": 52,
            "SELL": 35,
            "STRONG_SELL": 20
        }
        tech_score = base_map.get(rec, 50)

        if macd > macd_sig:
            tech_score += 6
        if close_price >= ema20:
            tech_score += 4
        if 30 <= rsi <= 45:
            tech_score += 5
        elif rsi >= 75:
            tech_score -= 8

        tech_score = max(5, min(98, int(tech_score)))

        return {
            "price": round(close_price, 2),
            "rsi": round(rsi, 1),
            "macd_bullish": macd > macd_sig,
            "tv_rec": rec,
            "tech_score": tech_score
        }
    except Exception as exc:
        print(f"[WARN] تعذر سحب بيانات TradingView لسهم {symbol}: {exc}")
        return None


# ==============================================================================
# 5. محرك القرار وإرسال تنبيهات تليجرام الجاهزة للتنفيذ على ثاندر (Thndr)
# ==============================================================================
def evaluate_stock(item: dict, is_egypt: bool = True) -> dict | None:
    symbol = item["symbol"]
    screener = "egypt" if is_egypt else "america"
    exchange = "EGX" if is_egypt else item["exchange"]
    currency = "ج.م" if is_egypt else "$"

    ta_data = fetch_technical_score(symbol, screener, exchange)
    if not ta_data:
        return None

    headlines = fetch_latest_news_rss(
        item["query"],
        lang="ar" if is_egypt else "en",
        country="EG" if is_egypt else "US"
    )
    news_score, news_summary = analyze_news_with_gemini(symbol, headlines)

    normalized_news = max(0, min(100, round((news_score + 100) / 2)))
    composite = round(ta_data["tech_score"] * TECH_WEIGHT + normalized_news * NEWS_WEIGHT)

    if composite >= 72:
        signal_type = "BUY"
        signal_ar = "🟢 شراء فوري (Buy Spot)"
    elif composite <= 42:
        signal_type = "SELL"
        signal_ar = "🔴 جني أرباح / بيع ما تملكه"
    else:
        signal_type = "WATCH"
        signal_ar = "🟡 انتظار ومراقبة"

    price = ta_data["price"]
    tp_price = round(price * (1 + TAKE_PROFIT_PCT / 100.0), 2)
    sl_price = round(price * (1 - STOP_LOSS_PCT / 100.0), 2)

    return {
        "symbol": symbol,
        "name": item["name"],
        "market": "EGX 33 Shariah" if is_egypt else "US Halal (AAOIFI)",
        "currency": currency,
        "price": price,
        "tp_price": tp_price,
        "sl_price": sl_price,
        "rsi": ta_data["rsi"],
        "tv_rec": ta_data["tv_rec"],
        "tech_score": ta_data["tech_score"],
        "news_score": news_score,
        "news_summary": news_summary,
        "composite": composite,
        "signal_type": signal_type,
        "signal_ar": signal_ar
    }


def send_telegram_message(text: str) -> None:
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("[INFO] لم يتم ضبط TG_BOT_TOKEN أو TG_CHAT_ID؛ طباعة التقرير في الـ Console:")
        print(text)
        return

    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": text}, timeout=12)
        if resp.status_code == 200:
            print("[OK] تم إرسال تنبيه الإشارات إلى تليجرام بنجاح.")
        else:
            print(f"[ERROR] فشل إرسال تليجرام: {resp.text}")
    except Exception as exc:
        print(f"[ERROR] خطأ أثناء الاتصال بتليجرام: {exc}")


def main() -> None:
    actionable_signals = []

    print("=== فحص أسهم مؤشر الشريعة المصري EGX 33 ===")
    for stock in EGX33_SHARIAH_STOCKS:
        res = evaluate_stock(stock, is_egypt=True)
        if res and res["signal_type"] in ("BUY", "SELL"):
            actionable_signals.append(res)

    print("=== فحص الأسهم الأمريكية الشرعية (AAOIFI / SPUS) ===")
    for stock in US_HALAL_STOCKS:
        res = evaluate_stock(stock, is_egypt=False)
        if res and res["signal_type"] in ("BUY", "SELL"):
            actionable_signals.append(res)

    actionable_signals.sort(key=lambda x: x["composite"], reverse=True)

    if not actionable_signals:
        send_telegram_message("☪ رادار الأسهم الشرعية (ثاندر): لا توجد إشارات شراء أو بيع حاسمة في هذه الجولة؛ جميع الأسهم في منطقة المراقبة.")
        return

    lines = ["☪ تقرير إشارات الأسهم الشرعية الفورية (منصة ثاندر - Spot Only)\n"]
    for sig in actionable_signals[:8]:
        c = sig["currency"]
        lines.append(
            f"{sig['signal_ar']}\n"
            f"• السهم: {sig['name']} ({sig['symbol']}) [{sig['market']}]\n"
            f"• الدرجة المركبة: {sig['composite']}/100 (فني: {sig['tech_score']} | أخبار: {sig['news_score']})\n"
            f"• سعر الدخول (Entry): {sig['price']} {c}\n"
            f"• هدف البيع (TP +{TAKE_PROFIT_PCT}%): {sig['tp_price']} {c}\n"
            f"• وقف الخسارة (SL -{STOP_LOSS_PCT}%): {sig['sl_price']} {c}\n"
            f"• RSI(1H): {sig['rsi']} | TradingView: {sig['tv_rec']}\n"
            f"• الخبر: {sig['news_summary']}\n"
            f"────────────────────"
        )

    send_telegram_message("\n".join(lines))


if __name__ == "__main__":
    main()
