from definitions import support, botowner, prefix, debug, db, srv, post, dm, best, priv, customprefix, holiday

# Imports, database definitions and all that kerfuffle.

import discord
from discord.ext import commands, tasks
import asyncio
import pyfiglet
from tinydb import TinyDB, Query, where
from tinydb.operations import add, subtract, delete
import aiohttp        
import aiofiles
import os.path
import os
import json
import random
from datetime import datetime, date
import logging
import ast
from colorthief import ColorThief
from PIL import Image
from colorama import init, Fore, Back, Style

# ----------------------------------------------------------------------------------------------

async def createAutovoteEmbed(channelId, possibleConfigs, channelConfig):
	embed = discord.Embed(title="Autovote settings", description="Get Reto to react to new posts on this channel.")
	for config in possibleConfigs:
		# Search if enabled or not
		enabled = "**[❌]**"
		if (channelConfig and channelId + "-" + config["database"] in channelConfig and channelConfig[channelId + "-" + config["database"]] == True):
			enabled = "**[✔️]**"
		embed.add_field(name=config["emoji"] + " " + config["name"], value=enabled + " " + config["description"], inline=False)
	embed.set_footer(text="The reactions below will dissapear after a minute of inactivity.")
	return embed

async def getTimestamp():
	return Fore.WHITE + Style.DIM + '[{:%Y-%m-%d %H:%M:%S}]'.format(datetime.now()) + Style.RESET_ALL

async def getCurrentPrefix(ctx):
	customprefix.clear_cache()
	if not ctx.message.guild: # is on DMs
		return prefix
	else:
		pre = customprefix.search(Query().server == ctx.guild.id)
		if pre:
			return pre[0]['prefix']
		else:
			return prefix

async def formatMessage(string, message):
	# DEFINITIONS

	# Username
	u = message.author.name
	# Username Mention
	um = message.author.mention
	# Channel Name
	c = message.channel.name
	# Channel Mention
	cm = message.channel.mention

	# Best Of Name
	best.clear_cache()
	base = best.get(Query().serverid == str(message.guild.id))
	if not base:
		print("No best of found for server " + str(message.guild.id))
		await sendErrorEmbed(message.channel, 'Looks like the #best-of channel doesn\'t exist!\nHave you ran `?setup` yet? If so, try `?reattach`ing the channel.')
		return
	
	bcid = base['channelid']
	bitem = discord.utils.get(message.guild.channels, id=bcid)
	if bitem:
		b = bitem.name
		# Best Of Mention
		bm = bitem.mention
	else:
		b = "#best-of"
		# Best Of Mention
		bm = "´#best-of´"
	

	# Message
	m = message.content
	# Server
	s = message.guild.name
	# Points added/subtracted
	if message == "10" or message == "10repeat":
		p = "10"
	else:
		p = "1"
	# Total karma (local)
	uid = str(message.author.id)
	query = db.get(Query()['username'] == uid)
	k = str(query.get(str(message.guild.id)))
	# Total karma (global)
	gk = str(query.get('points'))
	# Karma name
	kn = await getLocalKarma("name", message)
	# Karma emoji
	ke = await getLocalKarma("emoji", message)
	# Default emoji
	e = "<:karma:862440157525180488>"

	# Plus emoji
	pe = str(discord.utils.get(message.guild.emojis, name="plus"))
	if pe == None:
		pe = "💖"
	# Minus emoji
	me = str(discord.utils.get(message.guild.emojis, name="minus"))
	if me == None:
		me = "💔"
	# Ten/Star emoji
	#se = str(discord.utils.get(message.guild.emojis, name="10"))
	#if se == None:
	#	se = "⭐"
	# Unimplemented - Reto can't access the 10 emoji without role Curator,
	# and it's messy to update the allowed Roles for pre-existing emojis.
	
	# PARSING
	return string.replace('{u}', u).replace('{um}', um).replace('{c}', c).replace('{cm}', cm).replace('{b}', b).replace('{bm}', bm).replace('{m}', m).replace('{s}', s).replace('{p}', p).replace('{k}', k).replace('{gk}', gk).replace('{kn}', kn).replace('{ke}', ke).replace('{e}', e).replace('{pe}', pe).replace('{me}', me).replace('\\n', '\n')

async def getFormattedMessage(message, msgtype):
	serverid = str(message.guild.id)
	bestof = best.get(Query().serverid == str(serverid))
	if not bestof:
		return False
	elif msgtype + "Message" in bestof.keys():
		parsed = await formatMessage(bestof[msgtype + "Message"], message)
		return parsed
	else:
		return False

