import re
from collections import defaultdict

class SearchIndexer:
    def __init__(self):
        self.documents = {}
        self.index = defaultdict(set)
        
    def add_document(self , doc_id : int , content : str):
        self.documents[doc_id] = content

    def build_index(self):
        for doc_id , text in self.documents.items():
            words = re.findall(r'\w+' , text.lower())
            for word in words:
                self.index[word].add(doc_id)
                
    def search(self , keyword : str):
        keyword = keyword.lower()
        return list(self.index.get(keyword , []))
    
    
if __name__ == '__main__':
    s = SearchIndexer()
    
    s.add_document(1 , 'The cat sat on the mat')
    s.add_document(2 , 'the dog chased the cat')
    s.add_document(3 , 'the bird sang sweetly')
    
    s.build_index()
    
    print('search results for cat' , s.search('cat'))
    print('search results for dog' , s.search('dog'))
    print('search results for bird' , s.search('bird'))
    print('search results for lion' , s.search('lion'))