from discord.ext import commands
import discord

from utils.fjclasses import DiscordUser, UserNotRegisteredError


def is_registered():
	async def predicate(ctx):
		if not DiscordUser(ctx.author).is_registered():
			raise UserNotRegisteredError('User not registered')
		return True
	return commands.check(predicate)

def confirm(author):
	def inner_check(ctx):
		return author == ctx.author and ctx.content.upper() in ['Y','N']
	return inner_check

def is_number(author):
	def inner_check(ctx):
		return author == ctx.author and ctx.content.isdigit()
	return inner_check

def is_dm(ctx):
	return isinstance(ctx.channel, discord.DMChannel)