async def getProfile(author, ctx, self):
	valor = str(author)
	searchvalor = str(author.id)

	result = db.get(Query()['username'] == searchvalor)

	if not isinstance(ctx.message.channel, discord.channel.DMChannel):
		server = str(ctx.message.guild.id)
	#
	# GET VALUE IN LLB
	#

	if not isinstance(ctx.message.channel, discord.channel.DMChannel):
		
		allUsers = db.search(Query().servers.all([server]))
		lleaderboard = {} # Prepares an empty dictionary.
		for user in allUsers: # For each entry in the database:
			if user.get(server) != None:
				print(user)
				print(user.get("username"))
				print(str(ctx.message.guild.id))
				lleaderboard[user.get("username")] = int(user.get(server))
		lleaderboard = sorted(lleaderboard.items(), key = lambda x : x[1], reverse=True) # Sort this database by amount of points.
		print(lleaderboard)
		localvalue = 1

		for key, value in lleaderboard: # For each value in the new, sorted DB:
			print("key: " + key)
			print("value: " + searchvalor)
			if key == searchvalor:
				break
			else:
				localvalue += 1
	
	#
	# POINTS SENT
	#

	sentpoints = post.search(Query().voters.any([author.id]))

	#
	# STARS RECEIVED
	#

	starlist = post.search(Query().username == str(author.id))
	starsrec = 0
	for star in starlist:
		if 'stars' in star:
			starsrec += star['stars']

	#
	# SUPPORT BADGES (WIP)
	#

	#checkM = self.client.get_emoji(741669341409312889)
	#print(str(checkM))

	#
	# SEND THE EMBED
	#

	# Color of embed is the dominant of the user's avatar
	await author.avatar_url.save("images/avatar.png")

	# Make image smaller (saves time)
	image = Image.open('images/avatar.png')
	new_image = image.resize((64, 64))
	new_image.save('images/smallavatar.png')

	colorThief = ColorThief("images/smallavatar.png")
	dominantColor = colorThief.get_color(quality=8)

	embed=discord.Embed(title=author.name, color=discord.Colour.from_rgb(dominantColor[0], dominantColor[1], dominantColor[2]))
	embed.set_thumbnail(url=author.avatar_url)
	rank = ""
	presents = ""


	if not isinstance(ctx.message.channel, discord.channel.DMChannel) and result:
		karmaName = await getLocalKarma("name", ctx.message)
		karmaEmoji = await getLocalKarma("emoji", ctx.message)

		rank = "> ✨ Rank      `" + str(localvalue) + "`\n"
		if result.get(server):
			embed.add_field(name=karmaName, value=karmaEmoji + " " + str(result.get(server)), inline=True)
		else:
			embed.add_field(name=karmaName, value=karmaEmoji + " 0", inline=True)
	if result:
		embed.add_field(name="Global Karma", value="<:karma:862440157525180488> " + str(result.get('points')), inline=True)
	else:
		embed.add_field(name="Global Karma", value="<:karma:862440157525180488> 0", inline=True)
	if holiday:
		if 'openedGifts' in result:
			presents = "> 🎁 Gifts claimed ⠀`" + str(result["openedGifts"]) + "`\n"
		else:
			presents = "> 🎁 Gifts claimed ⠀`0`\n"
	if result:
		if not isinstance(ctx.message.channel, discord.channel.DMChannel):
			plusEmoji = discord.utils.get(ctx.guild.emojis, name="plus")
			if plusEmoji == None:
				plusEmoji = "❤️"
			#starEmoji = discord.utils.get(ctx.guild.emojis, name="10")
		else:
			plusEmoji = "❤️"
    		
		
		badges = await getBadges(self, ctx, result, author, True)
		globalRank = await getGlobalRank(ctx, author.id)
		embed.add_field(name="Badges", value=badges + "** **", inline=False)
		embed.add_field(name="Stats", value=rank + "> 🌐 Global Rank   `" + str(globalRank) + "`\n> " + str(plusEmoji) + " Times reacted  `" + str(len(sentpoints)) + "`\n" + presents, inline=False)
		# + "`\n" + str(starEmoji) + " Stars received `" + str(starsrec) + "`"
	
	# Holiday Inventory
	if holiday:
		holidayInventory = []

		with open('json/gifts.json') as f:
			gifts = json.load(f)

			for gift in gifts:
				if gift["code"] in result and gift["storable"] and result[gift["code"]] > 0:
					holidayInventory.append("\n> `(x" + str(result[gift["code"]]) + ")`  **" + gift["emoji"] + " " + gift["name"] + "**")
			
			if len(holidayInventory) == 0:
				holidayInventory = "\n> **You don't have any holiday items yet!**\n> Go to the **Reto Holiday `?tree`** to get started."

		embed.add_field(name="🎄 Inventory", value=''.join(holidayInventory), inline=False)
	await ctx.send(embed=embed)

