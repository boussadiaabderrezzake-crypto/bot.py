import streamlit as st
import requests
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

# ==========================================
# 1. إعدادات الصفحة والتصميم
# ==========================================
st.set_page_config(
    page_title="SMART TRADING AI | GOLDRIDER",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #e6edf3; }
    .main-title { color: #d4af37; text-align: center; font-size: 2.2rem; font-weight: bold; margin-bottom: 0.2rem; }
    .sub-title { color: #58a6ff; text-align: center; font-size: 1.1rem; margin-bottom: 2rem; }
    .card { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1.2rem; margin-bottom: 1rem; }
    .metric-value { color: #d4af37; font-size: 1.5rem; font-weight: bold; }
    .stButton>button { background-color: #1f6feb; color: white; border-radius: 6px; border: none; width: 100%; font-weight: bold; }
    .stButton>button:hover { background-color: #388bfd; color: white; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. بيانات التيليجرام
# ==========================================
TELEGRAM_TOKEN = "9206676062:AAH8_U0dY7UDCbJFQiNvoJ0p3EjmOf-ZzwI"
TELEGRAM_CHAT_ID = "-1003911614530"

def send_telegram_alert(msg: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        st.error(f"خطأ إرسال التليجرام: {e}")

# ==========================================
# 3. محرك التحليل (SMC + OBV)
# ==========================================
def calculate_obv(df):
    return (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()

def fetch_data(symbol, period="5d", interval="5m"):
    if symbol == "XAUUSD":
        ticker_symbol = "GC=F"
    elif symbol == "EURUSD":
        ticker_symbol = "EURUSD=X"
    elif symbol == "BTCUSD":
        ticker_symbol = "BTC-USD"
    else:
        ticker_symbol = symbol

    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period=period, interval=interval)
    return df

def analyze_smc(df):
    if len(df) < 50:
        return None
    
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()
    df['OBV'] = calculate_obv(df)
    df['OBV_MA'] = df['OBV'].rolling(window=20).mean()
    
    last_close = df['Close'].iloc[-1]
    sma50 = df['SMA50'].iloc[-1]
    sma200 = df['SMA200'].iloc[-1]
    obv = df['OBV'].iloc[-1]
    obv_ma = df['OBV_MA'].iloc[-1]
    
    fvg_type = None
    if len(df) >= 3:
        if df['Low'].iloc[-1] > df['High'].iloc[-3]:
            fvg_type = "Bullish FVG"
        elif df['High'].iloc[-1] < df['Low'].iloc[-3]:
            fvg_type = "Bearish FVG"

    structure = "تذبذب / غير محدد"
    signal = "NEUTRAL"
    if last_close > sma50 and sma50 > sma200 and obv > obv_ma:
        structure = "اختراق صاعد صريح (Bullish BOS)"
        signal = "BUY"
    elif last_close < sma50 and sma50 < sma200 and obv < obv_ma:
        structure = "اختراق هابط صريح (Bearish BOS)"
        signal = "SELL"
        
    return {
        "price": last_close,
        "structure": structure,
        "signal": signal,
        "fvg": fvg_type or "لا توجد فجوة حالية",
        "obv_status": "سيولة صاعدة" if obv > obv_ma else "سيولة هابطة",
    }

# ==========================================
# 4. واجهة التطبيق
# ==========================================
st.markdown('<div class="main-title">🌟 SMART TRADING AI 🌟</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">محرك التحليل المؤسسي والسيولة | GOLDRIDER & RAZAKE TRADING</div>', unsafe_allow_html=True)

st.sidebar.header("🕹️ لوحة التحكم")
symbol = st.sidebar.selectbox("اختر الأصول / الزوج:", ["XAUUSD", "EURUSD", "BTCUSD", "AAPL", "TSLA"])
timeframe = st.sidebar.selectbox("الإطار الزمني:", ["5m", "15m", "1h", "1d"])

period = "5d" if timeframe in ["5m", "15m"] else "1mo"
data = fetch_data(symbol, period=period, interval=timeframe)

tab1, tab2, tab3 = st.tabs(["📊 التحليل المباشر والتوصية", "🧮 حاسبة المخاطر", "📜 سجل ورسائل التليجرام"])

with tab1:
    if not data.empty:
        results = analyze_smc(data)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("السعر الحالي", f"${results['price']:.2f}")
        col2.metric("إشارة السوق", results['signal'])
        col3.metric("تدفق السيولة (OBV)", results['obv_status'])
        col4.metric("الفجوة السعرية (FVG)", results['fvg'])

        st.markdown("---")
        
        col_chart, col_info = st.columns([2, 1])
        
        with col_chart:
            st.subheader(f"رسم بياني حي لـ {symbol}")
            fig = go.Figure(data=[go.Candlestick(
                x=data.index,
                open=data['Open'], high=data['High'],
                low=data['Low'], close=data['Close'],
                name="Price"
            )])
            fig.update_layout(template="plotly_dark", margin=dict(l=10, r=10, t=10, b=10), height=450)
            st.plotly_chart(fig, use_container_width=True)

        with col_info:
            st.subheader("📋 تقرير التداول المؤسسي")
            st.write(f"**هيكل السوق:** {results['structure']}")
            
            entry = results['price']
            if results['signal'] == "BUY":
                sl = entry - 5.0
                tp1, tp2, tp3, tp4 = entry + 5.0, entry + 10.0, entry + 15.0, entry + 20.0
            else:
                sl = entry + 5.0
                tp1, tp2, tp3, tp4 = entry - 5.0, entry - 10.0, entry - 15.0, entry - 20.0

            st.write(f"🛑 **وقف الخسارة (SL):** `{sl:.2f}`")
            st.write(f"🎯 **الهدف 1 (TP1):** `{tp1:.2f}` (+5)")
            st.write(f"🎯 **الهدف 2 (TP2):** `{tp2:.2f}` (+10)")
            st.write(f"🎯 **الهدف 3 (TP3):** `{tp3:.2f}` (+15)")
            st.write(f"🎯 **الهدف 4 (TP4):** `{tp4:.2f}` (+20)")

            if st.button("📲 إرسال التقرير لتليجرام"):
                msg = f"🌟 *GOLDRIDER AI SIGNAL* 🌟\n\n" \
                      f"📈 *الزوج:* {symbol}\n" \
                      f"🔹 *النوع:* `{results['signal']}`\n" \
                      f"💰 *الدخول:* `{entry:.2f}`\n" \
                      f"🛑 *الستوب:* `{sl:.2f}`\n" \
                      f"🎯 *الأهداف:* `{tp1:.2f}` | `{tp2:.2f}` | `{tp3:.2f}` | `{tp4:.2f}`\n\n" \
                      f"👨‍💻 *RAZAKE TRADING*"
                send_telegram_alert(msg)
                st.success("تم إرسال التوصية إلى التليجرام بنجاح!")
    else:
        st.error("تعذر جلب البيانات الحالية. يرجى المحاولة لاحقاً.")

with tab2:
    st.subheader("🧮 حاسبة حجم العقود (Position Size & Risk Calculator)")
    col_r1, col_r2 = st.columns(2)
    
    with col_r1:
        balance = st.number_input("رأس المال ($)", value=10000.0, step=500.0)
        risk_percent = st.number_input("نسبة المخاطرة (%)", value=1.0, step=0.5)
        entry_price = st.number_input("سعر الدخول", value=results['price'] if 'results' in locals() else 2000.0)
    
    with col_r2:
        stop_loss_price = st.number_input("سعر وقف الخسارة", value=entry_price - 5.0 if 'entry_price' in locals() else 1995.0)
        take_profit_price = st.number_input("سعر الهدف الأول", value=entry_price + 5.0 if 'entry_price' in locals() else 2005.0)

    risk_amount = balance * (risk_percent / 100.0)
    price_difference = abs(entry_price - stop_loss_price)
    
    if price_difference > 0:
        lot_size = risk_amount / (price_difference * 100)
        reward_amount = abs(take_profit_price - entry_price)
        rr_ratio = reward_amount / price_difference
        
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        c1.metric("المبلغ المخاطر به", f"${risk_amount:.2f}")
        c2.metric("حجم العقد المناسب (Lot)", f"{lot_size:.2f} Lot")
        c3.metric("نسبة العائد/المخاطرة (R:R)", f"1:{rr_ratio:.2f}")
    else:
        st.warning("يرجى إدخال فارق سعر صحيح بين الدخول والستوب.")

with tab3:
    st.subheader("📜 معلومات البوت والتكامل")
    st.info("هذا التطبيق مدمج كلياً مع منصة التليجرام عبر Webhook ويرسل الإشارات مباشرة فور تحقق الشروط.")
    st.write("**علامة التداول:** GOLDRIDER")
    st.write("**المطور والمشرف:** RAZAKE TRADING")
