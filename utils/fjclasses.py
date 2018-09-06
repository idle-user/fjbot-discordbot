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

	def __str__(self):
		return self.id

	def set_teams(self, rows):
		for r in rows:
			self.teams.append((r['team'],r['bet_multiplier'],r['members']))
	
	def contains_contestant(self, name):
		print(name,'-',self.contestants) 
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
