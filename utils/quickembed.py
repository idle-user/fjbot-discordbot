import discord


color = {
	'None':0x36393F,
	'red':0xff0000,
	'blue':0x0080ff,
	'green':0x80ff00,
	'white':0xffffff,
	'black':0x000000,
	'orange':0xff8000,
	'yellow':0xffff00,
}

def filler(embed, desc, user):
	if user:
		if user.discord.bot:
			embed.set_author(name=desc, icon_url=user.discord.avatar_url)
		elif user.is_registered():
			embed.set_author(
				name='{0.discord.display_name} ({0.username})'.format(user), 
				icon_url=user.discord.avatar_url,
				url=user.url)
		else:
			embed.set_author(name=user.discord, icon_url=user.discord.avatar_url)
		embed.description = desc
	else:
		embed.set_author(name='Notification')

	embed.description = desc
	return embed

def general(desc, user=None):
	embed = discord.Embed(color=color['blue'])
	embed = filler(embed=embed, desc=desc, user=user)
	return embed

def info(desc, user=None):
	embed = discord.Embed(color=color['white'])
	embed = filler(embed=embed, desc=desc, user=user)
	return embed

def error(desc, user=None):
	embed = discord.Embed(color=color['red'])
	embed = filler(embed=embed, desc=desc, user=user)
	return embed

def success(desc, user=None):
	embed = discord.Embed(color=color['green'])
	embed = filler(embed=embed, desc=desc, user=user)
	return embed

def question(desc, user=None):
	embed = discord.Embed(color=color['yellow'])
	embed = filler(embed=embed,desc=desc, user=user)
	return embed
