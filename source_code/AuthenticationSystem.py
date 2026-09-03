import hashlib
import threading
import time

class User:
    def __init__(self , username , password):
        self.username = username
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        self.is_logged_in = False

    def verify_password(self , password):
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
    
class AuthSystem:
    def __init__(self):
        self.users = {}
        self.sessions = {}
        self.lock = threading.Lock()
        
    def register(self , username , password):
        with self.lock:
            if username in self.users:
                print(f'Username : {username} already exists')
                return False
            self.users[username] = User(username , password)
            print(f'User : {username} registered successfully')
            
            return True
        
    def login(self , username , password):
        with self.lock:
            user : User = self.users.get(username)
            if not user:
                print('user not found')
                return False
            if not user.verify_password(password):
                print('Invalid password')
                return False
            user.is_logged_in = True
            self.sessions[username] = time.time()
            print(f'User " {username} logged in successfully')
            
    def logout(self , username):
        with self.lock:
            user = self.users.get(username)
            if user and user.is_logged_in:
                user.is_logged_in = False
                self.sessions.pop(username , None)
                print(f'User : {username} logged out')
                return True
            
            print(f'No active sessions')
            return False
        
    def show_active_users(self):
        print(f'Active users : {list(self.sessions.keys())}')
        return list(self.sessions.keys())