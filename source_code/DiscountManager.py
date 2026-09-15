import datetime
import threading

class DiscountStrategy:
    def apply(self , total):
        raise NotImplementedError()
    
class PercentageDiscount:
    def __init__(self , percent):
        self.percent = percent

    def apply(self , total):
        return total - (total * self.percent / 100)
    
class FlatDiscount:
    def __init__(self , amount):
        self.amount = amount
        
    def apply(self , total):
        return max(total - self.amount , 0)
    
class Coupon:
    def __init__(self , cid , strategy , expiry , min_order , max_uses):
        self.id = cid
        self.strategy = strategy
        self.expiry = expiry
        self.min_order = min_order
        self.max_uses = max_uses
        self.current_uses = 0
        
class CouponManager:
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.coupons = {}
        self.use_lock = threading.Lock()
        
    @classmethod
    def instance(cls):
        if not cls._instance:
            cls._instance = CouponManager()
        return cls._instance
    
    def create_coupon(self , cid , ctype , amount , days_valid , min_order , max_uses):
        expiry = datetime.datetime.now() + datetime.timedelta(days = days_valid)
        
        if ctype == 'percent':
            strategy = PercentageDiscount(amount)
        else:
            strategy = FlatDiscount(amount)
        
        coupon = Coupon(cid , strategy , expiry , min_order , max_uses)
        self.coupons[cid] = coupon
        
    def validate(self , coupon : Coupon , total):
        if datetime.datetime.now() > coupon.expiry:
            return False , 'Expired'

        if coupon.current_uses >= coupon.max_uses:
            return False , 'Usage Limit reached'
        
        if total < coupon.min_order:
            return False , 'Minimum order not yet'
        
        return True , 'Valid'
    
    def apply_coupon(self , cid , total):
        if cid not in self.coupons:
            return False , 'Invalid Coupons' , total
        
        c = self.coupons[cid]
        valid , msg = self.validate(c , total)
        if not valid:
            return False , msg , total
        
        with self.use_lock:
            c.current_uses += 1
        discounted_total = c.strategy.apply(total)
        return True , 'Apllied' , discounted_total
    
    
    
# Testing

if __name__ == '__main__':
    
    manager = CouponManager.instance()
    
    manager.create_coupon('DISC10' , 'percent' , 10 , 3, 100 , 5)
    
    manager.create_coupon('FLAT50' , 'flat' , 50 ,5 ,200 , 2)
    
    print(manager.apply_coupon('DISC10' , 150))
    print(manager.apply_coupon('FLAT50' , 220))
    print(manager.apply_coupon('FLAT50' , 150))