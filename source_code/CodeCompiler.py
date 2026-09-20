import threading
import sys
import io
import traceback

class CodeSnippet:
    def __init__(self , sid , code):
        self.id = sid
        self.code = code

class ExecutionResult:
    def __init__(self , success , output = '', error = ''):
        self.success = success
        self.output = output
        self.error = error
        
class Repository:
    def __init__(self):
        self.snippets = []
        
    def add(self , code):
        sid = len(self.snippets)
        snippet = CodeSnippet(sid , code)
        self.snippets.append(snippet)
        return sid
    
    def get(self , sid):
        if 0 <= sid < len(self.snippets):
            return self.snippets[sid]
        return None
    
class ExecutionEngine:
    def execute(self , code):
        output_capture = io.StringIO()
        error_capture = ''
        
        def target():
            nonlocal error_capture
            try:
                restricted_globals = {'__builtins__' : {'print' : print}}
                sys.stdout = output_capture
                exec(code , restricted_globals)
            except Exception:
                error_capture = traceback.format_exc()
            finally:
                sys.stdout = sys.__stdout__
                
            thread = threading.Thread(target = target)
            thread.start
            
            thread.join(2)
            
            if thread.is_alive():
                return ExecutionResult(False , error= 'Timeout / Infinte loop detected')
            if error_capture:
                return ExecutionResult(False , error= error_capture)
            return ExecutionResult(True , output_capture.getValue())
    
class CompilerService:
    def __init__(self):
        self.repo = Repository()
        self.engine = ExecutionEngine()
        
    def submit(self , code):
        return self.repo.add(code)
    
    def run(self , sid):
        snippet = self.repo.get(sid)
        if not snippet:
            return ExecutionResult(False , error = 'Snippet Not Found')
        return self.engine.execute(snippet.code)
    
    def history(self):
        return [(snip.id , snip.code) for snip in self.repo.snippets]
    
    

## Testing
    
if __name__ == '__main__':
    
    service = CompilerService()
    
    print('Code')
    sid = service.submit("print('hello compiler !')")
    print('------Running Code------')
    result = service.run(sid)
    
    print('Success :' , result.success)
    print('Output :' , result.output)
    print('Error :' , result.error)