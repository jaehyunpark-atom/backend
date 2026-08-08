import unicodedata
from typing import Dict, Tuple

import pandas as pd
import yfinance as yf


# =========================
# 1. 자산 정의
# =========================
assets = {
    "133690": ("133690.KS", "TIGER 미국나스닥100", "NASDAQ", 46),
    "241180": ("241180.KS", "TIGER 일본니케이225", "JAPAN", 150),
    "VWO": ("VWO", "VWO", "EM", 67),
    "QQQM": ("QQQM", "QQQM", "NASDAQ", 10),
    "SCHD": ("SCHD", "SCHD", "DIV", 154),
    "458730": ("458730.KS", "TIGER 미국배당다우존스", "DIV", 430),
    "411060": ("411060.KS", "ACE KRX금현물", "GOLD", 130),
    "TQQQ": ("TQQQ", "TQQQ", "LEVERAGE", 0),
    "QLD": ("QLD", "QLD", "LEVERAGE", 1),
}

group_target = {
    "NASDAQ": 35,
    "DIV": 25,
    "JAPAN": 20,
    "EM": 10,
    "GOLD": 10,
    "LEVERAGE": 0,
}

group_order = ["NASDAQ", "DIV", "JAPAN", "EM", "GOLD", "LEVERAGE"]


# =========================
# 2. 문자열 정렬
# =========================

def get_visual_width(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)


def pad_right(text: str, width: int) -> str:
    return text + " " * max(0, width - get_visual_width(text))


def pad_left(text: str, width: int) -> str:
    return " " * max(0, width - get_visual_width(text)) + text


# =========================
# 3. 환율 및 가격 조회
# =========================

def get_usd_krw_rate() -> float:
    try:
        ticker = yf.Ticker("KRW=X")
        hist = ticker.history(period="5d")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
    except Exception:
        pass
    return 1500.0


def fetch_prices(assets: Dict[str, Tuple[str, str, str, int]]) -> Dict[str, float]:
    tickers = list({info[0] for info in assets.values()})
    prices: Dict[str, float] = {}

    if not tickers:
        return prices

    try:
        history = yf.download(
            tickers,
            period="5d",
            group_by="ticker",
            threads=False,
            progress=False,
        )
    except Exception as exc:
        print(f"경고: yf.download 실패 - {exc}")
        history = pd.DataFrame()

    for symbol, info in assets.items():
        ticker = info[0]
        price = None

        if isinstance(history, pd.DataFrame):
            try:
                if ticker in history.columns.get_level_values(0):
                    ticker_data = history[ticker]
                    close = ticker_data["Close"].dropna()
                    if not close.empty:
                        price = float(close.iloc[-1])
                elif "Close" in history.columns:
                    close = history["Close"].dropna()
                    if not close.empty:
                        price = float(close.iloc[-1])
            except Exception:
                price = None

        if price is None:
            try:
                fallback = yf.Ticker(ticker)
                p = fallback.fast_info.get("lastPrice")
                if p is not None and not pd.isna(p):
                    price = float(p)
            except Exception as exc:
                print(f"{symbol} fast_info fallback 실패: {exc}")

        if price is not None:
            prices[symbol] = price
        else:
            print(f"{symbol} 가격 조회 실패: {ticker}")

    return prices


# =========================
# 4. 포트폴리오 계산
# =========================

def calculate_portfolio(
    assets: Dict[str, Tuple[str, str, str, int]], usd_krw_rate: float, prices: Dict[str, float]
) -> Dict[str, Dict]:
    portfolio_details: Dict[str, Dict] = {}
    total_value_usd = 0.0

    for symbol, info in assets.items():
        qty = info[3]
        ticker = info[0]
        price = prices.get(symbol)

        if price is None:
            continue

        if ticker.endswith(".KS"):
            price_krw = price
            price_usd = price / usd_krw_rate
        else:
            price_usd = price
            price_krw = price * usd_krw_rate

        value_usd = price_usd * qty
        value_krw = price_krw * qty

        portfolio_details[symbol] = {
            "name": info[1],
            "group": info[2],
            "qty": qty,
            "price_usd": price_usd,
            "price_krw": price_krw,
            "value_usd": value_usd,
            "value_krw": value_krw,
        }
        total_value_usd += value_usd

    portfolio_details["__total__"] = {"total_usd": total_value_usd}
    return portfolio_details


