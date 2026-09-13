import hashlib , random , threading , time

class AuthSystem:
    def __init__(self):
        self.users = {}
        self.lock = threading.Lock()
        
    def hash_password(self , password):
        return hashlib.sha3_256(password.encode()).hexdigest()
    
    def register_user(self , username , password):
        with self.lock:
            if username in self.users:
                return f'User already exists'
            self.users[username] = {'password_hash' : self.hash_password(password) , 'otp' : None , 'otp_expiry' : 0}
        return f'User {username} registered successfully'
    
    def login(self , username , password):
        with self.lock:
            user = self.users.get(username)
            if not user:
                return f'User Not Found'
            if user['password_hash'] != self.hash_password(password):
                return 'Invalid Password'
            
        otp = random.randint(100000 , 999999)
        expiry = time.time() + 10
        user['otp'] = otp
        user['otp_expiry'] = expiry
        print(f'[SYSTEM] OTP for {username} : {otp} (valid for only 10 secs)')
        return f'Password verified . OTP sent'
    
    def verify_otp(self , username , otp):
        with self.lock:
            user = self.users.get(username)
            if not user or user['otp'] is None:
                return 'OTP is not generated , Please login first'
            if time.time() > user['otp_expiry']:
                return 'OTP expired.'
            if user['otp'] != otp:
                return 'Invalid OTP.'
        return f'Access Granted to [{username}]'


# testing

if __name__ == '__main__':
    auth = AuthSystem()
    
    print(auth.register_user('dracula' , 'dracula@123'))
    print(auth.login('dracula' , 'dracula@123'))
    
    otp_input = int(input('Enter recieved OTP : '))
    print(auth.verify_otp('dracula' , otp_input))