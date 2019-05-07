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

def filler(embed, author, desc, user):
	if author.bot:
		embed.set_author(name=desc, icon_url=author.avatar_url)
		return embed
	if user:
		embed.set_author(name='{} ({})'.format(author.display_name, user.username), icon_url=author.avatar_url, url=user.url)
	else:
		embed.set_author(name=author, icon_url=author.avatar_url)
	embed.description = desc
	return embed

def general(author, desc, user=None):
	embed = discord.Embed(color=color['blue'])
	embed = filler(embed=embed, author=author, desc=desc, user=user)
	return embed

def info(author, desc, user=None):
	embed = discord.Embed(color=color['white'])
	embed = filler(embed=embed, author=author, desc=desc, user=user)
	return embed

def error(author, desc, user=None):
	embed = discord.Embed(color=color['red'])
	embed = filler(embed=embed, author=author, desc=desc, user=user)
	return embed

def success(author, desc, user=None):
	embed = discord.Embed(color=color['green'])
	embed = filler(embed=embed, author=author, desc=desc, user=user)
	return embed

def question(author, desc, user=None):
	embed = discord.Embed(color=color['yellow'])
	embed = filler(embed=embed, author=author, desc=desc, user=user)
	return embed
