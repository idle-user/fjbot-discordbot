import datetime
import MySQLdb
import random
import string

from utils.fjclasses import User, UserStats, Match, Superstar
from utils.credentials import mysql


class DBHandler:
	def __init__(self):
		self.db = None
		self.c = None
		self.connect()

	def __del__(self):
		try:
			self.db.close()
			self.c.close()
		except:
			pass

	def connect(self):
		try:
			if self.db and self.c:
				try:
					self.c.execute('SELECT 1')
					self.db.commit()
					return True
				except:
					pass
			self.db = MySQLdb.connect(host=mysql['host'], db=mysql['db'], user=mysql['user'], passwd=mysql['secret'])
			self.db.autocommit(True)
			self.c = self.db.cursor(MySQLdb.cursors.DictCursor)
			return True
		except:
			print('[{}] DB Connection Failed'.format(datetime.datetime.now()))
			return False

	# general
	def user_by_id(self, user_id):
		self.connect()
		self.c.execute('SELECT * FROM user WHERE id=%s', (user_id,))
		return User(self.c.fetchone())

	def user_by_discord(self, discord_id):
		self.connect()
		self.c.execute('SELECT * FROM user WHERE discord_id=%s', (discord_id,))
		data = self.c.fetchone()
		if data:
			return User(data)
		return False

	def user_by_chatango(self, chatango_id):
		self.connect()
		self.c.execute('SELECT * FROM user WHERE chatango_id=%s', (chatango_id,))
		data = self.c.fetchone()
		if data:
			return User(data)
		return False

	def user_by_twitter(self, twitter_id):
		self.connect()
		self.c.execute('SELECT * FROM user WHERE twitter_id=%s', (twitter_id,))
		if data:
			return User(data)
		return False

	def user_login_token(self, user_id):
		token = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
		self.connect()
		self.c.execute('CALL usp_upd_user_login_token(%s, %s);', (user_id, token))
		return token

	def user_temp_password(self, user_id):
		temp = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
		self.connect()
		self.c.execute('CALL usp_upd_user_temp_secret(%s, %s);', (user_id, temp))
		return temp

	# chatango
	def chatango_register(self, username):
		self.connect()
		try:
			self.c.execute(''' 
				INSERT INTO user (username, date_created, chatango_id, chatango_last_updated)
				VALUES (%s, NOW(), %s, NOW())'''
			, (username, username))
			return self.user_by_chatango(username)
		except:
			return False

	# discord
	def discord_register(self, discord_id):
		self.connect()
		try:
			temp_username = 'Discord_User_{}'.format(discord_id)[:25]
			self.c.execute(''' 
				INSERT INTO user (username, date_created, discord_id, chatango_last_updated)
				VALUES (%s, NOW(), %s, NOW())'''
			, (temp_username, discord_id))
			return self.user_by_discord(discord_id)
		except:
			return False

	def discord_command(self, prefix):
		self.connect()
		self.c.execute('SELECT * FROM discord_command WHERE prefix=%s', (prefix,))
		return self.c.fetchone()

	def discord_command_add(self, command, response):
		self.connect()
		try:
			self.c.execute(""" 
				INSERT INTO discord_command (prefix, response)
				VALUES (%s, %s)"""
			,(command, response))
			return True
		except:
			return False

	def discord_command_update(self, command, response):
		self.connect()
		try:
			self.c.execute(""" 
				UPDATE discord_command SET response=%s
				WHERE prefix=%s"""
			,(response, command))
			return True
		except:
			return False

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

	def add_event(self, date, name):
		self.connect()
		self.c.execute('INSERT INTO event (date, name) VALUES (%s, %s)',(date,name))
		return self.c.fetchone()

	def next_event(self):
		self.connect()
		self.c.execute(""" 
			SELECT date_time, name, ppv
			FROM event
			WHERE date_time > NOW()
			ORDER BY date_time
			LIMIT 1"""
		)
		return self.c.fetchone()

	def events(self):
		self.connect()
		self.c.execute(""" 
			SELECT date_time, name
			FROM event
			WHERE date_time>=NOW() AND ppv=1
			ORDER BY date_time LIMIT 10"""
		)
		return self.c.fetchall()

	def user_stats(self, id):
		self.connect()
		self.c.execute('SELECT * FROM uv_user_stats WHERE user_id=%s', (id,))
		return UserStats(self.c.fetchone())

	def superstar_list(self):
		self.connect()
		self.c.execute('SELECT * FROM superstar')
		return [Superstar(s) for s in self.c.fetchall()]

	def superstar_by_id(self, id):
		self.connect()
		self.c.execute('SELECT * FROM superstar WHERE id=%s', (id,))
		return Superstar(self.c.fetchone())

	def superstar_by_name(self, name):
		self.connect()
		self.c.execute('SELECT * FROM superstar WHERE name LIKE %s', (name,))
		return self.c.fetchone()

	def superstar_twitter(self):
		self.connect()
		self.c.execute('SELECT * FROM superstar WHERE twitter_id<>0')
		return self.c.fetchall()

	def superstar_update(self, superstar):
		self.connect()
		try:
			return self.c.execute(''' 
				UPDATE superstar SET
					name=%s
					,brand_id=%s
					,height=%s
					,weight=%s
					,hometown=%s
					,dob=%s
					,signature_move=%s
					,page_url=%s
					,image_url=%s
					,bio=%s
					,twitter_id=%s
					,twitter_username=%s
					,last_updated=NOW()
				WHERE superstar.id=%s'''
			, (superstar.name, superstar.brand_id, superstar.height
				, superstar.weight, superstar.hometown, superstar.dob
				, superstar.signature_move, superstar.page_url
				, superstar.image_url, superstar.bio
				, superstar.twitter_id, superstar.twitter_username
				, superstar.id))
		except:
			return False

	def superstar_update_twitter_id(self, superstar_id, twitter_id):
		self.connect()
		return self.c.execute('UPDATE superstar SET twitter_id=%s WHERE id=%s', (twitter_id, superstar_id))

	def superstar_update_twitter_log(self, superstar_id, follow):
		self.connect()
		return self.c.execute('UPDATE superstar_social SET twitter_discord_log=%s WHERE superstar_id=%s', (follow, superstar_id))

	def superstar_birthdays(self):
		self.connect()
		self.c.execute('SELECT id,name,dob,twitter_name FROM superstar LEFT JOIN superstar_social ON superstar.id=superstar_id WHERE brand_id<5 AND MONTH(dob)=MONTH(NOW()) ORDER BY DAYOFYEAR(dob)')
		return self.c.fetchall()

	def superstars(self):
		self.connect()
		self.c.execute('SELECT * FROM superstar ORDER BY name')
		return [Superstar(s) for s in self.c.fetchall()]

	def superstar_search(self, name):
		self.connect()
		self.c.execute('SELECT * FROM superstar WHERE name LIKE %s ORDER BY name', (name,))
		return [Superstar(s) for s in self.c.fetchall()]

	def leaderboard_s1(self):
		self.connect()
		self.c.execute('SELECT * FROM uv_user_stats WHERE s1_wins+s1_losses>0 ORDER BY s1_total_points DESC LIMIT 10')
		return self.c.fetchall()

	def leaderboard_s2(self):
		self.connect()
		self.c.execute('SELECT * FROM uv_user_stats WHERE s2_wins+s2_losses>0 ORDER BY s2_total_points DESC LIMIT 10')
		return self.c.fetchall()

	def leaderboard_s3(self):
		self.connect()
		self.c.execute('SELECT * FROM uv_user_stats WHERE s3_wins+s3_losses>0 ORDER BY s3_total_points DESC LIMIT 10')
		return self.c.fetchall()

	def titles(self):
		self.connect()
		self.c.execute(""" 
			SELECT
				title.name AS 'title'
				,GROUP_CONCAT(superstar.name SEPARATOR ' & ') AS 'superstar'
			FROM title
			JOIN superstar ON superstar.id=title.superstar_id
			GROUP BY title.name
			ORDER BY title.id"""
		)
		return self.c.fetchall()

	def latest_match(self):
		self.connect()
		self.c.execute(""" 
			SELECT m.id
			FROM `match` m
			JOIN event ON event.id=m.event_id
			WHERE DATE(event.date_time)=CURDATE() 
			ORDER BY m.last_updated DESC
			LIMIT 1"""
		)
		return self.c.fetchone()

	def match_teams(self, match_id):
		self.connect()
		self.c.execute(""" 
			SELECT mc.team, mc.bet_multiplier ,GROUP_CONCAT(s.name) AS members
			FROM match_contestant mc
			JOIN superstar s ON s.id=mc.superstar_id
			WHERE mc.match_id=%s
			GROUP BY team
			ORDER BY team"""
		, (match_id,))
		return self.c.fetchall()

	def open_matches(self):
		self.connect()
		self.c.execute(""" 
			SELECT vm.*
			FROM uv_matches vm
			WHERE vm.completed=0 AND vm.match_type_id<>0"""
		)
		rows = self.c.fetchall()
		if rows:
			ms = []
			for row in rows:
				m = Match(row)
				m.set_teams(self.match_teams(m.id))
				ms.append(m)
			return ms
		return False

	def match(self, match_id):
		self.connect()
		self.c.execute(""" 
			SELECT vm.*
			FROM uv_matches vm
			WHERE vm.id=%s"""
		, (match_id,))
		row = self.c.fetchone()
		if row:
			m = Match(row)
			m.set_teams(self.match_teams(m.id))
			return m
		return False

	def user_bets(self, user_id):
		self.connect()
		self.c.execute(""" 
			SELECT
				ub.match_id
				,ub.user_id
				,GROUP_CONCAT(s.name) AS 'contestants'
				,ub.points
				,ubc.potential_cut_pct
				,ubc.potential_cut_points
			FROM user_bet ub
			JOIN user_bet_calculation ubc ON ubc.match_id=ub.match_id and ubc.user_id=%s
			JOIN match_contestant mc ON mc.match_id=ub.match_id AND ub.team=mc.team
			JOIN superstar s on s.id=mc.superstar_id
			JOIN `match` m ON m.id=ub.match_id
			WHERE m.team_won=0 and ub.user_id=%s
			GROUP BY m.id"""
		, (user_id, user_id))
		return self.c.fetchall()

	def user_bet_check(self, user_id, match_id):
		self.connect()
		self.c.execute('SELECT * FROM user_bet WHERE user_id=%s AND match_id=%s', (user_id, match_id))
		return self.c.fetchone()

	def user_bet(self, user_id, match_id, team, points):
		self.connect()
		try:
			self.c.execute(""" 
				INSERT INTO user_bet (user_id, match_id, team, points, dt_placed)
				VALUES (%s, %s, %s, %s, NOW())"""
			, (user_id, match_id, team, points))
			return True
		except:
			return False

	def user_rate(self, user_id, match_id, rating):
		self.connect()
		try:
			return self.c.execute('CALL usp_ins_user_match_rating(%s, %s, %s)', (user_id, match_id, rating))
		except:
			return False

	def royalrumble_check(self, user_id):
		self.connect()
		try:
			self.c.execute('SELECT * FROM royalrumble WHERE winner=0 LIMIT 1')
			rumble_id = self.c.fetchone()['id']
			self.c.execute('SELECT * FROM royalrumble_entry WHERE royalrumble_id=%s AND user_id=%s',(rumble_id, user_id))
			return self.c.fetchone()
		except:
			return False

	def royalrumble_entry(self, user_id):
		self.connect()
		try:
			user = self.user_info(user_id)
			self.c.execute('SELECT * FROM royalrumble WHERE winner=0 LIMIT 1')
			data = self.c.fetchone()
			rumble_id = data['id']
			self.c.execute('SELECT DISTINCT number FROM royalrumble_entry WHERE royalrumble_id=%s',(rumble_id,))
			max_e = data['entries']
			available_nums = list(range(1,max_e+1))
			self.c.execute('SELECT DISTINCT number FROM royalrumble_entry WHERE royalrumble_id=%s',(rumble_id,))
			curr_e = [i['number'] for i in self.c.fetchall()]
			available_nums = list(set(available_nums)-set(curr_e))
			if not available_nums:
				available_nums = list(range(1,max_e+1))
			rand_entry = random.choice(available_nums)
			self.c.execute('INSERT INTO royalrumble_entry (royalrumble_id, username, user_id, number, dt_entered) VALUES (%s, %s, %s, %s, NOW())', (rumble_id, user['username'], user['id'], rand_entry))
			return rand_entry
		except Exception as e:
			return False

