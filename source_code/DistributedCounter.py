class Node:
    def __init__(self , node_id , total_nodes , network):
        self.id = node_id
        self.counter = [0] * total_nodes
        self.network = network
        self.network.register(self)
        
    def increment(self):
        self.counter[self.id] += 1
        self.network.broadcast(self , self.counter)
        
    def decrement(self):
        self.counter[self.id] -= 1
        self.network.broadcast(self , self.counter)
        
    def merge(self , incoming):
        for i in range(len(self.counter)):
            self.counter[i] = max(self.counter[i] , incoming[i])
            
    def get_value(self):
        return sum(self.counter)
    
class Network:
    def __init__(self):
        self.nodes = []
        
    def register(self , node):
        self.nodes.append(node)
        
    def broadcast(self , sender , state):
        for node in self.nodes:
            if node != sender:
                node.merge(state)
                
                
                
# testing

if __name__ == '__main__':
    
    net = Network()
    
    a = Node(0 , 3, net)
    b = Node(1 , 3, net)
    c = Node(2 , 3, net)
    
    a.increment()
    a.increment()
    b.increment()
    c.increment()
    
    print('a value :' , a.get_value())
    print('b value :' , b.get_value())
    print('c value :' , c.get_value())