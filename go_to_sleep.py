import serial_comm
import check_hunting
import img_search_utils
import time
from log_context import trace_step, log_event

ERR_MSG = 0
STATUS_MSG = 1

@trace_step
def go_to_sleep_and_huntingChk(btn_name, character_name, sio, check_status=False):
  serial_comm.keyboard('g')

  # 절전모드 진입 확인
  for i in range(3):
    success, hunting_status = check_hunting.checkHunting()

    if success:
      break
  else:
    log_event(
      "sleep_verify",
      "END",
      "NOT_FOUND",
      checks=3
    )
    message = f"{btn_name} 절전모드 진입 실패"
    sio.emit("logEvent", [message, character_name, ERR_MSG])
    return False, message

  log_event(
    "sleep_verify",
    "END",
    "FOUND",
    checks=i + 1,
    status=hunting_status
  )

  # check_status는 현재 구조상 필수는 아니지만
  # 기존 호출부 호환성을 위해 남겨 둠
  if check_status:
    message = f"{btn_name}, {hunting_status} 완료"
  else:
    message = f"{btn_name} 완료"

  sio.emit("logEvent", [message, character_name, STATUS_MSG])
  return True, message