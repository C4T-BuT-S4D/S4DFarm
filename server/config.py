CONFIG = {
    # Don't forget to remove the old database (flags.sqlite) before each competition.

    # The clients will run sploits on TEAMS and
    # fetch FLAG_FORMAT from sploits' stdout.
    'TEAMS': {'Team #{}'.format(i): '172.29.{}.3'.format(i % 256)
              for i in range(1, 3) if i != 8},
    # 'FLAG_FORMAT': r'CTF\.Moscow\{[a-zA-Z\.0-9_-]+\}',
    'FLAG_FORMAT': r'[A-Z0-9]{31}=',

    # This configures how and where to submit flags.
    # The protocol must be a module in protocols/ directory.
    # RuCTF(E) and VolgaCTF checksystems are supported out-of-the-box.

    'SYSTEM_PROTOCOL': 'forcad_tcp',
    'SYSTEM_HOST': '10.10.10.10',
    'SYSTEM_PORT': 31337,
    'TEAM_TOKEN': 'c425c02bf4c80540',


    # 'SYSTEM_PROTOCOL': 'mctf_http',
    # 'SYSTEM_URL': 'http://10.23.0.7:8000',
    # 'SYSTEM_TOKEN': 'your_secret_token',

    # 'SYSTEM_PROTOCOL': 'ctf_moscow',
    # 'SYSTEM_HOST': '2019.ctf.moscow',
    # 'VOLGA_FORMAT': True,

    # The server will submit not more than SUBMIT_FLAG_LIMIT flags
    # every SUBMIT_PERIOD seconds. Flags received more than
    # FLAG_LIFETIME seconds ago will be skipped.
    'SUBMIT_FLAG_LIMIT': 100,
    'SUBMIT_PERIOD': 2,
    'FLAG_LIFETIME': 5 * 60,

    # Password for the web interface. This key will be excluded from config
    # before sending it to farm clients.
    # ########## DO NOT FORGET TO CHANGE IT ##########
    'SERVER_PASSWORD': 'c4tbs',
}
