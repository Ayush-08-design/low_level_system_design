class Book:
    def __init__(self , book_id : str , title : str , author : str , content : str = 'Heyyyyy'):
        self.book_id = book_id
        self.author = author
        self.title = title
        self.content = content
        self.is_borrowed = False

    def __str__(self):
        status = "Borrowed" if self.is_borrowed else "Available"
        return f'{self.book_id} | {self.title} by {self.author} [{status}]'
    
    def read(self):
        return self.content
    
class User:
    def __init__(self , user_id , name):
        self.user_id = user_id
        self.name = name
        self.borrowed_books : list[Book] = []
        
    def __str__(self):
        return f'{self.user_id} | {self.name} | Borrowed : {len(self.borrowed_books)} Books'
    
    
class Library:
    def __init__(self):
        self.books : dict[str , Book] = {}
        self.users = {}
        
    def add_book(self , book : Book):
        if book.book_id not in self.books:
            self.books[book.book_id] = Book
            print(f'Book {book.title} added successfully')
        else:
            print('Book already exist')
            
    def register_user(self , user : User):
        if user.user_id not in self.users:
            self.users[user.user_id] = user

            print(f'User {user.name} registered succesfully')
        else:
            print(f'Already registered')
    
    def borrow_book(self , user : User , book : Book):
        if user.user_id not in self.users:
            print(f'Invalid user')
            return
        if book not in self.books:
            return f'Book is not available'
        
        if book.is_borrowed:
            return 'Not available already borrowed by someone else'
        book.is_borrowed = True
        user.borrowed_books.append(book)
        print(f'Book {book.title} borrowed by {user.name}')
        
    def return_book(self , user : User , book : Book):
        if user.user_id not in self.users or book.book_id not in self.books:
            return f'Invalid IDs'
        if book in user.borrowed_books:
            book.is_borrowed = False
            user.borrowed_books.remove(book)
            print(f'{user.name} Returned {book}')
        else:
            print(f'User dont have book')
            
    def show_book(self , book_id):
        if book_id in self.books:
            self.books[book_id].read()