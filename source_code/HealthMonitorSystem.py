import threading

class AlertStrategy:
    def check(self , vitals , threshold):
        raise NotImplementedError()
    
class ThresholdAlertStrategy(AlertStrategy):
    def check(self , v , t):
        alerts = []
        
        if v['heart'] > t['heart']:
            alerts.append('High heart rate')
            
        if v['temp'] > t['temp']:
            alerts.append('High Tempreture')
            
        if v['bp'] > t['bp']:
            alerts.append('High blood pressure')
        return alerts
    
class UserProfile:
    def __init__(self , thresholds):
        self.thresholds = thresholds
        self.lastVitals = None
        self.logs = []
        self.lock = threading.Lock()
        
class HealthMonitor:
    __instance = None
    
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(HealthMonitor , cls).__new__(cls)
            cls.__instance.users = {}
            cls.__instance.alert_strategy = ThresholdAlertStrategy()
        return cls.__instance
    
    def add_user(self , uid , thresholds):
        self.users[uid] = UserProfile(thresholds)
        
    def update_vitals(self , uid , vitals):
        user = self.users.get(uid)
        if not user:
            return 
        with user.lock:
            user.lastVitals = vitals
            user.logs.append(vitals)
            
            alerts = self.alert_strategy.check(vitals , user.thresholds)
        return alerts
    
    def get_status(self , uid):
        u = self.users.get(uid)
        if not u:
            return None
        return {
            'lastVitals' : u.lastVitals,
            'logs' : u.logs[-5:]
        }
        
        
if __name__ == '__main__':
    
    monitor = HealthMonitor()
    
    monitor.add_user('user1' , {'heart' : 95 , 'temp' : 99 , 'bp' : 140})
    
    out1 = monitor.update_vitals('user1' , {'heart' : 95 , 'temp' : 98 , 'bp' : 150})
    
    out2 = monitor.update_vitals('user1' , {'heart' : 120 , 'temp' : 109 , 'bp' : 140})
    
    print('Alert 1 : ' , out1)
    print('Alert 2 : ' , out2)
    print('Status : ' , monitor.get_status('user1'))