# debug
debug = 0
log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'

# general
general = {
    'description': 'FJBot is a Discord Bot written in Python by FancyJesse',
    'guild_link': 'https://discord.gg/Q9mX5hQ',
    'owner_id': 192077042722799616,
    'guild_id': 361689774723170304,
    'default_prefix': '!',
    'startup_cogs': [
        'cogs.admin',
        'cogs.member',
        'cogs.scheduler',
        'cogs.matches',
        'cogs.chatango',
        'cogs.voice',
        'cogs.twitter',
        'cogs.fjbucks',
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
    'access_token': '',
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
