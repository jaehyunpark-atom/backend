import os

import yfinance as yf
import requests

# =========================
# Discord Webhook
# =========================
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def send_discord(msg: str):
    if not DISCORD_WEBHOOK_URL:
        print("DISCORD_WEBHOOK_URL 환경변수가 설정되지 않았습니다. 전송을 건너뜁니다.")
        return
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg})
    except:
        pass


# =========================
# CNN Fear & Greed Index
# =========================
def get_fear_greed():
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        data = requests.get(url).json()

        value = int(data["data"][0]["value"])
        label = data["data"][0]["value_classification"]

        return value, label
    except:
        return None, "UNKNOWN"


# =========================
# 가격 + 데일리 변화
# =========================
def get_price_and_change(ticker):
    df = yf.Ticker(ticker).history(period="5d")

    if df.empty or len(df) < 2:
        return None, None

    current = float(df["Close"].iloc[-1])
    prev = float(df["Close"].iloc[-2])

    change_pct = (current / prev - 1) * 100

    return current, change_pct


# =========================
# MAIN
# =========================
def main():

    # =========================
    # 시장 데이터
    # =========================
    ixic_price, ixic_chg = get_price_and_change("^IXIC")
    spx_price, spx_chg = get_price_and_change("^GSPC")
    btc_price, btc_chg = get_price_and_change("BTC-USD")

    vix_df = yf.Ticker("^VIX").history(period="5d")
    usdkrw_df = yf.Ticker("KRW=X").history(period="5d")

    vix = float(vix_df["Close"].iloc[-1]) if not vix_df.empty else None
    usdkrw = float(usdkrw_df["Close"].iloc[-1]) if not usdkrw_df.empty else None

    # =========================
    # CNN Fear & Greed
    # =========================
    fng_value, fng_label = get_fear_greed()

    # =========================
    # 메시지 생성
    # =========================
    msg = "📊 MARKET RADAR\n"

    # NASDAQ
    if ixic_price is not None:
        msg += f"NASDAQ (IXIC): {ixic_price:,.2f} ({ixic_chg:+.2f}%)\n"

    # S&P500
    if spx_price is not None:
        msg += f"S&P500 (SPX): {spx_price:,.2f} ({spx_chg:+.2f}%)\n"

    # BTC
    if btc_price is not None:
        msg += f"BTC: ${btc_price:,.0f} ({btc_chg:+.2f}%)\n"

    # VIX
    if vix is not None:
        msg += f"VIX: {vix:.2f}\n"

    # USD/KRW
    if usdkrw is not None:
        msg += f"USD/KRW: {usdkrw:.2f}\n"

    # CNN F&G
    if fng_value is not None:
        msg += f"CNN Fear & Greed: {fng_value} ({fng_label})\n"

    msg += "\n"

    # =========================
    # Discord 전송
    # =========================
    send_discord(msg)

    print(msg)


if __name__ == "__main__":
    main()
