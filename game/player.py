from enum import Enum


class Player:
    class State(Enum):
        ACTIVE = "active"
        DEAD = "dead"
        BANISHED = "banished"

    def __init__(id: int, is_traitor: bool = False, status: State = State.ACTIVE):
        pass
