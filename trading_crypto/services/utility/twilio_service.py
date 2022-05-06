import os
from dotenv import load_dotenv
from twilio.rest import Client
load_dotenv()

class TwilioService:
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_SID')
        self.account_token = os.getenv('TWILIO_TOKEN')
        self.client = Client(self.account_sid, self.account_token)


    def send_text(self, recipient_number, message):
        self.client.messages.create(
            to=recipient_number,
            from_="+12023355447",
            body=message)
         
    def call(self):
        return

    def get_record(self, id):
        return