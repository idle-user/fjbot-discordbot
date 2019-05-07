from discord.ext import commands
import discord

from utils.dbhandler import DBHandler
from utils import checks, credentials


class Admin(commands.Cog):

	def __init__(self, bot):
		self.dbhandler = DBHandler()
		self.bot = bot

# 	@commands.command(name='kick', hidden=True)
# 	@checks.is_admin()
# 	async def kick_member(self, ctx, member:discord.Member, reason:str=None):
# 		await self.bot.kick(member)
# 		await ctx.send('```{} has been kicked{}```'.format(member, ' for {}.'.format(reason) if reason else '.'))
# 
# 	@commands.command(name='ban', hidden=True)
# 	@checks.is_admin()
# 	async def ban_member(self, member:discord.Member, reason:str=None):
# 		await self.bot.ban(member)
# 		await ctx.send('```{} has been banned{}```'.format(member, ' for {}.'.format(reason) if reason else '.'))

	@commands.command(name='clear', hidden=True)
	@checks.is_mod()
	async def delete_messages(self, ctx, limit:int=1):
		await ctx.message.delete()
		await ctx.channel.purge(limit=limit)

	@commands.command(name='say', hidden=True)
	@checks.is_owner()
	async def repeat(self, ctx, *, msg:str):
		await ctx.message.delete()
		await ctx.send(msg)

	@commands.command(name='spam', hidden=True)
	@checks.is_mod()
	async def remove_spam(self, ctx):
		msgs = []
		spam = []
		async for msg in ctx.channel.history(limit=50):
			c = str(msg.author) + msg.content
			if c in msgs:
				spam.append(msg)
			else:
				msgs.append(c)

		spam.append(ctx.message)
		await ctx.channel.delete_messages(spam)
		if len(spam)>1:
			self.bot.log('Deleted {} spam messages.'.format(len(spam)))

	@commands.command(name='playing', hidden=True)
	@checks.is_owner()
	async def update_presence_game(self, ctx, *, arg:str):
		await self.bot.change_presence(activity=discord.Game(name=arg))

	@commands.command(name='addcommand', hidden=True)
	@checks.is_mod()
	async def add_discord_command(self, ctx, command:str, response:str):
		command = '!{}'.format(command.strip('!'))
		if self.dbhandler.discord_command_add(command, response):
			await ctx.send('Command `{}` added.'.format(command))
		else:
			await ctx.send('Unable to add command `{}`. Might already exist.'.format(command))

	@commands.command(name='updatecommand', hidden=True)
	@checks.is_owner()
	async def update_discord_command(self, ctx, command:str, response:str):
		command = '!{}'.format(command.strip('!'))
		if self.dbhandler.discord_command_update(command, response):
			await ctx.send('Command `{}` updated.'.format(command))
		else:
			await ctx.send('Unable to update command `{}`. Might not exist.'.format(command))

	@commands.command(name='mute', hidden=True)
	@checks.is_mod()
	async def mute_member(self, ctx, member:discord.Member, reason:str=None):
		role_mute = self.bot.get_channel(credentials.discord['role']['muted'])
		await member.add_roles(role_mute)
		await ctx.send('```{} has been muted{}```'.format(member, ' for {}.'.format(reason) if reason else '.'))

	@commands.command(name='unmute', hidden=True)
	@checks.is_mod()
	async def unmute_member(self, ctx, member:discord.Member):
		await self.bot.remove_roles(member, discord.utils.get(ctx.message.server.roles, id=credentials.discord['role']['muted']))
		await ctx.send('```{} has been unmuted.```'.format(member))

def setup(bot):
	bot.add_cog(Admin(bot))
