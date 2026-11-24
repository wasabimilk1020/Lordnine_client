from cProfile import run
from serial import win32
import os
import socketio
import datetime
import threading
import time
from mainloop import mainLoop
import button_func
import queue
import hashlib
import base64
import get_account
import serial_comm
import json
import logging
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "computer_restart"))
import computer_restart
import game_exe
import img_search_utils
import utils
import re
import code_update

# 로컬 상세 로그 파일 추가 (서버 알림과 별도)
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(log_dir, "client.log"), encoding="utf-8") #FileHandler가 로그를 파일에 저장함 "client.log"
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logging.info("event=CLIENT_START")

last_pong_time = None # 마지막으로 pong을 받은 시간
PONG_TIMEOUT = 20  # 초 (pong 응답 대기 시간)

character_list={}
  
# 작업 큐 생성
task_queue = queue.Queue()

# 작업 처리 스레드 함수
def process_tasks():
  while True:
    try:
      # 큐에서 작업 가져오기
      task = task_queue.get(timeout=10)
      if task is None:
        break  # None이 들어오면 스레드 종료
      print("클라이언트 메인루프 시작")
      # 작업 실행
      func, args = task
      logging.info("step=task_queue event=START func=%s pending=%s", func.__name__, task_queue.qsize())
      func(*args)
      logging.info("step=task_queue event=END result=COMPLETED func=%s", func.__name__)
    except queue.Empty:
      continue  # 작업이 없으면 다시 대기
    except Exception as e:
      logging.exception("step=task_queue event=ERROR")
      print(f"Error processing task: {e}")
    
# 작업 처리 스레드 시작
worker_thread = threading.Thread(target=process_tasks, daemon=True)
worker_thread.start()

#웹소켓 통신
sio = socketio.Client()

@sio.event
def connect():
  global last_pong_time
  global character_list

  print('connection established')
  last_pong_time = time.time()

  if serial_comm.ser is None or not serial_comm.ser.is_open:
    try:
      serial_comm.connect_serial()
    except Exception as e:
      logging.error(f"시리얼 연결 실패: {e}")

  sio.start_background_task(monitor_connection)
  sio.start_background_task(send_ping)

@sio.event
def disconnect():
  global last_pong_time

  last_pong_time = None

  if serial_comm.ser is not None and serial_comm.ser.is_open:
    try:
      serial_comm.close_serial()
    except Exception as e:
      logging.error(f"시리얼 연결 종료 실패: {e}")

@sio.event
def reqAccount(data):
  global character_list   
  try:
    success, result = get_account.get_account_list(sio)
  except Exception:
    logging.exception("step=reqAccount event=ERROR")
    raise

  if success:
    character_list = result
    sio.emit("revAccount", character_list)
  else:
    print(result)

#이렇게 일일이 버튼을 맵핑시켜주는게 아니라 버튼 생성하면 저절로 처리되도록 만들고 싶은데...
button_mapping={
  "status_check_button":button_func.statusChk,  
  "사냥":button_func.normalHunting,
  "어둠의숲":button_func.dungeon,
  "타락한미궁":button_func.dungeon,
  "수련의전당":button_func.dungeon,
  "안타라스":button_func.dungeon,
  "상아탑":button_func.dungeon,
  "여명의사원":button_func.dungeon,
  "운디네사원":button_func.dungeon,
  "이벤트던전":button_func.dungeon,
  "모닝":button_func.morning,
  "우편":button_func.postBox,
  "시즌패스":button_func.seasonpass,
  "아이템분해":button_func.decomposeItem,
  "스킬북분해":button_func.decomposeBook,
  "아이템삭제":button_func.itemDelete,
  "일괄사용":button_func.useItem,
  "사망체크":button_func.deathChk,
  "신탁서":button_func.paper,
  "이벤트상점":button_func.event_store,
  "아가시온":button_func.agasion,
  "모두":button_func.switch_get_item,
  "고급":button_func.switch_get_item,
  "희귀":button_func.switch_get_item,
  "10M":button_func.ten_meter,
  "제한없음":button_func.unlimit,
  # "바람":button_func.decomposeItem,
  # "불":button_func.decomposeItem,
  # "물":button_func.decomposeItem,
  "다이아":button_func.showDiamond,
  "제작":button_func.make_item,
  "파던입장":button_func.party_dun_entry,
  "파티해제":button_func.unparty,
  "귀환":button_func.go_home,
  "봉인사원":button_func.party_dungeon,
  "카이트해적":button_func.party_dungeon,
  "네뷸라이트":button_func.party_dungeon,
  "회색제단":button_func.party_dungeon,
  "최후정원":button_func.party_dungeon,
  "케트라":button_func.party_dungeon,
  "클래스합성":button_func.class_add,
  "아가합성":button_func.aga_add,
  "거래소":button_func.item_exchange,
  "재등록":button_func.re_exchange,
  "정산":button_func.get_exchange,
  "마력잉크":button_func.magic_ink,
  "창정렬":button_func.move_window,
  "실행광고":button_func.gameExe_adRemove,
  "상자열기":button_func.open_box,
  "힐OFF":button_func.heal_off,
  "힐ON":button_func.heal_on,
  "펫가호":button_func.petGaho,

 
}

