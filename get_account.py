import time
import win32gui
import win32com.client
shell = win32com.client.Dispatch("WScript.Shell")
from serial_comm import *
import img_search_utils
import re

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


def get_account_list(sio):
  account_dict={} #{"아이디":handle value}
  lin_handles = get_lin2m_hwnd_list()

  for hwnd in lin_handles:
    raw_title = win32gui.GetWindowText(hwnd)
    
    # "리니지2M l " 제거
    clean_title = re.sub(r"^LORDNINE\s*l\s*", "", raw_title).strip()
    
    if clean_title:  # 빈 문자열은 제외
        account_dict[hwnd] = hwnd
  # 가나다 순으로 정렬
  sorted_dict = dict(sorted(account_dict.items(), key=lambda x: x[0]))

  return sorted_dict
