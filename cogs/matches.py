import asyncio
import datetime
import logging

import discord
from discord.ext import commands

import config
from utils import checks, quickembed
from utils.fjclasses import DbHelper, DiscordUser, Match, Superstar


logger = logging.getLogger(__name__)


class Matches(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.showtime_schedule_task())

    async def showtime_schedule_task(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            event = DbHelper().future_events()[0]
            dt = datetime.datetime.now()
            event_start_timer = (event['date_time'] - dt).total_seconds()
            embed = quickembed.info(desc='Event')
            embed.add_field(
                name='{} has begun!'.format(event['name']), value='\u200b', inline=False
            )
            event_length_timer = 14400
            if event['ppv']:
                channel = self.bot.get_channel(config.discord['channel']['ppv'])
            else:
                continue
            logger.info(
                'showtime_schedule_task: channel:`{}` events:`{}` sleep until:`{}`'.format(
                    channel.name,
                    event['name'],
                    dt + datetime.timedelta(seconds=event_start_timer),
                )
            )
            await asyncio.sleep(event_start_timer)
            if channel:
                await channel.send('@everyone', embed=embed)
                activity = discord.Activity(
                    type=discord.ActivityType.watching, name=event['name']
                )
                await self.bot.change_presence(activity=activity)
                await asyncio.sleep(event_length_timer)
                await self.bot.change_presence(activity=None)
        logger.info('END showtime_schedule_task')

    @commands.command(name='currentmatch')
    async def current_match_info(self, ctx):
        user = DiscordUser(ctx.author)
        rows = user.search_match_by_current()
        if rows:
            embed = Match(rows[0].id).info_embed()
        else:
            embed = quickembed.error(desc='No match found', user=user)
        await ctx.send(embed=embed)

    @commands.command(name='lastmatch', aliases=['ratestart'])
    async def recent_match_info(self, ctx):
        user = DiscordUser(ctx.author)
        rows = user.search_match_by_recent_completed()
        if rows:
            embed = Match(rows[0].id).info_embed()
        else:
            embed = quickembed.error(desc='No match found', user=user)
        await ctx.send(embed=embed)

    @commands.command(name='events', aliases=['ppv', 'ppvs'])
    async def upcomming_events(self, ctx):
        user = DiscordUser(ctx.author)
        ppvs = user.future_events(ppv_check=1)
        embed = quickembed.info(desc='Upcoming Events (PT)', user=user)
        embed.add_field(
            name='\u200b',
            value='\n'.join(
                ['{} - **{}**'.format(e['date_time'], e['name']) for e in ppvs]
            ),
        )
        await ctx.send(embed=embed)

    @commands.command(name='info', aliases=['bio', 'superstar'])
    async def superstar_info(self, ctx, *, name):
        user = DiscordUser(ctx.author)
        superstar_list = user.search_superstar_by_name(name)
        if not superstar_list:
            embed = quickembed.error(
                desc="Unable to find Superstars matching '{}'".format(name), user=user
            )
        else:
            if len(superstar_list) > 1:
                msg = 'Select Superstar from List ...\n```'
                for i, e in enumerate(superstar_list):
                    msg = msg + '{}. {}\n'.format(i + 1, e.name)
                msg = msg + '```'
                await ctx.send(embed=quickembed.question(desc=msg, user=user))
                response = await self.bot.wait_for(
                    'message', check=checks.is_number(ctx.author), timeout=15.0
                )
                try:
                    index = int(response.content)
                    embed = Superstar(superstar_list[index - 1].id).info_embed()
                except (ValueError, IndexError):
                    embed = quickembed.error(desc='Invalid index', user=user)
            else:
                embed = Superstar(superstar_list[0].id).info_embed()
        await ctx.send(embed=embed)

    @commands.command(name='birthdays')
    async def superstar_birthdays(self, ctx):
        user = DiscordUser(ctx.author)
        bdays = user.superstar_birthday_upcoming()
        embed = quickembed.info(desc='Upcoming Birthdays', user=user)
        embed.add_field(
            name='\u200b',
            value='{}'.format(
                '\n'.join(['[{}] - {}'.format(b['dob'], b['name']) for b in bdays])
            ),
        )
        await ctx.send(embed=embed)

    @commands.command(name='leaderboard1', aliases=['top1'])
    async def leaderboard_season1(self, ctx):
        user = DiscordUser(ctx.author)
        lb = user.leaderboard(season=1)
        embed = discord.Embed(description='Season 1', color=0x0080FF)
        embed.set_author(
            name='Leaderboard',
            url='https://fancyjesse.com/projects/matches/leaderboard?season_id=1',
            icon_url=self.bot.user.avatar_url,
        )
        lb = [
            '{}. {} ({:,})'.format(i + 1, l['username'], l['total_points'])
            for i, l in enumerate(lb[:10])
        ]
        embed.add_field(
            name='\u200b', value='\n'.join(lb) if lb else 'Nothing found', inline=True
        )
        await ctx.send(embed=embed)

    @commands.command(name='leaderboard2', aliases=['top2'])
    async def leaderboard_season2(self, ctx):
        user = DiscordUser(ctx.author)
        lb = user.leaderboard(season=2)
        embed = discord.Embed(description='Season 2', color=0x0080FF)
        embed.set_author(
            name='Leaderboard',
            url='https://fancyjesse.com/projects/matches/leaderboard?season_id=2',
            icon_url=self.bot.user.avatar_url,
        )
        lb = [
            '{}. {} ({:,})'.format(i + 1, l['username'], l['total_points'])
            for i, l in enumerate(lb[:10])
        ]
        embed.add_field(
            name='\u200b', value='\n'.join(lb) if lb else 'Nothing found', inline=True
        )
        await ctx.send(embed=embed)

    @commands.command(name='leaderboard3', aliases=['top', 'leaderboard', 'top3'])
    async def leaderboard_season3(self, ctx):
        user = DiscordUser(ctx.author)
        lb = user.leaderboard(season=3)
        embed = discord.Embed(description='Season 3', color=0x0080FF)
        embed.set_author(
            name='Leaderboard',
            url='https://fancyjesse.com/projects/matches/leaderboard?season_id=3',
            icon_url=self.bot.user.avatar_url,
        )
        lb = [
            '{}. {} ({:,})'.format(i + 1, l['username'], l['total_points'])
            for i, l in enumerate(lb[:10])
        ]
        embed.add_field(
            name='\u200b', value='\n'.join(lb) if lb else 'Nothing found', inline=True
        )
        await ctx.send(embed=embed)

    # TODO
    @commands.command(name='titles', aliases=['champions', 'champs'], enabled=False)
    async def current_champions(self, ctx):
        return

    @commands.command(name='rumble', aliases=['royalrumble'])
    async def royalrumble_info(self, ctx):
        # response = user.royalrumble_info() # TODO
        user = DiscordUser(ctx.author)
        link = user.request_login_link()
        link = link.replace('projects/matches?', 'projects/matches/royalrumble?')
        msg = 'Join the rumble here! (link expires in 5 minutes)\n<{}>'.format(link)
        await ctx.author.send(embed=quickembed.general(desc=msg, user=user))
        embed = quickembed.success(user=user, desc='Rumble link DMed ;)')
        await ctx.send(embed=embed)

    @commands.command(name='joinrumble', enabled=False)
    @checks.is_registered()
    async def user_join_royalrumble(self, ctx):
        user = DiscordUser(ctx.author)
        response = user.join_royalrumble()
        if response['success']:
            embed = quickembed.success(
                desc='Entry Number: `{}`'.format(response['message']), user=user
            )
        else:
            embed = quickembed.error(desc=response['message'], user=user)
        await ctx.send(embed=embed)

    @commands.command(name='stats3', aliases=['stats', 'bal', 'points', 'profile'])
    @checks.is_registered()
    async def user_stats_season3(self, ctx):
        await ctx.send(embed=DiscordUser(ctx.author).stats_embed(season=3))

    @commands.command(name='stats2', aliases=['points2', 'bal2'])
    @checks.is_registered()
    async def user_stats_season2(self, ctx):
        await ctx.send(embed=DiscordUser(ctx.author).stats_embed(season=2))

    @commands.command(name='stats1', aliases=['points1', 'bal1'])
    @checks.is_registered()
    async def user_stats_season1(self, ctx):
        await ctx.send(embed=DiscordUser(ctx.author).stats_embed(season=1))

    @commands.command(name='bets', aliases=['currentbets', 'mybets'])
    @checks.is_registered()
    async def user_current_bets(self, ctx):
        user = DiscordUser(ctx.author)
        bets = user.current_bets()
        if bets:
            msg = "```{}```".format(
                '\n'.join(
                    [
                        'Match {}\n\t{:,} points on {}\n\t'
                        'Potential Winnings: {:,} ({}%)'.format(
                            bet['match_id'],
                            bet['points'],
                            bet['contestants'],
                            bet['potential_cut_points'],
                            bet['potential_cut_pct'] * 100,
                        )
                        for bet in bets
                    ]
                )
            )
            embed = quickembed.general(desc='Current Bets', user=user)
            embed.add_field(name='\u200b', value=msg, inline=False)
        else:
            embed = quickembed.error(desc='No current bets placed', user=user)
        await ctx.send(embed=embed)

    @commands.command(name='match')
    async def match_info(self, ctx, match_id=None):
        user = DiscordUser(ctx.author)
        try:
            match_id = int(match_id)
        except Exception:
            msg = 'Invalid `!match` command\n`!match [match_id]`'
            await ctx.send(embed=quickembed.error(desc=msg, user=user))
            return
        rows = user.search_match_by_id(match_id)
        if rows:
            await ctx.send(embed=Match(rows[0].id).info_embed())
        else:
            await ctx.send(
                embed=quickembed.error(
                    desc='Match `{}` not found'.format(match_id), user=user
                )
            )

    @commands.command(name='matches', aliases=['openmatches'])
    @commands.cooldown(1, 60.0, commands.BucketType.user)
    async def open_matches(self, ctx):
        user = DiscordUser(ctx.author)
        rows = user.search_match_by_open_bets()
        if len(rows) > 5:
            embed = quickembed.info(desc='Short View - Use `!match [id]` for full view')
            embed.set_author(name='Open Bet Matches')
            for row in rows:
                match = Match(row.id)
                embed.add_field(
                    name='[Match {}]'.format(match.id),
                    value='{}'.format(match.info_text_short()),
                    inline=True,
                )
            await ctx.send(embed=embed)
        elif len(rows) > 0:
            for row in rows:
                await ctx.send(embed=Match(row.id).info_embed())
        else:
            await ctx.send(
                embed=quickembed.error(desc='No open bet matches available', user=user)
            )

    @commands.command(name='bet', aliases=['placebet'])
    @checks.is_registered()
    async def place_match_bet(self, ctx, *args):
        user = DiscordUser(ctx.author)
        bet = None
        match_id = None
        team = None
        superstar_name = None
        try:
            bet = int(args[0].replace(',', ''))
            if len(args) == 3 and args[1].isdigit() and args[2].isdigit():
                match_id = int(args[1])
                team = int(args[2])
            elif len(args) > 1:
                superstar_name = ' '.join(args[1:])
                rows = user.search_match_by_open_bets_and_supertar_name(superstar_name)
                match_id = rows[0].id if rows else False  # use first match found
                if not match_id:
                    embed = quickembed.error(
                        desc='Unable to find an open match for contestant `{}`'.format(
                            superstar_name
                        ),
                        user=user,
                    )
                    await ctx.send(embed=embed)
                    return
            else:
                raise
        except Exception:
            msg = (
                'Invalid `!bet` command\n'
                '`!bet [bet_amount] [contestant]`\n'
                '`!bet [bet_amount] [match_id] [team]`'
            )
            await ctx.send(embed=quickembed.error(desc=msg, user=user))
            return
        match = Match(match_id)
        if not team and superstar_name:
            team = match.team_by_contestant(superstar_name)
        response = user.validate_bet(match_id, team, bet)
        if response['success']:
            embedquestion = quickembed.question(desc='[Y/N] Place this bet?', user=user)
            embedquestion.add_field(
                name='Info', value=match.info_text_short(), inline=False
            )
            embedquestion.add_field(
                name='Betting', value='{:,}'.format(bet), inline=True
            )
            embedquestion.add_field(
                name='Betting On', value=match.teams[team]['members'], inline=True
            )
            await ctx.send(embed=embedquestion)
            confirm = await self.bot.wait_for(
                'message', check=checks.confirm(ctx.author), timeout=15.0
            )
            confirm.content = confirm.content.upper()
            if confirm.content == 'Y':
                response = user.place_bet(match_id, team, bet)
                if response['success']:
                    msg = 'Placed `{:,}` point bet on `{}`'.format(
                        bet, match.teams[team]['members']
                    )
                    embed = quickembed.success(desc=msg, user=user)
                else:
                    embed = quickembed.error(desc=response['message'], user=user)
            elif confirm.content == 'N':
                embed = quickembed.error(desc='Bet cancelled', user=user)
        else:
            embed = quickembed.error(desc=response['message'], user=user)

        await ctx.send(embed=embed)

    @commands.command(name='rate', aliases=['ratematch'])
    @checks.is_registered()
    async def rate_match(self, ctx, *args):
        user = DiscordUser(ctx.author)
        try:
            if len(args) == 1:
                match_id = None
                rating = float(args[0])
            else:
                match_id = int(args[0])
                rating = float(args[1])
        except Exception:
            msg = (
                'Invalid `!rate` commant\n'
                '`!rate [rating]` (rates last match)\n'
                '`!rate [match_id] [rating]`'
            )
            embed = quickembed.error(desc=msg, user=user)
            await ctx.send(embed=embed)
            return
        if not match_id:
            rows = user.search_match_by_recent_completed()
            if not rows:
                msg = 'No current match set to rate'
                embed = quickembed.error(desc=msg, user=user)
                await ctx.send(embed=embed)
                return
            match_id = rows[0].id
        response = user.rate_match(match_id, rating)
        if response['success']:
            match = Match(match_id)
            stars = ''
            for i in range(1, 6):
                if rating >= i:
                    stars += '★'
                else:
                    stars += '☆'
            msg = 'Rated `Match {}` {} ({})\n{}'.format(
                match_id, stars, rating, match.info_text_short()
            )
            embed = quickembed.success(desc=msg, user=user)
        else:
            msg = response['message']
            embed = quickembed.error(desc=msg, user=user)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Matches(bot))
