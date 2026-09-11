import threading

class State:
    def __init__(self , name):
        self.name = name

class WorkflowDefinition:
    def __init__(self):
        self.status = {}
        self.transitions = {}
        
    def add_state(self , name):
        self.status[name] = State(name)
        
    def add_transition(self , from_state , to_state):
        if from_state not in self.transitions:
            self.transitions[from_state] = []
        self.transitions[from_state].append(to_state)
        
    def is_valid_transition(self , from_state , to_state):
        return to_state in self.transitions.get(from_state , [])
    
class WorkFlowInstance:
    def __init__(self , definition : WorkflowDefinition , start_state):
        self.definition = definition
        self.current_state = definition.status[start_state]
        self.history = [start_state]
        self.lock = threading.Lock()
        
    def move_to(self , next_state_name):
        with self.lock:
            if self.definition.is_valid_transition(self.current_state.name , next_state_name):
                self.current_state = self.definition.status[next_state_name]
                self.history.append(next_state_name)
                print(f'Transition to : {next_state_name}')
            else:
                print(f'Invalid Transition : {next_state_name}')
                
    def get_available_states(self):
        return self.definition.transitions.get(self.current_state.name , [])
    
    def get_history(self):
        return self.history
    
    
    
if __name__ == '__main__':
    
    w = WorkflowDefinition()
    
    for s in ['START' , 'IN_REVIEW' , 'APPROVED' , 'REJECTED']:
        w.add_state(s)
        
    w.add_transition('START' , "IN_REVIEW")
    w.add_transition("IN_REVIEW" , 'APPROVED')
    w.add_transition("IN_REVIEW" , 'REJECTED')
    
    instance = WorkFlowInstance(w , 'START')
    
    print(f'\n Available next : {instance.get_available_states()}')
    
    instance.move_to('IN_REVIEW')
    print(f'\n Available next : {instance.get_available_states()}')
    instance.move_to('APPROVED')
    
    print(f'Transition History : {instance.get_history()}')