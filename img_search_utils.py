import pyautogui
import os
import time
import pyautogui
import datetime
import base64
import win32con
import win32com.client
shell = win32com.client.Dispatch("WScript.Shell")
import win32gui
from serial_comm import *
import utils
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
from PIL import ImageGrab,ImageEnhance,Image,ImageOps,ImageFilter
import cv2
import numpy as np 
import logging
from log_context import log_event
from typing import Tuple, Optional


# 이미지 서치
def searchImg(imgTitle, beforeDelay, afterDelay, justChk=False, coord=[], chkCnt=5, _region=(300, 125, 1370, 790), accuracy=0.85):
  full_path = utils.file_path(f"{imgTitle}", "image_files")
  chkInterval = 0.5
  loopCnt = 0
  # auto_move_chk는 상위 대기 루프에서 횟수와 최종 결과를 요약 기록
  level = logging.DEBUG if imgTitle == "auto_move_chk.png" else logging.INFO
  log_event("searchImg", "START", level=level, image=imgTitle, max_checks=chkCnt, click=bool(coord) or not justChk)

  while loopCnt < chkCnt:
    loopCnt += 1
    try:
      time.sleep(beforeDelay)
      result = pyautogui.locateOnScreen(
        full_path, region=_region, confidence=accuracy
      )

      if result is None:  # 이미지 찾기 실패
        time.sleep(chkInterval)
        continue

      # 이미지 찾기 성공
      if coord:  # 이미지가 아닌 다른 곳 클릭 시
        randClick(coord[0], coord[1], coord[2], coord[3], 0)
      elif justChk:  # 클릭 없이 이미지 체크만 할 경우
        time.sleep(afterDelay)
        log_event("searchImg", "END", "FOUND", level=level, image=imgTitle, checks=loopCnt, click=False)
        return True, result 
      else:  # 이미지 클릭
        randClick(result[0], result[1], result[2], result[3], 0)

      time.sleep(afterDelay)
      log_event("searchImg", "END", "FOUND", level=level, image=imgTitle, checks=loopCnt, click=True)
      return True, result

    except pyautogui.ImageNotFoundException:
      print(f"Image '{imgTitle}' not found on screen.")
      time.sleep(chkInterval)
      continue

    except Exception as e:
      log_event("searchImg", "END", "ERROR", logging.ERROR, image=imgTitle, checks=loopCnt, error=repr(e))
      raise RuntimeError(f"이미지 검색 오류 ({imgTitle}): {e}") from e

  log_event("searchImg", "END", "NOT_FOUND", level=level, image=imgTitle, checks=loopCnt)
  return False, None
  

def caputure_image(name,x,y,sio):
  log_event("capture_image", "START", character=name, region=(x, y, 50, 30))
  full_path=utils.file_path(f"{name}.png","image_files","capture_img")  #file, folder, sub_folder

  time.sleep(0.2)
  pyautogui.screenshot(full_path, region=(x,y,50,30))
  with open(full_path, "rb") as f:
    b64_string = base64.b64encode(f.read())
    captureImg=b64_string
  now = datetime.datetime.now()
  nowDatetime=now.strftime('%H:%M')
  data=[name, nowDatetime, captureImg] 
  sio.emit("captured_image",data)
  log_event("capture_image", "END", "SENT", character=name)

# def getWindow(handle):
#   try:
#     time.sleep(0.1)
#     shell.SendKeys('%')
#     win32gui.SetForegroundWindow(handle)
#     time.sleep(0.1)

#     if win32gui.GetForegroundWindow() != handle:
#       return False, "윈도우 활성화 실패"

#     startClick(850, 440, 100, 100, 0)
#     return True, "성공"

#   except Exception as e:
#     raise RuntimeError(f"윈도우 오류: {e}") from e

def getWindow(handle):
  log_event("getWindow", "START", handle=handle)
  try:
    # 최소화된 창이면 복원
    if win32gui.IsIconic(handle):
      win32gui.ShowWindow(handle, win32con.SW_RESTORE)

    # 이미 활성화되어 있지 않을 때만 시도
    if win32gui.GetForegroundWindow() != handle:
      shell.SendKeys('%')
      win32gui.SetForegroundWindow(handle)

      # 최대 0.5초 동안 활성화 확인
      for i in range(10):
        if win32gui.GetForegroundWindow() == handle:
          break
        time.sleep(0.05)

      else:
        log_event("getWindow", "END", "ACTIVATION_FAILED", handle=handle)
        return False, "윈도우 활성화 실패"

    startClick(850, 440, 100, 100, 0)
    log_event("getWindow", "END", "SUCCESS", handle=handle)
    return True, "성공"

  except Exception as e:
    log_event("getWindow", "END", "ERROR", logging.ERROR, handle=handle, error=repr(e))
    raise RuntimeError(f"윈도우 오류: {e}") from e
    

# x, y, width, height = 810, 660, 295, 65 #자동 사냥 범위
# config="--psm 7 -c preserve_interword_spaces=1"
# binary_value=130

