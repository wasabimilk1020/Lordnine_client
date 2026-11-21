import img_search_utils
import time
import re

x, y, width, height = 835, 700, 250, 150

match_list = ["hunting.png"]

def checkHunting():
  for i in range(5):
    success, match_data = img_search_utils.img_matchTemplate(
      match_list, x, y, width, height
    )

    if success:
      title, _, _ = match_data
      return True, title.replace(".png", "")

    # 마지막 검사에서는 기다리지 않음
    if i < 4:
      time.sleep(0.3)

  return False, "사냥 멈춰있음"
