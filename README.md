# stock-alerts

주식 포트폴리오 추적·리밸런싱·레버리지 매매 알림 스크립트 모음.
(원래 `backend` + `storage` 두 레포로 나뉘어 있던 것을 이 레포 하나로 합쳤습니다.)

## 구성

- **`portfolio-leverage-alert/`** — 나스닥100(QQQ) 낙폭 기반 QLD/TQQQ tier 매수·익절·손절 알림
  시스템. GitHub Actions(`​.github/workflows/portfolio-leverage-alert.yml`)로 매일 계산해
  `state.json`에 결과를 커밋하고, 카카오톡 전송은 별도 Claude 클라우드 루틴이 담당. 자세한
  설계는 해당 폴더의 README 참고.
- **`storage/`** — 원래 `jaehyunpark-atom/storage` 레포에 있던 스크립트. 보유 포트폴리오
  리밸런싱 계산(`stock.py`), 데일리 시황(`Alert_daily.py`), 나스닥100 낙폭 알림
  (`Alert_NASDAQ.py`, Discord 전송). 자동 실행 workflow는 아직 없음.

## 참고

- `storage/`의 두 스크립트에는 Discord Webhook URL이 코드에 하드코딩되어 있습니다.
  GitHub Secrets나 환경변수로 옮기는 것을 권장합니다.
- 원본 `jaehyunpark-atom/storage` 레포는 삭제하지 않고 남겨뒀지만 더 이상 사용하지
  않습니다.
