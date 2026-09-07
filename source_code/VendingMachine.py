import threading
from dataclasses import dataclass
from typing import Dict , Tuple , List

@dataclass
class Product:
    code : str
    name : str
    price_cents : int
    qty : int

    def __str__(self ):
        return f'{self.code} : {self.name} - ${self.price_cents / 100 : .2f} ({self.qty} left)'
    
class Inventory:
    def __init__(self):
        self.products : Dict[str , Product] = {}
        
    def add_product(self , p : Product):
        if p.code in self.products:
            self.products[p.code].qty += p.qty
        else:
            self.products[p.code] = p

    def get_product(self , code : str) -> Product:
        return self.products.get(code)
    
    def list_products(self) -> List[Product]:
        return list(self.products.values())
    
class CashBox:
    def __init__(self , denominations : list[int]):
        self.coins : Dict[int , int] = {d : 0 for d in denominations}
        self.sorted_denoms = sorted(denominations , reverse = True)
        
    def add_coins(self , denom : int , count : int):
        if denom in self.coins:
            raise ValueError("Unsupported denominations")
        self.coins[denom] += count

    def total_cents(self) -> int:
        return sum(d*c for d , c in self.coins.items())
    
    def make_change(self , amount_cents : int) -> Tuple[bool , Dict[int , int]]:
        if amount_cents < 0:
            return (False , {})
        to_give , remaining = {} , amount_cents
        temp = self.coins.copy()
        for d in self.sorted_denoms:
            if remaining <= 0:
                break
            take = min(remaining // d , temp.get(d , 0))
            if take:
                to_give[d] = take
                temp[d] -= take
                remaining -= d * take

        if remaining != 0:
            return False , {}
        for d , c in to_give.items():
            self.coins[d] -= c
        return True , to_give

    def accept_payment(self , payment : Dict[int , int]):
        for d , c in payment.items():
            if d not in self.coins:
                raise ValueError("Unsupported Denomination")
            self.coins[d] += c

class VendingMachine:
    def __init__(self):
        self.denoms = [10000 , 5000 , 2000 , 1000 , 500 , 100 , 50 , 20 , 10 , 5, 1]
        self.cashbox = CashBox(self.denoms)
        self.inventory = Inventory()
        self.lock = threading.Lock()
        self._send_demo()
        
    def _send_demo(self):
        self.inventory.add_product(Product('A1' , 'water bottle' , 300 , 10))
        self.inventory.add_product(Product('A2' , 'soda can' , 30 , 20))
        self.inventory.add_product(Product('B1' , 'chips' , 40 , 50))
        
        initial_coins = {100 : 30 , 50 : 20 , 20 : 50}
        for d , c in initial_coins.items():
            if d in self.cashbox.coins:
                self.cashbox.add_coins(d , c)
                
    def list_products(self):
        for p in self.inventory.list_products():
            print(p)
            
    def restock(self , code : str , qty : int):
        with self.lock:
            p = self.inventory.get_product(code)
            if not p:
                print('Product not found')
                return
            p.qty += qty
            print(f'Restocked {code}. New Qty : {p.qty}')
            
    def refill_coins(self , denom : int , count : int):
        with self.lock:
            self.cashbox.add_coins(denom , count)
            print(f'Refilled {count} coins of {denom} cents')
            
    def purchase(self , code : str , payment : Dict[int , int]):
        total = sum(d * c for d , c in payment.items())
        with self.lock:
            product = self.inventory.get_product(code)
            if not product:
                return False , 'Product not found'
            if product.qty <= 0:
                return False , 'Out of stock'
            price = product.price_cents
            if total < price:
                return False , 'Insufficient Money'
            change_needed = total - price
            self.cashbox.accept_payment(payment)
            success , change_map = self.cashbox.make_change(change_needed)
            if not success:
                for d , c in payment.items():
                    self.cashbox.coins[d] -= c
                return False , 'Cannot provide change'
            product.qty -= 1
            return True , {'Product' : product.name , 'change_map' : change_map}
        