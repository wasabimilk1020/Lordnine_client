import time
import img_search_utils
from serial_comm import *
import re
import check_hunting
from waking_from_sleep import *
from go_to_sleep import *
import win32gui
import win32con
from log_context import trace_step, log_event

@trace_step
def start_attack():
  is_orange, _ = img_search_utils.find_hsv_center(
    1749, 701, 41, 37,
    lower=(14, 176, 60),
    upper=(26, 249, 183),
    min_area=300
  )

  is_gray, _ = img_search_utils.find_hsv_center(
    1753, 692, 56, 59,
    lower=(0, 0, 0),
    upper=(179, 79, 61),
    min_area=300
  )

  log_event("start_attack", "STATE", orange=is_orange, gray=is_gray)

  if is_orange and not is_gray:
    return True, "이미 공격 중"

  elif not is_orange and is_gray:
    log_event("start_attack", "ACTION", "CLICK_REQUESTED")
    randClick(1760, 720, 5, 5, 1)

    # 클릭 후 공격 상태 재확인
    attack_success, _ = img_search_utils.find_hsv_center(
      1749, 701, 41, 37,
      lower=(14, 176, 60),
      upper=(26, 249, 183),
      min_area=300
    )

    log_event(
      "start_attack", "STATE",
      "ATTACK_STARTED" if attack_success else "ATTACK_NOT_STARTED"
    )

    if not attack_success:
      return False, "공격 활성화 실패"

    return True, "공격 활성화 확인 완료"

  elif not is_orange and not is_gray:
    return False, "공격 버튼 상태 확인 실패"

  else:
    return False, "공격 버튼 상태 충돌"



@trace_step
def move_on_map(x, y, width=3, height=3, delay=1):
  # ===== 지도 열기 (최대 2번 시도) =====
  for attempt in range(2):
    log_event('move_on_map', 'OPEN_ATTEMPT', attempt=attempt + 1)
    keyboard('m')

    # 지도 UI 확인 1
    map_success, _ = img_search_utils.searchImg(
      'map_chk_1.png',
      beforeDelay=2, afterDelay=2,
      justChk=True, _region=(1590, 0, 330, 150)
    )

    # 첫 번째 이미지가 없을 때만 두 번째 확인
    if not map_success:
      map_success, _ = img_search_utils.searchImg(
        'map_chk_2.png',
        beforeDelay=1, afterDelay=1,
        justChk=True, _region=(1547, 6, 251, 232)
      )

    # 지도 열림 확인
    if map_success:
      break

    # 두 이미지 모두 미검출 → 기본 화면 확인
    normal_success, _ = img_search_utils.searchImg(
      'map_chk_3.png',
      beforeDelay=0, afterDelay=0,
      justChk=True, _region=(1510, 592, 260, 257)
    )

    # 기본 화면도 확인되지 않으면 상태 불명
    if not normal_success:
      return False, "지도 열기 상태 확인 실패"

    # 기본 화면 확인됐지만 재시도까지 실패
    if attempt == 1:
      return False, "지도 열기 실패"

  # ===== 지도에서 위치 클릭 =====
  log_event("move_on_map", "ACTION", "CLICK_REQUESTED", x=x, y=y, width=width, height=height)
  randClick(x, y, width, height, delay)

  # ===== 지도 닫기 =====
  log_event("move_on_map", "CLOSE_ATTEMPT", attempt=1)
  escKey()

  # 최대 2번 닫힘 상태 확인
  for attempt in range(2):

    # 지도 UI 확인 1
    map_success, _ = img_search_utils.searchImg(
      'map_chk_1.png',
      beforeDelay=2 if attempt == 0 else 1,
      afterDelay=0,
      justChk=True, _region=(1590, 0, 330, 150)
    )

    # 첫 번째 이미지가 없을 때만 두 번째 확인
    if not map_success:
      map_success, _ = img_search_utils.searchImg(
        'map_chk_2.png',
        beforeDelay=0, afterDelay=0,
        justChk=True, _region=(1547, 6, 251, 232)
      )

    # 지도가 여전히 열려 있으면 ESC 재시도
    if map_success:
      if attempt == 0:
        log_event("move_on_map", "CLOSE_ATTEMPT", attempt=2)
        escKey()
        continue

      return False, "지도 닫기 실패"

    # 지도 이미지 모두 미검출 → 기본 화면 확인
    # normal_success라는게 지도에서 나와 일반 ui에서 이미지 체크를 수행하는 것을 뜻함
    normal_success, _ = img_search_utils.searchImg(
      'map_chk_3.png',
      beforeDelay=0, afterDelay=0,
      justChk=True, _region=(1510, 592, 260, 257)
    )

    if normal_success:
      return True, "지도 조작 루틴 완료"

    return False, "지도 상태 확인 실패"

  return False, "지도 닫기 실패"


