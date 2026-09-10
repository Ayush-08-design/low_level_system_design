class PermissionSystem:
    def __init__(self):
        self.role_permissions = {}
        self.user_roles = {}
        
    def add_role(self , role_name):
        if role_name not in self.role_permissions:
            self.role_permissions[role_name] = set()
            
    def add_permission_to_role(self , role_name , permission):
        if role_name not in self.role_permissions:
            self.add_role(role_name)
        self.role_permissions[role_name].add(permission)
        
    def add_user(self , username):
        if username not in self.user_roles:
            self.user_roles[username] = set()
            
    def assign_role_to_user(self , username , role_name):
        if username not in self.user_roles:
            self.add_user(username)
        self.user_roles[username].add(role_name)
        
    def check_user_permission(self , username , permission):
        roles = self.user_roles.get(username , [])
        for role in roles:
            if permission in self.role_permissions.get(role , []):
                return True
            return False
        
    def display_user_access(self , username):
        if username not in self.user_roles:
            return f'User {username} not found'
        roles = self.user_roles[username]
        permissions = set()
        for role in roles:
            permissions |= self.role_permissions.get(role , set())
        return f'User {username} \n Roles : {roles} ,\n Permission : {permissions}'
    
    
if __name__ == '__main__':
    
    ps = PermissionSystem()
    
    ps.add_role('Admin')
    ps.add_role('Editor')
    
    ps.add_permission_to_role('Admin' , 'add_user')
    ps.add_permission_to_role('Admin' , 'delete_user')
    ps.add_permission_to_role('Editor' , 'edit_content')
    
    ps.add_user('Alice')
    ps.add_user('Bob')
    
    ps.assign_role_to_user('Alice' , 'Admin')
    ps.assign_role_to_user('Bob' , 'Editor')
    
    print(ps.display_user_access('Alice'))
    print(ps.display_user_access('Bob'))
    
    print('Can alice delete user' , ps.check_user_permission('Alice' , 'delete_user'))
    print('Can bob delete user' , ps.check_user_permission('Bob' , 'delete_user'))