async def getBadges(self, ctx, dbInfo, user, customEmoji):

	leadervalue = await getGlobalRank(ctx, user.id)
	# Global Leaderboard

	if dbInfo:
		if leadervalue == 1:
			leaderemblem = "🥇 "
		elif leadervalue == 2:
			leaderemblem = "🥈 "
		elif leadervalue == 3:
			leaderemblem = "🥉 "
		elif leadervalue <= 10:
			leaderemblem = "🏅 "
		else:
			leaderemblem = ""
	else:
		leaderemblem = ""
	
	# Tree badge

	treeemblem = ""
	if "tree" in dbInfo and customEmoji:
		if dbInfo["tree"] >= 20:
			treeemblem = "<:diamondtree:1056242357898588281> "
		elif dbInfo["tree"] >= 15:
			treeemblem = "<:goldtree:1056242352441806888> "
		elif dbInfo["tree"] >= 10:
			treeemblem = "<:silvertree:1056242350927663114> "
		elif dbInfo["tree"] >= 5:
			treeemblem = "<:bronzetree:1056242349447073842> "
		elif dbInfo["tree"] >= 1:
			treeemblem = "<:tree:1056242347983257610> "

	# Curator

	curatoremblem = ""
	if not isinstance(ctx.message.channel, discord.channel.DMChannel) and customEmoji:
		curatoremote = self.client.get_emoji(742136325628756000)
		role = discord.utils.get(ctx.guild.roles, name="Curator")
		if hasattr(user, "roles") and role in user.roles:
			curatoremblem = str(curatoremote) + " "

	# Bot owner

	botemblem = ""
	for x in botowner:
		if (int(user.id) == int(x)):
			botemblem = "👨‍💻 "

	# Rosebud

	rosebudemblem = ""
	if dbInfo and customEmoji:
		if "modifiedkarma" in dbInfo:
			rosebudemote = self.client.get_emoji(862441238267297834)
			rosebudemblem = str(rosebudemote) + " "
	
	return leaderemblem + treeemblem + curatoremblem + botemblem + rosebudemblem

async def getGlobalRank(ctx, userId):

	#
	# GET VALUE IN GLB
	#

	db.clear_cache()
	lbsult = db.all() # doesnt work
	leaderboard = {} # Prepares an empty dictionary.
	for x in lbsult: # For each entry in the database:
		leaderboard[x.get("username")] = int(x.get("points")) # ...save the user's ID and its amount of points in a new Python database.
	leaderboard = sorted(leaderboard.items(), key = lambda x : x[1], reverse=True) # Sort this database by amount of points.
	s = ""
	leadervalue = 1

	for key, value in leaderboard: # For each value in the new, sorted DB:
		if key == str(userId):
			break
		else:
			leadervalue += 1
	
	return leadervalue

async def printLeaderboard(page, leaderboard, self, ctx, ctxMessage, ctxChannel, args, isGlobal):
	numero = ((page-1) * 5) + 1
	ceronumero = 1
	lbEmbed = [None] * 12
	embedIds = [None] * 12
	typeArgs = 'default'
	checkM = self.client.get_emoji(660250625107296256)
	hardLimit = 6 #maximum amount of pages you can show on ?gplb. default is 6 (up to 25 messages)

	if len(leaderboard) == 0:
		await sendErrorEmbed(ctxChannel, "Looks like this leaderboard is empty! Why don't we get started by reacting to posts?")
		await ctxMessage.remove_reaction(checkM, self.client.user)

	elif (isGlobal == True and not page > hardLimit) or isGlobal == False: 
		if ctxMessage:
			react = await ctxMessage.add_reaction(checkM)
		
		for key,values in leaderboard[(numero-1):]:
			srvSettings = srv.search(Query().serverid == int(values[4]))
			if len(srvSettings) > 0:
				srvSettings = srvSettings[0];
			if (isGlobal == True and (("global" in srvSettings and srvSettings['global'] == True) or (not "global" in srvSettings))) or (isGlobal == False):
				if numero != ((page * 5) + 1):
					if args:
						if args[0] == "nsfw":
							if (values[6] == "True"):
								typeArgs = 'nsfw'
								lbEmbed[ceronumero] = await createLeaderboardEmbed(self, values, numero, ceronumero, ctx, ctxMessage, ctxChannel, lbEmbed, page, isGlobal)
								if lbEmbed[ceronumero]:
									embedIds[ceronumero] = lbEmbed[ceronumero].id
								numero = numero + 1
								ceronumero = ceronumero + 1
						elif args[0] == "sfw" and isGlobal == False:
							if (values[6] != "True" or values[6] == "None"):
								typeArgs = 'sfw'
								lbEmbed[ceronumero] = await createLeaderboardEmbed(self, values, numero, ceronumero, ctx, ctxMessage, ctxChannel, lbEmbed, page, isGlobal)
								if lbEmbed[ceronumero]:
									embedIds[ceronumero] = lbEmbed[ceronumero].id
								numero = numero + 1
								ceronumero = ceronumero + 1

						elif args[0] == "all" and isGlobal == True:
							typeArgs = 'all'
							lbEmbed[ceronumero] = await createLeaderboardEmbed(self, values, numero, ceronumero, ctx, ctxMessage, ctxChannel, lbEmbed, page, isGlobal)
							if lbEmbed[ceronumero]:
								embedIds[ceronumero] = lbEmbed[ceronumero].id
							numero = numero + 1
							ceronumero = ceronumero + 1
						else:
							typeArgs = 'mention'
							lbEmbed[ceronumero] = await createLeaderboardEmbed(self, values, numero, ceronumero, ctx, ctxMessage, ctxChannel, lbEmbed, page, isGlobal)
							if lbEmbed[ceronumero]:
								embedIds[ceronumero] = lbEmbed[ceronumero].id
							numero = numero + 1
							ceronumero = ceronumero + 1
					else:
						if isGlobal == False:
							typeArgs = 'default'
							lbEmbed[ceronumero] = await createLeaderboardEmbed(self, values, numero, ceronumero, ctx, ctxMessage, ctxChannel, lbEmbed, page, isGlobal)
							if lbEmbed[ceronumero]:
								embedIds[ceronumero] = lbEmbed[ceronumero].id
							numero = numero + 1
							ceronumero = ceronumero + 1
						elif values[6] != "True" or values[6] == "None":
							typeArgs = 'default'
							lbEmbed[ceronumero] = await createLeaderboardEmbed(self, values, numero, ceronumero, ctx, ctxMessage, ctxChannel, lbEmbed, page, isGlobal)
							if lbEmbed[ceronumero]:
								embedIds[ceronumero] = lbEmbed[ceronumero].id
							numero = numero + 1
							ceronumero = ceronumero + 1

		if any(lbEmbed):
			cleanIds = list(filter(None, embedIds))
			if (lbEmbed[(int(ceronumero)-1)] == False): 
				lbEmbed[(int(ceronumero)-1)] = lbEmbed[(int(ceronumero)-2)]
			remove = await lbEmbed[(int(ceronumero)-1)].add_reaction("🗑️")
			if page > 1:
				nextitem = await lbEmbed[(int(ceronumero)-1)].add_reaction("⬅️")
			if (numero) == ((page * 5) + 1) and (page != hardLimit - 1 or isGlobal == False):
				if (len(leaderboard) >= numero):
					nextitem = await lbEmbed[(int(ceronumero)-1)].add_reaction("➡️")

			dm.insert({'id': lbEmbed[(int(ceronumero)-1)].id, 'messages': cleanIds, 'type': typeArgs, 'page': page, 'global': isGlobal})
		else:
			await sendErrorEmbed(ctxChannel, "The leaderboard didn't generate itself correctly. This should happen either if no one has ever voted on a post (if you just installed Reto, for example), or if Reto has no access to any of the servers where the top posters are. (Using real databases in test bots, maybe?)")
		botid = self.client.user
		await ctxMessage.remove_reaction(checkM, botid)

