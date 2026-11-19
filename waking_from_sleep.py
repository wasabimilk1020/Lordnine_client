import img_search_utils
import serial_comm
import time

def waking_from_sleep_and_deathChk(btn_name, sleep_time, death_routine=None):  #death_routine=status_check시 루틴 수행을 위한 것
  #해제 전에 death 체크를 한 번 해야되 그냥 사냥 루틴일떄도 죽어 있을 수 있어서
  #절전모드 해제 
  serial_comm.keyboard('g')
  if death_routine==1:
    img_search_utils.searchImg('recover.png', beforeDelay=2, afterDelay=0, _region=(840,580, 200,200))
  time.sleep(sleep_time)   #실제로는 열렸는지 확인하는 코드 넣어야됨
  
  return 0