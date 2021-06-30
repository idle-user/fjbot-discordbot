"""This module contains all classes and models used throughout the bot."""
import logging
import random
import string

import MySQLdb
import discord
from discord.ext import commands

import config
from utils import quickembed

logger = logging.getLogger(__name__)


class UserNotRegisteredError(commands.CheckFailure):
    """Custom exception class. Thrown when command requires registered user."""

    pass


class GuildNotOriginError(commands.CheckFailure):
    """Custom exception class. Thrown when command requires origin guild."""

    pass


class _Database:
    """A generic database handler."""

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
        """

        :return: The database connection.
        """
        return self._connection

    @property
    def cursor(self):
        """

        :return: The database cursor.
        """
        return self._cursor

    @property
    def db(self):
        """

        :return: The database object (itself).
        """
        return self

    def close(self):
        """Closes the database connection and cursor. Fails gracefully."""
        try:
            self.connection.close()
            self.cursor.close()
        except Exception as e:
            logger.debug('Failed to close database connection: {}'.format(e))

    def execute(self, sql, params=None):
        """Executes query with or without params.

        :param sql: The SQL query.
        :param params: The parameters for the query.
        """
        self.cursor.execute(sql, params or ())

    def fetchall(self):
        """Grabs all values from query result.

        :return: All query results.
        """
        return self.cursor.fetchall()

    def fetchone(self):
        """Grabs single value from query result.

        :return: A single query result.
        """
        return self.cursor.fetchone()

    def query(self, sql, params=None):
        """Executes a query and returns all results in a single call.

        :param sql: The SQL query.
        :param params: The parameters for the query.
        :return: All query results.
        """
        self.execute(sql, params)
        return self.fetchall()


class _Base:
    """A generic class with only id and name attribute."""

    def __init__(self, id=None, name=None):
        super().__init__()
        self._id = id
        self._name = name

    @property
    def id(self):
        """

        :return: The object's unique identifier value.
        """
        return self._id

    @property
    def name(self):
        """

        :return: The name of the object.
        """
        return self._name

    def fetch_info(self):
        """Abstract function for fetching object's attribute values from database."""
        raise NotImplementedError

    def fill_info(self, row):
        """Abstract function for applying object's attribute values based on query result.

        :param row: The SQL result.
        """
        raise NotImplementedError


