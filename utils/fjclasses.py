import random
import string

import MySQLdb
import discord
from discord.ext import commands

import config
from utils import quickembed


class UserNotRegisteredError(commands.CheckFailure):
    pass


class GuildNotOriginError(commands.CheckFailure):
    pass


class _Database:
    def __init__(self):
        super().__init__()
        self._connection = MySQLdb.connect(
            host=config.mysql['host'],
            db=config.mysql['db'],
            user=config.mysql['user'],
            passwd=config.mysql['secret'],
        )
        self._connection.autocommit(True)
        self._cursor = self._connection.cursor(MySQLdb.cursors.DictCursor)

    def __enter__(self):
        return self

    def __exit__(self):
        self.close()

    def __del__(self):
        self.close()

    @property
    def connection(self):
        return self._connection

    @property
    def cursor(self):
        return self._cursor

    @property
    def db(self):
        return self

    def close(self):
        try:
            self.connection.close()
            self.cursor.close()
        except Exception:
            pass

    def execute(self, sql, params=None):
        self.cursor.execute(sql, params or ())

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()

    def query(self, sql, params=None):
        self.execute(sql, params)
        return self.fetchall()


class _Base:
    def __init__(self, id=None, name=None):
        super().__init__()
        self._id = id
        self._name = name

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    def fetch_info(self):
        raise NotImplementedError

    def fill_info(self, row):
        raise NotImplementedError


class _User(_Base):
    def __init__(self):
        super().__init__()
        self._username = None

    @property
    def username(self):
        return self._name

    @property
    def mention(self):
        raise NotImplementedError

    def refresh(self):
        self.fetch_info()

    def register(self):
        return NotImplementedError

    def fetch_info(self):
        raise NotImplementedError

    def fill_info(self, row):
        self._id = row['id']
        self._name = row['username']
        self.discord_id = row['discord_id']
        self.chatango_id = row['chatango_id']
        self.twitter_id = row['twitter_id']
        self.access = row['access']
        self.last_login = row['last_login']
        self.url = 'https://fancyjesse.com/projects/matches/user' '?user_id={}'.format(
            self.id
        )

    def is_registered(self):
        return True if self.id and self.username else False

    def stats(self, season):
        return self.db.query(
            'CALL usp_sel_user_stats_by_id(%s, %s)', (self.id, season)
        )[0]

    def place_bet(self, match_id, team, bet):
        return self.db.query(
            'CALL usp_ins_user_bet(%s, %s, %s, %s)', (self.id, match_id, team, bet)
        )[0]

    def rate_match(self, match_id, rating):
        return self.db.query(
            'CALL usp_ins_user_match_rating(%s, %s, %s)', (self.id, match_id, rating)
        )[0]

    def current_bets(self):
        return self.db.query('CALL usp_sel_user_current_bets(%s)', (self.id,))

    def validate_bet(self, match_id, team, bet):
        return self.db.query(
            'CALL usp_sel_user_bet_validate(%s, %s, %s, %s)',
            (self.id, match_id, team, bet),
        )[0]

    def request_login_link(self):
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
        self.db.query(
            'CALL usp_upd_user_login_token(%s, %s, %s);',
            (self.id, self.username, token),
        )
        link = 'https://fancyjesse.com/projects/matches?uid={}&token={}'.format(
            self.id, token
        )
        return link

    def request_reset_password_link(self):
        temp_secret = ''.join(
            random.choices(string.ascii_letters + string.digits, k=10)
        )
        self.db.query(
            'CALL usp_upd_user_temp_secret(%s, %s, %s);',
            (self.id, self.username, temp_secret),
        )
        link = (
            'https://fancyjesse.com/account?temp_pw={}&user_id={}'
            '&username={}&project=matches'.format(temp_secret, self.id, self.username)
        )
        return link

    def royalrumble_info(self):
        raise NotImplementedError

    def join_royalrumble(self):
        raise NotImplementedError


