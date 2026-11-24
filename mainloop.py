import win32gui
import img_search_utils
import serial_comm
import time
import check_hunting
from waking_from_sleep import *
from go_to_sleep import *
import copy
import logging
from itertools import count
from log_context import set_context, clear_context

ERR_MSG = 0
STATUS_MSG = 1

# 프로그램 실행 중 캐릭터별 작업 ID (재시작하면 1부터 시작)
_run_counter = count(1)

def mainLoop(sio, btn_func, func_data, id_handle, btn_name):
  for character_name, handle in id_handle:
    run_id = next(_run_counter)
    set_context(run_id, character_name, handle, btn_name)
    logging.info(
      "run=%s char=%s handle=%s routine=%s event=START",
      run_id, character_name, handle, btn_name
    )

    if not win32gui.IsWindow(handle):
      print("핸들 없음", handle)
      sio.emit("logEvent", ["윈도우 없음", character_name, ERR_MSG])
      logging.warning("run=%s event=END result=INVALID_WINDOW", run_id)
      clear_context()
      continue

    result = "UNKNOWN"
    try:
      sio.emit("logEvent", [f"{btn_name} 시작", character_name, STATUS_MSG])

      # 윈도우 앞으로 가져오기 (기존 반환값 유지)
      success, message = img_search_utils.getWindow(handle)
      if not success:
        result = "WINDOW_ACTIVATION_FAILED"
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
        result = "ROUTINE_FAILED"
        sio.emit("logEvent", [data["message"], character_name, ERR_MSG])
        continue

      # 절전 모드 및 성공 이후의 처리
      action = data["action"]
      message = data["message"]

      if action == "sleep":
        sleep_success, _ = go_to_sleep_and_huntingChk(btn_name, character_name, sio)
        result = "SUCCESS" if sleep_success else "SLEEP_FAILED"

      elif action == "status":
        sio.emit("logEvent", [f"{message} 완료", character_name, STATUS_MSG])
        result = "SUCCESS"

      elif action == "skip":
        result = "SKIPPED"

      else:
        raise ValueError(f"알 수 없는 루틴 처리 방식: {action}")

    except Exception as e:
      result = "EXCEPTION"
      logging.exception("run=%s char=%s routine=%s event=ERROR", run_id, character_name, btn_name)
      sio.emit("logEvent", [f"루틴 실행 오류: {e}", character_name, ERR_MSG])
      continue

    finally:
      logging.info("run=%s event=END result=%s", run_id, result)
      clear_context()

  sio.emit("stop_animation", btn_name)


    