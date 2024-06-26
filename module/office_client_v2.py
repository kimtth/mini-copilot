
from office365.graph_client import GraphClient
from configparser import ConfigParser
from datetime import datetime
from dotenv import load_dotenv
import msal
import os


class O365Client:
    """
    A class for interacting with the Microsoft Office 365 API.

    Attributes:
        settings (ConfigParser): A ConfigParser object containing the settings for the API client.
    """

    def __init__(self):
        """
        Initializes the O365Client object.
        """
        load_dotenv(verbose=False)
        self.settings = self.__load_settings__()

    @staticmethod
    def __load_settings__() -> ConfigParser:
        """
        Loads the settings from the configuration file.

        Returns:
            ConfigParser: A ConfigParser object containing the settings.
        """
        cp = ConfigParser()
        mode = os.getenv("PROD_DEV")
        current_file_path = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_file_path)
        config_file = os.path.join(parent_dir, "settings.dev.cfg" if mode == "DEV" else "settings.cfg")
        cp.read(config_file)

        return cp
    
    def __acquire_token_by_client_credentials__(self) -> dict:
        """
        Acquire token via MSAL
        """
        settings = self.settings
        print(settings)
        authority_url = f'https://login.microsoftonline.com/{settings.get("default", "tenant")}'
        app = msal.ConfidentialClientApplication(
            authority=authority_url,
            client_id=settings.get("client_credentials", "client_id"),
            client_credential=settings.get("client_credentials", "client_secret")
        )
        token = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        return token

    def outlook_event_add(self, subject: str, start_time: datetime, end_time: datetime) -> str:
        """
        Adds a new event to the user's Outlook calendar.

        Args:
            subject (str): The subject of the event.
            start_time (datetime): The start time of the event.
            end_time (datetime): The end time of the event.

        Returns:
            str: The ID of the newly created event.
        """
        client = GraphClient(self.__acquire_token_by_client_credentials__)
        my_user_id = self.settings.get("user_credentials", "username")
        new_event = client.users[my_user_id].calendar.events.add(
            subject=subject,
            body="Scheduled by Outlook Agent",
            start=start_time,
            end=end_time,
            attendees=[my_user_id],
        )
        new_event.execute_query()
        return new_event.id
    

    def outlook_event_update(self, event_id: str, subject: str, start_time: datetime, end_time: datetime):
        """
        Updates an existing event in the user's Outlook calendar.

        Args:
            event_id (str): The ID of the event to update.
            subject (str): The new subject of the event.
            start_time (datetime): The new start time of the event.
            end_time (datetime): The new end time of the event.
        """
        client = GraphClient(self.__acquire_token_by_client_credentials__)
        my_user_id = self.settings.get("user_credentials", "username")
        event_to_update = client.users[my_user_id].calendar.events[event_id]
        event_to_update.subject = subject
        event_to_update.start = start_time
        event_to_update.end = end_time
        # property 'attendees' of 'Event' object has no setter
        event_to_update.update().execute_query()


    def outlook_event_delete(self, schedule_id: str):
        """
        Deletes an event from the user's Outlook calendar.

        Args:
            schedule_id (str): The ID of the event to delete.
        """
        client = GraphClient(self.__acquire_token_by_client_credentials__)
        my_user_id = self.settings.get("user_credentials", "username")
        event_id = schedule_id
        event_to_del = client.users[my_user_id].calendar.events[event_id]
        event_to_del.delete_object().execute_query()


    def outlook_event_list(self) -> list:
        """
        Retrieves a list of events from the user's Outlook calendar.

        Returns:
            list: A list of dictionaries containing information about each event.
        """
        events_payload = []
        client = GraphClient(self.__acquire_token_by_client_credentials__)
        my_user_id = self.settings.get("user_credentials", "username")
        events = client.users[my_user_id].calendar.events.get_all().select(["id", "subject", "body", "start", "end"]).execute_query()
        for idx, event in enumerate(events):
            # print(event.id, event.subject)
            events_payload.append({
                "no": str(idx),
                "id": event.id,
                "subject": event.subject,
                "start": event.start.dateTime,
                "end": event.end.dateTime
            })
        return events_payload
