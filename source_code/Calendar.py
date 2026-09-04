class Booking:
    def __init__(self , bid , title , start , end):
        self.id = bid
        self.title = title
        self.start = start
        self.end = end

    def __str__(self):
        return f'{self.title} => FROM {self.start} TO {self.end}'
    
class Calendar:
    def __init__(self):
        self.bookings : list[Booking] = []
        
    def add_booking(self , bid , title , start , end):
        new_booking = Booking(bid , title , start , end)
        
        for b in self.bookings:
            if not (end <= b.start or start >= b.end):
                print(f'conflicting dates with : {b.title}')
                return False
            
        self.bookings.append(new_booking)
        self.bookings.sort(key = lambda x : x.start)
        print(f'Booking added {title} ({start} -> {end})')
        return True
    
    def remove_booking(self , bid):
        for b in self.bookings:
            if b.id == bid:
                self.bookings.remove(b)
                print(f'Booking removed {b.title}')
                return True
            
        print(f'Booking ID not found')
        return False
    
    def show_bookings(self):
        if not self.bookings:
            print(f'No bookings available')
            
        else:
            print('Current Schedule')
            for b in self.bookings:
                print(b)
        
                
# testing
cal = Calendar()


cal.add_booking(1 , 'meeting' , 9, 10)
cal.add_booking(2 , 'client call' , 10 , 11)
cal.add_booking(3 , 'lunch' , 12 , 13)
cal.add_booking(4 ,'overlapping tasks' , 9.5 , 10.5)

cal.show_bookings()

cal.remove_booking(2)

cal.show_bookings()