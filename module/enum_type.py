from enum import Enum


class Speaker(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class GeneratePrompt(Enum):
    INTENT = "intent"
    ODSL = "odsl"
    SCHEDULE_ID = "schedule_id"


class UserIntent(Enum):
    ADD_SCHEDULE = 1
    MODIFY_SCHEDULE = 2
    REMOVE_SCHEDULE = 3
    LIST_SCHEDULE = 4
    DEFAULT = 5