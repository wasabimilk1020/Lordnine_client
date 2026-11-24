# 2차 로컬 로깅 적용 안내

## 적용할 파일
- 현재 실행 중인 프로젝트의 Python 파일은 백업해 둔 뒤, 이 폴더의 `client.py`, `mainloop.py`, `log_context.py` 및 나머지 7개 Python 파일을 프로젝트 루트에 같은 이름으로 복사한다.
- 1차 수정본 `client.py`/`mainloop.py` 위에 추가 적용한 **통합본**이다. 원본 1차 수정본과 파일을 섞어 쓰지 않는다.
- 이 ZIP에는 독립 테스트 실행에 필요한 `utils.py`, `macro.ino`, 게임 이미지/설정과 기타 import 모듈은 포함돼 있지 않다. 기존 프로젝트를 유지한다.

## 로그 경로와 흐름
- `logs/client.log` (기존 파일에 이어 기록)
- `mainLoop()`는 캐릭터마다 run 번호를 할당하고 `log_context`가 같은 작업자 스레드의 하위 함수에 전달한다.
- 작업 큐 처리 시작/끝, 시리얼 명령 시도/전송/ACK/오류, 이미지 검색 단위 시작/종료 및 최종 결과, 주요 루틴의 시작/종료가 기록된다.
- `auto_move_chk.png` 개별 검색과 `hunting.png` 중첩 템플릿 검사는 너무 빈번하므로 DEBUG로만 기록한다. 대신 50회 이동 대기와 사냥 상태 검사 함수의 요약이 INFO로 기록된다.
- ACK의 `COMMAND_COMPLETED`는 Arduino 입력 루틴 응답일 뿐 **게임 동작 확인 성공을 의미하지 않는다**.
- 일반 함수 `event=END result=SUCCESS`는 그 함수가 `(True, ...)`를 반환했다는 뜻이며 게임 상태를 별도 검증했다는 의미는 아니다.
- `reqAccount()`는 `mainLoop()` 외부에서 발생하므로 별도로 예외 traceback을 기록하고 기존과 같이 다시 예외를 전달한다.
- 명령 후 `delay` 값이 있는 경우 `serial.execute_command`에 `WAIT_START/WAIT_END`로 대기 구간을 기록한다.

## 로그 예시 (형식 예시일 뿐 실측 로그 아님)
```text
2026-11-23 19:30:01 [INFO] run=1 char=캐릭터A handle=123 routine=사냥 event=START
2026-11-23 19:30:02 [INFO] run=1 char=캐릭터A routine=사냥 step=serial.send_and_wait event=START result=- cmd=3!b timeout=3.0
2026-11-23 19:30:02 [INFO] run=1 char=캐릭터A routine=사냥 step=serial.send_and_wait event=ACK result=COMMAND_COMPLETED elapsed_ms=35
2026-11-23 19:30:03 [INFO] run=1 char=캐릭터A routine=사냥 step=searchImg event=START result=- image=storeBuy.png max_checks=5 click=True
2026-11-23 19:30:09 [INFO] run=1 char=캐릭터A routine=사냥 step=searchImg event=END result=FOUND image=storeBuy.png checks=1 click=True
2026-11-23 19:30:20 [INFO] run=1 char=캐릭터A routine=사냥 step=auto_move_wait event=WAIT_START result=- image=auto_move_chk.png max_checks=50
2026-11-23 19:30:30 [INFO] run=1 char=캐릭터A routine=사냥 step=auto_move_wait event=WAIT_END result=NOT_FOUND checks=4
2026-11-23 19:30:40 [INFO] run=1 event=END result=SUCCESS
```

## 주의
- Windows/실제 게임 장치 테스트는 진행하지 않았다. Python 문법 검사와 일부 모의 테스트만 수행했다.
- `get_account` 등 `mainLoop` 외부 실행은 `run=-` 로 표기된다.
- 기존 정상/오류 분기, 서버 `logEvent` 형식, Arduino 명령 형식은 변경하지 않았다.
