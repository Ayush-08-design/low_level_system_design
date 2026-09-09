import re

class Field:
    def __init__(self , name , value , validators = None):
        self.name = name
        self.value = value
        self.validators = validators or []
        
    def validate(self):
        errors = []
        for v in self.validators:
            result = v(self.value)
            if result is not True:
                errors.append(result)
        return errors
    
def required( value):
    if value is None or str(value).strip() == '':
        return f'Field is required'
    return True

def min_length(n):
    def inner(value):
        if len(str(value)) < n:
            return f'Minimum length should be {n}'
        return True
    return inner


def max_length(n):
    def inner(value):
        if len(str(value)) > n:
            return f'Maximum length should be {n}'
        return True
    return inner

def email_validator(value):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(pattern , str(value)):
        return 'Invalid email format'
    return True

def age_validator(value : int):
    if not isinstance(value , int) or value <= 0:
        return "Age must be a positive no"
    return True

class FormValidator:
    def __init__(self):
        self.fields = []
    
    def add_field(self , field):
        self.fields.append(field)
        
    def validate(self):
        errors = {}
        for f in self.fields:
            result = f.validate()
            if result:
                errors[f.name] = result
        return errors
    
    
if __name__ == '__main__':
    form = FormValidator()
    
    form.add_field(Field('username' , 'dracula' , [required , min_length(3)]))
    form.add_field(Field('email' , 'dracula@gmail.com' , [required , email_validator]))
    form.add_field(Field('age' , 0 , [required , age_validator]))
    form.add_field(Field('password' , 'dracula@123' , [required , min_length(6)]))
    
    result = form.validate()
    
    if not result:
        print('All validation passed')
    else:
        print('Validation Errors')
        for field , error in result.items():
            for e in error:
                print(f'- {field} : {e}')