
"""
This module contains the implementation of a ChatbotInterface and a ChatBot class that implements the interface.
The ChatBot class uses IntentStrategy classes to execute different actions based on the user's intent.
The ChatBot class also uses the O365Client class to interact with Microsoft Office 365 API to manage schedules.
The ChatBot class uses the generate_odsl_execute function from the odsl_interpreter module to execute ODSL commands.
The ChatBot class uses the chat_completion function from the method_util module to generate responses based on the conversation history and user input.
The DialogAction class is used to represent a dialog action with an id, intent, speaker, message, and timestamp.
The Speaker enum is used to represent the speaker of a dialog action (USER or ASSISTANT).
The GeneratePrompt enum is used to represent the type of prompt to generate a response.
The UserIntent enum is used to represent the user's intent (MODIFY_SCHEDULE, REMOVE_SCHEDULE, LIST_SCHEDULE, ADD_SCHEDULE, or DEFAULT).
"""
import logging
from uuid import uuid4 as uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from module.odsl_interpreter import generate_odsl_execute
from module.office_client_v2 import O365Client
from module.enum_type import Speaker, GeneratePrompt, UserIntent
from module.method_util import get_func_list, replace_first_param, try_get_first_parameter_in_function_call, try_parse_int, chat_completion


class DialogAction(BaseModel):
    id: str
    intent: Optional[int] = 0
    speaker: Speaker
    message: str
    timestamp: str


class IntentStrategy(ABC):
    def __init__(self, chatbot):
        self.chatbot = chatbot

    @abstractmethod
    def execute(self, question: str, intent: int):
        pass


class ModifyScheduleStrategy(IntentStrategy):
    def execute(self, question: str, intent: int):
        return self.chatbot.get_respond(question, intent)

class RemoveScheduleStrategy(IntentStrategy):
    def execute(self, question: str, intent: int):
        return self.chatbot.get_respond(question, intent)
    
class ListScheduleStrategy(IntentStrategy):
    def execute(self, question: str, intent: int):
        return self.chatbot.get_schedule_list()

class DefaultStrategy(IntentStrategy):
    def execute(self, question: str, intent: int):
        return self.chatbot.get_respond(question, intent)


class ChatbotInterface(ABC):
    @abstractmethod
    def __init__(self):
        self.conversation_history: List[DialogAction] = []

    @abstractmethod
    def send_message(self, question: str):
        pass

    @abstractmethod
    def get_intent(self, question: str):
        pass

    @abstractmethod
    def get_schedule_list(self):
        pass

    @abstractmethod
    def get_respond(self, question: str):
        pass


class ChatBot(ChatbotInterface):

    def __init__(self):
        super().__init__()
        self.conversation_history = []
        self.office_client = O365Client()
        self.strategies = {
            UserIntent.MODIFY_SCHEDULE.value: ModifyScheduleStrategy(self),
            UserIntent.REMOVE_SCHEDULE.value: RemoveScheduleStrategy(self),
            UserIntent.LIST_SCHEDULE.value: ListScheduleStrategy(self)
        }
        self.schedule_list = []

    def send_message(self, question: str) -> str:
        try:
            # Here you can implement your message sending logic
            intent = self.get_intent(question)
            action = DialogAction(id=str(uuid()), intent=intent, speaker=Speaker.USER,
                                  message=question, timestamp=str(datetime.now()))
            self.conversation_history.append(action)
            logging.info('<send_message>')
            logging.info(action)
            # If intent is not a key in the dictionary, it returns DefaultStrategy()
            strategy = self.strategies.get(intent, DefaultStrategy(self))
            respond_message = strategy.execute(question, intent)
            return respond_message
        except Exception as e:
            logging.error(e)
            raise Exception('Failed to send message')

    def get_intent(self, question: str) -> int:
        try:
            # msg_history = self.get_conversation_history_with_speaker()
            intent_result = chat_completion([], question, GeneratePrompt.INTENT.value)

            if try_parse_int(intent_result):
                intent_num = int(intent_result)
            else:
                intent_num = int(UserIntent.DEFAULT.value)
            logging.info('<get_intent>')
            logging.info(intent_num)
            return intent_num
        except Exception as e:
            logging.error(e)
            raise Exception('Failed to get intent')

    def get_schedule_list(self) -> str:
        try:
            schedule_ids = self.office_client.outlook_event_list()
            self.schedule_list = schedule_ids
            schedule_ids_select = "".join(
                [f"No.{s['no']} {s['subject']} {s['start']}-{s['end']}\n" for s in schedule_ids])
            
            if schedule_ids_select == "":
                schedule_ids_select = "No schedule found"

            nx_action = DialogAction(id=str(uuid()), intent=UserIntent.LIST_SCHEDULE.value, speaker=Speaker.ASSISTANT,
                                     message=f"{schedule_ids_select}", timestamp=str(datetime.now()))
            self.conversation_history.append(nx_action)

            logging.info('<get_schedule_list>')
            logging.info(nx_action)
            return nx_action.message
        except Exception as e:
            logging.error(e)
            raise Exception('Failed to get schedule list')

    def get_respond(self, question: str, intent: int) -> str:
        try:
            msg_history = self.get_conversation_history_with_speaker()
            response = chat_completion(msg_history,
                                       question, GeneratePrompt.ODSL.value)
            response_action = DialogAction(id=str(uuid()), intent=intent, speaker=Speaker.ASSISTANT,
                                           message=response, timestamp=str(datetime.now()))
            logging.info('<get_respond>')
            logging.info(msg_history)
            logging.info(response_action)
            self.conversation_history.append(response_action)

            func_list = get_func_list()

            if any(func in response_action.message for func in func_list):
                func_call = response_action.message
                logging.info('<get_respond><func_call>')
                logging.info(func_call)
                schedule_id = self.get_schedule_id(func_call)

                if schedule_id:
                    schedule_id = self.get_schedule_id(func_call)
                    func_call = replace_first_param(func_call, schedule_id)
                    logging.info('<get_respond><func_call>2')
                    logging.info(func_call)
                    generate_odsl_execute(func_call)
                else:
                    generate_odsl_execute(func_call)

                response_action.message = func_call

            return response_action.message
        except Exception as e:
            raise Exception('Failed to get respond: {}'.format(e))

    def get_schedule_id(self, question: str) -> str:
        try:
            _target_no = try_get_first_parameter_in_function_call(question)

            # find schedule id in schedule list by schedule no.
            import re
            match = re.search(r'\d+', _target_no)  # "No.4 H2 Goals" -> "4"
            target_no = None
            if match:
                target_no = match.group()
            schedule_ids = self.office_client.outlook_event_list()
            schedule_no = [schedule['id'] for schedule in schedule_ids if str(
                schedule['no']) == target_no]

            schedule_id = None
            logging.info(
                f'<get_schedule_no>:{_target_no}:{target_no}:{schedule_no}')
            if len(schedule_no) > 0:
                schedule_id = schedule_no[0]

            logging.info(f'<get_schedule_id>{schedule_id}')

            return schedule_id
        except Exception as e:
            logging.error(f'Failed to get schedule id: {e}')
            raise Exception('Failed to get schedule id')

    def get_conversation_history(self) -> List[DialogAction]:
        return self.conversation_history

    def clear_conversation_history(self):
        self.conversation_history.clear()

    def get_conversation_history_with_speaker(self) -> List[dict]:
        conversation_history_for_oai = [
            {"role": action.speaker.value, "content": action.message} for action in self.conversation_history]

        return conversation_history_for_oai
