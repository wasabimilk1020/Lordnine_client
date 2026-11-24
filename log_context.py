"""현재 작업자 스레드의 실행 ID와 공통 구조화 로그.

로그 기록만 추가하며 기존 함수의 반환값/예외 전파는 변경하지 않는다.
"""
import logging
import threading
from functools import wraps

_state = threading.local()


def set_context(run_id, character_name, handle, routine):
  _state.run_id = run_id
  _state.character_name = character_name
  _state.handle = handle
  _state.routine = routine


def clear_context():
  for name in ("run_id", "character_name", "handle", "routine"):
    if hasattr(_state, name):
      delattr(_state, name)


def _format_fields(fields):
  def printable(value):
    if isinstance(value, str) and any(c.isspace() for c in value):
      return repr(value)
    return str(value)

  return " ".join("%s=%s" % (key, printable(value)) for key, value in fields.items())


def log_event(step, event, result=None, level=logging.INFO, **fields):
  if not logging.getLogger().isEnabledFor(level):
    return

  # 로그 출력이 활성화된 경우에만 부가 필드를 조합한다.
  extra = _format_fields(fields)
  logging.log(
    level,
    "run=%s char=%s routine=%s step=%s event=%s result=%s %s",
    getattr(_state, "run_id", "-"),
    getattr(_state, "character_name", "-"),
    getattr(_state, "routine", "-"),
    step, event, result if result is not None else "-", extra
  )


def trace_step(func):
  """정상 반환·실패 반환·예외를 기록하고 원래 반환/예외는 그대로 전달한다."""
  @wraps(func)
  def wrapper(*args, **kwargs):
    log_event(func.__name__, "START")
    try:
      value = func(*args, **kwargs)
    except Exception as e:
      log_event(func.__name__, "END", "EXCEPTION", logging.ERROR, error=repr(e))
      raise

    result = "COMPLETED"
    fields = {}
    if isinstance(value, tuple) and value and isinstance(value[0], bool):
      result = "SUCCESS" if value[0] else "FAILED"
      if len(value) > 1:
        detail = value[1]
        if isinstance(detail, dict):
          if detail.get("action"):
            fields["action"] = detail["action"]
          if not value[0] and detail.get("message"):
            fields["reason"] = detail["message"]
        elif not value[0] and isinstance(detail, str):
          fields["reason"] = detail
    log_event(func.__name__, "END", result, **fields)
    return value

  return wrapper
