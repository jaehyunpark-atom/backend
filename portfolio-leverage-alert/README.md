# portfolio-leverage-alert

나스닥100(QQQ) 사상 최고가 대비 낙폭을 추적해서, QLD(-10/-15/-20%)·TQQQ(-30/-40/-45%) 매수·매도 시점을 카카오톡으로 알린다.

두 시스템으로 나뉘어 동작한다:

1. **이 repo의 GitHub Actions** (`.github/workflows/portfolio-leverage-alert.yml`)
   매일 05:30 KST에 `check_drawdown.py`를 실행해 yfinance로 QQQ 현재가/사상 최고가를 정확히 계산하고, `state.json`에 결과를 커밋한다.
   - **매수**: 새 트리거 단계에 도달해도 바로 알림을 보내지 않고 `pending_tiers`에 대기시킨다. 최근 15거래일 저점 대비 +3% 반등하거나 2거래일 연속 상승 마감(반등 확인)하면, 그때 대기 중인 단계들을 모아 `pending_alert`에 알림을 남기고 `open_positions`에 기록한다. 알림에는 각 단계의 매수 비중(`TRANCHE_PCT`: QLD 15/35/50%, TQQQ도 기본값으로 동일 패턴 적용)이 함께 표시된다.
   - **매도**: `open_positions`에 있는 단계는 낙폭이 진입 시점보다 10%p 개선되면(`RECOVERY_STEP_PCT`, 예: -20% 진입 → -10%까지 회복) 매도 알림을 보내고 제거한다.
2. **Claude 클라우드 루틴** (claude.ai routines, 이 repo 밖에서 관리)
   매일 06:00 KST에 이 repo를 클론해 `state.json`의 `pending_alert`를 읽고, 값이 있으면 카카오톡(PlayMCP)으로 전송한 뒤 `pending_alert`를 `null`로 되돌려 커밋한다.

계산(정확한 네트워크 접근이 필요)과 전송(카카오톡 MCP 접근이 필요)을 분리한 이유: Claude 클라우드 루틴 실행 환경은 Bash의 직접 네트워크 호출이 막혀 있어 yfinance 같은 API를 안정적으로 쓸 수 없다. 대신 일반 네트워크 접근이 가능한 GitHub Actions에서 계산하고, 클라우드 루틴은 결과 파일만 읽어서 카카오톡 전송만 담당한다.
