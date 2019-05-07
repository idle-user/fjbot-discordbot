from discord.ext import commands

from utils import credentials


def confirm(m):
	return m.content.upper() in ['Y','N']

def is_number(m):
	return m.content.isdigit()

def is_owner_check(ctx):
	return credentials.discord['owner_id'] == ctx.message.author.id

def is_admin_or_higher_check(ctx):
	return credentials.discord['role']['admin'] in [role.id for role in ctx.message.author.roles] or is_owner_check(ctx)

def is_mod_or_higher_check(ctx):
	return credentials.discord['role']['mod'] in [role.id for role in ctx.message.author.roles] or is_admin_or_higher_check(ctx)

def is_owner():
	return commands.check(is_owner_check)

def is_admin():
	return commands.check(is_admin_or_higher_check)

def is_mod():
	return commands.check(is_mod_or_higher_check)
