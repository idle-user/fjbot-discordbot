# general
general = {
    'description': 'FJBot is a Discord Bot written in Python by FancyJesse',
    'command_prefix': '!',
    'startup_cogs': [
        'cogs.admin',
        'cogs.member',
        'cogs.scheduler',
        'cogs.matches',
        'cogs.chatango',
        'cogs.voice',
        'cogs.twitter',
    ],
}

# mysql
mysql = {
    'host': '',
    'db': '',
    'user': '',
    'secret': '',
}

# discord
discord = {
    'owner': 0,
    'guild': 0,
    'access_token': '',
    'invite_link': '',
    'role': {'admin': 0, 'mod': 0, 'muted': 0},
    'channel': {
        'log': 0,
        'twitter': 0,
        'chatango': 0,
        'general': 0,
        'voice': 0,
        'ppv': 0,
        'wwe': 0,
        'aew': 0,
    },
}

# twitter
twitter = {
    'consumer_key': '',
    'consumer_secret': '',
    'access_token': '',
    'access_token_secret': '',
}

# chatango
chatango = {
    'username': '',
    'secret': '',
    'rooms': [],
}
