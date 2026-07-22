"""
나스닥100(QQQ) 사상 최고가 대비 낙폭을 계산해 QLD/TQQQ 매수 트리거 단계에
새로 도달했는지 판단하고, 결과를 state.json에 기록한다.

- 이 스크립트는 GitHub Actions에서 정기 실행된다. Claude 클라우드 루틴 실행 환경은
  직접 네트워크 호출(yfinance 등)이 막혀있어 정밀 계산이 어렵기 때문에, 정확한 계산은
  일반 네트워크 접근이 가능한 GitHub Actions 쪽에서 담당하고, 계산 결과만 state.json에
  남긴다. 실제 카카오톡 알림 전송은 별도의 Claude 클라우드 루틴이 이 state.json을 읽어서
  수행한다 (이 스크립트는 카카오톡을 직접 보내지 않는다).
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


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"alerted_tiers": [], "pending_alert": None}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    hist = yf.Ticker(TICKER).history(period="max")
    if hist.empty:
        raise RuntimeError(f"{TICKER} 가격 데이터를 가져오지 못했습니다.")

    current_price = float(hist["Close"].iloc[-1])
    ath = float(hist["Close"].max())
    ath_date = hist["Close"].idxmax().strftime("%Y-%m-%d")
    drawdown_pct = (current_price - ath) / ath * 100  # 항상 0 이하

    state = load_state()
    alerted = set(state.get("alerted_tiers", []))

    # 고점을 상당 부분 회복했으면 다음 하락 사이클을 위해 이력 초기화
    if drawdown_pct > RESET_THRESHOLD_PCT and alerted:
        alerted = set()

    reached = [t for t in (QLD_TIERS + TQQQ_TIERS) if drawdown_pct <= t]
    new_tiers = [t for t in reached if t not in alerted]

    if new_tiers:
        deepest_new = min(new_tiers)  # 가장 깊은(가장 음수인) 새 단계
        product = "TQQQ" if deepest_new in TQQQ_TIERS else "QLD"
        state["pending_alert"] = (
            f"🔔 나스닥100(QQQ) 고점({ath_date}) 대비 {drawdown_pct:.1f}% 하락, "
            f"{deepest_new}% 단계 도달 → {product} 매수 검토 구간"
        )
        alerted.update(new_tiers)
    # new_tiers가 없으면 기존 pending_alert(아직 카톡 루틴이 못 읽었을 수 있음)를 그대로 둔다

    state["ticker"] = TICKER
    state["current_price"] = round(current_price, 2)
    state["ath"] = round(ath, 2)
    state["ath_date"] = ath_date
    state["drawdown_pct"] = round(drawdown_pct, 2)
    state["alerted_tiers"] = sorted(alerted, reverse=True)
    state.setdefault("pending_alert", None)

    save_state(state)
    print(json.dumps(state, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