class DbHelper(_Database):
    def __init__(self):
        super().__init__()

    def search_user_by_name(self, name):
        return [
            _Base(id=row['id'], name=row['username'])
            for row in self.db.query('CALL usp_sel_user_by_name(%s)', (name,))
        ]

    def search_superstar_by_name(self, name):
        return [
            _Base(id=row['id'], name=row['name'])
            for row in self.db.query('CALL usp_sel_superstar_by_name(%s)', (name,))
        ]

    def search_match_by_id(self, id):
        return [
            _Base(id=row['id'])
            for row in self.db.query(
                'SELECT id FROM `match` WHERE match_type_id<>0 AND id=%s', (id,)
            )
        ]

    def search_match_by_open_bets(self):
        return [
            _Base(id=row['id'])
            for row in self.db.query(
                'SELECT id FROM `match` WHERE match_type_id<>0 AND bet_open=1'
            )
        ]

    def search_match_by_open_bets_and_supertar_name(self, name):
        return [
            _Base(id=row['match_id'])
            for row in self.db.query(
                'SELECT match_id '
                'FROM match_calculation '
                'JOIN `match` ON id=match_id '
                'WHERE bet_open=1 AND match_type_id<>0 AND contestants LIKE %s',
                ('%{}%'.format(name),),
            )
        ]

    def search_match_by_current(self):
        return [
            _Base(id=row['id']) for row in self.db.query('CALL usp_sel_match_current()')
        ]

    def search_match_by_recent_completed(self):
        return [
            _Base(id=row['id'])
            for row in self.db.query('CALL usp_sel_match_recent_completed()')
        ]

    def leaderboard(self, season):
        return self.db.query('CALL usp_sel_user_leaderboard(%s)', (season,))

    def chatroom_command(self, command):
        rows = self.db.query('CALL usp_sel_chatroom_command(%s)', (command,))
        if rows:
            return rows[0]
        return False

    def chatroom_command_list(self):
        return self.db.query('SELECT * FROM chatroom_command ORDER BY command')

    def add_chatroom_command(self, command, response):
        pass

    def update_chatroom_command(self, command, response):
        pass

    def future_events(self, ppv_check=0):
        return self.db.query('CALL usp_sel_event_future(%s)', (ppv_check,))

    def superstar_birthday_upcoming(self):
        return self.db.query('CALL usp_sel_superstar_birthday_upcoming()')


class DiscordUser(_User, DbHelper):
    def __init__(self, author):
        super().__init__()
        self._author = author
        self.fetch_info()

    @property
    def name(self):
        return self._author.name

    @property
    def mention(self):
        return self._author.mention

    @property
    def discord(self):
        return self._author

    def fetch_info(self):
        rows = self.db.query(
            'SELECT * FROM user WHERE discord_id=%s', (self.discord.id,)
        )
        if rows:
            self.fill_info(rows[0])

    def register(self):
        return self.db.query(
            'CALL usp_ins_user_from_discord(%s, %s)', (self.discord, self.discord.id)
        )[0]

    def stats_embed(self, season):
        row = self.stats(season)
        embed = quickembed.general(desc='Season {}'.format(season), user=self)
        embed.add_field(name='Wins', value=row['wins'], inline=True)
        embed.add_field(name='Losses', value=row['losses'], inline=True)
        embed.add_field(name='Ratio', value=row['winloss_ratio'], inline=True)
        embed.add_field(
            name='Total Points', value='{:,}'.format(row['total_points']), inline=True
        )
        embed.add_field(
            name='Available Points',
            value='{:,}'.format(row['available_points']),
            inline=True,
        )
        return embed


