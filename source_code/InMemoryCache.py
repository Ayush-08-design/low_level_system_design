from collections import OrderedDict
import threading

class InMemoryCache:
    def __init__(self , capacity):
        self.capacity = capacity
        self.cache = OrderedDict()
        self.lock = threading.Lock()
        
    def get(self , key):
        with self.lock:
            if key not in self.cache:
                print(f'Key {key} Not found')
                return None
            self.cache.move_to_end(key)
            print(f'Get : {key} -> {self.cache[key]}')
            return self.cache[key]
        
    def put(self , key , value):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.capacity:
                removed = self.cache.popitem(last = False)
                print(f'Evicted (LRU) : {removed}')
            print(f'PUT : {key} -> {value}')
            
    def display(self):
        with self.lock:
            print(f'Current cache status -> {dict(self.cache)}')