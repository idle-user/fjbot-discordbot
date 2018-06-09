#!/usr/bin/env python3
from datetime import datetime
import MySQLdb
import random
import string

from .credentials import mysql


class DBHandler:
	def __init__(self):
		self.db = None
		self.c = None
		self.connect()

	def __del__(self):
		self.db.close()
		self.c.close()

	def connect(self):
		try:
			if self.db and self.c:
				try:
					self.c.execute('SELECT 1')
					return True
				except:
					print('failed')
					pass
			self.db = MySQLdb.connect(host=mysql['host'], db=mysql['db'], user=mysql['user'], passwd=mysql['secret'])
			self.db.autocommit(True)
			self.c = self.db.cursor(MySQLdb.cursors.DictCursor)
			print('[{}] New DB Connection Started'.format(datetime.now()))
			return True
		except:
			print('[{}] DB Connection Failed'.format(datetime.now()))
			return False

	# general
	def user_info(self, user_id):
		self.connect()
		self.c.execute('SELECT id, username, date_created FROM user WHERE id=%s', (user_id,))
		return self.c.fetchone()

	def user_temp_password(self, user_id):
		temp = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
		self.connect()
		self.c.execute('CALL user_set_temp_secret(%s, %s);', (user_id, temp))
		return temp
	
	# chatango
	def chatango_username_info(self, username):
		self.connect()
		self.c.execute('SELECT * FROM user_chatango WHERE chatango_id=%s', (username,))
		return self.c.fetchone()
	
	def chatango_register(self, username):
		self.connect()
		self.c.execute('CALL user_chatango_register(%s, @oid)', (username,))
		self.c.execute('SELECT @oid')
		return self.c.fetchone()

	
	# discord
	# always called first - handles reconnect if connection has gone away
	def discord_command(self, prefix):
		self.connect()
		self.c.execute('SELECT * FROM discord_command WHERE prefix=%s', (prefix,))
		return self.c.fetchone()
	
	
	def discord_command_cnt(self, id):
		self.connect()
		self.c.execute('UPDATE discord_command SET cnt=cnt+1 WHERE id=%s', (id,))
	
	def misc_commands(self):
		self.connect()
		self.c.execute(""" 
			SELECT REPLACE(prefix,'!','') AS prefix
			FROM discord_command
			WHERE id NOT IN (9,1)
			ORDER BY prefix"""
		)
		return [mc['prefix'] for mc in self.c.fetchall()]
	
	def next_event(self):
		self.connect()
		self.c.execute(""" 
			SELECT 
				wwe_event.date, wwe_event.start_time, wwe_event.name, wwe_event.ppv,
				TIMESTAMP(wwe_event.date, wwe_event.start_time) as dt
			FROM wwe_event
			WHERE TIMESTAMP(date, start_time) > NOW()
			ORDER BY TIMESTAMP(wwe_event.date, wwe_event.start_time)
			LIMIT 1"""
		)	
		return self.c.fetchone()
	
	def ppvs(self):
		self.connect()
		self.c.execute(""" 
			SELECT wwe_event.date, wwe_event.name
			FROM wwe_event
			WHERE date>=CURDATE() AND ppv=1
			ORDER BY date LIMIT 10"""
		)	
		return self.c.fetchall()
	
	def user_discord(self, discord_id):
		self.connect()
		self.c.execute(""" 
			SELECT user.id, user.username, user.access, user_discord.discord_id FROM user_discord
			JOIN user ON user.id=user_discord.user_id
			WHERE discord_id=%s"""
		,(discord_id,))
		return self.c.fetchone()
	
	def user_chatango(self, chatango_id):
		self.connect()
		self.c.execute(""" 
			SELECT user.id, user.username, user_chatango.chatango_id FROM user_chatango
			JOIN user ON user.id=user_chatango.user_id
			WHERE chatango_id=%s"""
		,(chatango_id,))
		return self.c.fetchone()
	
	def user_stats(self, user_id):
		self.connect()
		self.c.execute('SELECT * FROM view_wwe_s2_user_stats WHERE id=%s', (user_id,))
		return self.c.fetchone()

	def user_stats_s1(self, user_id):
		self.connect()
		self.c.execute('SELECT wwe_user_stats.*,user.username FROM wwe_user_stats JOIN user ON user.id=wwe_user_stats.user_id WHERE user_id=%s', (user_id,))
		return self.c.fetchone()
	
	def superstar_bio(self, superstar):
		self.connect()
		self.c.execute('SELECT * FROM wwe_superstar WHERE name LIKE %s', (superstar,))
		return self.c.fetchone()
	
	def superstar_twitter(self):
		self.connect()
		self.c.execute('SELECT * FROM wwe_superstar WHERE official_twitter LIKE %s', ('@%',))
		return self.c.fetchall()
	
	def superstar_update_twitter_id(self, superstar_id, twitter_id):
		self.connect()
		if twitter_id:
			return self.c.execute('UPDATE wwe_superstar SET official_twitter_id=%s WHERE id=%s', (twitter_id, superstar_id))
		else:
			return self.c.execute('UPDATE wwe_superstar SET official_twitter=%s, official_twitter_id=%s WHERE id=%s', ('', '', superstar_id))
			
	def superstar_birthdays(self):
		self.connect()
		self.c.execute('SELECT name,dob,official_twitter FROM wwe_superstar WHERE brand_id!=5 AND MONTH(dob)=MONTH(NOW()) ORDER BY DAYOFYEAR(dob)')
		return self.c.fetchall()
	
	def superstars(self):
		self.connect()
		self.c.execute('SELECT * FROM wwe_superstar ORDER BY name')
		return self.c.fetchall()
	
	def leaderboard(self):
		self.connect()
		self.c.execute('SELECT * FROM view_wwe_s2_user_stats WHERE wins+losses>0 ORDER BY total_points DESC LIMIT 10')
		return self.c.fetchall()

	def leaderboard_s1(self):
		self.connect()
		self.c.execute("""
			SELECT 
				user.username 
				,wwe_user_stats.s1_wins AS wins
				,wwe_user_stats.s1_losses AS losses				
				,wwe_user_stats.s1_points AS points
			FROM wwe_user_stats 
			JOIN user on user.id=wwe_user_stats.user_id
			WHERE s1_wins+s1_losses>0
			ORDER BY points DESC
			LIMIT 10"""
		)
		return self.c.fetchall()
	
	def titles(self):
		self.connect()
		self.c.execute(""" 
			SELECT 
				wwe_title.name AS 'title'
				,GROUP_CONCAT(wwe_superstar.name SEPARATOR ' & ') AS 'superstar'
			FROM wwe_title
			JOIN wwe_superstar ON wwe_superstar.id=wwe_title.superstar_id
			GROUP BY wwe_title.name
			ORDER BY wwe_title.id"""
		)
		return self.c.fetchall()
	
	def open_matches(self):
		self.connect()
		self.c.execute(""" 
			SELECT
				view_wwe_s2_matches.*
				,view_wwe_s2_matches_bets.*				
				,wwe_match_type.name AS 'match_type'
				,wwe_title.name AS 'title'
				,wwe_match_contestant.team
				,wwe_match_contestant.bet_multiplier AS 'team_bet_multiplier' 
				,GROUP_CONCAT(wwe_superstar.name) AS 'contestants'
			FROM view_wwe_s2_matches
			JOIN view_wwe_s2_matches_bets ON view_wwe_s2_matches_bets.id=view_wwe_s2_matches.id
			JOIN wwe_match_type ON wwe_match_type.id=view_wwe_s2_matches.match_type_id
			JOIN wwe_match_contestant ON wwe_match_contestant.match_id=view_wwe_s2_matches.id
			JOIN wwe_superstar ON wwe_superstar.id=wwe_match_contestant.superstar_id
			LEFT JOIN wwe_title ON wwe_title.id=view_wwe_s2_matches.title_id
			WHERE view_wwe_s2_matches.team_won=0 AND view_wwe_s2_matches.match_type_id>0
			GROUP BY view_wwe_s2_matches.id, wwe_match_contestant.team
			ORDER BY view_wwe_s2_matches.date DESC, view_wwe_s2_matches_bets.bet_multiplier DESC"""
		)
		matches = self.c.fetchall()
		if matches:
			match_set = {}
			for m in matches:
				if not m['id'] in match_set:
					match_set[m['id']] = {
						'id':m['id'],
						'date':m['date'],
						'event':m['event'],
						'title':m['title'],
						'bet_open':m['bet_open'],
						'match_type':m['match_type'],
						'match_note':m['match_note'],
						'bet_multiplier':m['bet_multiplier'],
						'base_pot':m['base_pot'],
						'total_pot':m['total_pot'],
						'team':[],
						}
				match_set[m['id']]['team'].append((m['team'],m['team_bet_multiplier'],m['contestants']))
			return match_set
		return False
	
	def match(self, match_id):
		self.connect()
		self.c.execute(""" 
			SELECT
				view_wwe_all_matches.*
				,view_wwe_all_matches_bets.*
				,wwe_match_type.name AS 'match_type'
				,wwe_title.name AS 'title'
				,wwe_match_contestant.team
				,wwe_match_contestant.bet_multiplier AS 'team_bet_multiplier'
				,GROUP_CONCAT(wwe_superstar.name) AS 'contestants'
			FROM view_wwe_all_matches
			JOIN view_wwe_all_matches_bets ON view_wwe_all_matches_bets.id=view_wwe_all_matches.id
			JOIN wwe_match_type ON wwe_match_type.id=view_wwe_all_matches.match_type_id
			JOIN wwe_match_contestant ON wwe_match_contestant.match_id=view_wwe_all_matches.id
			JOIN wwe_superstar ON wwe_superstar.id=wwe_match_contestant.superstar_id
			LEFT JOIN wwe_title ON wwe_title.id=view_wwe_all_matches.title_id
			WHERE view_wwe_all_matches.id=%s
			GROUP BY view_wwe_all_matches.id, wwe_match_contestant.team"""
		, (match_id,))
		matches = self.c.fetchall()
		if matches:
			match_set = {}
			for m in matches:
				if not m['id'] in match_set:
					match_set[m['id']] = {
						'id':m['id'],
						'date':m['date'],
						'event':m['event'],
						'title':m['title'],
						'bet_open':m['bet_open'],
						'team_won':m['team_won'],
						'superstars':m['superstars'],
						'match_type':m['match_type'],
						'match_note':m['match_note'],
						'rating':m['user_rating_avg'],
						'winner_note':m['winner_note'],
						'bet_multiplier':m['bet_multiplier'],
						'base_pot':m['base_pot'],
						'total_pot':m['total_pot'],
						'team':[],
						}
				match_set[m['id']]['team'].append((m['team'],m['team_bet_multiplier'],m['contestants']))
			return match_set.get(match_id, None)
		return False
	
	def user_bets(self, user_id):
		self.connect()
		self.c.execute(""" 
			SELECT
				wwe_user_bet.match_id
				,wwe_user_bet.team
				,GROUP_CONCAT(wwe_superstar.name) AS 'contestants'
				,wwe_user_bet.points
				,wwe_user_bet.points/FUNC_WWE_MATCH_TEAM_POT(wwe_match.id, wwe_user_bet.team) AS 'pot_cut' 
			FROM wwe_user_bet
			JOIN wwe_match ON wwe_match.id=wwe_user_bet.match_id
			JOIN wwe_match_contestant ON wwe_match_contestant.match_id=wwe_match.id 
				AND wwe_match_contestant.team=wwe_user_bet.team
			JOIN wwe_superstar ON wwe_superstar.id=wwe_match_contestant.superstar_id
			WHERE wwe_match.team_won=0 AND wwe_user_bet.user_id=%s
			GROUP BY wwe_match.id, wwe_match_contestant.team
			ORDER BY wwe_match.id"""
		, (user_id,))
		return self.c.fetchall()
	
	def user_bet_check(self, user_id, match_id):
		self.connect()
		self.c.execute('SELECT * FROM wwe_user_bet WHERE user_id=%s AND match_id=%s', (user_id, match_id))
		return self.c.fetchone()
	
	def user_bet(self, user_id, match_id, team, points):
		self.connect()
		try:
			self.c.execute(""" 
				INSERT INTO wwe_user_bet (user_id, match_id, team, points, dt_placed)
				VALUES (%s, %s, %s, %s, NOW())"""
			, (user_id, match_id, team, points))
			return True
		except:
			return False
	
	def user_rate(self, user_id, match_id, rate):
		self.connect()
		try:
			self.c.execute(""" 
			INSERT INTO wwe_user_match_rating (user_id, match_id, rate, updates, dt_updated)
			VALUES (%s, %s, %s, 1, NOW())
			ON DUPLICATE KEY UPDATE rate=%s, updates=updates+1, dt_updated=NOW()"""
			, (user_id, match_id, rate, rate))
			return True
		except:
			return False

	def royalrumble_check(self, user_id):
		self.connect()
		try:
			self.c.execute('SELECT * FROM wwe_royalrumble WHERE winner=0 LIMIT 1')
			rumble_id = self.c.fetchone()['id']
			self.c.execute('SELECT * FROM wwe_royalrumble_entry WHERE royalrumble_id=%s AND user_id=%s',(rumble_id, user_id))
			return self.c.fetchone()
		except:
			return False

	def royalrumble_entry(self, user_id):
		self.connect()
		try:
			user = self.user_info(user_id)
			self.c.execute('SELECT * FROM wwe_royalrumble WHERE winner=0 LIMIT 1')
			data = self.c.fetchone()
			rumble_id = data['id']
			self.c.execute('SELECT DISTINCT number FROM wwe_royalrumble_entry WHERE royalrumble_id=%s',(rumble_id,))
			max_e = data['entries']
			available_nums = list(range(1,max_e+1))
			self.c.execute('SELECT DISTINCT number FROM wwe_royalrumble_entry WHERE royalrumble_id=%s',(rumble_id,))
			curr_e = [i['number'] for i in self.c.fetchall()]
			available_nums = list(set(available_nums)-set(curr_e))
			if not available_nums:
				available_nums = list(range(1,max_e+1))
			rand_entry = random.choice(available_nums)
			self.c.execute('INSERT INTO wwe_royalrumble_entry (royalrumble_id, username, user_id, number, dt_entered) VALUES (%s, %s, %s, %s, NOW())', (rumble_id, user['username'], user['id'], rand_entry))
			return rand_entry
		except Exception as e:
			return False
