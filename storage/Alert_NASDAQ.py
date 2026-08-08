import yfinance as yf
import requests
import json
import os

# =========================
# Discord
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
# State
# =========================
STATE_FILE = "state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# =========================
# Drawdown
# =========================
def get_drawdown():
    df = yf.Ticker("^NDX").history(period="max", auto_adjust=True)

    ath = float(df["High"].max())
    current = float(df["Close"].iloc[-1])

    dd = (current / ath - 1) * 100

    return float(dd), ath, current


# =========================
# Level 정의
# =========================
def get_level(dd):

    if dd <= -50:
        return "-50"
    elif dd <= -40:
        return "-40"
    elif dd <= -30:
        return "-30"
    elif dd <= -20:
        return "-20"
    elif dd <= -10:
        return "-10"
    else:
        return "0"


# =========================
# 알림 로직 (양방향)
# =========================
def check_and_alert(dd, state):

    levels = ["0", "-10", "-20", "-30", "-40", "-50"]

    new_level = get_level(dd)
    old_level = state.get("ndx", "0")

    if old_level not in levels:
        old_level = "0"

    if new_level == old_level:
        return state

    old_idx = levels.index(old_level)
    new_idx = levels.index(new_level)

    # =========================
    # 📉 하락
    # =========================
    if new_idx > old_idx:
        send_discord(f"NDX DOWN {old_level} → {new_level}: {dd:.2f}%")

    # =========================
    # 📈 반등 (리바운드)
    # =========================
    elif new_idx < old_idx:
        send_discord(f"NDX REBOUND {old_level} → {new_level}: {dd:.2f}%")

    state["ndx"] = new_level

    return state


# =========================
# MAIN
# =========================
def main():

    state = load_state()

    dd, ath, current = get_drawdown()

    print(f"NDX ATH: {ath:.2f}")
    print(f"NDX Current: {current:.2f}")
    print(f"NDX Drawdown: {dd:.2f}%")

    state = check_and_alert(dd, state)

    msg = (
        f"📊 NDX STATUS\n"
        f"ATH: {ath:.2f}\n"        
        f"Current: {current:.2f}\n"
        f"Drawdown: {dd:.2f}%"
    )

    send_discord(msg)

    save_state(state)


if __name__ == "__main__":
    main()
