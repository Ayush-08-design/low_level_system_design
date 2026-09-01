import threading

class Account:
    '''Account Class representing a User's Bank account'''
    def __init__(self , acc_no : str , pin : str , balance : int = 0):
        self.acc_no = acc_no
        self.pin = pin
        self.balance = balance

    def verifyPIN(self , pin : str) -> bool:
        return self.pin == pin
    
    def deposit(self , ammount : int) -> bool:
        if ammount <= 0:
            print(f'Invalid ammount')
            return False
        self.balance += ammount
        return True

    def withdraw(self , ammount : int) -> bool | int:
        if ammount <= 0:
            print(f'Invalid ammount of money')
            return False
        elif ammount < self.balance:
            print(f'Insufficient balance')
            return False
        self.balance -= ammount
        return ammount
    
    def getBalance(self):
        return self.balance
    
    
class ATM:
    '''ATM class represent atm machine'''
    def __init__(self , total_cash : int):
        self.total_cash = total_cash
        self.accounts = dict[int , Account]
        self.lock = threading.Lock()
        
    def addAccount(self , acc : Account):
        self.accounts[acc.acc_no] = acc
        
    def authenticate(self , acc_no : str , pin : str):
        acc : Account = self.accounts.get(acc_no , None)
        if acc and acc.verifyPIN(pin):
            print(f'Login successful')
            return acc
        print('Wrong pin')
        return None
    
    def withdraw(self , acc : Account , amt : int):
        with self.lock:
            if amt > self.total_cash:
                return f'Not enough Money'
            result = acc.withdraw(amt)
            if result :
                self.total_cash -= amt
            return result
        
    def deposit(self , acc : Account , amt : int):
        with self.lock:
            result = acc.deposit(amt)
            if result:
                self.total_cash += amt
            return result
        
        
        