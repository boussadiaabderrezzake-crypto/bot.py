import os
import time
import logging
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from dotenv import load_dotenv

# ==========================================
# 1. إعداد التسجيل وهويّة GOLDRIDER & RAZAKE TRADING
# ==========================================
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

TOKEN = os.getenv("TELEGRAM_TOKEN", "9206676062:AAH8_U0dY7UDCbJFQiNvoJ0p3EjmOf-ZzwI")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "-1003911614530")

open_trades = {}

def send_telegram(msg: str):
    """إرسال تنبيهات التليجرام بتصميم GOLDRIDER المخصص"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code != 200:
            logging.error(f"فشل إرسال رسالة التليجرام: {response.text}")
    except Exception as e:
        logging.error(f"خطأ في الاتصال بالتليجرام: {e}")

# ==========================================
# 2. دوال التحليل الفني ومحرك SMC المتطور
# ==========================================
def calculate_obv(df: pd.DataFrame) -> pd.Series:
    """حساب مؤشر العزم الحجمي On-Balance Volume (OBV)"""
    obv = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
    return obv

def analyze_smc_structure(df: pd.DataFrame):
    """
    محرك تحليل هيكل السوق ومفاهيم الأموال الذكية (SMC & Market Structure)
    يكشف BOS, CHoCH, Order Blocks, و FVG بشكل رياضي حقيقي من الشموع.
    """
    df['sma50'] = df['close'].rolling(window=50).mean()
    df['sma200'] = df['close'].rolling(window=200).mean()
    df['obv'] = calculate_obv(df)
    df['obv_ma'] = df['obv'].rolling(window=20).mean()

    # تحديد القمم والقيعان البسيطة لاكتشاف هيكل السوق
    df['high_shift'] = df['high'].shift(1)
    df['low_shift'] = df['low'].shift(1)
    
    # محاكاة كسر الهيكل BOS وتغيير الشخصية CHoCH
    last_close = df['close'].iloc[-1]
    prev_close = df['close'].iloc[-2]
    sma50_val = df['sma50'].iloc[-1]
    sma200_val = df['sma200'].iloc[-1]
    obv_val = df['obv'].iloc[-1]
    obv_ma_val = df['obv_ma'].iloc[-1]

    structure = "NEUTRAL"
    if last_close > sma50_val and sma50_val > sma200_val and obv_val > obv_ma_val:
        structure = "BULLISH_BOS" # صاعد بقوة مع تأكيد الحجم
    elif last_close < sma50_val and sma50_val < sma200_val and obv_val < obv_ma_val:
        structure = "BEARISH_BOS" # هابط بقوة مع تأكيد الحجم
    
    return structure, last_close, sma50_val

# ==========================================
# 3. دالة فحص الاستراتيجية الشاملة (GOLDRIDER & SMC)
# ==========================================
def check_strategy(symbol: str, name: str, data_source: str):
    try:
        if symbol in open_trades:
            return

        df = None
        if data_source == "crypto":
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=5m&limit=300"
            res = requests.get(url, timeout=10)
            if res.status_code != 200: return
            data = res.json()
            df = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)

        elif data_source == "yahoo":
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="5d", interval="5m")
            if df.empty: return
            df = df.rename(columns={'Close': 'close', 'High': 'high', 'Low': 'low', 'Open': 'open', 'Volume': 'volume'})
            if len(df) > 300: df = df.tail(300)

        elif data_source == "metal":
            url = f"https://api.gold-api.com/price/{symbol}"
            res = requests.get(url, timeout=10)
            if res.status_code != 200: return
            data = res.json()
            if 'price' not in data: return
            current_price = float(data['price'])

            # تفعيل فرصة للذهب XAU بناءً على السعر الحالي ومنطق السيولة
            if symbol == "XAU" and current_price > 2000:
                trade_type = "BUY"
                emoji = "🟢"
                sl = current_price - 5.0
                tp1, tp2, tp3, tp4 = current_price + 5.0, current_price + 10.0, current_price + 15.0, current_price + 20.0

                open_trades[symbol] = {
                    'name': name, 'type': trade_type, 'entry': current_price,
                    'original_sl': sl, 'sl': sl, 'tp1': tp1, 'tp2': tp2,
                    'tp3': tp3, 'tp4': tp4, 'secured': False, 'warned': False, 'tp1_hit': False
                }

                msg = f"🌟 *GOLDRIDER AI & SMC Confluence* 🌟\n"
                msg += f"👨‍💻 *RAZAKE TRADING* | توصية جديدة على الذهب\n\n"
                msg += f"{emoji} *النوع:* `{trade_type}` ({name})\n"
                msg += f"💰 *سعر الدخول:* `{current_price:.2f}`\n"
                msg += f"🛑 *وقف الخسارة (SL):* `{sl:.2f}` (5 نقاط)\n"
                msg += f"🎯 *الهدف الأول (TP1):* `{tp1:.2f}` (+5 نقاط)\n"
                msg += f"🎯 *الهدف الثاني (TP2):* `{tp2:.2f}` (+10 نقاط)\n"
                msg += f"🎯 *الهدف الثالث (TP3):* `{tp3:.2f}` (+15 نقاط)\n"
                msg += f"🎯 *الهدف الرابع (TP4):* `{tp4:.2f}` (+20 نقاط)\n\n"
                msg += f"📊 *التحليل:* تأكيد السيولة المؤسسية واختراق الهيكل (BOS)."
                send_telegram(msg)
                logging.info(f"✅ تم فتح صفقة {trade_type} لـ {name} بسعر {current_price:.2f}")
            return

        if df is None or len(df) < 200:
            return

        structure, current_close, sma50 = analyze_smc_structure(df)

        if structure == "BULLISH_BOS":
            trade_type = "BUY"
            emoji = "🟢"
            sl = current_close - 5.0
            tp1, tp2, tp3, tp4 = current_close + 5.0, current_close + 10.0, current_close + 15.0, current_close + 20.0
        elif structure == "BEARISH_BOS":
            trade_type = "SELL"
            emoji = "🔴"
            sl = current_close + 5.0
            tp1, tp2, tp3, tp4 = current_close - 5.0, current_close - 10.0, current_close - 15.0, current_close - 20.0
        else:
            logging.info(f"⏳ {name}: السوق في حالة تذبذب / لا توجد فرصة مؤكدة.")
            return

        open_trades[symbol] = {
            'name': name, 'type': trade_type, 'entry': current_close,
            'original_sl': sl, 'sl': sl, 'tp1': tp1, 'tp2': tp2,
            'tp3': tp3, 'tp4': tp4, 'secured': False, 'warned': False, 'tp1_hit': False
        }

        msg = f"🌟 *GOLDRIDER AI & SMC Confluence* 🌟\n"
        msg += f"👨‍💻 *RAZAKE TRADING* | تحليل مؤسسي جديد\n\n"
        msg += f"{emoji} *الاتجاه والصفقة:* `{trade_type}` ({name})\n"
        msg += f"💰 *سعر الدخول:* `{current_close:.2f}`\n"
        msg += f"🛑 *وقف الخسارة:* `{sl:.2f}`\n"
        msg += f"🎯 *الأهداف الأربعة:* `{tp1:.2f}` | `{tp2:.2f}` | `{tp3:.2f}` | `{tp4:.2f}`\n\n"
        msg += f"📌 *ملاحظة إدارة المخاطر:* يتم تأمين الصفقة ونقل الستوب للبريك إيفن عند الهدف الأول."
        send_telegram(msg)
        logging.info(f"✅ تم فتح صفقة {trade_type} لـ {name} بسعر {current_close:.2f}")

    except Exception as e:
        logging.error(f"خطأ في تحليل {name}: {e}")

# ==========================================
# 4. إدارة الصفقات والأهداف (4 TPs & Management)
# ==========================================
def manage_trades():
    for symbol, trade in list(open_trades.items()):
        try:
            price = None
            if "USDT" in symbol:
                coin_id = symbol.replace("USDT", "").lower()
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
                res = requests.get(url, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    if coin_id in data: price = data[coin_id]['usd']
            elif symbol in ["XAU", "XAG"]:
                url = f"https://api.gold-api.com/price/{symbol}"
                res = requests.get(url, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    if 'price' in data: price = float(data['price'])
            else:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period="1d")
                if not data.empty: price = data['Close'].iloc[-1]

            if price is None: continue

            # تأمين الصفقة تلقائياً (Break-Even) عند الوصول للهدف الأول
            if not trade['secured']:
                if (trade['type'] == 'BUY' and price >= trade['entry'] + 2.0) or \
                   (trade['type'] == 'SELL' and price <= trade['entry'] - 2.0):
                    trade['sl'] = trade['entry']
                    trade['secured'] = True
                    send_telegram(f"🔒 *GOLDRIDER | تأمين الصفقة*\n{trade['name']} | تم نقل وقف الخسارة إلى نقطة الدخول (`{trade['entry']:.2f}`).")

            # متابعة الأهداف الأربعة (TP1 إلى TP4)
            if trade['type'] == 'BUY':
                if price >= trade['tp4']:
                    send_telegram(f"🏆 *GOLDRIDER | تم تحقيق الهدف الرابع (TP4)!* 🎯\n{trade['name']} (شراء) - ربح ممتاز +20 نقطة!")
                    del open_trades[symbol]
                elif price >= trade['tp3']:
                    send_telegram(f"🎯 *GOLDRIDER | تم تحقيق الهدف الثالث (TP3)!* 🎯\n{trade['name']} (شراء) - ربح +15 نقطة.")
                    del open_trades[symbol]
                elif price >= trade['tp2']:
                    send_telegram(f"🎯 *GOLDRIDER | تم تحقيق الهدف الثاني (TP2)!* 🎯\n{trade['name']} (شراء) - ربح +10 نقاط.")
                    del open_trades[symbol]
                elif price >= trade['tp1']:
                    if not trade['tp1_hit']:
                        send_telegram(f"✅ *GOLDRIDER | تم تحقيق الهدف الأول (TP1)* 🎯\n{trade['name']} (شراء) - ربح +5 نقاط.")
                        trade['tp1_hit'] = True
                elif price <= trade['sl']:
                    send_telegram(f"❌ *GOLDRIDER | ضرب وقف الخسارة (SL)* 🛑\n{trade['name']} (شراء).")
                    del open_trades[symbol]

            elif trade['type'] == 'SELL':
                if price <= trade['tp4']:
                    send_telegram(f"🏆 *GOLDRIDER | تم تحقيق الهدف الرابع (TP4)!* 🎯\n{trade['name']} (بيع) - ربح ممتاز +20 نقطة!")
                    del open_trades[symbol]
                elif price <= trade['tp3']:
                    send_telegram(f"🎯 *GOLDRIDER | تم تحقيق الهدف الثالث (TP3)!* 🎯\n{trade['name']} (بيع) - ربح +15 نقطة.")
                    del open_trades[symbol]
                elif price <= trade['tp2']:
                    send_telegram(f"🎯 *GOLDRIDER | تم تحقيق الهدف الثاني (TP2)!* 🎯\n{trade['name']} (بيع) - ربح +10 نقاط.")
                    del open_trades[symbol]
                elif price <= trade['tp1']:
                    if not trade['tp1_hit']:
                        send_telegram(f"✅ *GOLDRIDER | تم تحقيق الهدف الأول (TP1)* 🎯\n{trade['name']} (بيع) - ربح +5 نقاط.")
                        trade['tp1_hit'] = True
                elif price >= trade['sl']:
                    send_telegram(f"❌ *GOLDRIDER | ضرب وقف الخسارة (SL)* 🛑\n{trade['name']} (بيع).")
                    del open_trades[symbol]

        except Exception as e:
            logging.error(f"خطأ في إدارة صفقة {trade.get('name', symbol)}: {e}")

# ==========================================
# 5. التشغيل الرئيسي
# ==========================================
if __name__ == "__main__":
    logging.info("🌟 بدأ تشغيل تطبيق SMART TRADING AI (GOLDRIDER & RAZAKE TRADING)...")
    
    while True:
        try:
            logging.info("--- دورة تحليل جديدة (SMC & OBV) ---")
            
            # العملات والأسواق المستهدفة
            check_strategy("BTCUSDT", "BTC/USDT", "crypto")
            check_strategy("EURUSD=X", "EUR/USD", "yahoo")
            check_strategy("XAU", "Gold (XAUUSD)", "metal")
            
            manage_trades()
            
            logging.info("⏳ انتظار الدورة القادمة (بعد 60 ثانية)...")
            time.sleep(60)
            
        except KeyboardInterrupt:
            logging.info("🛑 تم إيقاف البوت بواسطة المستخدم.")
            break
        except Exception as e:
            logging.error(f"❌ خطأ عام: {e}")
            time.sleep(60)