# data=[1142, 375, 10, 10, 0.0]=[x,y,xRange,yRange,delay]
@trace_step
def statusChk(sio, data, btn_name, character_name, handle):
  coord = data
  delay = data[4]
  name = character_name

  success, hunting_status = check_hunting.checkHunting()

  if not success or hunting_status == "rest":  # 사냥 중이 아니거나 휴식 중
    waking_from_sleep_and_deathChk(sleep_time=2)
    result = normalHunting(sio, data, btn_name, character_name, handle)
    return result

  else:  # 사냥 중
    return True, {"action": "status", "message": hunting_status}


@trace_step
def normalHunting(sio, data, btn_name, character_name, handle):
  coord=data
  flag=data[4]
  name=character_name

  keyboard('b') #귀환

  success, _ = img_search_utils.searchImg('storeBuy.png', beforeDelay=5, afterDelay=5, _region=(1500,660,420,300))
  if not success:
    return False, {"message": "귀환 실패"}

  success, _ = img_search_utils.searchImg('autoBuy.png', beforeDelay=0, afterDelay=1, chkCnt=20, _region=(75,845,350,200))
  if not success:
    return False, {"message": "자동구매 실패"}

  randClick(1045,800,10,10,1) #확인
  escKey()

  time.sleep(2)
  keyboard('m') #지도

  success, _ = img_search_utils.searchImg('favorite.png', beforeDelay=2, afterDelay=1, _region=(0,820,100,150))
  if not success:
    return False, {"message": "즐겨찾기 실패"}

  success, _ = img_search_utils.searchImg('hunting_place.png', beforeDelay=0, afterDelay=2, _region=(70,220,250,400))
  if not success:
    return False, {"message": "사냥터 클릭 실패"}

  success, _ = img_search_utils.searchImg('hunting_portal.png', beforeDelay=0, afterDelay=1, _region=(1490,155,400,800))
  if not success:
    return False, {"message": "포탈 클릭 실패"}

  randClick(1735,990,10,10,1) #빠른이동
  success, _ = img_search_utils.searchImg('confirm.png', beforeDelay=0, afterDelay=7, _region=(985,575,300,200))
  if not success:
    return False, {"message": "확인 실패"}

  match_list=["chk.png"]
  success, match_data=img_search_utils.img_matchTemplate(match_list, 1669, 0, 229, 180)
  if not success:
    return False, {"message": "이동 체크 실패"}
  time.sleep(2)

  #지도 열고 이동
  success, message = move_on_map(835, 690, 3, 3, 1)
  if not success:
    return False, {"message": message}

  log_event("auto_move_wait", "WAIT_START", image="auto_move_chk.png", max_checks=50)
  for i in range(50):
    success, _ = img_search_utils.searchImg('auto_move_chk.png', beforeDelay=0, afterDelay=1, justChk=True, _region=(830,600,300,150))
    if not success:
      break
  log_event("auto_move_wait", "WAIT_END", "LIMIT_REACHED" if success else "NOT_FOUND", checks=i + 1)

  #공격
  success, message = start_attack()
  if not success:
    return False, {"message": message}

  img_search_utils.caputure_image(name, 180, 180, sio) #name, x, y, sio

  return True, {"action": "sleep", "message":"사냥 루틴 완료"}




def postBox(sio, data,btn_name, character_name, handle):
  pass
  # keyboard(',')
  
  # result=img_search_utils.searchImg('allAccept.png',beforeDelay=1, afterDelay=2)
  # if(result==0):  
  #   return 0, "우편 모두받기 실패"

  # img_search_utils.searchImg('confirm.png',beforeDelay=1, afterDelay=1, accuracy=0.9, _region=(920,580,300,200))

  # escKey()  #우편 나가기
  
  # return 1, "message:None"


