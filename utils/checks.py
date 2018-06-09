from discord.ext import commands

from utils import credentials


def is_owner_check(ctx):
    return credentials.discord['owner_id'] == ctx.message.author.id

def is_owner():
	return commands.check(is_owner_check)
