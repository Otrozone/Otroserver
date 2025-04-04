import json

def load_config():
    with open('otroserver.json') as config_file:
        config_data = json.load(config_file)
    return config_data

otroconfig = load_config()