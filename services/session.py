from enum import Enum

class State(str, Enum):
    IDLE = "idle"
    WAITING_OPTION = "waiting_option"

_sessions: dict[str, State] = {}

def get_state(phone: str) -> State:
    return _sessions.get(phone, State.IDLE)

def set_state(phone: str, state: State):
    _sessions[phone] = state

def reset(phone: str):
    _sessions.pop(phone, None)