@sio.event
def button_schedule(data):  #data={"버튼이름":[데이터],"character_list":{"아이디1":핸들 값1,"아이디2":핸들 값2}}
  #global 변수 character_list

  # character_list를 제외한 키가 버튼 이름
  button_name = next((key for key in data if key != "character_list"), None)

  if button_name is None:
      print("버튼 이름 없음")
      return
  
  func_data = data[button_name]
  if len(func_data) != 5:
    print("데이터 개수 오류")
    return
  
  # 대상 캐릭터 목록
  selected = data.get("character_list", {})
  if selected == {}:
      id_handle = list(character_list.items())
  else:
      id_handle = list(selected.items())

  # 버튼에 해당하는 함수 가져오기
  print("버튼이름:", button_name)
  btn_func = button_mapping[button_name]
  # mainLoop 호출을 큐에 추가
  task_queue.put((mainLoop, (sio, btn_func, func_data, id_handle, button_name)))

@sio.event
def recvImage(data):
  img=data[0]
  hash_value=data[1]
  file_name=data[2]
  calculated_hash = hashlib.sha256(img.encode("utf-8")).hexdigest()

  full_path=utils.file_path(f"{file_name}","image_files")  #file, folder, sub_folder

  # 해시 확인
  if hash_value==calculated_hash: 
    image_data = base64.b64decode(img)
    # 파일로 저장
    with open(full_path, "wb") as f:
      f.write(image_data)
    for name in character_list.keys():
      sio.emit("logEvent",["이미지 저장", name, 1]) 
  else:
    print("데이터가 손상되었거나 무결성 검증 실패!")

@sio.event
def reboot_computer(data):  #data={'days': 'WED', 'time': '07:00'}
  computer_restart.run_bat_as_admin(data)

@sio.event
def game_start(data):
  game_exe.start_game()

@sio.event
def update_code(data):
  code_update.run_git_update()

@sio.event
def pong(data):
  global last_pong_time
  # logging.info(f"Received pong from server: {data['time']}")
  last_pong_time = time.time()  # pong 수신 시 갱신

def monitor_connection():
  global last_pong_time

  while not sio.connected:  #첫 호출 시 연결상태 확인. 반드시 연결 후 아래 루프 시작하기 위해서
    time.sleep(0.01)
    continue

  while True:
    if last_pong_time and time.time() - last_pong_time > PONG_TIMEOUT:
      logging.error("서버 응답 없음, 연결 종료.")
      sio.disconnect()  # 명시적으로 연결 종료
      break
    time.sleep(1)  # 1초마다 상태 확인

def send_ping():
  while not sio.connected:  #첫 호출 시 연결상태 확인. 반드시 연결 후 아래 루프 시작하기 위해서
    time.sleep(0.01)
    continue
  
  while True:
    if not sio.connected:
      break

    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sio.emit("ping", {"time": current_time})
    time.sleep(5)

#client_config.json에서 클라이언트 설정
cfg=utils.load_json("client_config.json","config_json")

server_url = cfg["server_url"]
computer_id = cfg["computer_id"]

sio.connect(f"{server_url}?computer_id={computer_id}")

sio.wait()

#길드: 이미지 서치 추가해야함, 상점 루틴: 이건 잘 되는듯 hsv인가 이걸로 확실히 실행이 됬는지 확인 되게 해야 할듯
#절전모드 후 완료 메세지
#윈도우 활설화 실패도 종종 뜨네
#normalHunting 앞 부분 루틴 안정성 있게 만들자. 지도 여는 부분을 수정하라고 하는대 다시 확인하고 질문 해보자
#로그 기록 되게 추가하자.
#주석 처리 할 것 처리해서 chatgpt에게 파일 올려 구조 파악하게 하자.
#왜 그런진 모르겠는대 부활 루틴이 잘 안됨.

# 1. 아두이노 명령 루틴에서 오류가 자주 발생 하는듯. 즉, 아두이노 자체는 실행 됬는대 게임에서 명령이 씹히는듯...
# 2. 아니면 사망 상태에서 실패 한건대 recover.png를 클릭 한 후 너무 짧은 주기 후 바로 던전 진입을 해서 그런가?
# 이건 원인이 부활하기 하고 한 참 걸리는 때가 있음. 임시로 딜레이를 더 주고 확실하게는 부활 됬는지 이미지 체크하자. 임시로 딜레이 7초줌



# 3. 이동 체크 실패 뜨고 사냥터 포탈에 멈춤
# 4. 아래 코드 부분에서 템플릿 매칭이 되지 않음. 왜지? 아직 chk.png가 뜨기 전이라서? 아니면 떳는대도 실패 했나?
#  match_list=["chk.png"]
  # success, match_data=img_search_utils.img_matchTemplate(match_list, 1669, 0, 229, 180)
  # if not success:
  #   return False, {"message": "이동 체크 실패"}
  # time.sleep(2)
