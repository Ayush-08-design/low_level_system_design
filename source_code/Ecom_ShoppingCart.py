import threading

class Product:
    def __init__(self , pid , name , price):
        self.id = pid
        self.name = name
        self.price = price

class CartItem:
    def __init__(self , product : Product , quantity = 1):
        self.product = product
        self.quantity = quantity
        
    def total_price(self):
        return self.product.price * self.quantity
    
class ShoppingCart:
    def __init__(self):
        self.items = {}
        self.lock = threading.Lock()
        
    def add_product(self , product : Product , qty = 1):
        with self.lock:
            if product.id in self.items:
                self.items[product.id].quantity += qty
            else:
                self.items[product.id] = CartItem(product , qty)
            print(f'Added {qty} X {product.name} to Cart')
            
    def remove_product(self , product_id):
        with self.lock:
            if product_id in self.items:
                removed = self.items.pop(product_id)
                print(f'Removed {removed.product.name} from cart ...')
            else:
                print('Product is not found in the cart or deleted already')
                
                
    def view_cart(self):
        print('\n Cart Contents...')
        if not self.items:
            print('Cart is Empty')
            return
        total = 0
        for item in self.items.values():
            cost = item.total_price()
            total += cost
            print(f'{item.product.name} X {item.quantity} = ${cost : .2f}')
        print(f'Total : ${total : .2f}')
        
        
    def checkout(self):
        with self.lock:
            total = sum(item.total_price() for item in self.items.values())
            print(f'Checkout Successfull! Total Amount : ${total : .2f}')
            self.items.clear()
            
            
## testing
if __name__ == '__main__':
    
    p1 = Product(1 , 'Laptop' , 1200.00)
    p2 = Product(2 , 'HeadPhones' , 200.00)
    p3 = Product(3 , 'Mouse' , 100.00)
    
    cart = ShoppingCart()
    
    cart.add_product(p1 , 1)
    cart.add_product(p2 , 2)
    cart.add_product(p3 , 3)
    
    cart.view_cart()
    
    cart.remove_product(2)
    
    cart.view_cart()
    
    cart.checkout()