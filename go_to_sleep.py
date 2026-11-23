import serial_comm
import check_hunting
import img_search_utils
import time

ERR_MSG = 0
STATUS_MSG = 1

def go_to_sleep_and_huntingChk(btn_name, character_name, sio, check_status=False):
  serial_comm.keyboard('g')

  # 절전모드 진입 확인
  for i in range(3):
    success, _ = img_search_utils.searchImg(
      'sleepChk.png',
      beforeDelay=1,
      afterDelay=0,
      justChk=True,
      _region=(811, 638, 299, 232)
    )

    if success:
      break
  else:
    message = f"{btn_name} 절전모드 진입 실패"
    sio.emit("logEvent", [message, character_name, ERR_MSG])
    return False, message

  # 필요한 경우 사냥 상태 추가 확인
  if check_status:
    success, hunting_status = check_hunting.checkHunting()

    if not success:
      message = f"{btn_name}, {hunting_status}"
      sio.emit("logEvent", [message, character_name, ERR_MSG])
      return False, message

    message = f"{btn_name}, {hunting_status} 완료"

  else:
    message = f"{btn_name} 완료"

  sio.emit("logEvent", [message, character_name, STATUS_MSG])
  return True, message