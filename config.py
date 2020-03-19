"""This module contains all account and database credentials."""

##################################
# General Bot Author Information #
#   Be sure to update this if    #
#   you create own instance.     #
##################################
base = {
    'description': 'FJBot is a Discord Bot written in Python by FancyJesse',
    'default_prefix': '!',  # The default command prefix
    'invite': {  # The invite links for the guild and the bot
        'guild': 'https://discord.gg/Q9mX5hQ',
        'bot': 'https://discordapp.com/oauth2/authorize?&client_id=364938585675137035&scope=bot&permissions=199680',
    },
    'owner_id': 192077042722799616,  # The author's Discord ID
    'guild_id': 361689774723170304,  # The originating Discord Server ID
    'startup_cogs': [  # List of cogs to load on startup
        'cogs.admin',
        'cogs.member',
        'cogs.scheduler',
        'cogs.matches',
        'cogs.chatango',
        'cogs.voice',
        'cogs.twitter',
        'cogs.fjbucks',
    ],
    'channel': {  # Dictionary of Discord Server Channels - Must update IDs
        'log': 0,  # This is a custom channel used by the bot to log messages
        'general': 0,  # The default channel when first creating a Server
        'voice': 0,  # The general voice channel
        'chatango': 0,  # This is a custom channel used by Chatango cog
        'twitter': 0,  # This is a custom channel used by Twitter cog
        'ppv': 0,  # This is a custom channel used by Matches cog
        'wwe': 0,  # This is a custom channel used by Matches cog
        'aew': 0,  # This is a custom channel used by Matches cog
    },
}

###########################
# Discord Bot Credentials #
###########################
discord = {
    'access_token': '',
}

##############################
# MySQL Database Credentials #
##############################
mysql = {
    'host': '',  # The host of the database
    'db': '',  # The database/schema name
    'user': '',  # The database user to login with (should have write permissions)
    'secret': '',  # The database user's password
}

######################################
# Chatango Bot Credentials and Rooms #
######################################
chatango = {
    'username': '',  # The Chatango account username
    'secret': '',  # The Chatango account password
    'rooms': [],  # The list of rooms to have the bot join
}

###########################
# Twitter Bot Credentials #
###########################
twitter = {
    'consumer_key': '',
    'consumer_secret': '',
    'access_token': '',
    'access_token_secret': '',
}

####################
# Logging Settings #
####################
logging = {
    'debug': 0,  # Levels - 0=Info, 1=Debug
    'format': '%(asctime)s - %(levelname)s - %(name)s - %(message)s',  # The logging format
}
