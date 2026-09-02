from abc import ABC , abstractmethod
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import time


class Notifier(ABC):
    
    @abstractmethod
    def send(self , message : str):
        pass

class EmailNotifier(Notifier):
    def send(self , message : str) -> None:
        time.sleep(0.5)
        print(f'Email Sent : {message}')
        
class SMSNotifier(Notifier):
    def send(self , message : str) -> None:
        time.sleep(0.5)
        print(f'SMS Sent : {message}')
        
class PushNotifier(Notifier):
    def send(self , message : str) -> None:
        time.sleep(0.5)
        print(f'Push Notification Sent : {message}')
        
class NotificationManager:
    def __init__(self):
        self.channels = []
        self.lock = Lock()
        
    def register_channel(self , notifier : Notifier):
        with self.lock:
            self.channels.append(notifier)
            
    def send_notification(self , message : str):
        with ThreadPoolExecutor(max_workers = len(self.channels)) as executor:
            for ch in self.channels:
                executor.submit(ch.send , message)
                
                
# Testing
if __name__ == '__main__':
    manager = NotificationManager()
    manager.register_channel(SMSNotifier())
    manager.register_channel(EmailNotifier())
    manager.register_channel(PushNotifier())
    
    manager.send_notification("Double Digit IQ joining the table - Hey smarty think fast")