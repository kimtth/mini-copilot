
"""
This module contains the ODSLInterpreter class and the Command class.
The ODSLInterpreter class is responsible for generating and executing ODSL commands.
The Command class represents a command in the ODSL language and is responsible for executing the command.
"""
from datetime import date, datetime
import logging
from textx import metamodel_from_file

from abc import ABC, abstractmethod
from pydantic import Field

import os
from module.office_client_v2 import O365Client


class ODSLInterface(ABC):
    @abstractmethod
    def execute(self):
        """
        Abstract method to be implemented by subclasses.
        """
        pass


class Command(ODSLInterface):
    """
    Class representing a command in the ODSL language.
    """
    command: str = Field(...)
    command_name: str = Field(...)

    def __init__(self, command):
        """
        Initializes a new instance of the Command class.

        :param command: The command to be executed.
        """
        self.command = command
        self.command_name = self.__cname__(command)
        self.client = O365Client()

    def execute(self, **kwargs):
        """
        Executes the command.
        """
        commands = {
            'AddOutlookSchedule': self.add_outlook_schedule,
            'ModifyOutlookSchedule': self.modify_outlook_schedule,
            'RemoveOutlookSchedule': self.remove_outlook_schedule
        }
        if self.command_name in commands:
            commands[self.command_name](**kwargs)
        else:
            raise Exception('Command not found')

    def __str_to_datetime__(self, datetime_str: str) -> datetime:
        """
        Converts a string representation of a datetime to a datetime object.

        :param datetime_str: The string representation of the datetime.
        :return: A datetime object.
        """
        try:
            return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        except Exception as e:
            try:
                # '2023-10-16T11:00:00.0000000' 
                return datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S.%f')
            except Exception as e:
                logging.info(e)
                raise Exception('Invalid datetime format')
    
    def __cname__(self, o) -> str:
        """
        Gets the name of a class.

        :param o: The class.
        :return: The name of the class.
        """
        return o.__class__.__name__

    def add_outlook_schedule(self, description: str, start_time: str, end_time: str):
        """
        Adds an Outlook schedule.

        :param subject: The subject of the schedule.
        :param start_time: The start time of the schedule.
        :param end_time: The end time of the schedule.
        """
        try:
            if 'YYYY-MM-DD' in start_time:
                start_time = start_time.replace('YYYY-MM-DD', str(date.today())) # str(date.today()) returns 2023-11-16
            if 'YYYY-MM-DD' in end_time:
                end_time = end_time.replace('YYYY-MM-DD', str(date.today()))
                
            start_time = self.__str_to_datetime__(start_time) # type: ignore
            end_time = self.__str_to_datetime__(end_time) # type: ignore

            self.client.outlook_event_add(description, start_time, end_time) # type: ignore
            logging.info(f'Add Outlook schedule with subject {description} from {start_time} to {end_time}')
        except Exception as e:
            logging.info(e)
            raise Exception('Failed to add Outlook schedule')

    def modify_outlook_schedule(self, schedule_id: str, description: str, start_time: str, end_time: str):
        """
        Modifies an Outlook schedule.

        :param schedule_id: The ID of the schedule.
        :param subject: The new subject of the schedule.
        :param start_time: The new start time of the schedule.
        :param end_time: The new end time of the schedule.
        """
        try:
            if 'YYYY-MM-DD' in start_time:
                start_time = start_time.replace('YYYY-MM-DD', str(date.today()))
            if 'YYYY-MM-DD' in end_time:
                end_time = end_time.replace('YYYY-MM-DD', str(date.today()))

            start_time = self.__str_to_datetime__(start_time) # type: ignore
            end_time = self.__str_to_datetime__(end_time) # type: ignore
            
            self.client.outlook_event_update(schedule_id, description, start_time, end_time) # type: ignore
            logging.info(f'{schedule_id}: Modify Outlook schedule with subject {description} from {start_time} to {end_time}')
        except Exception as e:
            logging.info(e)
            raise Exception('Failed to modify Outlook schedule')

    def remove_outlook_schedule(self, schedule_id: str):
        """
        Removes an Outlook schedule.

        :param schedule_id: The ID of the schedule.
        """
        try:
            self.client.outlook_event_delete(schedule_id)
            logging.info(f'{schedule_id}: Remove Outlook schedule')
        except Exception as e:
            logging.info(e)
            raise Exception('Failed to remove Outlook schedule')
        
    def list_outlook_schedule(self):
        """
        Lists up Outlook schedules.
        """
        try:
            events_payload = self.client.outlook_event_list()
            logging.info('List up Outlook schedules')
            logging.info(events_payload)
            return events_payload
        except Exception as e:
            logging.info(e)
            raise Exception('Failed to list up Outlook schedules')
        

def generate_odsl_execute(script_str: str):
    """
    Generates and executes ODSL commands.

    :param script: The ODSL script to be executed.

    http://textx.github.io/textX/3.1/
    https://github.com/textX/textX
    """
    try:
        # Create meta-model from the grammar.
        mm_def_path = os.path.join(os.path.dirname(__file__), 'odsl_model.txt')
        mm = metamodel_from_file(mm_def_path)

        # script_str sample => add_outlook_schedule("Meeting with AB", "2023-11-16 9:00:00", "2023-11-16 10:00:00")
        model = mm.model_from_str(script_str)
        
        # get paramters from model
        logging.info('<generate_odsl_execute>')
        logging.info(model)

        # Let's interpret the model
        for command in model.commands:
            logging.info('<generate_odsl_execute>:<command>')
            logging.info(vars(command))

            cl = Command(command)
            allowed_keys = {'description', 'start_time', 'end_time', 'schedule_id'}
            kwargs = vars(command)   
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in allowed_keys}

            logging.info(cl.command_name)
            logging.info(filtered_kwargs)
            cl.execute(**filtered_kwargs)
    except Exception as e:
        raise Exception('Failed to generate and execute ODSL commands: {}'.format(e))
