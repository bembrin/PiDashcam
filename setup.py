import os
from configparser import ConfigParser

def setup(**args):
    if not os.path.isdir(args['vid_dir']):
        os.system('mkdir {}'.format(args['vid_dir']))

    if not os.path.isdir(args['highlight_dir']):
        os.system('mkdir {}'.format(args['highlight_dir']))

    args['setup'] = 0 

    config['SETTINGS'] = args

    with open('config.ini', 'w') as configfile:
        config.write(configfile)

config = ConfigParser()
config.read('config.ini')
settings = config['SETTINGS']

setup(**settings)
