import threading
import time

class PointStrategy:
    def calculate(self , amount):
        raise NotImplementedError
    
class DefaultPointStrategy(PointStrategy):
    def calculate(self , amount):
        return amount // 10
    
class User:
    def __init__(self , user_id , name):
        self.user_id = user_id
        self.name = name
        self.points = 0
        
    def add_points(self , p):
        self.points += p

    def deduct_points(self , p):
        if self.points >= p:
            self.points -= p
            return True
        return False
    
class LoyaltyService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(LoyaltyService , cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.users = {}
        self.transactions = []
        self.lock = threading.Lock()
        self.strategy = DefaultPointStrategy()
        
    def enroll_user(self , user_id , name):
        self.users[user_id] = User(user_id , name)
        
    def earn_points(self , user_id , amount):
        pts = self.strategy.calculate(amount)
        
        with self.lock:
            user = self.users[user_id]
            user.add_points(pts)
            self.transactions.append(
                ('earn' , user_id , pts , time.time())
            )
        return pts
    
    def redeem_points(self , user_id , pts_required):
        with self.lock:
            user : User = self.users[user_id]
            if user.deduct_points(pts_required):
                self.transactions.append(
                    ('redeem' , user_id , pts_required , time.time())
                )
                return True
            return False
        
    def get_user_points(self , user_id):
        return self.users[user_id].points
    
    
    
# Testing

if __name__ == '__main__':
    
    service = LoyaltyService()
    
    service.enroll_user('U1' , 'Dracula')
    
    earned = service.earn_points('U1' , 250)
    print('Points earned' , earned)
    
    redeemed = service.redeem_points('U1' , 10)
    print('redeemed' , redeemed)
    
    print('Current Points' , service.get_user_points('U1'))