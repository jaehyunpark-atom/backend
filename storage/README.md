# storage (migrated)

이 폴더는 원래 `jaehyunpark-atom/storage` 레포에 있던 스크립트를 이 레포로 옮겨온 것입니다.
원본 storage 레포는 더 이상 사용하지 않지만 참고용으로 남아 있습니다.

- `stock.py`: 보유 포트폴리오(나스닥100/닛케이225/VWO/QQQM/SCHD/미국배당다우존스/금현물/TQQQ/QLD) 현재가·평가액을 조회해 그룹별 목표 비중 대비 리밸런싱 필요 금액을 계산·출력
- `Alert_daily.py`: 나스닥/S&P500/BTC/VIX/USD-KRW/CNN Fear&Greed Index를 조회해 Discord로 매일 시황 요약 전송
- `Alert_NASDAQ.py`: NDX(나스닥100) 낙폭이 -10/-20/-30/-40/-50% 구간을 넘나들 때 Discord로 하락/반등 알림 전송 (자체 `state.json` 관리)

## Discord Webhook 설정

`Alert_daily.py`, `Alert_NASDAQ.py`는 `DISCORD_WEBHOOK_URL` 환경변수에서 Webhook URL을
읽습니다 (더 이상 코드에 하드코딩되어 있지 않습니다). 환경변수가 없으면 전송을 건너뛰고
콘솔에만 출력합니다.

- **로컬/데스크탑에서 실행할 때**: 셸에서 `export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."`
  하고 실행하거나, `.env` 파일(git에 커밋 금지)에 넣고 `python-dotenv` 등으로 로드하세요.
- **GitHub Actions에서 실행할 때**: 레포 Settings → Secrets and variables → Actions →
  New repository secret 에서 `DISCORD_WEBHOOK_URL`을 등록하고, workflow에서
  `env: { DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }} }`로 넘기세요.
  (Claude에게는 레포 Secrets를 만들 수 있는 권한/도구가 없어서 이 등록은 직접 해주셔야 합니다.)

## TODO
- 이 스크립트들을 자동 실행하는 GitHub Actions workflow는 아직 없습니다 (원본 storage 레포에도 없었음). 필요하면 `portfolio-leverage-alert.yml`을 참고해 추가하세요.
- `requirements.txt`는 참고용으로 함께 추가했습니다 (원본 storage 레포에는 없었음).
