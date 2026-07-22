# portfolio-leverage-alert

나스닥100(QQQ) 사상 최고가 대비 낙폭을 추적해서, QLD(-10/-15/-20%)·TQQQ(-30/-40/-45%) 매수 검토 구간에 새로 도달하면 카카오톡으로 알림을 보낸다.

두 시스템으로 나뉘어 동작한다:

1. **이 repo의 GitHub Actions** (`.github/workflows/portfolio-leverage-alert.yml`)
   매일 05:30 KST에 `check_drawdown.py`를 실행해 yfinance로 QQQ 현재가/사상 최고가를 정확히 계산하고, `state.json`에 결과를 커밋한다. 새 트리거 단계에 도달하면 `pending_alert` 필드에 알림 메시지를 남긴다.
2. **Claude 클라우드 루틴** (claude.ai routines, 이 repo 밖에서 관리)
   매일 06:00 KST에 이 repo를 클론해 `state.json`의 `pending_alert`를 읽고, 값이 있으면 카카오톡(PlayMCP)으로 전송한 뒤 `pending_alert`를 `null`로 되돌려 커밋한다.

계산(정확한 네트워크 접근이 필요)과 전송(카카오톡 MCP 접근이 필요)을 분리한 이유: Claude 클라우드 루틴 실행 환경은 Bash의 직접 네트워크 호출이 막혀 있어 yfinance 같은 API를 안정적으로 쓸 수 없다. 대신 일반 네트워크 접근이 가능한 GitHub Actions에서 계산하고, 클라우드 루틴은 결과 파일만 읽어서 카카오톡 전송만 담당한다.