async def createLeaderboardEmbed(self, values, numero, ceronumero, ctx, ctxMessage, ctxChannel, lbEmbed, page, isGlobal):
	guild = ctxMessage.guild

	username = self.client.get_user(str(values[2]))
	if not username:
		username = await self.client.fetch_user(str(values[2]))
	guild = self.client.get_guild(int(values[4]))
	if username and guild:
		contenido=values[1]
		autor=username
		foto=username.avatar_url
		if(len(values[3]) > 0):
			imagen=values[3]

		if numero == 1:
			emberino=discord.Embed(description=contenido, colour=discord.Colour(0xffd700))
		elif numero == 2:
			emberino=discord.Embed(description=contenido, colour=discord.Colour(0xc0c0c0))
		elif numero == 3:
			emberino=discord.Embed(description=contenido, colour=discord.Colour(0xcd7f32))
		else:
			emberino=discord.Embed(description=contenido, colour=discord.Colour(0xa353a9))
		
		authorDatabase = db.get(Query()['username'] == str(autor.id))
		badges = await getBadges(self, ctx, authorDatabase, autor, False)

		# the user may not have a profile pic!
		if (foto):
			emberino.set_author(name=autor.name + " " + badges, icon_url=foto)
		else:
			emberino.set_author(name=autor.name + " " + badges)

		# the server may not have an icon!
		if (guild.icon_url):
			emberino.set_footer(text=guild, icon_url=guild.icon_url)
		else:
			emberino.set_footer(text=guild)

		# Parsing embeds:

		if values[7]:
			for embed in ast.literal_eval(values[7]):
				thisEmbed = emberino.to_dict()
				if not (len(values[3]) > 0) and not "image" in thisEmbed:
					if "thumbnail" in embed:
						emberino.set_image(url=embed['thumbnail']['url'])
					if "image" in embed:
						emberino.set_image(url=embed['image']['url'])
				title = ""
				description = ""
				if "title" in embed:
					title = embed['title']
				elif "author" in embed:
					title = embed['author']['name']
				if "description" in embed:
					description = embed['description']
				if title and description:
					emberino.add_field(name=title, value=description, inline=False)
				if "fields" in embed:
					for field in embed["fields"]:
						emberino.add_field(name=field['name'], value=field['value'], inline=False)

		if numero == 1:
			emberino.add_field(name="Position", value="🥇 "+str(numero), inline=True)
		elif numero == 2:
			emberino.add_field(name="Position", value="🥈 "+str(numero), inline=True)
		elif numero == 3:
			emberino.add_field(name="Position", value="🥉 "+str(numero), inline=True)
		else:
			emberino.add_field(name="Position", value="✨ "+str(numero), inline=True)
		
		if isGlobal:
			karmaName = "Karma"
			karmaEmoji = "<:karma:862440157525180488>"
		else:
			karmaName = await getLocalKarma("name", ctx.message)
			karmaEmoji = await getLocalKarma("emoji", ctx.message)
		
		emberino.add_field(name=karmaName, value=karmaEmoji + " " + str(values[0]), inline=True)
		if (values[5] != "None"): #if theres 'stars' value in post
			emberino.add_field(name="Stars", value=":star2: "+str(values[5]), inline=True)
		if(len(values[3]) > 0):
			emberino.set_image(url=values[3])

		if numero != ((page * 5) + 1):
			lbEmbed[ceronumero] = await ctxChannel.send(embed=emberino)
		else:
			lbEmbed[ceronumero] = False
		return lbEmbed[ceronumero]

