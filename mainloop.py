import win32gui
import img_search_utils
import serial_comm
import time
import check_hunting
from waking_from_sleep import *
from go_to_sleep import *
import copy
import logging

ERR_MSG = 0
STATUS_MSG = 1

def mainLoop(sio, btn_func, func_data, id_handle, btn_name):
  for character_name, handle in id_handle:
    if not win32gui.IsWindow(handle):
      print("핸들 없음", handle)
      sio.emit("logEvent", ["윈도우 없음", character_name, ERR_MSG])
      continue

    try:
      sio.emit("logEvent", [f"{btn_name} 시작", character_name, STATUS_MSG])

      # 윈도우 앞으로 가져오기 (기존 반환값 유지)
      success, message = img_search_utils.getWindow(handle)
      if not success:
        sio.emit("logEvent", [message, character_name, ERR_MSG])
        continue

      # 절전 해제 및 사망 체크
      if btn_name != "status_check_button":
        waking_from_sleep_and_deathChk(sleep_time=2)

      # 버튼 루틴 실행
      success, data = btn_func(
        sio, func_data, btn_name, character_name, handle
      )

      # 루틴 실패
      if not success:
        sio.emit("logEvent", [data["message"], character_name, ERR_MSG])
        continue

      # 성공 이후의 처리
      action = data["action"]
      message = data["message"]

      if action == "sleep":
        go_to_sleep_and_huntingChk(btn_name, character_name, sio)

      elif action == "status":
        sio.emit("logEvent", [f"{message} 완료", character_name, STATUS_MSG])

      elif action == "skip":
        pass

      else:
        raise ValueError(f"알 수 없는 루틴 처리 방식: {action}")

    except Exception as e:
      logging.exception(f"mainLoop 실행 오류: {character_name}")
      sio.emit("logEvent", [f"루틴 실행 오류: {e}", character_name, ERR_MSG])
      continue

  sio.emit("stop_animation", btn_name)


    