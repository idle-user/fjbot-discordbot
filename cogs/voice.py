import asyncio

from discord.ext import commands
import discord

from utils import checks, credentials


class Voice:

	def __init__(self, bot):
		self.bot = bot
		self.channel_voice = discord.Object(id=credentials.discord['channel']['misc-voice'])
		self.voice_client = False
		self.player = False

	def __unload(self):
		if self.player:
			self.player.stop()

	@commands.command(name='vcjoin', pass_context=True, hidden=True)
	@checks.is_owner()
	async def join_channel(self, ctx):
		await self.bot.delete_message(ctx.message)
		if not self.voice_client:
			self.voice_client = await self.bot.join_voice_channel(self.channel_voice)

	@commands.command(name='vcleave', pass_context=True, hidden=True)
	@checks.is_mod()
	async def leave_channel(self, ctx):
		await self.bot.delete_message(ctx.message)
		if self.player:
			self.player.stop()
		if self.voice_client:
			await self.voice_client.disconnect()

	async def play_audio(self, voice_channel, player):
		self.player = player
		solo_time = 0
		solo_limit = 30
		self.player.start()
		self.player.volume = 0.25
		while not self.player.is_done():
			await asyncio.sleep(1)
			if len(voice_channel.voice_members)==1:
				solo_time = solo_time + 1
			else:
				solo_time = 0
			if solo_time > solo_limit:
				self.bot.log('Stopping Audio. Idle Rule.')
				self.player.stop()
				break

		if self.voice_client and len(voice_channel.voice_members)==1:
			self.bot.log('Leaving Voice Channel. Idle Rule.')
			await self.voice_client.disconnect()
			self.voice_client = False
		self.player = False

	@commands.command(name='play', pass_context=True, hidden=True)
	@checks.is_mod()
	async def play_url(self, ctx, url:str):
		await self.bot.delete_message(ctx.message)
		vc = discord.utils.get(ctx.message.server.channels, id=self.channel_voice.id)
		if not self.voice_client:
			self.voice_client = await self.bot.join_voice_channel(vc)
		if self.player:
			self.player.stop()
		self.bot.log('Downloading {} ...'.format(url))
		player = await self.voice_client.create_ytdl_player(url)
		await self.play_audio(vc, player)

	@commands.command(name='volume', pass_context=True)
	@checks.is_mod()
	async def volume(self, ctx, value:int):
		await self.bot.delete_message(ctx.message)
		if self.player and not self.player.is_done():
			self.player.volume = value / 100
			self.bot.log('Voice volume set to {:.0%}'.format(self.player.volume))

def setup(bot):
	bot.add_cog(Voice(bot))