async def sendErrorEmbed(ctxChannel, description):
	title = "Looks like something went wrong..."
	if random.randint(0,100) == 69:
		title = "Oopsie Woopsie! UwU. We made a fricky wicky!!"
	embed=discord.Embed(title=title, description=description, color=0xfe2c2c)
	embed.set_footer(text="Need help? Reach us at our support server! " + support)
	errorEmbed = await ctxChannel.send(embed=embed)
	return errorEmbed

async def exportData(userId, ctx):
	dbTable = [
		{
			'query': db.search(Query()['username'] == userId),
			'name': 'profile'
		},
		{
			'query': post.search(Query()['username'] == userId),
			'name': 'comments'
		},
		{
			'query': priv.search(Query()['username'] == int(userId)),
			'name': 'privacy'
		}
	]

	if not os.path.exists('export/'):
		os.mkdir('export')
	
	for table in dbTable:
		if table:
			filename = table['name'] + "_" + userId + ".json"
			filepath = "export/" + filename
			with open(filepath, "a+", encoding="utf-8") as writeJson:
				writeJson.write(str(table['query']))
			with open(filepath, encoding="utf-8") as readJson:
				await ctx.message.author.send(file=discord.File(readJson, filename))
			os.remove(filepath)

async def createBestOfEmbed(message):
	# Decipher the color of the pre-existing embed, if there's any
	colour = discord.Color.from_rgb(32, 34, 37)

	if message.embeds:
		previousEmbed = message.embeds[0].to_dict()
		if "color" in previousEmbed:
			colour = previousEmbed['color']
	
	# Create the Embed element
	embed = discord.Embed(description=message.content, color=colour)

	# Set the embed's author and jump-to URL
	messageUrl = "https://discordapp.com/channels/" + str(message.guild.id) + "/" + str(message.channel.id) + "/" + str(message.id)
	embed.set_author(name=message.author.name, url=messageUrl, icon_url=message.author.avatar_url)

	# --- ATTACH REPLY (IF IT EXISTS) ---

	if hasattr(message, 'reference'):
		if message.reference:
			reply = await message.channel.fetch_message(message.reference.message_id)
			if reply and reply.content:
				embed.add_field(name="Replying to " + reply.author.name, value=reply.content, inline=False)
	
	# --- PARSE THROUGH IMAGES/ATTACHMENTS ---
	
	if(len(message.attachments) > 0): #?
		attachmentUrl = message.attachments[0].url
		validAttachment = False
		# Is this a valid image file? If so, set the image to it.
		for e in ['jpg','jpeg','png','webp','gif']:
			if attachmentUrl[-len(e)-1:]==f'.{e}':
				embed.set_image(url=attachmentUrl)
				validAttachment = True
		if validAttachment == False:
			# Try and match the file extension with the object type.
			postIncludes = "an attachment"
			for e in ['mp4', 'mov']:
				if attachmentUrl[-len(e)-1:]==f'.{e}':
					postIncludes = "a video"
			for e in ['wav', 'mp3', 'ogg']:
				if attachmentUrl[-len(e)-1:]==f'.{e}':
					postIncludes = "an audio file"
			# Send a footer warning!
			embed.set_footer(text="This post includes " + postIncludes + "! Click on the link above to see the attachment.")
		# If there's more than one image, set a warning on the footer!
		if(len(message.attachments) > 1 and validAttachment == True):
			embed.set_footer(text="This post includes more than one image! Click on the link above to see the rest.")

	# --- PARSE THROUGH EMBEDS ---
	
	if (message.embeds):
		for previousEmbed in message.embeds:
			# Get both embeds in a readable form.
			previousEmbed = previousEmbed.to_dict()
			thisEmbed 	  = embed.to_dict()

			# Set the image to that of the previousEmbed if there are no other images in thisEmbed.
			if (len(message.attachments) == 0) and not "image" in thisEmbed:
				if "thumbnail" in previousEmbed:
					embed.set_image(url=previousEmbed['thumbnail']['url'])
				if "image" in previousEmbed:
					embed.set_image(url=previousEmbed['image']['url'])

			# Set the footer to that of the previousEmbed if there's no footer on thisEmbed.
			if not "footer" in thisEmbed:
				if "footer" in previousEmbed:
					embed.set_footer(text=previousEmbed['footer']['text'])
				else:
					footer = ""
					if "provider" in previousEmbed:
						footer = previousEmbed['provider']['name']
					if "author" in previousEmbed and not "title" in previousEmbed:
						footer = previousEmbed['author']['name']
					if footer:
						embed.set_footer(text=footer)
			
			# Set the title, author and/or description based on the previousEmbed (where applicable)
			title = ""
			description = ""
			if "title" in previousEmbed:
				title = previousEmbed['title']
			elif "author" in previousEmbed:
				title = previousEmbed['author']['name']
			if "description" in previousEmbed:
				description = previousEmbed['description']
			if title and description:
				embed.add_field(name=title, value=description, inline=False)
			if "fields" in previousEmbed:
				for field in previousEmbed["fields"]:
					embed.add_field(name=field['name'], value=field['value'], inline=False)

	# --- ADD EMBED FOR JUMPING TO MESSAGE ---
	
	embed.add_field(name="** **", value="[🔗 Jump to message](" + messageUrl + ")", inline=False)
	
	return embed