#---------던전---------#
@trace_step
def dungeon(sio, data, btn_name, character_name, handle):
  coord=data
  charging=data[4]
  name=character_name

  if btn_name=="어둠의숲":
    keyboard('`') #던전
    # for i in range(charging):
    #   keyboard("1")
    #   time.sleep(2)

    success, _ = img_search_utils.searchImg('darkDun.png', beforeDelay=1, afterDelay=1, _region=(122, 481, 289, 251))
    if not success:
      return False, {"message": "어둠의숲 클릭 실패"}

    randClick(1465,975,10,10,7) #입장

    # randClick(coord[0],coord[1],coord[2],coord[3],3)  #층 클릭 (현재는 층이 선택되어 있어 필요 없지만 혹시 몰라 남김)
    #이동 완료 체크
    match_list=["chk.png"]
    success, match_data = img_search_utils.img_matchTemplate(match_list, 1669, 0, 229, 180)
    if not success:
      return False, {"message": "이동 체크 실패"}
    time.sleep(2)

    #지도 열고 이동
    success, message = move_on_map(960,700,3,3,1)
    if not success:
      return False, {"message": message}

    log_event("auto_move_wait", "WAIT_START", image="auto_move_chk.png", max_checks=50)
    for i in range(50):
      success, _ = img_search_utils.searchImg('auto_move_chk.png', beforeDelay=0, afterDelay=1, justChk=True, _region=(830,600,300,150))
      if not success:
        break
    log_event("auto_move_wait", "WAIT_END", "LIMIT_REACHED" if success else "NOT_FOUND", checks=i + 1)

    #공격
    success, message = start_attack()
    if not success:
      return False, {"message": message}

  elif btn_name=="타락한미궁":
    keyboard('`') #던전
    # for i in range(charging):
    #   keyboard("1")
    #   time.sleep(2)

    success, _ = img_search_utils.searchImg('destroyDun.png', beforeDelay=1, afterDelay=1, _region=(114, 683, 347, 253))
    if not success:
      return False, {"message": "타락한미궁 클릭 실패"}

    randClick(1465,975,10,10,7) #입장

    # randClick(coord[0],coord[1],coord[2],coord[3],3)  #층 클릭 (현재는 층이 선택되어 있어 필요 없지만 혹시 몰라 남김)
    #이동 완료 체크
    match_list=["chk.png"]
    success, match_data = img_search_utils.img_matchTemplate(match_list, 1669, 0, 229, 180)
    if not success:
      return False, {"message": "이동 체크 실패"}
    time.sleep(2)

    #지도 열고 이동
    success, message = move_on_map(900,490,3,3,1)
    if not success:
      return False, {"message": message}

    log_event("auto_move_wait", "WAIT_START", image="auto_move_chk.png", max_checks=50)
    for i in range(50):
      success, _ = img_search_utils.searchImg('auto_move_chk.png', beforeDelay=0, afterDelay=1, justChk=True, _region=(830,600,300,150))
      if not success:
        break
    log_event("auto_move_wait", "WAIT_END", "LIMIT_REACHED" if success else "NOT_FOUND", checks=i + 1)

    #공격
    success, message = start_attack()
    if not success:
      return False, {"message": message}

  elif btn_name=="수련의전당":
    keyboard('`') #던전
    # for i in range(charging):
    #   keyboard("1")
    #   time.sleep(2)

    #여기 마우스 드래그로 아래로 내려주는 것 필요함
    success, _ = img_search_utils.searchImg('trainDun.png', beforeDelay=1, afterDelay=1, _region=(85, 714, 359, 257))
    if not success:
      return False, {"message": "수련의전당 클릭 실패"}

    randClick(1465,975,10,10,7) #입장

    # randClick(coord[0],coord[1],coord[2],coord[3],3)  #층 클릭 (현재는 층이 선택되어 있어 필요 없지만 혹시 몰라 남김)
    #이동 완료 체크
    match_list=["chk.png"]
    success, match_data = img_search_utils.img_matchTemplate(match_list, 1669, 0, 229, 180)
    if not success:
      return False, {"message": "이동 체크 실패"}
    time.sleep(2)

    # keyboard('m')
    # result=img_search_utils.searchImg('map_chk.png', beforeDelay=2, afterDelay=2, justChk=True, _region=(1590,0,330,150))
    # if(result==0):
    #   return 0, "지도 체크 실패"

    # randClick(960,700,3,3,1)  #지도에서 위치 클릭
    # escKey()  #여기서 가끔 esc가 안눌러지는지 씹히는 경우가 있네
    # time.sleep(5)
    # for i in range(50):
    #   result=img_search_utils.searchImg('auto_move_chk.png', beforeDelay=0, afterDelay=1, justChk=True, _region=(830,600,300,150))
    #   if(result==0):
    #     break

    # result=img_search_utils.find_hsv_center(1749, 701, 41, 37, lower=(14, 176, 60), upper=(26, 249, 183), min_area=300) #주황색 hsv 공격 중
    # if(result==None):
    #   randClick(1760,720,5,5,1) #공격

  elif btn_name=="상아탑":
    for i in range(charging):
      keyboard("4")
      time.sleep(2)

    # keyboard('v')
    # img_search_utils.searchImg('stop_schedule.png',beforeDelay=0.5, afterDelay=0.5, _region=(1260,790,300,100))
    # randClick(1075,820,10,10,0.5) #초기화 클릭

    # result=img_search_utils.searchImg('sanga.png',beforeDelay=0.5, afterDelay=0.5, _region=(480, 455, 400, 300))
    # if(result==0):
    #   return 0, "상아탑 클릭 실패"

    # randClick(coord[0],coord[1],coord[2],coord[3],1)  #층 클릭 (설정 해줘야함 json에서)

    # result_coord=img_search_utils.searchImg('plus.png',beforeDelay=0, afterDelay=0, justChk=True, _region=(1450,340,200,100)) #시간충전 좌표

    # for i in range(7):
    #   randClick(result_coord[0],result_coord[1],0,0,0.3) #시간 충전

    # result_3=img_search_utils.searchImg('clk_schedule_start.png',beforeDelay=0, afterDelay=0, _region=(1260,790,300,100))

  elif btn_name=="이벤트던전":
    keyboard('`') #던전
    # for i in range(charging):
    #   keyboard("1")
    #   time.sleep(2)

    time.sleep(3)
    randClick(240,425,10,10,0)  #층수 문제 때문에 일단 다른 던전 한 번 클릭

    success, _ = img_search_utils.searchImg('eventDun.png', beforeDelay=1, afterDelay=1, _region=(125, 88, 314, 271))
    if not success:
      return False, {"message": "이벤트던전 클릭 실패"}

    randClick(1465,975,10,10,7) #입장

    # randClick(coord[0],coord[1],coord[2],coord[3],3)  #층 클릭 (현재는 층이 선택되어 있어 필요 없지만 혹시 몰라 남김)
    #이동 완료 체크
    match_list=["chk.png"]
    success, match_data = img_search_utils.img_matchTemplate(match_list, 1669, 0, 229, 180)
    if not success:
      return False, {"message": "이동 체크 실패"}
    time.sleep(2)

    #지도 열고 이동
    success, message = move_on_map(940,610,3,3,1)
    if not success:
      return False, {"message": message}

    log_event("auto_move_wait", "WAIT_START", image="auto_move_chk.png", max_checks=50)
    for i in range(50):
      success, _ = img_search_utils.searchImg('auto_move_chk.png', beforeDelay=0, afterDelay=1, justChk=True, _region=(830,600,300,150))
      if not success:
        break
    log_event("auto_move_wait", "WAIT_END", "LIMIT_REACHED" if success else "NOT_FOUND", checks=i + 1)

    #공격
    success, message = start_attack()
    if not success:
      return False, {"message": message}

  img_search_utils.caputure_image(name, 180, 170, sio) #name, x, y, sio

  return True, {"action": "sleep", "message": "message:None"}