class _User(_Base):
    """A generic class used by different user types."""

    def __init__(self):
        super().__init__()
        self._username = None
        self.discord_id = None
        self.chatango_id = None
        self.twitter_id = None
        self.access = None
        self.last_login = None
        self.url = None

    @property
    def username(self):
        """

        :return: The user's username.
        """
        return self._name

    @property
    def mention(self):
        """Abstract function to notify the user inside the chat."""
        raise NotImplementedError

    def refresh(self):
        """Re-initializes the user's attribute values."""
        self.fetch_info()

    def register(self):
        """Abstract function to register the user."""
        raise NotImplementedError

    def fetch_info(self):
        """Abstract function to fetch the user info."""
        pass

    def fill_info(self, row):
        """Applies attributes based on query result.

        :param row: The query result.
        """
        self._id = row['id']
        self._name = row['username']
        self.discord_id = row['discord_id']
        self.chatango_id = row['chatango_id']
        self.twitter_id = row['twitter_id']
        self.access = row['access']
        self.last_login = row['last_login']
        self.url = 'https://idleuser.com/projects/matches/user' '?user_id={}'.format(
            self.id
        )

    def is_registered(self):
        """Checks if the user is registered.

        :return: `True` if id and username values exist, `False` otherwise.
        """
        return True if self.id and self.username else False

    def stats(self, season):
        """Return user's stats for the Matches season.

        :param season: The Match season to fetch stats for.
        :return: The user stats for the Matches season.
        """
        return self.db.query(
            'CALL usp_matches_sel_stats_by_id(%s, %s)', (self.id, season)
        )[0]

    def place_bet(self, match_id, team, bet):
        """Places a bet for match.

        :param match_id: The Match id to bet for.
        :param team:  The Match team id to bet for.
        :param bet: The amount betting.
        :return: Query result with success or failure message.
        """
        return self.db.query(
            'CALL usp_matches_ins_bet(%s, %s, %s, %s)', (self.id, match_id, team, bet)
        )[0]

    def rate_match(self, match_id, rating):
        """Places a rating for a match.

        :param match_id: The Match id to rate for.
        :param rating: The rating for the match.
        :return: Query result with success or failure message.
        """
        return self.db.query(
            'CALL usp_matches_ins_rating(%s, %s, %s)', (self.id, match_id, rating)
        )[0]

    def current_bets(self):
        """Return the list of currently placed bets.

        :return: Query result of currently placed bets. Error message if none.
        """
        return self.db.query('CALL usp_matches_sel_current_bets(%s)', (self.id,))

    def validate_bet(self, match_id, team, bet):
        """Checks to see if user is able to place the bet through a stored procedure.

        :param match_id: The Match id to bet for.
        :param team: The Match team id to bet for.
        :param bet: The amount betting.
        :return: Query result with success or failure message.
        """
        return self.db.query(
            'CALL usp_matches_sel_validate_bet(%s, %s, %s, %s)',
            (self.id, match_id, team, bet),
        )[0]

    def request_login_link(self):
        """Creates hyperlink to auto-login user to the website.

        This creates a randomized token that allows the user to bypass initial login screen.

        .. important::
            Do not post this link in a public chat. It must be DMed to the user requesting it only.
            Once the hyperlink can only be used once and within a short time frame.

        :return: The hyperlink to auto-login a user to the website.
        """
        login_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        self.db.query(
            'UPDATE user SET login_token=%s, login_token_exp=DATE_ADD(NOW(), INTERVAL 5 MINUTE) WHERE id=%s',
            (login_token, self.id),
        )
        link = 'https://idleuser.com?login_token={}&redirect_to=/projects/matches'.format(login_token)
        return link

    def request_reset_password_link(self):
        """Creates hyperlink to reset the user's password.

        Once called a temporary password is set for the user to bypass their original password. This is required for
        users that have no yet set up a password for their account; users that registered through the bot and not the
        website. A login link is used to automatically sign-in users.

        .. important::
            Do not post this link in a public chat. It must be DMed to the user requesting it only.
            Once the hyperlink can only be used once and within a short time frame.

        :return: The hyperlink to reset the user's password for the website.
        """
        reset_token = ''.join(
            random.choices(string.ascii_letters + string.digits, k=32)
        )
        self.db.query(
            'UPDATE user SET temp_secret=%s, temp_secret_exp=DATE_ADD(NOW(), INTERVAL 30 MINUTE) WHERE id=%s;',
            (reset_token, self.id),
        )
        link = 'https://idleuser.com/reset-password?reset_token={0}'.format(reset_token)
        return link

    def royalrumble_info(self):
        """TODO

        """
        raise NotImplementedError

    def join_royalrumble(self):
        """TODO

        """
        raise NotImplementedError


