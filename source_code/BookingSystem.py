import threading

class Booking:
    def __init__(self , user , resource , start , end):
        self.user = user
        self.resource = resource
        self.start = start
        self.end = end

    def __repr__(self):
        return f'[{self.user} -> {self.resource} ({self.start} -- {self.end})]'
    
class BookingManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.bookings = {}
                cls._instance.manager_lock = threading.Lock()
            return cls._instance
        
    def _conflict(self , resource , start , end):
        if resource not in self.bookings:
            return False
        for b in self.bookings[resource]:
            if not(end <= b.start or start >= b.end):
                return True
            return False
        
    def create_booking(self , user , resource , start , end):
        with self.manager_lock:
            if self._conflict(resource , start , end):
                return False , 'Conflict " Resource is already booked in this time slot'

            b = Booking(user , resource , start , end)
            self.bookings.setdefault(resource , []).append(b)
            return True , 'Booking Confirmed...'
        
    def cancel_booking(self , user , resource):
        with self.manager_lock:
            if resource not in self.bookings:
                return False , 'No Booking Found'
            
            for b in list(self.bookings[resource]):
                if b.user == user:
                    self.bookings[resource].remove(b)
                    return True , 'Booking Cancelled'
            return False , 'No Booking Found'
        
    def list_bookings(self):
        return self.bookings
    
    
# Testing

if __name__ == '__main__':
    
    bm = BookingManager()
    
    print('Creating Bookings...')
    
    print(bm.create_booking('Alice' , 'room1' , 10 , 12))
    print(bm.create_booking('Bob' , 'room1' , 12 , 14))
    print(bm.create_booking('Charlie' , 'room1' , 11 , 13))
    
    print('\n Current Bookings')
    
    print(bm.list_bookings())
    
    print('\n Cancelling Booking')
    
    print(bm.cancel_booking('Alice' , 'room1'))
    
    print('\n Final Bookings')
    
    print(bm.list_bookings())