import os
import validators.volgactf

CONFIG = {
    # Don't forget to remove the old database (flags.sqlite) before each competition.
    'DEBUG': os.getenv('DEBUG') == '1',

    # The clients will run sploits on TEAMS and
    # fetch FLAG_FORMAT from sploits' stdout.
    #'TEAMS': {'Team #{}'.format(i): '10.5.1{}.3'.format(i % 256)
    #          for i in range(1, 100) if i != 1
    #          },
    'TEAMS': {'Team #{}'.format(str(i).zfill(2)): '10.5.1{}.3'.format(str(i).zfill(2)) for i in range(0, 100)},
    # 'FLAG_FORMAT': r'CTF\.Moscow\{[a-zA-Z\.0-9_-]+\}',
    'FLAG_FORMAT': r'VolgaCTF{[\w-]*\.[\w-]*\.[\w-]*}',

    # This configures how and where to submit flags.
    # The protocol must be a module in protocols/ directory.
    # RuCTF(E) and VolgaCTF checksystems are supported out-of-the-box.

    # 'SYSTEM_PROTOCOL': 'ructf_http',
    # 'SYSTEM_URL': 'http://monitor.ructfe.org/flags',
    # 'SYSTEM_TOKEN': '275_17fc104dd58d429ec11b4a5e82041cd2',

    #'SYSTEM_PROTOCOL': 'forcad_tcp',
    #'SYSTEM_HOST': '10.10.10.10',
    #'SYSTEM_PORT': '31337',
    #'TEAM_TOKEN': '4fdcd6e54faa8991',
    'SYSTEM_PROTOCOL': 'volgactf',
    'SYSTEM_VALIDATOR' : 'volgactf',
    'SYSTEM_HOST' : 'final.volgactf.ru',
    'SYSTEM_SERVER_KEY' : validators.volgactf.get_public_key('https://final.volgactf.ru'),

    # The server will submit not more than SUBMIT_FLAG_LIMIT flags
    # every SUBMIT_PERIOD seconds. Flags received more than
    # FLAG_LIFETIME seconds ago will be skipped.
    'SUBMIT_FLAG_LIMIT': 5,
    # Don't make more than INFO_FLAG_LIMIT requests to get flag info,
    # usually should be more than SUBMIT_FLAG_LIMIT
    'INFO_FLAG_LIMIT': 10,
    'SUBMIT_PERIOD': 2,
    'FLAG_LIFETIME': 5 * 60,

    # Password for the web interface. This key will be excluded from config
    # before sending it to farm clients.
    # ########## DO NOT FORGET TO CHANGE IT ##########
    'SERVER_PASSWORD': '1234',
}