#---------월드 보스---------#
@trace_step
def world_boss(sio, data, btn_name, character_name, handle):
  coord=data
  charging=data[4]
  name=character_name

  randClick(1845,60,10,10,1)  #메뉴 클릭
  success, match_data=img_search_utils.searchImg('boss_menu.png', beforeDelay=0, afterDelay=1, _region=(1350, 120, 550, 680))
  if not success:
    return False, {"message": "보스 메뉴 실패"}
  
  success, match_data=img_search_utils.searchImg('boss_destroyer.png', beforeDelay=0, afterDelay=2, _region=(130, 6, 900, 226))
  if not success:
    return False, {"message": "파괴자 실패"}

  randClick(710,775,5,5,3)  #파괴자 위치 (라탄)

  randClick(1735,990,10,10,1) #빠른이동
  success, _ = img_search_utils.searchImg('confirm.png', beforeDelay=0, afterDelay=80, _region=(985,575,300,200))
  if not success:
    return False, {"message": "확인 실패"}

  log_event("auto_move_wait", "WAIT_START", image="auto_move_chk.png", max_checks=10)
  for i in range(10):
    success, _ = img_search_utils.searchImg('auto_move_chk.png', beforeDelay=0, afterDelay=1, justChk=True, _region=(830,600,300,150))
    if not success:
      break
  log_event("auto_move_wait", "WAIT_END", "LIMIT_REACHED" if success else "NOT_FOUND", checks=i + 1)

  keyboard('w',4000)  #앞으로 4초간 이동
  
  #공격
  success, message = start_attack()
  if not success:
    return False, {"message": message}

  img_search_utils.caputure_image(name, 180, 170, sio) #name, x, y, sio
  
  
  return True, {"action": "sleep", "message": "message:None"}

