import img_search_utils
import serial_comm
import time

def waking_from_sleep_and_deathChk(sleep_time):
  result, _ =img_search_utils.searchImg('death.png', beforeDelay=0, afterDelay=0, chkCnt=2, _region=(770, 675, 400,200))

  #절전모드 해제 
  serial_comm.keyboard('g')
  
  if(result==1):
    img_search_utils.searchImg('recover.png', beforeDelay=2, afterDelay=1, _region=(840,580, 200,200))
    return
    
  time.sleep(sleep_time)   #실제로는 열렸는지 확인하는 코드 넣어야됨
  
