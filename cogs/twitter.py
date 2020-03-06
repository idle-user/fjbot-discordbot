import asyncio
import datetime
import logging

import tweepy
from discord.ext import commands

import config
from utils import checks, quickembed
from utils.fjclasses import DbHelper, DiscordUser, Superstar


logger = logging.getLogger(__name__)


class Twitter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auth = tweepy.OAuthHandler(
            config.twitter['consumer_key'], config.twitter['consumer_secret']
        )
        self.auth.set_access_token(
            config.twitter['access_token'], config.twitter['access_token_secret']
        )
        self.twitter = tweepy.API(self.auth)
        logger.info('START TwitterBot `{}`'.format(self.twitter.me().screen_name))

        # self.bot.loop.create_task(self.superstar_birthday_task())
        # self.bot.loop.create_task(self.stream_test())

    def __unload(self):
        pass

    def latest_tweets(self, twitter_id, count=1):
        return self.twitter.user_timeline(id=twitter_id, count=count, include_rts=False)

    def live_tweet(self, msg):
        status = self.twitter.update_status(msg)
        link = 'https://twitter.com/{}/status/{}'.format(
            status.user.screen_name, status.id
        )
        return link

    async def tweet_log(self, message):
        channel = self.bot.get_channel(config.discord['channel']['twitter'])
        await channel.send(message)

    class MyStreamListener(tweepy.StreamListener):
        def on_data(self, data):
            print(data)
            return True

        def on_error(self, status):
            print(status)

    async def stream_test(self):
        await self.bot.wait_until_ready()
        listener = self.MyStreamListener()
        self.myStream = tweepy.Stream(auth=self.auth, listener=listener)
        self.myStream.filter(track=['jesse'], is_async=True)
        print('end stream_test')

    async def superstar_birthday_task(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            events = []
            dt = datetime.datetime.now()
            timer = (
                ((24 - dt.hour - 1) * 60 * 60)
                + ((60 - dt.minute - 1) * 60)
                + (60 - dt.second)
            )
            for s in DbHelper().superstar_birthday_upcoming():
                if not s['twitter_name']:
                    continue
                s['dt'] = datetime.datetime(dt.year, s['dob'].month, s['dob'].day)
                if s['dt'] > dt:
                    if events and events[0]['dt'] != s['dt']:
                        break
                    events.append(s)
                    timer = (events[0]['dt'] - dt).total_seconds()
            logger.info(
                'birthday_schedule_task: sleep_until:{}, event:{}'.format(
                    dt + datetime.timedelta(seconds=timer),
                    ','.join(e['twitter_name'] for e in events),
                )
            )
            await asyncio.sleep(timer)
            if events:
                tweet_link = self.live_tweet(
                    'Happy Birthday, {}! #BDAY\n- Sent from everyone '
                    'at https://discord.gg/Q9mX5hQ #discord #fjbot'.format(
                        ', '.join(e['twitter_name'] for e in events)
                    )
                )
                channel = self.bot.get_channel(config.discord['channel']['twitter'])
                await channel.send(tweet_link)
        logger.info('END birthday_schedule_task')

    @commands.command(name='sendtweet', aliases=['tweetsend'])
    @commands.is_owner()
    async def send_tweet(self, ctx, *, message: str):
        await ctx.send('Send Tweet? [Y/N]```{}```'.format(message))
        confirm = await self.bot.wait_for('message', check=checks.confirm, timeout=10.0)
        if confirm and confirm.content.upper() == 'Y':
            tweet_link = self.live_tweet(message)
            channel = self.bot.get_channel(config.discord['channel']['twitter'])
            await channel.send(tweet_link)
        else:
            await ctx.send('`Tweet cancelled.`')

    @commands.command(name='tweets', aliases=['viewtweets'])
    @commands.cooldown(1, 30.0, commands.BucketType.user)
    @checks.is_registered()
    async def superstar_tweets(self, ctx, name, limit=1):
        user = DiscordUser(ctx.author)
        try:
            limit = 1 if limit < 1 else limit
            limit = 5 if limit > 5 else limit
        except Exception:
            embed = quickembed.error(
                desc='Invalid `!tweets` command\n`!tweets [superstar]`', user=user
            )
            ctx.say(embed=embed)
            return
        rows = user.search_superstar_by_name(name)
        if not rows:
            embed = quickembed.error(
                desc='Unable to find superstar `{}`'.format(name), user=user
            )
            await ctx.send(embed=embed)
        else:
            superstar = Superstar(rows[0].id)
            if superstar.twitter_id:
                tweets = self.latest_tweets(superstar.twitter_id, limit)
                for tweet in tweets:
                    await ctx.send('https://twitter.com/statuses/{}'.format(tweet.id))
            else:
                embed = quickembed.error(
                    desc='Unable to find Tweets for `{}`'.format(superstar.name),
                    user=user,
                )
                await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Twitter(bot))
