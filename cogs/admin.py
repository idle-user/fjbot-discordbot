from discord.ext import commands
import discord

from utils.dbhandler import DBHandler
from utils import checks, credentials


class Admin:

	def __init__(self, bot):
		self.dbhandler = DBHandler()
		self.bot = bot

	@commands.command(name='kick', pass_context=True, hidden=True)
	@checks.is_mod()
	async def kick_member(self, ctx, member:discord.Member, reason:str=None):
		await self.bot.kick(member)
		await self.bot.say('```{} has been kicked{}```'.format(member, ' for {}.'.format(reason) if reason else '.'))

	@commands.command(name='ban', hidden=True)
	@checks.is_mod()
	async def ban_member(self, member:discord.Member, reason:str=None):
		await self.bot.ban(member)
		await self.bot.say('```{} has been banned{}```'.format(member, ' for {}.'.format(reason) if reason else '.'))

	@commands.command(name='clear', pass_context=True, hidden=True)
	@checks.is_mod()
	async def clear_log(self, ctx, count:int=1):
		msgs = []
		async for msg in self.bot.logs_from(ctx.message.channel, limit=count+1):
			msgs.append(msg)
		await self.bot.delete_messages(msgs)

	@commands.command(name='say', pass_context=True, hidden=True)
	@checks.is_owner()
	async def repeat(self, ctx, *, msg:str):
		await self.bot.delete_message(ctx.message)
		await self.bot.say(msg)

	@commands.command(name='spam', pass_context=True, hidden=True)
	@checks.is_mod()
	async def remove_spam(self, ctx):
		msgs = []
		spam = []
		async for msg in self.bot.logs_from(ctx.message.channel, limit=100):
			c = str(msg.author) + msg.content
			if c in msgs:
				spam.append(msg)
			else:
				msgs.append(c)
		if(len(spam)>1):
			spam.append(ctx.message)
			await self.bot.delete_messages(spam)
		else:
			await self.bot.delete_message(ctx.message)

	""" 
	@commands.command(name='nickname', pass_context=True, hidden=True)
	@checks.is_owner()
	async def change_nickname(self, ctx, *, nickname:str):
		await self.bot.change_nickname(self.bot, nickname)
	"""

	@commands.command(name='status', pass_context=True, hidden=True)
	@checks.is_owner()
	async def change_status(self, ctx, *, game:str=None):
		if game:
			await self.bot.change_presence(game=discord.Game(name=game))
		else:
			await self.bot.change_presence(game=None)

	@commands.command(name='addcommand', hidden=True)
	@checks.is_mod()
	async def add_discord_command(self, command:str, response:str):
		command = '!{}'.format(command.strip('!'))
		if self.dbhandler.discord_command_add(command, response):
			await self.bot.say('Command `{}` added.'.format(command))
		else:
			await self.bot.say('Unable to add command `{}`. Might already exist.'.format(command))

	@commands.command(name='updatecommand', hidden=True)
	@checks.is_owner()
	async def update_discord_command(self, command:str, response:str):
		command = '!{}'.format(command.strip('!'))
		if self.dbhandler.discord_command_update(command, response):
			await self.bot.say('Command `{}` updated.'.format(command))
		else:
			await self.bot.say('Unable to update command `{}`. Might not exist.'.format(command))

	@commands.command(name='mute', pass_context=True, hidden=True)
	@checks.is_mod()
	async def mute_member(self, ctx, member:discord.Member, reason:str=None):
		await self.bot.add_roles(member, discord.utils.get(ctx.message.server.roles, id=credentials.discord['role']['muted']))
		await self.bot.say('```{} has been muted{}```'.format(member, ' for {}.'.format(reason) if reason else '.'))

	@commands.command(name='unmute', pass_context=True, hidden=True)
	@checks.is_mod()
	async def unmute_member(self, ctx, member:discord.Member):
		await self.bot.remove_roles(member, discord.utils.get(ctx.message.server.roles, id=credentials.discord['role']['muted']))
		await self.bot.say('```{} has been unmuted.```'.format(member))

def setup(bot):
	bot.add_cog(Admin(bot))
