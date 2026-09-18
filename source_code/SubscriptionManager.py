from datetime import datetime , timedelta

class Subsription:
    def __init__(self , sub_id , user_id , plan_name , start_date , end_date):
        self.sub_id = sub_id
        self.user_id = user_id
        self.plan_name = plan_name
        self.start_date = start_date
        self.end_date = end_date
        self.status = 'ACTIVE'
        
    def is_active(self):
        today = datetime.now().date()
        return self.status == 'ACTIVE' and today <= self.end_date
    
    def renew(self , days):
        self.end_date += timedelta(days=days)
        
    def cancel(self):
        self.status = 'CANCELLED'
        
class SubscriptionManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SubscriptionManager , cls).__new__(cls)
            cls._instance.subscriptions = {}
        return cls._instance
    
    def add_subscription(self , subscription):
        if subscription.user_id not in self.subscriptions:
            self.subscriptions[subscription.user_id] = []
        self.subscriptions[subscription.user_id].append(subscription)
        
    def cancel_subscription(self , user_id , sub_id):
        for s in self.subscriptions.get(user_id , []):
            if s.sub_id == sub_id:
                s.cancel()
                
    def renew_subscription(self , user_id , sub_id , days):
        for s in self.subscriptions.get(user_id , []):
            if s.sub_id == sub_id:
                s.renew(days)
                
                
    def get_active(self , user_id):
        return [s for s in self.subscriptions.get(user_id , []) if s.is_active()]
    
    
    
    
    
# Testing
if __name__ == '__main__':   
    m = SubscriptionManager()
    s1 = Subsription(
        1 , 101 , 'Premium' , datetime.now().date() , datetime.now().date() + timedelta(days=7)
    )
    m.add_subscription(s1)
    
    print('Active subs before cancel' , [s.plan_name for s in m.get_active(101)])
    
    m.cancel_subscription(101 , 1)
    print('Active subs after cancel' , [s.plan_name for s in m.get_active(101)])
    
    m.renew_subscription(101 , 1, 10)
    
    print(f'Renew Attempted -> Status {s1.status} , | End date {s1.end_date}')