class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class AutoCommpleteSystem:
    def __init__(self):
        self.root = TrieNode()
        
    def insert(self , word):
        node = self.root

        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True

    def _collect(self , node : TrieNode , prefix , result):
        if node.is_end:
            result.append(prefix)
            
        for ch in sorted(node.children.keys()):
            child = node.children[ch]
            self._collect(child , prefix + ch , result)
            
    def suggest(self , prefix):
        node = self.root

        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]
            
        result = []
        self._collect(node , prefix , result)
        return result
        
if __name__ == '__main__':
    
    ac = AutoCommpleteSystem()
    
    words = ['apple' , 'app' , 'ape' , 'bat' , 'ball' , 'banana']
    
    for w in words:
        ac.insert(w)
        
    print('Suggestions for [ap] :' , ac.suggest('ap'))
    print('Suggestions for [ba] :' , ac.suggest('ba'))
    print('Suggestions for [app] :' , ac.suggest('app'))