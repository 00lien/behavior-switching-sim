from configparser import ConfigParser
import io
import ast
import json

class Configs:

    def __init__(self) -> None:
        self.config = ConfigParser()
        self.config.read('config.ini')
        self.load_all()
            
    
    def list_all(self):
        print("List all contents")
        for section in self.config.sections():
            print("Section: %s" % section)
            for options in self.config.options(section):
                print("x %s:::%s:::%s" % (options,
                                        self.config.get(section, options),
                                        str(type(options))))
                
    def get_main(self, key):
        try:
            return self.config.get('main',key)
        except:
            return None
    
    def set_main(self, key, value):
        self.config.set('main',key, value)
        self.save()

    def get_main_json(self, key):
        try:
            return json.loads(self.config.get('main',key))
        except Exception as e:
            return None
    
    def set_main_json(self, key, value):
        self.config.set('main',key, str(value))
        self.save()

    def load_all(self):
        try:
            self.config = ConfigParser(allow_no_value=True)
            self.config.read('config.ini')
        except Exception as e:
            print(e)
            self.config = ConfigParser()
            self.config.read('config.ini')
            self.config.add_section('main')
            self.save()

    def save(self):
        with open('config.ini', 'w') as f:
            self.config.write(f)