async def createBestOfChannel(message):

	# Verify if no channel named best-of exists
	channelsearch = discord.utils.get(message.guild.channels, name="best-of")

	# Verify if no channels are saved in the best DB
	bestsearch = best.search(Query().serverid == str(message.guild.id))
	bestOfChannel = False

	if "channelid" in bestsearch:
		# If a channel is saved on the BD, verify if it actually exists
		bestOfChannel = discord.utils.get(message.guild.channels, id=bestsearch["channelid"])

	if channelsearch == None and (not bestsearch or not bestOfChannel):
		# If the best-of channel is nowhere to be found, then create it
		newBestOf = await message.guild.create_text_channel('best-of')
		best.upsert({'serverid': str(message.guild.id), 'channelid': newBestOf.id, 'notification': "message"}, Query().serverid == str(message.guild.id))
		# Return the channel element
		return newBestOf
	else:
		# If it does exist, return False
		return False

async def reactionAdded(bot, payload):

	# Ignore if we're on DMs.
	if payload.guild_id is None:
		return

	# --- VARIABLE DEFINITIONS ---

	User = Query() # For TinyDB queries.
	userId = payload.user_id
	serverId = payload.guild_id

	# Get user, channel, server, member and message.
	user = bot.get_user(payload.user_id)
	if not user:
		user = await bot.fetch_user(payload.user_id)
	channel = bot.get_channel(payload.channel_id)
	if not channel:
		channel = await bot.fetch_channel(payload.channel_id)
	guild = bot.get_guild(payload.guild_id)
	if not guild:
		guild = await bot.fetch_guild(payload.guild_id)
	member = guild.get_member(payload.user_id)
	if not member:
		member = await guild.fetch_member(payload.user_id)
	message = await channel.fetch_message(payload.message_id)

	# Author (of the original message)'s variables.
	authorId = message.author.id

	# Message related variables.
	messageId = payload.message_id

	# Channel related variables.
	channel = message.channel
	isNsfw = channel.is_nsfw()

	# Emoji name
	emojiName = payload.emoji.name.lower()

	# Check notification types
	best.clear_cache()
	notificationMode = best.get(Query().serverid == str(serverId))
	if 'notification' in notificationMode:
		notificationMode = notificationMode['notification']
	else:
		notificationMode = "message"
	retoThumbsUp = bot.get_emoji(660217963911184384)

	# Privacy data
	privacySettings = priv.get(Query().username == userId)

	# Timestamps
	timestamp = str(datetime.now())

	# What type is it, again?
	types = {
		"plus": {
			"mode": "add",
			"points": 1,
			"message": "{pe} Hearted! `(+{p})`\n**{u}** now has {ke} {k} **{kn}**. ({e} {gk})",
			"bestOf": False,
			"requiresCurator": False,
			"starsAdded": 0,
			"unicodeEmoji": "💖",
			"foreColor": Fore.RED,
			"justDid": "Hearted"
		},
		"minus": {
			"mode": "subtract",
			"points": -1,
			"message": "{me} Crushed. `(-{p})`\n**{u}** now has {ke} {k} **{kn}**. ({e} {gk})",
			"bestOf": False,
			"requiresCurator": False,
			"starsAdded": 0,
			"unicodeEmoji": "💔",
			"foreColor": Fore.BLUE,
			"justDid": "Crushed"
		},
		"10": {
			"mode": "add",
			"points": 10,
			"message": "Congrats, **{u}**! `(+{p})` Your post will be forever immortalized in the **{bm}** channel.\nYou now have {ke} {k} **{kn}**. ({e} {gk})",
			"bestOf": True,
			"requiresCurator": True,
			"starsAdded": 1,
			"unicodeEmoji": "⭐",
			"foreColor": Fore.YELLOW,
			"justDid": "Starred"
		},
		"10repeat": {
			"mode": "add",
			"points": 10,
			"message": "Congrats, **{u}**! `(+{p})` Your post was so good it was Starred more than once.\nYou now have {ke} {k} **{kn}**. ({e} {gk})",
			"bestOf": False,
			"requiresCurator": True,
			"starsAdded": 1,
			"unicodeEmoji": "🌟",
			"foreColor": Fore.GREEN,
			"justDid": "Starred (multiple times)"
		}
	}

	# One-time Shooting Star
	isShootingStar = False
	if holiday:
		if await treeEnabled(guild.id):
			opener = db.get(Query()['username'] == str(userId))
			if opener:
				if "shootingstar" in opener and opener["shootingstar"] > 0:
					isShootingStar = True
					db.update(subtract(str("shootingstar"), 1), where('username') == str(userId))
					emojiName = "10"

	if ((userId != authorId) or (debug == True)) and not user.bot:
		if not isinstance(payload.emoji, str):
			if any(item.lower() == emojiName for item in types.keys()) or isShootingStar:

				# Is the comment already available on the database?
				commentExists = post.count(Query().msgid == str(messageId))
				
				# Get the values from the types dict.!
				starExists = post.get(Query().msgid == str(messageId))
				starExists = starExists['stars'] if starExists else False

				if starExists and emojiName == "10":
					emojiName = "10repeat"
				
				typeVariables = types[emojiName]
				timestamp = await getTimestamp()
				print(timestamp + " " + typeVariables['unicodeEmoji'] + " " + typeVariables['foreColor'] + user.name + Style.RESET_ALL + " just " + typeVariables['justDid'] + " " + typeVariables['foreColor'] + message.author.name + Style.RESET_ALL + "'s message")

				# If the role requires Curator and the user doesn't have it, boot 'em out
				if not isShootingStar:
					if discord.utils.get(member.roles, name="Curator") is None and typeVariables['requiresCurator']:
						await message.remove_reaction(payload.emoji, user)
						return

				# --- ADDING POINTS ---

				# Check if the user is on the database.
				userExists = db.count(Query().username == str(authorId)) # NOTE: Stored as strings.
				if not userExists:
					db.insert({'username': str(authorId), 'points': typeVariables['points'], 'servers': [serverId], str(serverId): typeVariables['points']})
				else:
					# Add points to user.
					db.update(add('points', typeVariables['points']), where('username') == str(authorId))
					
					# Check if the user has any servers assigned to them. If not, assign!
					serverExists = db.count((User.servers.any([serverId])) & (User.username == str(authorId)))
					if not serverExists:
						db.update(add('servers',[serverId]), where('username') == str(authorId))
					
					# Check if the user has server karma.
					userData = db.get(User.username == str(authorId))
					if str(serverId) in userData:
						db.update(add(str(serverId), typeVariables['points']), where('username') == str(authorId))
					else:
						db.upsert({str(serverId): typeVariables['points']}, where('username') == str(authorId))

				# --- SEND TO THE BEST OF ---
				
				# Dummy variable (for comment database later down the line)
				bestOfSentEmbed = False
				if typeVariables['bestOf']:
					bestOfEmbed = await createBestOfEmbed(message)
					if not starExists:
						bestOfSettings = best.get(Query().serverid == str(serverId))
						if 'channelid' in bestOfSettings:
							try:
								bestOfChannel = discord.utils.get(message.guild.channels, id=bestOfSettings['channelid'])
								# If the best-of  has been deleted...
								if not bestOfChannel:
									await sendErrorEmbed(channel, 'It appears the Best Of channel has been deleted. Creating a new one...')
									bestOfChannel = await createBestOfChannel(message)
								bestOfSentEmbed = await bestOfChannel.send(embed=bestOfEmbed)
							except discord.errors.Forbidden:
								await sendErrorEmbed(channel, "I don't have sufficient permissions to post on the " + bestOfChannel.mention + " channel!")
						else:
							await sendErrorEmbed(channel, 'It looks like there\'s no Best Of channel on this server! Creating a new one...')
							await createBestOfChannel(message)
				
				# --- LOG ON POST LEADERBOARD ---
				
				if not commentExists:
					# If the comment doesn't exist, let's create a new value on the DB!
					# If Privacy Mode isn't on:
					if not privacySettings or "mode" in privacySettings and privacySettings['mode'] == False or not "mode" in privacySettings:
						# Dummy variables
						attachments = ""
						richEmbeds = ""
						bestOfId = ""
						# If attachments or embeds exist, assign them to a readable format
						if (len(message.attachments) > 0):
							attachments = message.attachments[0].url
						if (message.embeds):
							richEmbeds = [None]*len(message.embeds)
							i = 0
							for embed in message.embeds:
								richEmbeds[i] = embed.to_dict()
								i = i + 1
						# If the post was sent to Best Of, track that ID
						if bestOfSentEmbed:
							bestOfId = bestOfSentEmbed.id
						# And insert all that into the Comment DB!
						post.insert({'msgid': str(messageId), 'username': str(authorId), 'points': typeVariables['points'], 'servers': str(serverId), 'content': message.content, 'embed': attachments, 'richembed': richEmbeds, 'voters': [userId], 'stars': typeVariables['starsAdded'], 'nsfw': isNsfw, 'timestamp': timestamp, 'bestofid': bestOfId})
				else:
					# If the comment does exist, let's just add points onto it.
					post.update(add('points', typeVariables['points']), where('msgid') == str(messageId))
					post.update(add('voters', [userId]), where('msgid') == str(messageId))
					post.update(add('stars', typeVariables['starsAdded']), where('msgid') == str(messageId))

				# --- POST A CONFIRMATION MESSAGE ---

				# If set to Reaction, add then remove it.
				if notificationMode == "reaction":
					await message.add_reaction(retoThumbsUp)
					await asyncio.sleep(1)
					await message.remove_reaction(retoThumbsUp, bot.user)
				# If set to Message or notificationMode is null, send a message.
				if (notificationMode != "reaction") and (notificationMode != "disabled"):
					formattedMessage = await getFormattedMessage(message, emojiName)
					if not formattedMessage:
						# If a custom Message Notification doesn't exist, send the default.
						formattedDefault = await formatMessage(typeVariables['message'], message)
						confirmationMessage = await channel.send(formattedDefault)
					else:
						confirmationMessage = await channel.send(formattedMessage)					
					await asyncio.sleep(3) 
					await confirmationMessage.delete()

