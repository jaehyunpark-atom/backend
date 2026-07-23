"""
나스닥100(QQQ) 사상 최고가 대비 낙폭을 계산해 QLD/TQQQ 매수 트리거 단계에
새로 도달했는지 판단하고, 결과를 state.json에 기록한다.

- 이 스크립트는 GitHub Actions에서 정기 실행된다. Claude 클라우드 루틴 실행 환경은
  직접 네트워크 호출(yfinance 등)이 막혀있어 정밀 계산이 어렵기 때문에, 정확한 계산은
  일반 네트워크 접근이 가능한 GitHub Actions 쪽에서 담당하고, 계산 결과만 state.json에
  남긴다. 실제 카카오톡 알림 전송은 별도의 Claude 클라우드 루틴이 이 state.json을 읽어서
  수행한다 (이 스크립트는 카카오톡을 직접 보내지 않는다).

- 트리거 단계에 도달해도 바로 알림을 보내지 않는다. 하락 중인 칼날을 잡지 않기 위해
  "반등 확인"(최근 저점 대비 +3% 반등 또는 2거래일 연속 상승 마감)이 될 때까지
  해당 단계를 pending_tiers에 대기시켰다가, 반등이 확인되면 그때 알림을 보낸다.
"""
import json
from pathlib import Path

import yfinance as yf

STATE_PATH = Path(__file__).parent / "state.json"

TICKER = "QQQ"  # 나스닥100 추종 ETF, 사상 최고가/현재가 기준

# 낙폭 트리거 단계 (고점 대비 하락률, %). 음수 기준이며 낮을수록(더 많이 빠질수록) 깊은 단계.
QLD_TIERS = [-10, -15, -20]
TQQQ_TIERS = [-30, -40, -45]

# 낙폭이 이 값보다 얕아지면(고점을 상당 부분 회복하면) 다음 하락 사이클을 위해
# 알림 이력을 초기화한다.
RESET_THRESHOLD_PCT = -10

# 반등 확인 기준
LOCAL_LOW_LOOKBACK_DAYS = 15  # 최근 며칠 중 저점을 "직전 저점"으로 볼지
BOUNCE_PCT_THRESHOLD = 3.0  # 저점 대비 이만큼(%) 반등하면 확인
CONSECUTIVE_UP_DAYS = 2  # 또는 며칠 연속 상승 마감하면 확인


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"alerted_tiers": [], "pending_tiers": [], "pending_alert": None}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def check_bounce(closes) -> dict:
    """최근 종가 시계열(closes, 오래된 순)로 반등 확인 여부를 판단한다."""
    recent = closes[-LOCAL_LOW_LOOKBACK_DAYS:]
    local_low = float(min(recent))
    current = float(closes[-1])
    bounce_pct = (current - local_low) / local_low * 100

    consecutive_up = 0
    for i in range(len(closes) - 1, 0, -1):
        if closes[i] > closes[i - 1]:
            consecutive_up += 1
        else:
            break

    confirmed = bounce_pct >= BOUNCE_PCT_THRESHOLD or consecutive_up >= CONSECUTIVE_UP_DAYS
    return {
        "local_low": round(local_low, 2),
        "bounce_pct": round(bounce_pct, 2),
        "consecutive_up_days": consecutive_up,
        "confirmed": confirmed,
    }


def main() -> None:
    hist = yf.Ticker(TICKER).history(period="max")
    if hist.empty:
        raise RuntimeError(f"{TICKER} 가격 데이터를 가져오지 못했습니다.")

    closes = hist["Close"].tolist()
    current_price = float(closes[-1])
    ath = float(hist["Close"].max())
    ath_date = hist["Close"].idxmax().strftime("%Y-%m-%d")
    drawdown_pct = (current_price - ath) / ath * 100  # 항상 0 이하

    bounce = check_bounce(closes)

    state = load_state()
    alerted = set(state.get("alerted_tiers", []))
    pending = set(state.get("pending_tiers", []))

    # 고점을 상당 부분 회복했으면 다음 하락 사이클을 위해 이력 초기화
    if drawdown_pct > RESET_THRESHOLD_PCT and (alerted or pending):
        alerted = set()
        pending = set()

    reached = [t for t in (QLD_TIERS + TQQQ_TIERS) if drawdown_pct <= t]
    # 아직 알림도, 대기 등록도 안 된 새 단계 -> 대기(pending) 목록에 추가
    newly_reached = [t for t in reached if t not in alerted and t not in pending]
    pending.update(newly_reached)

    # 대기 중인 단계가 있고 반등이 확인되면, 대기 중인 단계 전부를 한 번에 알림
    if pending and bounce["confirmed"]:
        deepest_pending = min(pending)
        product = "TQQQ" if deepest_pending in TQQQ_TIERS else "QLD"
        state["pending_alert"] = (
            f"🔔 나스닥100(QQQ) 고점({ath_date}) 대비 {drawdown_pct:.1f}% 하락, "
            f"{deepest_pending}% 단계 반등 확인(저점대비 +{bounce['bounce_pct']:.1f}%) "
            f"→ {product} 매수 시점"
        )
        alerted.update(pending)
        pending = set()
    # 반등 미확인이면 기존 pending_alert(아직 카톡 루틴이 못 읽었을 수 있음)를 그대로 둔다

    state["ticker"] = TICKER
    state["current_price"] = round(current_price, 2)
    state["ath"] = round(ath, 2)
    state["ath_date"] = ath_date
    state["drawdown_pct"] = round(drawdown_pct, 2)
    state["bounce"] = bounce
    state["alerted_tiers"] = sorted(alerted, reverse=True)
    state["pending_tiers"] = sorted(pending, reverse=True)
    state.setdefault("pending_alert", None)

    save_state(state)
    print(json.dumps(state, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
