# storage (migrated)

이 폴더는 원래 `jaehyunpark-atom/storage` 레포에 있던 스크립트를 이 레포로 옮겨온 것입니다.
원본 storage 레포는 더 이상 사용하지 않지만 참고용으로 남아 있습니다.

- `stock.py`: 보유 포트폴리오(나스닥100/닛케이225/VWO/QQQM/SCHD/미국배당다우존스/금현물/TQQQ/QLD) 현재가·평가액을 조회해 그룹별 목표 비중 대비 리밸런싱 필요 금액을 계산·출력
- `Alert_daily.py`: 나스닥/S&P500/BTC/VIX/USD-KRW/CNN Fear&Greed Index를 조회해 Discord로 매일 시황 요약 전송
- `Alert_NASDAQ.py`: NDX(나스닥100) 낙폭이 -10/-20/-30/-40/-50% 구간을 넘나들 때 Discord로 하락/반등 알림 전송 (자체 `state.json` 관리)

## TODO
- `Alert_daily.py`, `Alert_NASDAQ.py`에 Discord Webhook URL이 코드에 하드코딩되어 있습니다. 환경변수나 GitHub Secrets로 옮기는 것을 권장합니다.
- 이 스크립트들을 자동 실행하는 GitHub Actions workflow는 아직 없습니다 (원본 storage 레포에도 없었음). 필요하면 `portfolio-leverage-alert.yml`을 참고해 추가하세요.
- `requirements.txt`는 참고용으로 함께 추가했습니다 (원본 storage 레포에는 없었음).
