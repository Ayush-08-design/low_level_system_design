class Document:
    def __init__(self):
        self.text = ''
        
    def show(self):
        print(f'Document Text : {self.text}')
        
class Command:
    def execute(self):
        pass

    def unexecute(self):
        pass

class AddTextCommand(Command):
    def __init__(self , document , text):
        self.doc = document
        self.text = text
    
    def execute(self):
        self.doc.text += self.text

    def unexecute(self):
        self.doc.text = self.doc.text[ : -len(self.text)]
        
class UndoManager:
    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []
        
    def execute(self , command):
        command.execute()
        self.undo_stack.append(command)
        self.redo_stack.clear()
        
    def undo(self):
        if not self.undo_stack:
            print(f'Nothing to UNDO')
            return
        cmd = self.undo_stack.pop()
        cmd.unexecute()
        self.redo_stack.append(cmd)
        
    def redo(self):
        if not self.redo_stack:
            print('Nothing to redo')
            return
        cmd = self.redo_stack.pop()
        cmd.execute()
        self.undo_stack.append(cmd)
        
        
## Testing

if __name__ == '__main__':
    
    doc = Document()
    manager = UndoManager()
    
    print(f'\n--------Performing Actions ----------')
    manager.execute(AddTextCommand(doc , 'Hello'))
    manager.execute(AddTextCommand(doc , 'World'))
    doc.show()
    
    print('\n ---------- Undo 1 -----------')
    manager.undo()
    doc.show()
    
    print('\n ---------- Undo 2 -----------')
    manager.undo()
    doc.show()
        
    print('\n ---------- Redo 1 -----------')
    manager.redo()
    doc.show()
    
    print('\n ---------- Redo 2 -----------')
    manager.redo()
    doc.show()