def capture_text_from_region(x, y, width, height, _config, binary_val):
  log_event("capture_text_from_region", "START", region=(x, y, width, height))
  bbox = (x, y, x + width, y + height)

  try:
    screenshot = ImageGrab.grab(bbox)

    # 이미지 확대
    scaled = screenshot.resize(
      (screenshot.width * 2, screenshot.height * 2),
      Image.Resampling.LANCZOS
    )

    # 흑백 변환 및 대비 증가
    grayscale = scaled.convert("L")
    enhanced = ImageEnhance.Contrast(grayscale).enhance(2.0)

    # 이진화 및 반전
    binary = enhanced.point(
      lambda x: 0 if x < binary_val else 255
    )
    inverted_image = ImageOps.invert(binary)

    # OCR
    text = pytesseract.image_to_string(
      inverted_image, lang='kor', config=_config
    ).strip()

  except Exception as e:
    log_event("capture_text_from_region", "END", "ERROR", logging.ERROR, error=repr(e))
    raise RuntimeError(f"OCR 처리 오류: {e}") from e

  if not text:
    log_event("capture_text_from_region", "END", "NOT_FOUND")
    return False, "문자 인식 실패"

  log_event("capture_text_from_region", "END", "FOUND", length=len(text))
  return True, text

def preprocess_image(temp_imgTitle, output_path):  #이미지 전처리
  log_event("preprocess_image", "START", image=temp_imgTitle)
  input_path=utils.file_path(f"{temp_imgTitle}","image_files")  #file, folder, sub_folder
  # 이미지 로드
  template_image = cv2.imread(input_path)
  
  # 1. 그레이스케일
  gray = cv2.cvtColor(template_image, cv2.COLOR_BGR2GRAY)
  # 2. 대비 향상 (CLAHE)
  clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
  contrast = clahe.apply(gray)
  # 3. 샤프닝
  kernel = np.array([[0, -1, 0],
                     [-1, 5, -1],
                     [0, -1, 0]])
  sharpened = cv2.filter2D(contrast, -1, kernel)
  # # 4. 이진화 (Otsu Threshold)
  # _, binary = cv2.threshold(
  #     sharpened, 0, 255,
  #     cv2.THRESH_BINARY + cv2.THRESH_OTSU
  # )
  # 저장
  cv2.imwrite(output_path, sharpened)
  log_event("preprocess_image", "END", "COMPLETED", path=output_path)


def img_matchTemplate(temp_img_list, x, y, width, height, confidence=0.75, chk_cnt=5):
  level = logging.DEBUG if temp_img_list == ["hunting.png"] else logging.INFO
  log_event("img_matchTemplate", "START", level=level, templates=len(temp_img_list), max_checks=chk_cnt)

  bbox = (x, y, x + width, y + height)

  for cnt in range(chk_cnt):
    # 화면 캡처
    target_pil = ImageGrab.grab(bbox)
    img = cv2.cvtColor(np.array(target_pil), cv2.COLOR_RGB2BGR)

    # 전처리
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast = clahe.apply(gray)
    kernel = np.array([[0, -1, 0],
                       [-1, 5, -1],
                       [0, -1, 0]])
    sharpened = cv2.filter2D(contrast, -1, kernel)

    # 템플릿 검색
    for title in temp_img_list:
      template_path = utils.file_path(title, "image_files")
      try:
        template_img = cv2.imdecode(
          np.fromfile(template_path, dtype=np.uint8),
          cv2.IMREAD_GRAYSCALE
        )
      except Exception as e:
        raise RuntimeError(f"템플릿 파일 읽기 오류 ({template_path}): {e}") from e

      if template_img is None:
        raise ValueError(f"템플릿 이미지 디코딩 실패: {template_path}")

      try:
        result = cv2.matchTemplate(
          sharpened, template_img, cv2.TM_CCOEFF_NORMED
        )
      except Exception as e:
        raise RuntimeError(f"템플릿매칭 오류 발생: {e}") from e

      _, max_val, _, max_loc = cv2.minMaxLoc(result)

      if max_val >= confidence:
        log_event("img_matchTemplate", "END", "FOUND", level=level, image=title, score=round(max_val, 3), checks=cnt + 1)
        return True, (title, max_val, max_loc)

    # 마지막 검사에서는 기다릴 필요 없음
    if cnt < chk_cnt - 1:
      time.sleep(0.5)

  log_event("img_matchTemplate", "END", "NOT_FOUND", level=level, checks=chk_cnt)
  return False, None


def find_hsv_center(x, y, width, height, lower, upper, min_area=300):
    log_event("find_hsv_center", "START", region=(x, y, width, height), lower=lower, upper=upper)

    # 1. 캡처
    img = ImageGrab.grab(bbox=(x, y, x+width, y+height))
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    # 2. HSV 변환
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 3. 전달받은 HSV 범위 적용
    lower = np.array(lower, dtype=np.uint8)
    upper = np.array(upper, dtype=np.uint8)

    mask = cv2.inRange(hsv, lower, upper)

    # 4. 노이즈 제거
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # 5. 컨투어
    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
      log_event("find_hsv_center", "END", "NOT_FOUND")
      return False, None

    # 6. 가장 큰 색상 영역
    cnt = max(contours, key=cv2.contourArea)

    if cv2.contourArea(cnt) < min_area:
      log_event("find_hsv_center", "END", "NOT_FOUND")
      return False, None

    # 7. 중심 좌표
    M = cv2.moments(cnt)
    if M["m00"] == 0:
      log_event("find_hsv_center", "END", "NOT_FOUND")
      return False, None

    cx = int(M["m10"] / M["m00"]) + x
    cy = int(M["m01"] / M["m00"]) + y

    log_event("find_hsv_center", "END", "FOUND", x=cx, y=cy)
    return True, (cx, cy)