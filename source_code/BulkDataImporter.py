import json
import csv
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

DATA_STORE = []
DB_LOCK = Lock()

class DataStore:
    
    @staticmethod
    def save(record):
        with DB_LOCK:
            DATA_STORE.append(record)
            
    @staticmethod
    def list_all():
        return DATA_STORE
    
class BaseImporter:
    def __init__(self , file_path):
        self.file_path = file_path
        self.failed_records = []
        
    def load(self):
        raise NotImplementedError()
    
    def validate(self , record):
        return True , ''
    
    def process(self , record):
        DataStore.save(record)
        
    def run(self):
        records = self.load()
        
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(self._process_record , records))
        retry_results = []
        for r in self.failed_records:
            ok , msg = self.validate(r)
            if ok:
                self.process(r)
            else:
                retry_results.append((r , msg))
                
        return {
            'total' : len(records),
            'success' : len(records) - len(retry_results),
            'failed' : len(retry_results),
            'data' : DataStore.list_all()
        }
        
    def _process_record(self , record):
        ok , msg = self.validate(record)
        if ok:
            self.process(record)
        else:
            self.failed_records.append(record)
            
class CSVImporter(BaseImporter):
    def load(self):
        records = []
        
        with open(self.file_path , 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
                
        return records
    
    def validate(self , record):
        if not record.get('id'):
            return False , 'Missing ID'
        return True , ''
    
class JsonImporter(BaseImporter):

    def load(self):
        records = []
        
        with open(self.file_path , 'r') as f:
           return json.load(f)
       
    def validate(self, record):
        if 'id' not in record:
            return False , 'Missing ID'
        return True , ''
    
class ImporterFactory:
    
    @staticmethod
    def get_importer(file_path : str):
        if file_path.endswith('.csv'):
            return CSVImporter(file_path)
        if file_path.endswith('.json'):
            return CSVImporter(file_path)
        raise Exception("Unsupported File Type")
    
    
## Testing

if __name__ == '__main__':
    
    file_name = 'sample.csv'
    with open(file_name , 'w') as f:
        f.write('id,name\n1,Alice\n,Invalid\n2,Bob\n')
        
    importer = ImporterFactory.get_importer(file_name)
    
    output = importer.run()
    
    print("Import Summary")
    print(json.dumps(output , indent = 2))