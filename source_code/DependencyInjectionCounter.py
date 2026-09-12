from abc import ABC , abstractmethod

class IStorage:
    
    @abstractmethod
    def get_value(self):
        pass

    @abstractmethod
    def set_value(self , v):
        pass

class InMemoryStorage(IStorage):
    def __init__(self):
        self.value = 0
        
    def get_value(self):
        return self.value
    
    def set_value(self, v):
        self.value = v

class Counter:
    def __init__(self , storage : IStorage):
        self.storage = storage

    def increment(self):
        current = self.storage.get_value()
        print(f'Changing value {current} to {current + 1}')
        self.storage.set_value(current + 1)
        
    def value(self):
        return self.storage.get_value()
    
if __name__ == '__main__':
    storage = InMemoryStorage()
    
    counter = Counter(storage)
    
    counter.increment()
    counter.increment()
    counter.increment()
    
    print(f'Final counter value : ', counter.value())