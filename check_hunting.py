import img_search_utils
import time
import re

x, y, width, height = 835,700, 250, 150 #매칭 위치

match_list=["hunting.png"]
def checkHunting():
  for i in range(5):
    match_result=img_search_utils.img_matchTemplate(match_list, x, y, width, height)
    if match_result[0]==2:  #템플릿 매칭 예외 발생
      return match_result[0], match_result[1]
    elif match_result[0] in match_list: #매칭 성공 return title, "capture_text 성공", max_val, max_loc
      return match_result[0].replace(".png", ""), ""
    time.sleep(0.3)
  return 0, "사냥 멈춰있음" #실패를 나타냄g