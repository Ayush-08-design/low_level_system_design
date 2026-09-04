import time , threading

class TrafficLight:
    def __init__(self , name):
        self.name = name
        self.current_state = 'RED'
        self.durations = {'GREEN' : 5 , "YELLOW" : 2 , 'RED' : 5}
        self.running = False

    def set_state(self , state):
        self.current_state = state
        print(f'[{self.name}] Light -> {state}')
        
    def run_cycle(self):
        while self.running:
            for state in ['GREEN' , "YELLOW" , 'RED']:
                self.set_state(state)
                time.sleep(self.durations[state])
                
class TrafficController:
    def __init__(self):
        self.lights = [
            TrafficLight("NORTH"),
            TrafficLight("EAST")
        ]
        self.threads = []
        
    def start_cycle(self):
        for i in self.lights:
            t = threading.Thread(target = i.run_cycle)
            self.threads.append(t)
            t.start()
            
    def emergency_override(self , direction):
        print(f'\n Emergency on {direction} Giving priority')
        for light in self.lights:
            if light.name == direction:
                light.set_state('GREEN')
            else:
                light.set_state('RED')
                
                
# testing
if __name__ == '__main__':
    controller = TrafficController()
    controller.start_cycle()
    
    time.sleep(6)
    controller.emergency_override('EAST')
    
    time.sleep(5)
    for i in controller.lights:
        i.running = False
    print('\n Traffic simulation complete')