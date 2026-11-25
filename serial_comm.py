import serial
import time
import random
import utils
import logging
from log_context import log_event

ser = None

cfg = utils.load_json("client_config.json", "config_json")


# 시리얼 연결
# 정상: (True, 메시지) / 예외: 상위 함수로 전달
def connect_serial():
  global ser

  try:
    if ser is None or not ser.is_open:
      log_event("serial.connect", "START", port=cfg.get("serial_port"))
      ser = serial.Serial(
        cfg["serial_port"],
        cfg.get("serial_baudrate", 9600),
        timeout=0.1
      )
      time.sleep(0.5)  # 아두이노 리셋 대기
      print("Serial connected")
      log_event("serial.connect", "END", "SUCCESS")

    return True, "시리얼 연결 완료"

  except Exception as e:
    log_event("serial.connect", "END", "ERROR", level=logging.ERROR, error=repr(e))
    ser = None
    raise ConnectionError(f"Serial connection failed: {e}") from e


# 시리얼 연결 종료
# 정상: (True, 메시지) / 예외: 상위 함수로 전달
def close_serial():
  global ser

  try:
    if ser is not None and ser.is_open:
      log_event("serial.close", "START")
      ser.close()
      log_event("serial.close", "END", "SUCCESS")

    return True, "시리얼 연결 종료 완료"

  finally:
    ser = None


# 명령 전송 및 ACK 대기
# 정상: (True, 메시지) / 예외: 상위 함수로 전달
def send_and_wait(cmd, timeout=3.0):
  global ser

  log_event("serial.send_and_wait", "START", cmd=cmd, timeout=timeout)

  try:
    connect_serial()
    # 입력 버퍼 정리
    ser.reset_input_buffer()

    # 명령 전송
    ser.write((str(cmd) + "\n").encode("utf-8"))
    ser.flush()
    log_event("serial.send_and_wait", "SENT", cmd=cmd)

    # ACK 대기
    start = time.monotonic()
    while time.monotonic() - start < timeout:
      line = ser.readline().decode(errors="ignore").strip()
      if line == "ACK":
        log_event("serial.send_and_wait", "ACK", "COMMAND_COMPLETED", elapsed_ms=round((time.monotonic() - start) * 1000))
        return True, "ACK 수신"

    raise TimeoutError("Arduino ACK timeout")

  except Exception as e:
    log_event("serial.send_and_wait", "END", "ERROR", level=logging.ERROR, error=repr(e), cmd=cmd)
    # 통신 실패 시 연결 종료. 종료 과정의 오류가 원래 예외를 가리지 않도록 함.
    try:
      close_serial()
    except Exception:
      pass
    raise

# 공통 명령 실행
# 정상: (True, 메시지) / 예외: 상위 함수로 전달
def execute_command(cmd, delay=0, timeout=3.0):
  success, message = send_and_wait(cmd, timeout=timeout)

  if delay > 0:
    log_event("serial.execute_command", "WAIT_START", seconds=delay)
    time.sleep(delay)
    log_event("serial.execute_command", "WAIT_END", seconds=delay)

  return success, message


# 랜덤 좌표 계산: 상태 반환이 필요 없는 내부 계산 함수
def random_position(value, range_value):
  end = value + range_value
  return random.randint(min(value, end), max(value, end))


# 랜덤 왼쪽 클릭 (명령 1)
def randClick(xVal, yVal, xRange, yRange, clkSleep):
  randX = random_position(xVal, xRange)
  randY = random_position(yVal, yRange)

  val = f'1!{randX}!{randY}'
  return execute_command(val, clkSleep)


# 랜덤 오른쪽 클릭 (명령 11)
def randClickRight(xVal, yVal, xRange, yRange, clkSleep):
  randX = random_position(xVal, xRange)
  randY = random_position(yVal, yRange)

  val = f'11!{randX}!{randY}'
  return execute_command(val, clkSleep)


# 마우스 드래그 (명령 2)
def mouseDrag(dragValues):
  randStartX = random.randint(
    dragValues['fromStartX'],
    dragValues['toStartX']
  )
  randStartY = random.randint(
    dragValues['fromStartY'],
    dragValues['toStartY']
  )
  randEndX = random.randint(
    dragValues['fromEndX'],
    dragValues['toEndX']
  )
  randEndY = random.randint(
    dragValues['fromEndY'],
    dragValues['toEndY']
  )

  val = f'2!{randStartX}!{randStartY}!{randEndX}!{randEndY}'
  return execute_command(val)


# 키보드 입력 (명령 3)
def keyboard(input, hold_ms=None):
  if hold_ms is None:
    val = f'3!{input}'
  else:
    if not isinstance(hold_ms, int) or isinstance(hold_ms, bool) or hold_ms <= 0:
      raise ValueError("hold_ms는 양의 정수여야 함")
    val = f'3!{input}!{hold_ms}'

  duration_ms = hold_ms if hold_ms is not None else 50
  timeout = max(3.0, len(input) * (duration_ms + 10) / 1000 + 2.0)

  return execute_command(val, timeout=timeout)


# 첫 마우스 사용 시 (명령 5)
def startClick(xVal, yVal, xRange, yRange, clkSleep=0):
  randX = random_position(xVal, xRange)
  randY = random_position(yVal, yRange)

  val = f'5!{randX}!{randY}'
  return execute_command(val, clkSleep)


# ENTER (명령 6)
def enterKey():
  return execute_command('6')


# WIN + B (명령 7)
def winKey():
  return execute_command('7')


# WIN + LEFT (명령 8)
def win_left():
  return execute_command('8')


# ESC (명령 9)
def escKey():
  return execute_command('9')


# 기존 명령 10
def winKey_1():
  return execute_command('10')


def spaceKey():
  return execute_command('12')