class ChatangoUser(_User, DbHelper):
    def __init__(self, author):
        super().__init__()
        self._author = author
        self.fetch_info()

    @property
    def name(self):
        return self._author.name

    @property
    def mention(self):
        return '@{}'.format(self._author.name)

    @property
    def chatango(self):
        return self._author

    def fetch_info(self):
        rows = self.db.query(
            'SELECT * FROM user WHERE chatango_id=%s', (self._author.name,)
        )
        if rows:
            self.fill_info(rows[0])

    def register(self):
        return self.db.query('CALL usp_ins_user_from_chatango(%s)', (self.name,))[0]

    def stats_text(self, season):
        row = self.stats(season)
        return (
            'Total Points: {:,} | Available Points: {:,} | '
            'Wins: {} | Losses: {} | '
            '{}'.format(
                row['total_points'],
                row['available_points'],
                row['wins'],
                row['losses'],
                self.url,
            )
        )


class Superstar(_Base, DbHelper):
    def __init__(self, id=None):
        super().__init__(id=id)
        self.fetch_info()

    def fetch_info(self):
        rows = self.query('CALL usp_sel_superstar_by_id(%s)', (self.id,))
        if rows:
            self.fill_info(rows[0])

    def fill_info(self, row):
        self._id = row['id']
        self._name = row['name']
        self.brand_id = row['brand_id']
        self.height = row['height']
        self.weight = row['weight']
        self.hometown = row['hometown']
        self.dob = row['dob']
        self.age = row['age']
        self.signature_move = row['signature_move']
        self.page_url = row['page_url']
        self.image_url = row['image_url']
        self.bio = row['bio']
        self.twitter_id = row['twitter_id']
        self.twitter_username = row['twitter_username']
        self.last_updated = row['last_updated']

    def info_embed(self):
        embed = discord.Embed(color=quickembed.color['blue'])
        embed.set_author(
            name=self.name,
            url='https://fancyjesse.com/projects/matches/superstar?superstar_id={}'.format(
                self.id
            ),
        )
        if self.dob:
            embed.add_field(
                name='Age', value='{} ({})\n'.format(self.age, self.dob), inline=True
            )
        if self.height:
            embed.add_field(name='Height', value=self.height, inline=True)
        if self.weight:
            embed.add_field(name='Weight', value=self.weight, inline=True)
        if self.hometown:
            embed.add_field(name='Hometown', value=self.hometown, inline=True)
        if self.signature_move:
            embed.add_field(
                name='Signature Moves(s)',
                value='\n'.join(self.signature_move.split(';')),
                inline=True,
            )
        if self.bio:
            bio = '{} ...'.format(self.bio[:1000]) if len(self.bio) > 1000 else self.bio
            embed.add_field(name='\u200b', value='```{}```'.format(bio), inline=False)
        if self.image_url:
            embed.set_image(url=self.image_url)
        return embed


