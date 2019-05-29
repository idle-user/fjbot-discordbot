import asyncio
import logging

import discord
import youtube_dl
from discord.ext import commands

from utils import checks, quickembed
from utils.fjclasses import DiscordUser

logger = logging.getLogger(__name__)

youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}
ffmpeg_options = {'options': '-vn'}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @checks.is_registered()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        await channel.connect()

    @commands.command(name='playlocal')
    @commands.is_owner()
    async def play_local(self, ctx, *, query):
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
        ctx.voice_client.play(
            source, after=lambda e: logger.error('Player error: %s' % e) if e else None
        )
        await ctx.send('Now playing: {}'.format(query))
        await ctx.send(
            embed=quickembed.info(
                desc='Now playing: {}'.format(query), user=DiscordUser(ctx.author)
            )
        )

    @commands.command(name='ytdl')
    @commands.is_owner()
    async def play_yt(self, ctx, *, url):
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
            ctx.voice_client.play(
                player,
                after=lambda e: logger.error('Player error: %s' % e) if e else None,
            )
        await ctx.send(
            embed=quickembed.info(
                desc='Now playing: {}'.format(player.title),
                user=DiscordUser(ctx.author),
            )
        )

    @commands.command(name='stream', aliases=['play', 'yt', 'vplay'])
    @checks.is_registered()
    async def stream_yt(self, ctx, *, url):
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(
                player,
                after=lambda e: logger.error('Player error: %s' % e) if e else None,
            )
        await ctx.send(
            embed=quickembed.info(
                desc='Now playing: {}'.format(player.title),
                user=DiscordUser(ctx.author),
            )
        )

    @commands.command(name='volume')
    @checks.is_registered()
    async def change_volume(self, ctx, volume: int):
        user = DiscordUser(ctx.author)
        if ctx.voice_client is None:
            return await ctx.send(
                embed=quickembed.error(
                    desc='Not connected to a voice channel', user=user
                )
            )
        ctx.voice_client.source.volume = volume / 100
        await ctx.send(
            embed=quickembed.info(
                desc='Changed volume to {}%'.format(volume), user=user
            )
        )

    @commands.command(name='vstop')
    @checks.is_registered()
    async def stop_audio(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send(
                embed=quickembed.info(
                    desc=':mute: Stopped the party :mute:', user=DiscordUser(ctx.author)
                )
            )

    @commands.command(name='vpause')
    @checks.is_registered()
    async def pause_audio(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send(
                embed=quickembed.info(
                    desc=':mute: Paused the party :mute:', user=DiscordUser(ctx.author)
                )
            )

    @commands.command(name='vresume')
    @checks.is_registered()
    async def resume_audio(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send(
                embed=quickembed.info(
                    desc=':musical_note: Resumed the party :musical_note:',
                    user=DiscordUser(ctx.author),
                )
            )

    @play_local.before_invoke
    @play_yt.before_invoke
    @stream_yt.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send(
                    embed=quickembed.error(
                        desc='You must be in a voice channel to use that command',
                        user=DiscordUser(ctx.author),
                    )
                )
                raise commands.CommandError('Author not connected to a voice channel')
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


def setup(bot):
    bot.add_cog(Voice(bot))
