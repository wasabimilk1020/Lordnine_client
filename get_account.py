import time
import win32gui
import win32com.client
shell = win32com.client.Dispatch("WScript.Shell")
from serial_comm import *
import img_search_utils
import re
import waking_from_sleep
import os
import json
import go_to_sleep
from log_context import trace_step, log_event

# 현재 실행중인 윈도우 핸들 목록 가져오기
def get_lin2m_hwnd_list():
  lin2m_handle_list=[]  #린2m 핸들 리스트

  def callback(_hwnd, _result: list):
    title = win32gui.GetWindowText(_hwnd)
    if win32gui.IsWindowEnabled(_hwnd) and win32gui.IsWindowVisible(_hwnd) and title is not None and len(title) > 0:
      _result.append(_hwnd)
    return True
  hwnd_list = []  #윈도우 핸들 리스트트
  win32gui.EnumWindows(callback, hwnd_list)
  
  for hwnd in hwnd_list:
    title = win32gui.GetWindowText(hwnd)
    result = title.split(' ')[0].strip()
    if result == "LORDNINE":
      lin2m_handle_list.append(hwnd)
  return lin2m_handle_list

@trace_step
def get_account_list(sio):
  account_dict = {}
  lin_handles = get_lin2m_hwnd_list()
  log_event("get_account_list", "HANDLES", count=len(lin_handles))

  time.sleep(2) #바로 시작 되는것을 막기 위한 임시 조치

  if not lin_handles:
    return False, "게임 창을 찾지 못함"

  # 기존 캐릭터 정보 불러오기
  saved_accounts = utils.load_json("account.json", "config_json")

  # 현재 존재하는 게임 핸들만 유지
  current_handles = set(lin_handles)

  for name, hwnd in saved_accounts.items():
    hwnd = int(hwnd)

    if hwnd in current_handles:
      account_dict[name] = hwnd 

  # 새로 발견된 핸들만 추출
  new_handles = [
    hwnd for hwnd in lin_handles
    if hwnd not in account_dict.values()
  ]

  match_list = []

  if new_handles:
    accounts_dir = utils.file_path("", "image_files", "accounts")

    match_list = [
      os.path.join("accounts", filename)
      for filename in sorted(os.listdir(accounts_dir))
      if filename.lower().endswith(".png")
    ]

    if not match_list:
      return False, "캐릭터 이미지 파일 없음"

  log_event("get_account_list", "CACHE", saved=len(saved_accounts), reused=len(account_dict), new=len(new_handles))

  # 새로 발견된 핸들만 처리
  for hwnd in new_handles:
    log_event("get_account_list", "NEW_HANDLE", handle=hwnd)
    # 윈도우 활성화
    success, message = img_search_utils.getWindow(hwnd)
    if not success:
      return False, f"윈도우 활성화 실패: {hwnd}"

    # 절전 해제 및 캐릭터 정보 화면 열기
    waking_from_sleep.waking_from_sleep_and_deathChk(sleep_time=2)
    keyboard('x')
    time.sleep(1)
    randClick(750, 115, 10, 10, 0)

    # 캐릭터 이름 템플릿 매칭
    success, match_data = img_search_utils.img_matchTemplate(
      match_list, 1179, 92, 286, 236
    )

    if not success:
      return False, f"캐릭터 이름 매칭 실패: {hwnd}"

    # 매칭된 파일명에서 캐릭터 이름 추출
    title, score, location = match_data
    character_name = os.path.splitext(os.path.basename(title))[0]

    # 동일 캐릭터명 중복 방지
    if character_name in account_dict:
      return False, f"캐릭터 이름 중복: {character_name}"

    account_dict[character_name] = hwnd
    log_event("get_account_list", "MATCHED", character=character_name, handle=hwnd, score=round(score, 3))

    keyboard('x') #설정 창 나가기

    # 새 캐릭터 확인 후 절전모드 전환
    success, message = go_to_sleep.go_to_sleep_and_huntingChk(
      "캐릭터 확인", character_name, sio
    )

    if not success:
      return False, message

  # 가나다순 정렬
  accounts = dict(sorted(account_dict.items(), key=lambda x: x[0]))

  # 변경된 경우에만 JSON 저장
  if accounts != saved_accounts:
    log_event("get_account_list", "CACHE_SAVE", count=len(accounts))
    utils.save_json("account.json", "config_json", accounts)

  return True, accounts
