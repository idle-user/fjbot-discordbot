from discord.ext import commands
import discord

from utils.fjclasses import DiscordUser
from utils import config, checks, quickembed


class Admin(commands.Cog):
	def __init__(self, bot):
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
	@commands.is_owner()
	async def delete_messages(self, ctx, limit:int=1):
		await ctx.message.delete()
		await ctx.channel.purge(limit=limit)

	@commands.command(name='say', hidden=True)
	@commands.is_owner()
	async def repeat_message(self, ctx, *, msg:str):
		await ctx.message.delete()
		await ctx.send(msg)

	@commands.command(name='spam', hidden=True)
	@commands.has_any_role(config.discord['role']['admin'], config.discord['role']['mod'])
	async def delete_spam_messages(self, ctx):
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
			embed = quickembed.info('```Deleted {} spam messages```'.format(len(spam)), DiscordUser(ctx.author))
			self.bot.log(embed=embed)

	@commands.command(name='playing', hidden=True)
	@commands.is_owner()
	async def update_presence_playing(self, ctx, *, name=None):
		activity = discord.Activity(type=discord.ActivityType.playing, name=name)
		await self.bot.change_presence(activity=activity)

	@commands.command(name='streaming', hidden=True)
	@commands.is_owner()
	async def update_presence_streaming(self, ctx, url:str=None, *, name=None):
		activity = discord.Activity(type=discord.ActivityType.streaming, name=name, url=url)
		await self.bot.change_presence(activity=activity)

	@commands.command(name='watching', hidden=True)
	@commands.is_owner()
	async def update_presence_watching(self, ctx, *, name=None):
		activity = discord.Activity(type=discord.ActivityType.watching, name=name)
		await self.bot.change_presence(activity=activity)

	@commands.command(name='listening', hidden=True)
	@commands.is_owner()
	async def update_presence_listening(self, ctx, *, name=None):
		activity = discord.Activity(type=discord.ActivityType.listening, name=name)
		await self.bot.change_presence(activity=activity)

	@commands.command(name='addcommand', hidden=True)
	@commands.has_any_role(config.discord['role']['admin'], config.discord['role']['mod'])
	async def add_discord_command(self, ctx, command:str, response:str):
		command = '!{}'.format(command.strip('!'))
		if self.dbhandler.discord_command_add(command, response):
			await ctx.send('Command `{}` added.'.format(command))
		else:
			await ctx.send('Unable to add command `{}`. Might already exist.'.format(command))

	@commands.command(name='updatecommand', hidden=True)
	@commands.is_owner()
	async def update_discord_command(self, ctx, command:str, response:str):
		command = '!{}'.format(command.strip('!'))
		if self.dbhandler.discord_command_update(command, response):
			await ctx.send('Command `{}` updated.'.format(command))
		else:
			await ctx.send('Unable to update command `{}`. Might not exist.'.format(command))

	@commands.command(name='mute', hidden=True)
	@commands.has_any_role(config.discord['role']['admin'], config.discord['role']['mod'])
	async def mute_member(self, ctx, member:discord.Member, reason:str=None):
		role_mute = self.bot.get_channel(config.discord['role']['muted'])
		await member.add_roles(role_mute)
		await ctx.send('```{} has been muted{}```'.format(member, ' for {}.'.format(reason) if reason else '.'))

	@commands.command(name='unmute', hidden=True)
	@commands.has_any_role(config.discord['role']['admin'], config.discord['role']['mod'])
	async def unmute_member(self, ctx, member:discord.Member):
		await self.bot.remove_roles(member, discord.utils.get(ctx.message.server.roles, id=config.discord['role']['muted']))
		await ctx.send('```{} has been unmuted.```'.format(member))

def setup(bot):
	bot.add_cog(Admin(bot))
