import img_search_utils
import serial_comm
import time
from log_context import trace_step, log_event

@trace_step
def waking_from_sleep_and_deathChk(sleep_time):
  success, _ =img_search_utils.searchImg('death.png', beforeDelay=0, afterDelay=0, chkCnt=2, _region=(770, 675, 400,200))

  log_event("death_check", "END", "FOUND" if success else "NOT_FOUND", image="death.png")

  #절전모드 해제 
  serial_comm.keyboard('g')
  
  if success: #죽어 있다는 뜻
    recovery_found, _ = img_search_utils.searchImg('recover.png', beforeDelay=2, afterDelay=1, _region=(840,580, 200,200))
    log_event('recovery_check', 'END', 'FOUND' if recovery_found else 'NOT_FOUND', image='recover.png')
    return True, "사망체크 루틴 실행"
    
  time.sleep(sleep_time)   #실제로는 열렸는지 확인하는 코드 넣어야됨
  return True, "절전해제 실행"