async def getLocalKarma (nameOrEmoji, message):	
	curKarmaSettings = srv.get(Query().server == message.guild.id)
	if nameOrEmoji == "name":
		value = message.guild.name + " Karma"
	elif nameOrEmoji == "emoji":
		value = "<:karma:862440157525180488>"
	
	if curKarmaSettings:
		if "karmaname" in curKarmaSettings and nameOrEmoji == "name":
			if curKarmaSettings['karmaname'] != False:
				value = curKarmaSettings['karmaname']
		if "karmaemoji" in curKarmaSettings and nameOrEmoji == "emoji":
			if curKarmaSettings['karmaemoji'] != False:
				value = curKarmaSettings['karmaemoji']
	
	return value

async def treeEnabled(serverid):
	server = srv.get(Query().serverid == serverid)
	
	if not 'holiday' in server:
		return True
	elif not server:
		return False
	else:
		return server["holiday"]

def addOrInsertToDatabase(key, value, dbId):
	database = db.get(Query()['username'] == str(dbId))

	if key in database:
		db.update(add(key, value), where('username') == str(dbId))
	else:
		db.upsert({key: value}, where('username') == str(dbId))

async def reactionRemoved(bot, payload):
	if payload.guild_id is None:
		return
	User = Query()
	userid  = payload.user_id

	# Misc. definitions.
	# Attempt a get_x command for brevity. If that doesn't work, use fetch_x (slow).
	user = bot.get_user(payload.user_id)
	if not user:
		user = await bot.fetch_user(payload.user_id)
	channel = bot.get_channel(payload.channel_id)
	if not channel:
		channel = await bot.fetch_channel(payload.channel_id)
	guild = bot.get_guild(payload.guild_id)
	if not guild:
		guild = await bot.fetch_guild(payload.guild_id)
	member = guild.get_member(payload.user_id)
	if not member:
		member = await guild.fetch_member(payload.user_id)
	# no such thing as "get_message"
	message = await channel.fetch_message(payload.message_id)

	server = str(message.guild.id)
	
	if ((userid != message.author.id) or (debug == True)) and not user.bot:
		if not isinstance(payload.emoji, str):

			channel       = message.channel
			bestOfId      = best.get(Query().serverid == server)
			bestOfChannel = await bot.fetch_channel(bestOfId["channelid"])

			timestamp = await getTimestamp()
			print(timestamp + " 💔 " + Fore.BLUE + user.name + Style.RESET_ALL + " just unreacted (" + payload.emoji.name + ") " + Fore.BLUE + message.author.name + Style.RESET_ALL + "'s message")

			removable = None
			if payload.emoji.name == '10':
				# the bot auto-removes stars given out by non-curators.
				# if this is from a non-curator, ignore all this code! otherwise we're just removing points without adding them first.
				if discord.utils.get(member.roles, name="Curator") is None:
					return
				removable = 10
			if payload.emoji.name == 'plus':
				removable = 1
			if payload.emoji.name == 'minus':
				removable = -1

			if removable:
				# Remove the user's karma.
				value = message.author.id
				exists = db.count(Query().username == str(value))
				if not (exists == 0):
					db.update(subtract('points', removable), where('username') == str(value))
					db.update(subtract(server, removable), where('username') == str(value))
				# Remove the comment's karma.
				valuetwo = str(message.id)
				postexists = post.count(Query().msgid == str(valuetwo))
				if not (postexists == 0):
					post.update(subtract('points',removable), where('msgid') == str(valuetwo))
					#post.update(subtract('voters',[user.id]), where('msgid') == str(valuetwo))
					if payload.emoji.name == '10':
						post.update(subtract('stars',1), where('msgid') == str(valuetwo))
						# Get stars from post
						finalPost = post.get(where('msgid') == str(valuetwo))
						if "bestofid" in finalPost and finalPost["stars"] <= 0:
							bestOfMessage = await bestOfChannel.fetch_message(finalPost["bestofid"])
							await bestOfMessage.delete()
				
				# we shouldn't send a message if someone un-reacted, that'd be mean.
				# instead, we send a reaction unless notifications are disabled
				checkM = bot.get_emoji(660217963911184384)
				notifmode = best.get(Query().serverid == server)
				if "notification" in notifmode:
					notifmode = notifmode['notification']
				else:
					notifmode = "message"
				if notifmode != "disabled":
					react = await message.add_reaction(checkM)
					await asyncio.sleep(1) 
					botid = bot.user
					await message.remove_reaction(checkM, botid)