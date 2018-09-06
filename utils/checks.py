from discord.ext import commands
from utils import credentials


def confirm(m):
	return m.content.upper() in ['Y','N']

def is_number(m):
	return m.content.isdigit()

def is_owner_check(ctx):
    return credentials.discord['owner_id'] == ctx.message.author.id

def is_mod_check(ctx):
	for role in ctx.message.author.roles:
		if role.name.replace('@','') in credentials.discord['role']['mod']:
			return True
	return False

def is_owner():
	return commands.check(is_owner_check)

def is_mod():
	return commands.check(is_mod_check)