@trace_step
def decomposeItem(sio, data,btn_name, character_name, handle):
  coord=data
  delay=data[4]
  name=character_name

  keyboard("=") #장비공방
  success, _ =img_search_utils.searchImg('decomposeItem.png', beforeDelay=2, afterDelay=2, _region=(754, 44, 370, 234))
  if not success:
    randClick(930,155,10,10,0)  #아이템 분해 클릭 (화면에 글씨 표시 되는 부분이라 이미서치 안되면)
  #이 부분에 무조건 클릭되게 하면 안되고 클릭 해도 되는지 확인이 먼저 필요함

  success, _ =img_search_utils.searchImg('item_auto_registration.png', beforeDelay=1, afterDelay=2, _region=(1290,805,300,150))
  if not success:
    return False, {"message":"분해 실패"}
  #아이템 분해 할게 없어서 아무것도 등록 안되도 아래 부분이 진행되고 정상 종료 되야 하는대
  #위의 이미지 서치 자체가 실패하는건가???
  spaceKey()
  time.sleep(3)
  spaceKey()
  time.sleep(3)
  img_search_utils.caputure_image(name, 459, 285, sio) #name, x, y, sio
  escKey()
  time.sleep(1)

  return True, {"action": "sleep", "message":"분해 완료"}

@trace_step
def showDiamond(sio, data, btn_name, character_name, handle):
  coord = data
  delay = data[4]
  name = character_name

  keyboard('x')

  # Box(left=880, top=196, width=25, height=27)
  success_1, result_1 = img_search_utils.searchImg(
    'diamondChk_1.png',
    beforeDelay=1, afterDelay=0,
    justChk=True, _region=(840,180,100,60), accuracy=0.7
  )

  success_2, result_2 = img_search_utils.searchImg(
    'diamondChk_2.png',
    beforeDelay=0, afterDelay=0,
    justChk=True, _region=(920,180,80,60), accuracy=0.7
  )

  if success_1 and success_2:
    x = result_1.left + result_1.width
    capture_width = result_2.left - x
    y, height = 190, 35

    config = "--psm 7 -c tessedit_char_whitelist=0123456789,"
    binary_val = 150

    success, text = img_search_utils.capture_text_from_region(
      x, y, capture_width, height, config, binary_val
    )

    if not success:
      return False, {"message": text}

    numbers = ''.join(re.findall(r'\d+', re.sub(r"[.,]", "", text)))
    if not numbers:
      return False, {"message": "다이아 숫자 추출 실패"}
    
    diamond = numbers

  else:
    return False, {"message": "다이아 이미지서치 실패"}

  escKey()  # 나가기

  # 서버로 다이아몬드 전송
  sio.emit("get_diamond", [diamond, character_name])

  return True, {"action": "sleep", "message": "다이아 확인 완료"}




#거리 10M
@trace_step
def ten_meter(sio, data, btn_name, character_name, handle):
  coord=data
  delay=data[4]
  name=character_name

  keyboard("x") #환경설정

  success, _ = img_search_utils.searchImg('ten_meter.png', beforeDelay=1, afterDelay=1, _region=(1075,255,850,150))
  if not success:
    return False, {"message": "10M 클릭 실패"}

  img_search_utils.caputure_image(name, 1210, 290, sio) #name, x, y, sio

  escKey()  #나가기
  time.sleep(1)

  return True, {"action": "sleep", "message": "message:None"}