class Match(_Base, DbHelper):
    def __init__(self, id=None):
        super().__init__(id=id)
        self.fetch_info()

    def set_teams(self, rows):
        for r in rows:
            self.teams[r['team']]((r['team'], r['bet_multiplier'], r['members']))

    def contains_contestant(self, name):
        return name.lower() in self.contestants.lower()

    def contestants_by_team(self, team_id):
        for i in self.teams:
            if team_id == self.teams[i]['team']:
                return self.teams[i]['members']
        return False

    def team_by_contestant(self, name):
        name = name.lower()
        for i in self.teams:
            if name in self.teams[i]['members'].lower():
                return self.teams[i]['team']
        return False

    def fill_info(self, row):
        self._id = row['id']
        self.completed = row['completed']
        self.pot_valid = row['pot_valid']
        self.bet_open = row['bet_open']
        self.event = row['event']
        self.date = row['date']
        self.title = row['title']
        self.match_type = row['match_type']
        self.match_note = row['match_note']
        self.team_won = row['team_won']
        self.winner_note = row['winner_note']
        self.contestants = row['contestants']
        self.contestants_won = row['contestants_won']
        self.contestants_lost = row['contestants_lost']
        self.bet_multiplier = row['bet_multiplier']
        self.base_pot = row['base_pot']
        self.total_pot = row['total_pot']
        self.base_winner_pot = row['base_winner_pot']
        self.base_loser_pot = row['base_loser_pot']
        self.user_bet_cnt = row['user_bet_cnt']
        self.user_bet_loser_cnt = row['user_bet_loser_cnt']
        self.user_bet_winner_cnt = row['user_bet_winner_cnt']
        self.user_rating_avg = row['user_rating_avg']
        self.user_rating_cnt = row['user_rating_cnt']
        self.star_rating = ''.join(
            ['★' if self.user_rating_avg >= i else '☆' for i in range(1, 6)]
        )
        self.url = 'https://fancyjesse.com/projects/matches/matches?match_id={}'.format(
            self.id
        )
        self.teams = {}

    def fetch_info(self):
        rows = self.query('CALL usp_sel_match_by_id(%s)', (self.id,))
        if rows:
            self.fill_info(rows[0])
            team_rows = self.query('CALL usp_sel_match_teams(%s)', (self.id,))
            for team_row in team_rows:
                self.teams.update({team_row['team']: team_row})

    def info_text_short(self):
        return '{} | {}'.format(
            self.match_type, ' vs '.join([self.teams[t]['members'] for t in self.teams])
        )

    def info_text(self):
        if self.completed:
            rating = '{0.star_rating} ({0.user_rating_avg})'.format(self)
            pot = '{0.base_pot:,} ({0.bet_multiplier}x) -> {0.total_pot:,}'.format(self)
        else:
            rating = ''
            pot = '{0.base_pot:,} (?x) -> TBD'.format(self)
        if self.title and self.match_note:
            match_detail = '({0.title} - {0.match_note})'.format(self)
        elif self.title:
            match_detail = '({0.title})'.format(self)
        elif self.match_note:
            match_detail = '({0.match_note})'.format(self)
        else:
            match_detail = ''
        teams = '\n\t'.join(
            'Team {}. ({}x) {}'.format(
                self.teams[t]['team'],
                self.teams[t]['bet_multiplier'],
                self.teams[t]['members'],
            )
            for t in self.teams
        )
        team_won = self.team_won if self.team_won else 'TBD'
        winner_note = '({0.winner_note})'.format(self) if self.winner_note else ''
        betting = 'Open' if self.bet_open else 'Closed'
        return (
            '[Match {0.id}] {1}\n'
            'Event: {0.event} {0.date}\n'
            'Bets: {2}\nPot: {3}\n'
            '{0.match_type} {4}\n'
            '\t{5}\nTeam Won: {6} {7}'.format(
                self, rating, betting, pot, match_detail, teams, team_won, winner_note
            )
        )

    def info_embed(self):
        if self.completed:
            header = '[Match {0.id}] {0.star_rating} ({0.user_rating_avg:.3f})'.format(
                self
            )
        else:
            header = '[Match {0.id}]'.format(self)
        bet_status = 'Open' if self.bet_open else 'Closed'
        teams = '\n'.join(
            '{}. ({}x) {}'.format(
                self.teams[t]['team'],
                self.teams[t]['bet_multiplier'],
                self.teams[t]['members'],
            )
            for t in self.teams
        )

        color = quickembed.color['blue']
        embed = discord.Embed(color=color)
        embed.set_author(name='{}'.format(header), url='{}'.format(self.url))
        embed.description = '{0.date} | {0.event}'.format(self)
        embed.add_field(name='Bets', value='{}'.format(bet_status), inline=True)
        embed.add_field(
            name='Base Pot', value='{:,}'.format(self.base_pot), inline=True
        )
        if self.completed:
            embed.add_field(
                name='Multiplier', value='{}x'.format(self.bet_multiplier), inline=True
            )
            embed.add_field(
                name='Total Pot', value='{:,}'.format(self.total_pot), inline=True
            )
        embed.add_field(
            name='Match Type', value='{}'.format(self.match_type), inline=False
        )
        if self.title:
            embed.add_field(name='Title', value='{}'.format(self.title), inline=False)
        embed.add_field(name='Teams', value='{}'.format(teams), inline=True)
        if self.team_won:
            embed.add_field(
                name='Team Won', value='{}'.format(self.team_won), inline=True
            )

        return embed
