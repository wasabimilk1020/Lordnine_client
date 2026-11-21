import serial_comm
import check_hunting
import img_search_utils
import time

ERR_MSG = 0
STATUS_MSG = 1

def go_to_sleep_and_huntingChk(btn_name, character_name, sio):
  serial_comm.keyboard('g')

  for i in range(3):
    result, _=img_search_utils.searchImg('sleepChk.png', beforeDelay=1, afterDelay=0, _region=(811, 638, 299, 232)) 
    if(result==1):
      sio.emit("logEvent",["사냥 완료", character_name, STATUS_MSG])
      return
    
  sio.emit("logEvent",["사냥 실패", character_name, ERR_MSG])


  
  # value=check_hunting.checkHunting()  #value=성공 시="자동 사냥 중" or "스케줄 자동 진행 중", 실패 시=0
  # if value[0]==0: #0을 return (사냥을 하지 않고 있다는 뜻)
  #   sio.emit("logEvent",[f"{value[1]}", character_name, ERR_MSG])
  # elif value[0]==2: #capture_text_from_region 예외 발생
  #   sio.emit("logEvent",[f"{value[1]}", character_name, STATUS_MSG])
  # else:
  #   sio.emit("logEvent",[f"{btn_name}, {value[0]} 완료", character_name, STATUS_MSG])