#거리 제한없음
@trace_step
def unlimit(sio, data, btn_name, character_name, handle):
  coord=data
  delay=data[4]
  name=character_name

  keyboard("x") #환경설정

  success, _ = img_search_utils.searchImg('unlimit_meter.png', beforeDelay=1, afterDelay=1, _region=(1075,255,850,150))
  if not success:
    return False, {"message": "제한없음 클릭 실패"}

  img_search_utils.caputure_image(name, 1765, 290, sio) #name, x, y, sio

  escKey()  #나가기
  time.sleep(1)

  return True, {"action": "sleep", "message": "message:None"}


# #데일리 출석 루틴
# def daily(sio, data,btn_name, character_name, handle):
#   coord=data
#   list_cnt=data[4]  #궁극적으로는 출석체크 목록갯수를 저절로 파악하게 만들어야된다.
#   name=character_name

#   keyboard(";") #출석

#   #빨간색 점 없애는 루틴
#   chk_y=320
#   for i in range(list_cnt):
#     randClick(1485,chk_y,10,10,0.5)
#     chk_y+=80
  
#   y = 255
#   for i in range(list_cnt):
#     region = (1530, y, 100, 70)
    
#     result=img_search_utils.searchImg('dailyRedDotChk.png', beforeDelay=0, afterDelay=0, justChk=True, chkCnt=2, _region=region) 
#     if result:
#       randClick(result.left-100, result.top+30,10,10,1)
#       result=img_search_utils.searchImg('accept.png', beforeDelay=1, afterDelay=1, _region=(1105,420,400,200)) 
#       if(result==1):
#         result=img_search_utils.searchImg('confirm.png', beforeDelay=1, afterDelay=0, _region=(920,580,300,200)) 
#     y += 80 #y축 80씩 증가
 
#   #데일리 나가기
#   escKey()

#   return

# #혈맹 출석 루틴
# def guild(sio, data,btn_name, character_name, handle):
#   coord=data
#   delay=data[4]
#   name=character_name
#   keyboard('.')

#   result=img_search_utils.searchImg('guildAttendance.png', beforeDelay=1, afterDelay=1, accuracy=0.9,_region=(500,610,300,150)) 
#   if(result==0):
#     return 0, "혈맹 체크 실패"
  
#   randClick(915, 820, 20, 20, 0)  #기부
  
#   result=img_search_utils.searchImg('donation.png', beforeDelay=1, afterDelay=1,_region=(440,660,400,200)) 
#   if(result==0):
#     return 0, "일괄기부 실패"
  
#   img_search_utils.searchImg('confirm.png',beforeDelay=1, afterDelay=1, accuracy=0.9, _region=(920,580,300,200))
  
#   escKey()  #기부 나가기
#   escKey()  #혈맹 나가기

#   return 1, "message:None"

# def store(sio, data,btn_name, character_name, handle):
#   coord=data
#   delay=data[4]
#   name=character_name
#   #상점 클릭
#   keyboard('u')
  
#   result=img_search_utils.searchImg('adChk.png', beforeDelay=5, afterDelay=1, _region=(235,665,350,235))  #광고 체크 
#   #광고 없으면 그냥 진행 (예외처리 필요 없음)
  
#   #교환소 클릭
#   result=img_search_utils.searchImg('exchange.png', beforeDelay=0, afterDelay=1, _region=(340,210,1260,160))
#   if(result==0):
#     escKey()
#     return 0, "교환소 클릭 실패"
  
#   # #품절 체크
#   # result=img_search_utils.searchImg('soldoutChk.png', beforeDelay=0, afterDelay=0, chkCnt=3, _region=(600,660,750,200))
#   # if(result==1):
#   #   return 0, "솔드아웃"

#   #--2주년 기념 상품 임시 루틴
#   #일괄 구매
#   result=img_search_utils.searchImg('allBuy.png', beforeDelay=0, afterDelay=1, _region=(1300,790,350,200))
#   if(result==0):
#     return 0, "일괄구매 실패"

#   randClick(1045,780,10,10,3) #구매 클릭
#   #--여기까지

#   pic_lists=["pandora.png","leah_castle.png"]
#   for pic in pic_lists:
#     result=img_search_utils.searchImg(pic, beforeDelay=1, afterDelay=1, accuracy=0.9, _region=(1360,315,200,250)) 
#     #일괄 구매
#     result=img_search_utils.searchImg('allBuy.png', beforeDelay=0, afterDelay=1, _region=(1300,790,350,200))
#     if(result==0):
#       return 0, "일괄구매 실패"
  