def summarize_groups(
    portfolio_details: Dict[str, Dict], total_value_usd: float, usd_krw_rate: float
) -> Dict[str, Dict]:
    group_value: Dict[str, float] = {}

    for symbol, detail in portfolio_details.items():
        if symbol == "__total__":
            continue
        group = detail["group"]
        group_value[group] = group_value.get(group, 0.0) + detail["value_usd"]

    group_summary: Dict[str, Dict] = {}
    for group in group_order:
        value_usd = group_value.get(group, 0.0)
        group_summary[group] = {
            "target": group_target.get(group, 0),
            "value_usd": value_usd,
            "value_krw": value_usd * usd_krw_rate,
            "percent": (value_usd / total_value_usd * 100) if total_value_usd else 0,
        }

    return group_summary


def calculate_rebalance(group_summary: Dict[str, Dict], total_value_usd: float) -> Dict[str, float]:
    rebalance: Dict[str, float] = {}
    for group, summary in group_summary.items():
        target = summary["target"]
        current = summary["percent"]
        diff = target - current
        if diff > 0:
            rebalance[group] = total_value_usd * (diff / 100)
    return rebalance


# =========================
# 5. 출력
# =========================

def format_portfolio_portion(detail: Dict[str, float], percentage: float) -> str:
    price_str = f"${detail['price_usd']:.2f} (₩{detail['price_krw']:,.0f})"
    total_str = f"${detail['value_usd']:.2f} (₩{detail['value_krw']:,.0f})"
    return (
        pad_right(detail["name"], 26)
        + pad_left(detail["group"], 10)
        + pad_left(f"{percentage:.1f}%", 8)
        + pad_left(price_str, 30)
        + pad_left(f"{detail['qty']:,}", 8)
        + pad_left(total_str, 30)
    )


def format_group_portion(group: str, summary: Dict[str, float], rebalance_usd: float, usd_krw_rate: float) -> str:
    rebalance_text = "-"
    if rebalance_usd > 0:
        rebalance_text = f"${rebalance_usd:,.0f} (₩{rebalance_usd * usd_krw_rate:,.0f})"

    return (
        f"{group:<10}"
        f"{summary['target']:>8.0f}%"
        f"{summary['percent']:>10.1f}%"
        f"{f'${summary['value_usd']:,.0f} (₩{summary['value_krw']:,.0f})':>32}"
        f"{rebalance_text:>28}"
    )


def print_summary(
    portfolio_details: Dict[str, Dict],
    group_summary: Dict[str, Dict],
    rebalance: Dict[str, float],
    total_value_usd: float,
    usd_krw_rate: float,
) -> None:
    sorted_items = sorted(
        (symbol, detail) for symbol, detail in portfolio_details.items() if symbol != "__total__"
    )
    sorted_items.sort(key=lambda item: item[1]["value_usd"], reverse=True)

    print("\n📈 포트폴리오 요약")
    print("-" * 140)
    for _, detail in sorted_items:
        percentage = detail["value_usd"] / total_value_usd * 100 if total_value_usd else 0
        print(format_portfolio_portion(detail, percentage))
    print("-" * 140)

    print("\n📊 그룹 요약")
    print("-" * 140)
    print(
        f"{'GROUP':<10}"
        f"{'TARGET':>8}"
        f"{'CURRENT':>10}"
        f"{'VALUE (USD/KRW)':>32}"
        f"{'REBALANCE':>28}"
    )
    print("-" * 140)

    for group in group_order:
        summary = group_summary[group]
        rebalance_usd = rebalance.get(group, 0.0)
        print(format_group_portion(group, summary, rebalance_usd, usd_krw_rate))

    print("-" * 140)
    total_rebalance_usd = sum(rebalance.values())
    print(
        f"{'TOTAL':<10}"
        f"{'':>20}"
        f"{f'${total_value_usd:,.0f} (₩{total_value_usd * usd_krw_rate:,.0f})':>32}"
        f"{f'${total_rebalance_usd:,.0f} (₩{total_rebalance_usd * usd_krw_rate:,.0f})':>28}"
    )
    print("-" * 140)


def main() -> None:
    usd_krw_rate = get_usd_krw_rate()
    print(f"\n💵 환율: 1 USD = {usd_krw_rate:,.2f} KRW")
    print("🔄 데이터 수집 중...")

    prices = fetch_prices(assets)
    portfolio_details = calculate_portfolio(assets, usd_krw_rate, prices)
    total_value_usd = portfolio_details["__total__"]["total_usd"]

    group_summary = summarize_groups(portfolio_details, total_value_usd, usd_krw_rate)
    rebalance = calculate_rebalance(group_summary, total_value_usd)

    print_summary(portfolio_details, group_summary, rebalance, total_value_usd, usd_krw_rate)


if __name__ == "__main__":
    main()
