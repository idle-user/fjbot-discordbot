from datetime import datetime

import discord

from utils import quickembed


class User:
	def __init__(self, row):
		self.id = row['id']
		self.username = row['username']
		self.access = row['access']
		self.last_login = row['last_login']
		self.discord_id = row['discord_id']
		self.chatango_id = row['chatango_id']
		self.twitter_id = row['twitter_id']
		self.url = 'https://fancyjesse.com/projects/matches/user?user_id={}'.format(self.id)

class UserStats:
	def __init__(self, row):
		self.id = row['user_id']
		self.username = row['username']
		self.date_created = row['date_created']
		self.favorite_superstar_id = row['favorite_superstar_id']
		self.combined_total_wins = row['total_wins']
		self.combined_total_losses = row['total_losses']
		self.combined_total_points = row['total_points']
		self.s1_wins = row['s1_wins']
		self.s1_losses = row['s1_losses']
		self.s1_daily_points = row['s1_daily_points']
		self.s1_bet_points = row['s1_bet_points']
		self.s1_total_points = row['s1_total_points']
		self.s1_available_points = row['s1_available_points']
		self.s2_wins = row['s2_wins']
		self.s2_losses = row['s2_losses']
		self.s2_daily_points = row['s2_daily_points']
		self.s1_bet_points = row['s2_bet_points']
		self.s2_total_points = row['s2_total_points']
		self.s2_available_points = row['s2_available_points']
		self.s3_wins = row['s3_wins']
		self.s3_losses = row['s3_losses']
		self.s3_daily_points = row['s3_daily_points']
		self.s3_bet_points = row['s3_bet_points']
		self.s3_total_points = row['s3_total_points']
		self.s3_available_points = row['s3_available_points']
		self.url = 'https://fancyjesse.com/projects/matches/user?user_id={}'.format(self.id)

	def season_winloss_ratio(self, season):
		wins = self.season_wins(season)
		losses = self.season_losses(season)
		if wins==0 and losses==0:
			return 'N/A'
		if losses==0:
			losses = 1
		return '{:.3f}'.format(wins/losses)

	def season_wins(self, season):
		if season==1:
			return self.s1_wins
		elif season==2:
			return self.s2_wins
		elif season==3:
			return self.s3_wins
		return 0

	def season_losses(self, season):
		if season==1:
			return self.s1_losses
		elif season==2:
			return self.s2_losses
		elif season==3:
			return self.s3_losses
		return 0

	def season_total_points(self, season):
		if season==1:
			return self.s1_total_points
		elif season==2:
			return self.s2_total_points
		elif season==3:
			return self.s3_total_points
		return 0

	def season_available_points(self, season):
		if season==1:
			return self.s1_available_points
		elif season==2:
			return self.s2_available_points
		elif season==3:
			return self.s3_available_points
		return 0
	
	def season_stats_text(self, season):
		return 'Total Points: {:,} | Available Points: {:,} | Wins: {} | Losses: {} | {}'.format(
			self.season_total_points(season), 
			self.season_available_points(season), 
			self.season_wins(season), 
			self.season_losses(season),
			self.url)

	def stats_embed(self, author, season):
		embed = quickembed.general(author=author, desc='Season {}'.format(season), user=self)
		embed.add_field(name='Wins', value=self.season_wins(season), inline=True)
		embed.add_field(name='Losses', value=self.season_losses(season), inline=True)
		embed.add_field(name='Ratio', value=self.season_winloss_ratio(season), inline=True)
		embed.add_field(name='Total Points', value='{:,}'.format(self.season_total_points(season)), inline=True)
		embed.add_field(name='Available Points', value='{:,}'.format(self.season_available_points(season)), inline=True)
		return embed


class Superstar:
	def __init__(self, row):
		self.id = row['id']
		self.name = row['name']
		self.brand_id = row['brand_id']
		self.height = row['height']
		self.weight = row['weight']
		self.hometown = row['hometown']
		self.dob = row['dob']
		self.signature_move = row['signature_move']
		self.page_url = row['page_url']
		self.image_url = row['image_url']
		self.bio = row['bio']
		self.twitter_id = row['twitter_id']
		self.twitter_username = row['twitter_username']
		self.last_updated = row['last_updated']

	def calc_age(self):
		today = datetime.now().date()
		return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))

	def info_text_short(self):
		name = self.name + ' ({})'.format(self.twitter_username) if self.twitter_username else ''
		dob = 'DOB: {} ({})\n'.format(self.dob, self.calc_age()) if self.dob else ''
		height = 'Height: {}\n'.format(self.height) if self.height else ''
		weight = 'Weight: {}\n'.format(self.weight) if self.weight else ''
		hometown = 'Hometown: {}\n'.format(self.hometown) if self.hometown else ''
		signature_move = 'Signature Move(s): {}'.format(self.signature_move) if self.signature_move else ''
		return '{}\n{}\n{}{}{}{}{}'.format(name,'-'*len(name),dob,height,weight,hometown,signature_move)

	def info_text(self):
		return '{}\n\n{}'.format(self.info_text_short(), self.bio)

	def info_embed(self):
		embed = discord.Embed(color=quickembed.color['blue'])
		embed.set_author(name=self.name, url='https://fancyjesse.com/projects/matches/superstar?superstar_id={}'.format(self.id))
		if self.dob:
			embed.add_field(name='Age', value='{} ({})\n'.format(self.calc_age(), self.dob), inline=True)
		if self.height:
			embed.add_field(name='Height', value=self.height, inline=True)
		if self.weight:
			embed.add_field(name='Weight', value=self.weight, inline=True)
		if self.hometown:
			embed.add_field(name='Hometown', value=self.hometown, inline=True)
		if self.signature_move:
			embed.add_field(name='Signature Moves(s)', value='\n'.join(self.signature_move.split(';')), inline=True)
		if self.bio:
			bio = '{} ...'.format(self.bio[:1000]) if len(self.bio)>1000 else self.bio
			embed.add_field(name='\u200b', value='```{}```'.format(bio), inline=False)
		if self.image_url:
			embed.set_image(url=self.image_url)
		return embed