#     randClick(1045,780,10,10,5) #구매 클릭  #여기 시간을 3초, 5초 이런식으로 조절하고 싶은대 루틴마다 다르게


#   #상점 나가기
#   escKey()

#   return 1, "message:None"

#------------모닝 루틴------------#
@trace_step
def morning(sio, data,btn_name, character_name, handle):
  coord=data
  delay=data[4]
  name=character_name

  #--길드
  keyboard('.') #길드
  time.sleep(2)
  #화면 전화 의미 없는 것 하지 말고 길드 들어 갔을 때 나오는 문자를 이미지서치하자.
  randClick(910,585,10,10,2)  #화면 전환을 위한 클릭
  spaceKey()  #길드 기부
  success, _ =img_search_utils.searchImg('donation.png',beforeDelay=2, afterDelay=1, _region=(690,665,200,150))
  if not success:
    return False, {"message": "기부 실패"}
  else: 
    for i in range(5):
      randClick(750,720,0,0,1)
    escKey()
    time.sleep(1)
    escKey()
    time.sleep(1)

  #--상점
  keyboard('u') #상점
  time.sleep(3)
  spaceKey()
  time.sleep(2)
  spaceKey()
  time.sleep(2)
  spaceKey()
  time.sleep(5)
  escKey()
  time.sleep(1)
  
  keyboard('b') #귀환

  #--우호도 상인
  success, _ =img_search_utils.searchImg('good_store.png',beforeDelay=5, afterDelay=5, _region=(1500,660,420,300))
  if not success:
    return False, {"message": "귀환 실패"}

  
  success, _ = img_search_utils.searchImg('autoBuy.png', beforeDelay=0, afterDelay=1, chkCnt=15, justChk=True, _region=(75,845,350,200))
  y = 290
  if success:
    for i in range(3):
      randClick(32, y, 10, 10, 1)
      img_search_utils.searchImg('autoBuy.png', beforeDelay=0, afterDelay=1, _region=(75,845,350,200))
      success, _ = img_search_utils.searchImg('good_confirm.png', beforeDelay=0, afterDelay=1, _region=(970,780,300,200))
      if not success:
        return False, {"message": "확인 실패"}
      y = y + 75
  else:
    return False, {"message": "우호상인 실패"}
  
  escKey()

  #--룬 상인
  success, _ =img_search_utils.searchImg('roon_store.png',beforeDelay=1, afterDelay=5, _region=(1500,660,420,300))
  if not success:
    return False, {"message": "룬 상인 실패"}

  success, _ =img_search_utils.searchImg('roon.png',beforeDelay=0, afterDelay=1, chkCnt=10, _region=(85,115,300,300))
  if not success:
    return False, {"message": "룬 클릭 실패"}

  randClick(1110,595,5,5,1) #max
  success, _ =img_search_utils.searchImg('buy.png', beforeDelay=0, afterDelay=1, _region=(970,745,300,200))
  if not success:
    return False, {"message": "룬 구매 실패"}

  escKey()
  time.sleep(1)

  #모닝루틴 완료 후 사냥터 이동
  result=normalHunting(sio, data, btn_name, character_name, handle)
  return result


def party_dun_entry(sio, data,btn_name, character_name, handle):
  pass
  # coord=data
  # cnt=data[4]
  # name=character_name

  # keyboard('t') #파티설정
  # result=img_search_utils.searchImg('party_dun_entry.png',beforeDelay=1, afterDelay=1, _region=(960, 755, 200, 100))
  # if(result==0):
  #   randClick(950,795,5,5,0.5)

  # return 1, "message:None"

def unparty(sio, data,btn_name, character_name, handle):
  pass
  # coord=data
  # cnt=data[4]
  # name=character_name

  # randClick(865,480,30,30,0.5)  #전리품 확인 클릭
  # randClick(568,345,3,3,1)  #미니맵으로 전환 클릭

  # result=img_search_utils.searchImg('unparty.png',beforeDelay=0.5, afterDelay=0.5, _region=(485, 365, 150, 150))
  # if(result==0):
  #   return 0, "파티해제 실패"
  # result=img_search_utils.searchImg('confirm.png',beforeDelay=0.5, afterDelay=0.5, _region=(880, 570, 320, 200))
  # if(result==0):
  #   return 0, "확인 실패"

  # result=normalHunting(sio, data, btn_name, character_name, handle)
  # return result

