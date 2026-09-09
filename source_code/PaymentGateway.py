import threading , random , time

class PaymentStrategy:
    def process_payment(self , amount , transform_id):
        pass

class CardPayment(PaymentStrategy):
    def process_payment(self, amount, transform_id):
        print(f'[Card] Transaction {transform_id} : Processing ${amount} via Credit/Debit card')
        time.sleep(1)
        print(f'Transaction {transform_id} Payment Successful')
        
class UPIPayment(PaymentStrategy):
    def process_payment(self, amount, transform_id):
        print(f'[UPI] Transaction {transform_id} : Processing ${amount} via UPI')
        time.sleep(1)
        print(f'Transaction {transform_id} Payment Successful')
        
class WalletPayment(PaymentStrategy):
    def process_payment(self, amount, transform_id):
        print(f'[Wallet] Transaction {transform_id} : Deducting ${amount} from Wallet')
        time.sleep(1)
        print(f'Transaction {transform_id} Payment Successful')
        
class PaymentGateway:
    def __init__(self):
        self.strategies = {
            'card' : CardPayment(),
            'upi' : UPIPayment(),
            'wallet' : WalletPayment(),
        }
        self.transactions = {}
        self.lock = threading.Lock()
    
    def pay(self , mode , amount):
        transaction_id = random.randint(1000 , 9999)
        if mode not in self.strategies:
            print(f'[Gateway] Invalid Payment Method')
            return
        
        with self.lock:
            self.transactions[transaction_id] = {'amount' : amount , 'status' : 'pending'}
        self.strategies[mode].process_payment(amount , transaction_id)
        
        with self.lock:
            self.transactions[transaction_id]['status'] = 'SUCCESS'
        print(f'[Gateway] Transaction {transaction_id} Completed \n')
        
        
if __name__ == '__main__':
    pg = PaymentGateway()
    
    t1 = threading.Thread(target = pg.pay , args = ('card' , 2500))
    t2 = threading.Thread(target = pg.pay , args = ('upi' , 200))
    t3 = threading.Thread(target = pg.pay , args = ('wallet' , 27500))
    
    t1.start(); t2.start(); t3.start()
    
    t1.join(); t2.join(); t3.join()
    
    print(f'Final Transaction Logs' , pg.transactions)