class DbHelper(_Database):
    """This class handles the most common and generic queries."""

    def __init__(self):
        super().__init__()

    def search_user_by_name(self, name):
        """Fetches User info by name.

        :param name: The User's name to query for.
        :return: A list of :class:'utils.fjclasses._Base'.
        """
        return [
            _Base(id=row['id'], name=row['username'])
            for row in self.db.query('CALL usp_user_sel_by_username(%s)', (name,))
        ]

    def search_superstar_by_name(self, name):
        """Fetches Superstar info by name.

        :param name: The Superstar's name to query for.
        :return: A list of :class:'utils.fjclasses._Base'.
        """
        return [
            _Base(id=row['id'], name=row['name'])
            for row in self.db.query('CALL usp_matches_sel_superstar_by_name(%s)', (name,))
        ]

    def search_match_by_id(self, id):
        """Fetches Match info by id.

        :param id: The Match id.
        :return: A list of :class:'utils.fjclasses._Base'.
        """
        return [
            _Base(id=row['id'])
            for row in self.db.query(
                'SELECT id FROM matches_match WHERE match_type_id<>0 AND id=%s', (id,)
            )
        ]

    def search_match_by_open_bets(self):
        """Fetches info for Matches that are available to bet on.

        :return: A list of :class:'utils.fjclasses._Base'.
        """
        return [
            _Base(id=row['id'])
            for row in self.db.query(
                'SELECT id FROM matches_match WHERE match_type_id<>0 AND bet_open=1'
            )
        ]

    def search_match_by_open_bets_and_superstar_name(self, name):
        """Fetches info for Matches that are available to bet on and contain the Superstar.

        :param name: The Superstar name.
        :return: A list of :class:'utils.fjclasses._Base'.
        """
        return [
            _Base(id=row['match_id'])
            for row in self.db.query(
                'SELECT match_id '
                'FROM matches_match_calculation '
                'JOIN matches_match ON id=match_id '
                'WHERE bet_open=1 AND match_type_id<>0 AND contestants LIKE %s',
                ('%{}%'.format(name),),
            )
        ]

    def search_match_by_current(self):
        """Fetches info for the current Match.

        :return: A list of :class:'utils.fjclasses._Base'.
        """
        return [
            _Base(id=row['id']) for row in self.db.query('CALL usp_matches_sel_current_match()')
        ]

    def search_match_by_recent_completed(self):
        """Fetches info for the most recently completed Match.

        :return: A list of :class:'utils.fjclasses._Base'.
        """
        return [
            _Base(id=row['id'])
            for row in self.db.query('CALL usp_matches_sel_match_recent_completed()')
        ]

    def leaderboard(self, season):
        """Fetches the leaderboard for the season.

        :param season: The season id.
        :return: Query result of User stats ordered by total points for the season.
        """
        return self.db.query('CALL usp_matches_sel_leaderboard(%s)', (season,))

    def guild_info(self, guild_id):
        """Fetches Discord guild information by id.

        :param guild_id: The guild id.
        :return: The command prefix for the guild, `False` otherwise.
        """
        rows = self.db.query('SELECT prefix FROM guild_info WHERE id=%s', (guild_id,))
        if rows:
            return rows[0]
        return False

    def update_guild_info(self, guild, prefix):
        """Updates the Discord guild's information and command prefix.

        .. note::
            If an entry for the guild does not exist, a new entry for the guild is inserted.

        :param guild: The guild object.
        :param prefix: The guild's command prefix to update to.
        :return: TODO
        """
        return self.db.query(
            'CALL usp_guild_ins_info(%s, %s, %s, %s)',
            (guild.id, guild.name, guild.owner_id, prefix),
        )

    def chatroom_command(self, command):
        """Fetches response to a quick chatroom command.

        :param command: The command to fetch the response for.
        :return: The query result if found, `False` otherwise.
        """
        rows = self.db.query('CALL usp_chatroom_sel_command(%s)', (command,))
        if rows:
            return rows[0]
        return False

    def chatroom_command_list(self):
        """Fetches the complete list of available chatroom commands.

        :return: The query result of chatroom commands ordered by alpha.
        """
        return self.db.query('SELECT * FROM chatroom_command ORDER BY command')

    def add_chatroom_command(self, command, response):
        """TODO

        :param command: The chatroom command to insert.
        :param response: The response for the chatroom command.
        """
        pass

    def update_chatroom_command(self, command, response):
        """TODO

        :param command: The chatroom command to update.
        :param response: The updated response for the chatroom command.
        """
        pass

    def future_events(self, ppv_check=0):
        """Fetches list of upcoming PPV events.

        :param ppv_check: The PPV flag check. Default is 0.
        :return: The query result of upcoming events.
        """
        return self.db.query('CALL usp_matches_sel_future_event(%s)', (ppv_check,))

    def superstar_birthday_upcoming(self):
        """Fetches Superstar info who's birthday is coming up.

        :return: The query result of Superstars.
        """
        return self.db.query('CALL usp_matches_sel_superstar_birthday_upcoming()')

    def chatroom_scheduler_list(self):
        """Fetches list of weekly alert scheduler.

        :return: The query result for the weekly schedule.
        """
        return self.db.query('SELECT * FROM chatroom_scheduler ORDER BY id')


