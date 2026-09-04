import time
import threading
from typing import Optional , Literal


class Elevator:
    def __init__(self , floors : int = 10):
        self.current_floor = 0
        self.direction : Literal["UP" , "DOWN"] = 'UP'
        self.requests = []
        self.total_floors = floors
        self.running : bool = True
        
    def add_request(self , floor : int):
        if 0 <= floor < self.total_floors:
            if floor not in self.requests:
                self.requests.append(floor)
                self.requests.sort()
                print(f'Request added for floor {floor}')
            else:
                print('Invalid floor request')
                
    def move(self):
        while self.running:
            if not self.requests:
                time.sleep(1)
                continue

            target_floor = self.requests[0]
            if self.current_floor < target_floor:
                self.direction = "UP"
                self.current_floor += 1
            elif self.current_floor > target_floor:
                self.direction = 'DOWN'
                self.current_floor -= 1
            else:
                print(f'Reached floor {self.current_floor}. Doors Opening')
                self.requests.pop(0)
                print('Doors closing...')
                continue
            
            print(f'Moving {self.direction} | Current floor {self.current_floor}')
            time.sleep(0.5)
            
    def run(self):
        t = threading.Thread(target=self.move)
        t.daemon = True
        t.start()
        
        
# testing
if __name__ == '__main__':
    e = Elevator(10)
    e.run()
    
    e.add_request(5)
    e.add_request(7)
    e.add_request(2)
    
    time.sleep(10)
    e.running = False
    print("END")