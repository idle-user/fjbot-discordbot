import json
import asyncio
import unicodedata
import requests
from bs4 import BeautifulSoup

from discord.ext import commands
import discord

from utils import checks, credentials


class Voice(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		self.channel_voice = discord.Object(id=credentials.discord['channel']['voice'])
		self.voice_client = False
		self.player = False

	def __unload(self):
		if self.player:
			self.player.stop()

	@commands.command(name='vcjoin', hidden=True)
	@checks.is_admin()
	async def join_channel(self, ctx):
		await ctx.message.delete()
		if not self.voice_client:
			self.voice_client = await self.bot.join_voice_channel(self.channel_voice)

	@commands.command(name='vcleave', hidden=True)
	@checks.is_mod()
	async def leave_channel(self, ctx):
		await ctx.message.delete()
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
		while self.player and not self.player.is_done():
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


	async def yt_search_info(self, keyword):
		yt_base = 'youtube.com/watch?v='
		if yt_base not in keyword:
			response = requests.get('https://www.youtube.com/results?search_query={}'.format(keyword))
			if response.status_code == 200:
				url = BeautifulSoup(response.text, 'html.parser').find(attrs={'class':'yt-uix-tile-link'})['href']
			else:
				return False
		else:
			url = keyword
		video_id = url.split('?v=')[1].split('&')[0]
		response = requests.get('https://www.youtube.com/oembed?url={}{}&format=json'.format(yt_base, video_id))
		if response.status_code == 200:
			yt_info = json.loads(response.text)
			yt_info['title'] = unicodedata.normalize('NFD', yt_info['title']).encode('ascii', 'ignore').decode('utf-8').strip()
			yt_info['url'] = 'https://www.youtube.com/watch?v={}'.format(video_id)
			return yt_info
		else:
			return False

	@commands.command(name='play', hidden=True)
	@checks.is_mod()
	async def play(self, ctx, *, message:str):
		self.bot.log('Play Command: [{}] {}'.format(ctx.message.author, message))
		await ctx.message.delete()
		vc = discord.utils.get(ctx.message.server.channels, id=self.channel_voice.id)
		yt_info = await self.yt_search_info(message)
		if not yt_info:
			return False
		if not self.voice_client:
			self.voice_client = await self.bot.join_voice_channel(vc)
		self.bot.log('Downloading "{}" - {} ...'.format(yt_info['title'], yt_info['url']))
		player = await self.voice_client.create_ytdl_player(yt_info['url'])
		if self.player:
			self.player.stop()
		self.player = player
		await self.play_audio(vc, self.player)

	@commands.command(name='volume')
	@checks.is_mod()
	async def volume(self, ctx, value:int):
		await ctx.message.delete()
		if self.player and not self.player.is_done():
			self.player.volume = value / 100
			self.bot.log('Voice volume set to {:.0%}'.format(self.player.volume))

def setup(bot):
	bot.add_cog(Voice(bot))