class DiscordUser(_User, DbHelper):
    """This class is used to refer to individual Discord authors."""

    def __init__(self, author):
        super().__init__()
        self._author = author
        self.fetch_info()

    @property
    def name(self):
        """

        :return: The author's name value.
        """
        return self._author.name

    @property
    def mention(self):
        """

        :return: The author's mention value.
        """
        return self._author.mention

    @property
    def discord(self):
        """

        :return: The author object. (itself)
        """
        return self._author

    def fetch_info(self):
        """Fetches attribute values from database using current Discord author unique identifier (id).

        .. note::
            If no results are found with id, no attributes are set.
        """
        rows = self.db.query(
            'SELECT * FROM user WHERE discord_id=%s', (self.discord.id,)
        )
        if rows:
            self.fill_info(rows[0])

    def register(self):
        """Inserts the author as a User in the database using Discord profile.

        :return: Query result with success or failure message.
        """
        return self.db.query(
            'CALL usp_user_ins_from_discord(%s, %s)', (self.discord, self.discord.id)
        )[0]

    def stats_embed(self, season):
        """Creates rich content of the User's stats for the season.

        :param season: The season id.
        :return: Rich content.
        """
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

    def royalrumble_info(self):
        """TODO

        """
        pass

    def join_royalrumble(self):
        """TODO

        """
        pass

    def fjbucks_wallet_embed(self):
        """Creates rich content of the User's FJBucks wallet.

        :return: Rich content.
        """
        row = self.fjbucks_wallet()
        embed = quickembed.general(desc='FJBucks Wallet', user=self)
        embed.add_field(
            name='Balance', value='{:,}'.format(row['balance']), inline=True
        )
        embed.add_field(
            name='Transactions',
            value='{:,}'.format(row['transaction_cnt']),
            inline=False,
        )
        embed.add_field(
            name='Last Transaction (PST)',
            value=row['last_transaction_on'],
            inline=False,
        )
        return embed


class ChatangoUser(_User, DbHelper):
    """This class is used to refer to individual Chatango authors."""

    def __init__(self, author):
        super().__init__()
        self._author = author
        self.fetch_info()

    @property
    def name(self):
        """

        :return: The author's name.
        """
        return self._author.name

    @property
    def mention(self):
        """

        :return: The author's mention.
        """
        return '@{}'.format(self._author.name)

    @property
    def chatango(self):
        """

        :return: The author. (itself)
        """
        return self._author

    def fetch_info(self):
        """Fetches attribute values from database using current Chatango author unique identifier (name).

        .. note::
            If no results are found with id, no attributes are set.
        """
        rows = self.db.query(
            'SELECT * FROM user WHERE chatango_id=%s', (self._author.name,)
        )
        if rows:
            self.fill_info(rows[0])

    def register(self):
        """Inserts the author as a User in the database using Discord profile.

        :return: Query result with success or failure message.
        """
        return self.db.query('CALL usp_user_ins_from_chatango(%s)', (self.name,))[0]

    def stats_text(self, season):
        """Formats the user's stats for the season as plain text.

        :param season: The season id.
        :return: Formatted text message.
        """
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

    def royalrumble_info(self):
        """TODO

        """
        pass

    def join_royalrumble(self):
        """TODO

        """
        pass


