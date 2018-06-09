from discord.ext import commands
import discord

from utils import checks


class Admin:

	def __init__(self, bot):
		self.bot = bot
		
	@commands.command(name='kick', pass_context=True, hidden=True)
	@checks.is_owner()
	async def kick_member(self, ctx, member:discord.Member, reason:str=None):
		await self.bot.kick(member)
		await self.bot.say('```{} has been kicked{}```'.format(member, ' for {}.'.format(reason) if reason else '.'))

	@commands.command(name='ban', hidden=True)
	@checks.is_owner()
	async def ban_member(self, member:discord.Member, reason:str=None):
		await self.bot.ban(member)
		await self.bot.say('{} has been banned{}'.format(member, ' for {}.'.format(reason) if reason else '.'))

	@commands.command(name='clear', pass_context=True, hidden=True)
	@checks.is_owner()
	async def clear_log(self, ctx, count:int=1):
		msgs = []
		async for msg in self.bot.logs_from(ctx.message.channel, limit=count+1):
			msgs.append(msg)
		await self.bot.delete_messages(msgs)

	@commands.command(name='playing', hidden=True)
	@checks.is_owner()
	async def update_presence(self, game:str):
		await self.bot.change_presence(game=discord.Game(name=game))
		await self.bot.say('```Presence Updated.```')

	@commands.command(name='spam', pass_context=True, hidden=True)
	@checks.is_owner()
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

def setup(bot):
	bot.add_cog(Admin(bot))
