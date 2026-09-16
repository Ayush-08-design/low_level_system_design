import time
import threading

class Auction:
    def __init__(self , auction_id , item_name , start_price , duration_seconds):
        self.id = auction_id
        self.item_name = item_name
        self.highest_bid = start_price
        self.highest_bidder = None
        self.start_time = time.time()
        self.end_time = self.start_time + duration_seconds
        self.bid_history = []
        self.lock = threading.Lock()
        
        
    def is_active(self):
        return time.time() < self.end_time
    
    def place_bid(self , user , amount):
        with self.lock:
            if not self.is_active():
                return f'Auction Already Ended'
            if amount <= self.highest_bid:
                return f'Your Bid is too low Minimum bid {self.highest_bid + 1}'
            self.highest_bid = amount
            self.highest_bidder = user
            
            self.bid_history.append((user , amount , time.time()))
            return f'Bid accepted : {user} -> {amount}'
        
class AuctionManager:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(AuctionManager , cls).__new__(cls)
            cls._instance.auctions = {}
        return cls._instance
    
    def create_auction(self , auction_id , item  , start_price , duration_seconds):
        auction = Auction( auction_id , item  , start_price , duration_seconds)
        self.auctions[auction_id] = auction
        return auction
    
    def get_auction(self , auction_id):
        return self.auctions.get(auction_id)
    
    def place_bid(self , auction_id , user , amount):
        auc : Auction | None = self.get_auction(auction_id)
        
        if not auc:
            return 'Auction Not Found'
        return auc.place_bid(user , amount)
    
    def end_auction(self , auction_id):
        auc = self.get_auction(auction_id)
        if not auc:
            return 'Auction Not Found'
        if auc.highest_bidder is None:
            return f'Auction Ended with No winner'
        return f'Winner : [{auc.highest_bidder}] with amount [{auc.highest_bid}]'
    
    
    
# Testing
if __name__ == '__main__':
    
    manager = AuctionManager()
    
    auction = manager.create_auction('A1' , 'Laptop' , 500 , 5)
    
    print(manager.place_bid('A1' , 'Alice' , 500))
    print(manager.place_bid('A1' , 'Bob' , 600))
    
    time.sleep(6) # bidding expires after this
    
    print(manager.place_bid('A1' , 'Charlie' , 700)) # Invalid
    
    print(manager.end_auction('A1'))