class Superstar(_Base, DbHelper):
    """This class is used to refer to individual Superstars."""

    def __init__(self, id=None):
        super().__init__(id=id)
        self.brand_id = None
        self.height = None
        self.weight = None
        self.hometown = None
        self.dob = None
        self.age = None
        self.signature_move = None
        self.page_url = None
        self.image_url = None
        self.bio = None
        self.twitter_id = None
        self.twitter_username = None
        self.last_updated = None
        self.fetch_info()

    def fetch_info(self):
        """Fetches attribute values from database using current Chatango author unique identifier (id).

         .. note::
            If no results are found with id, no attributes are set.
         """
        rows = self.query('CALL usp_matches_sel_superstar_by_id(%s)', (self.id,))
        if rows:
            self.fill_info(rows[0])

    def fill_info(self, row):
        """Applies attributes based on query result.

        :param row: The query result.
        """
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
        """Creates rich content of the Superstar's info.

        :return: Rich content.
        """
        embed = discord.Embed(color=quickembed.color['blue'])
        embed.set_author(
            name=self.name,
            url='https://idleuser.com/projects/matches/superstar?superstar_id={}'.format(
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
    """The class is used to refer to individual Matches."""

    def __init__(self, id=None):
        super().__init__(id=id)
        self.completed = None
        self.pot_valid = None
        self.bet_open = None
        self.event = None
        self.date = None
        self.title = None
        self.match_type = None
        self.match_note = None
        self.team_won = None
        self.winner_note = None
        self.contestants = None
        self.contestants_won = None
        self.contestants_lost = None
        self.bet_multiplier = None
        self.base_pot = None
        self.total_pot = None
        self.base_winner_pot = None
        self.base_loser_pot = None
        self.user_bet_cnt = None
        self.user_bet_loser_cnt = None
        self.user_bet_winner_cnt = None
        self.user_rating_avg = None
        self.user_rating_cnt = None
        self.star_rating = None
        self.url = None
        self.teams = None
        self.fetch_info()

    def set_teams(self, rows):
        """Initializes teams attribute with query result.

        :param rows: The list of contestants in the Match.
        """
        for r in rows:
            self.teams[r['team']]((r['team'], r['bet_multiplier'], r['members']))

    def contains_contestant(self, name):
        """Checks if Superstar is a Match contestant.

        :param name: The Superstar name.
        :return: `True` if the Superstar is a contestant, `False` otherwise.
        """
        return name.lower() in self.contestants.lower()

    def contestants_by_team(self, team_id):
        """Returns the list of Superstars in the Match based on the team id.

        :param team_id: The team id.
        :return: The list Superstars in the team, `False` otherwise.
        """
        for i in self.teams:
            if team_id == self.teams[i]['team']:
                return self.teams[i]['members']
        return False

    def team_by_contestant(self, name):
        """Returns the team id of Superstar in the Match based on the Superstar's name.

        :param name: The Superstar's name.
        :return: The Superstar's team, `False` otherwise.
        """
        name = name.lower()
        for i in self.teams:
            if name in self.teams[i]['members'].lower():
                return self.teams[i]['team']
        return False

    def fill_info(self, row):
        """Applies attributes based on query result.

        :param row: The query result.
        """
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
        self.url = 'https://idleuser.com/projects/matches/matches?match_id={}'.format(
            self.id
        )
        self.teams = {}

    def fetch_info(self):
        """Fetches attribute values from database using current Match unique identifier (id).

        .. note::
            If no results are found with id, no attributes are set.
        """
        rows = self.query('CALL usp_matches_sel_match_by_id(%s)', (self.id,))
        if rows:
            self.fill_info(rows[0])
            team_rows = self.query('CALL usp_matches_sel_match_teams(%s)', (self.id,))
            for team_row in team_rows:
                self.teams.update({team_row['team']: team_row})

    def info_text_short(self):
        """Formatted text of a Match's info. (short version)

        :return: Formatted text.
        """
        if self.title:
            return '{} | {} | {}'.format(
                self.match_type,
                self.title,
                ' vs '.join([self.teams[t]['members'] for t in self.teams]),
            )
        else:
            return '{} | {}'.format(
                self.match_type,
                ' vs '.join([self.teams[t]['members'] for t in self.teams]),
            )

    def info_text(self):
        """Formatted text of a Match's info. (long version)

        :return: Formatted text.
        """
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
        """Creates rich content of the Match's info.

        :return: Rich content.
        """
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
