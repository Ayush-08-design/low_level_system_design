from cryptography.fernet import Fernet

class PasswordVault:
    def __init__(self):
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
        self.vault_data = {}
        
    def add_account(self , service , username , password):
        encrypted_pw = self.cipher.encrypt(password.encode())
        self.vault_data[service] = (username , encrypted_pw)
        print(f'[+] Added {service} account securely')
        
    def get_password(self , service):
        if service in self.vault_data:
            username , enc_pw = self.vault_data[service]
            decryp_pw = self.cipher.decrypt(enc_pw).decode()
            
            print(f'Service : {service}')
            print(f'Username : {username}')
            print(f'Password : {decryp_pw}')
        else:
            print(f'[-] No such service found')
            
    def list_accounts(self):
        if not self.vault_data:
            print(f'Vault is Empty')
            return
        print('Stored Accounts ...')
        for s in self.vault_data:
            print(f' -' , s)
            
    def delete_account(self , service):
        if service in self.vault_data:
            del self.vault_data[service]
            print(f'[X] Deleted {service} from vault')
            
        else:
            print(f'[-] Service not found')
            
# testing

if __name__ == '__main__':
    
    vault = PasswordVault()
    
    vault.add_account('Gmail' , 'draula@gmail.com' , 'dracula@123')
    vault.add_account('GitHub' , 'dracula-08-design' , 'hey-hey@123')
    
    vault.list_accounts()
    
    vault.get_password('GitHub')
    
    vault.delete_account('GitHub')
    
    vault.list_accounts()