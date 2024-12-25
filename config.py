import json

class config:
    def __init__(self):
        self.config = json.load(open('config.json'))
    
    def get(self):
        return self.config

    def update(self, new_config):
        self.config = new_config
        json.dump(self.config, open('config.json', 'w'))

    def get_nota_minima(self):
        return self.config['nota']['minima']

    def get_nota_maxima(self):
        return self.config['nota']['maxima']

    def get_nota_aprobar(self):
        return self.config['nota']['aprobar']

    def get_nota_objetivo(self):
        return self.config['nota']['objetivo']
