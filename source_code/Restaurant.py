from threading import Lock
from typing import Literal , Dict


class MenuItem:
    def __init__(self , item_id , name , price):
        self.id = item_id
        self.name = name
        self.price = price

class Order:
    def __init__(self , order_id , items):
        self.id = order_id
        self.items = items
        self.total = sum(i.price for i in items)
        self.status : Literal["Pending" , 'served' , 'preparing'] = 'Pending'
        
class Restaurant:
    def __init__(self ,):
        self.menu_items = {}
        self.orders : dict[str , Order] = {}
        self.lock = Lock()
        
    def add_menu_item(self , item_id , name , price):
        self.menu_items[item_id] = MenuItem(item_id , name , price)
        
    def place_order(self , order_id , item_ids):
        with self.lock:
            items =  [self.menu_items[i] for i in item_ids if i in self.menu_items]
            order = Order(order_id , items)
            self.orders[order_id] = order
            return order
        
    def update_order_status(self , order_id , new_status):
        with self.lock:
            if order_id in self.orders:
                self.orders[order_id].status = new_status
                
    def show_orders(self):
        for o in self.orders.values():
            item_names = [i.name for i in o.items]
            print(f'Order #{o.id}: {item_names} | Total: ${o.total} | Status: {o.status}')
            
            
            
# testing
if __name__ == '__main__':
    r = Restaurant()
    r.add_menu_item(1 , "Pizza" , 250)
    r.add_menu_item(2 , "Coffee" , 250)
    r.add_menu_item(3 , "Tea" , 250)
    
    o1 = r.place_order('101' , [1 ,2])
    o2 = r.place_order(201 , [3])
    
    r.show_orders()
    
    r.update_order_status('101' , 'preparing')
    r.update_order_status(201 , 'served')
    
    r.show_orders()