def party_dungeon(sio, data, btn_name, character_name, handle):
  pass
  # coord=data
  # charging=data[4]
  # name=character_name

  # keyboard("`") #던전
  # # result=utils.searchImg('favorite.png', beforeDelay=1, afterDelay=1,  _region=(700, 230, 800, 120))  #즐겨찾기 클릭
  # result=img_search_utils.searchImg('party.png',beforeDelay=1, afterDelay=1, _region=(630, 230, 400, 100))
  # if(result==0):
  #   return 0, "파티클릭 실패"
  
  # if btn_name=="봉인사원":
  #   for i in range(charging):
  #     keyboard("2")
  #     time.sleep(2)

  #   result=img_search_utils.searchImg('sealing_temple.png',beforeDelay=1, afterDelay=1)
  #   if(result==0):
  #     return 0, "봉인의 사원 클릭 실패"

  # elif btn_name=="카이트해적":
  #   for i in range(charging):
  #     keyboard("2")
  #     time.sleep(2)

  #   result=img_search_utils.searchImg('kite_pirates.png',beforeDelay=1, afterDelay=1)
  #   if(result==0):
  #     return 0, "카이트해적 클릭 실패"
    
  # elif btn_name=="네뷸라이트":
  #   for i in range(charging):
  #     keyboard("2")
  #     time.sleep(2)

  #   result=img_search_utils.searchImg('nebul.png',beforeDelay=1, afterDelay=1)
  #   if(result==0):
  #     return 0, "네뷸라이트 클릭 실패"
    
  # elif btn_name=="회색제단":
  #   for i in range(charging):
  #     keyboard("2")
  #     time.sleep(2)

  #   dragValues={'fromStartX':680, 'toStartX':980,'fromStartY':650,'toStartY':750,'fromEndX':680, 'toEndX':980,'fromEndY':120,'toEndY':160}
  #   serial_comm.mouseDrag(dragValues)
  #   time.sleep(2)   

  #   result=img_search_utils.searchImg('gray_ash.png',beforeDelay=1, afterDelay=1)
  #   if(result==0):
  #     return 0, "회색제단 클릭 실패"
    
  # elif btn_name=="최후정원":
  #   for i in range(charging):
  #     keyboard("2")
  #     time.sleep(2)

  #   result=img_search_utils.searchImg('last_garden.png',beforeDelay=1, afterDelay=1)
  #   if(result==0):
  #     return 0, "최후정원 클릭 실패"
    
  # elif btn_name=="케트라":
  #   for i in range(charging):
  #     keyboard("2")
  #     time.sleep(2)

  #   dragValues={'fromStartX':680, 'toStartX':980,'fromStartY':650,'toStartY':750,'fromEndX':680, 'toEndX':980,'fromEndY':120,'toEndY':160}
  #   serial_comm.mouseDrag(dragValues)
  #   time.sleep(2)

  #   result=img_search_utils.searchImg('ketra.png',beforeDelay=1, afterDelay=1)
  #   if(result==0):
  #     return 0, "케트라 클릭 실패"

  # result=img_search_utils.searchImg('request_enter.png', beforeDelay=0, afterDelay=1, _region=(1200, 750, 400, 150))  #입장신청
  # if(result==0):
  #   return 0, f"{btn_name} 입장 클릭 실패"
  
  # randClick(coord[0],coord[1],coord[2],coord[3],1)  #층 클릭
  # result=img_search_utils.searchImg('confirm_enter.png', beforeDelay=0, afterDelay=1, _region=(880, 570, 320, 200))  #입장신청
  # if(result==0):
  #   return 0, f"{btn_name} 입장신청 확인 실패"

  # return 1, "message:None"

def move_window(sio, data, btn_name, character_name, handle):
  pass
#   coord=data
#   cnt=data[4]
#   name=character_name
#   win32gui.SetWindowPos(
#     handle,
#     None,
#     320, 180,      # x, y
#     0, 0,      # width, height (무시)
#     win32con.SWP_NOSIZE | win32con.SWP_NOZORDER
# )

#   return 1, "message:None"


def gameExe_adRemove(sio, data, btn_name, character_name, handle):
  pass
  # coord=data
  # cnt=data[4]
  # name=character_name
  # result=img_search_utils.searchImg('adChk.png', beforeDelay=0.5, afterDelay=0.5, _region=(235,665,350,235))  #광고 체크 

  # return 1, "message:None"