class Match:
	def __init__(self, row):
		self.id = row['id']
		self.completed = row['completed']
		self.pot_valid = row['pot_valid']
		self.date = row['date']
		self.event = row['event']
		self.title = row['title']
		self.contestants = row['contestants']
		self.match_type = row['match_type']
		self.match_note = row['match_note']
		self.team_won = row['team_won']
		self.winner_note = row['winner_note']
		self.contestants_won = row['contestants_won']
		self.contestants_lost = row['contestants_lost']
		self.bet_open = row['bet_open']
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
		self.teams = []
		self.star_rating = ''.join(['★' if self.user_rating_avg>=i else '☆' for i in range(1,6)])
		self.url = 'https://fancyjesse.com/projects/matches/matches?match_id={}'.format(self.id)

	def __str__(self):
		return self.id

	def set_teams(self, rows):
		for r in rows:
			self.teams.append((r['team'],r['bet_multiplier'],r['members']))

	def contains_contestant(self, name):
		return name.lower() in self.contestants.lower()

	def contestants_by_team(self, team_id):
		for t in self.teams:
			if team_id == t[0]:
				return t[2]
		return False

	def team_by_contestant(self, name):
		name = name.lower()
		for t in self.teams:
			if name in t[2].lower():
				return t[0]
		return False

	def display_short(self):
		return '{0.match_type} | {1}'.format(self,' vs '.join([t[2] for t in self.teams]))

	def display_full(self):
		if self.completed:
			rating = '{0.star_rating} ({0.user_rating_avg:.3f})'.format(self)
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
		teams = '\n\t'.join('Team {}. ({}x) {}'.format(t[0], t[1], t[2]) for t in self.teams)
		team_won = self.team_won if self.team_won else 'TBD'
		winner_note = '({0.winner_note})'.format(self) if self.winner_note else ''
		betting = 'Open' if self.bet_open else 'Closed'
		return '[Match {0.id}] {1}\nEvent: {0.event} {0.date}\nBets: {2}\nPot: {3}\n{0.match_type} {4}\n\t{5}\nTeam Won: {6} {7}'.format(self, rating, betting, pot, match_detail, teams, team_won, winner_note)

	def info_embed(self):
		if self.completed:
			header = '[Match {0.id}] {0.star_rating} ({0.user_rating_avg:.3f})'.format(self)
		else:
			header = '[Match {0.id}]'.format(self)
		bet_status = 'Open' if self.bet_open else 'Closed'
		teams = '\n'.join('{}. ({}x) {}'.format(t[0], t[1], t[2]) for t in self.teams)

		#if self.bet_open:
		#	color = quickembed.color['green']
		#else:
		#	if self.completed:
		#		color = quickembed.color['black']
		#	else:
		#		color = quickembed.color['yellow']

		color = quickembed.color['blue']
		embed = discord.Embed(color=color)
		embed.set_author(name='{}'.format(header), url='{}'.format(self.url))
		embed.description = '{0.date} | {0.event}'.format(self)
		embed.add_field(name='Bets', value='{}'.format(bet_status), inline=True)
		embed.add_field(name='Base Pot', value='{:,}'.format(self.base_pot), inline=True)
		if self.completed:
			embed.add_field(name='Multiplier', value='{}x'.format(self.bet_multiplier), inline=True)
			embed.add_field(name='Total Pot', value='{:,}'.format(self.total_pot), inline=True)
		embed.add_field(name='Match Type', value='{}'.format(self.match_type), inline=False)
		if self.title:
			embed.add_field(name='Title', value='{}'.format(self.title), inline=False)
		embed.add_field(name='Teams', value='{}'.format(teams), inline=True)
		if self.team_won:
			embed.add_field(name='Team Won', value='{}'.format(self.team_won), inline=True)

		return embed
