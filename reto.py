# Import global variables and databases.
from definitions import bottoken, botname, botver, prefix, debug, db, srv, activity, customprefix, gusername, grepo

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
import requests
import json
import random
from datetime import datetime, date
import logging
import traceback
import sys
from colorama import init, Fore, Back, Style
from yaspin import yaspin

# sharedFunctions
from sharedFunctions import sendErrorEmbed, reactionAdded, reactionRemoved, getTimestamp

# ----------------------------------------------------------------------------------------------

# Start Colorama ANSI
init(autoreset=True)

# Loading icon
spinner = yaspin(text="Loading " + botname + "... " + Style.DIM + "(This may take a while.)", color="blue")
spinner.start()

getactivities = activity.all()
botactivity = []
for value in getactivities:
	botactivity.append(value["activity"])

def get_prefix(bot, msg):
	customprefix.clear_cache()
	if not msg.guild: # is on DMs
		return commands.when_mentioned_or(prefix)(bot,msg)
	else:
		pre = customprefix.search(Query().server == msg.guild.id)
		if pre:
			return pre[0]["prefix"] # custom prefix on json db
		else:
			return prefix # default prefix

bot = commands.Bot(command_prefix=get_prefix)
client = discord.Client()
asciiBanner = pyfiglet.figlet_format(botname, justify="center")

@bot.command
async def load(ctx, extension):
	bot.load_extension(f'cogs.{extension}')

@bot.command
async def unload(ctx, extension):
	bot.unload_extension(f'cogs.{extension}')

@bot.event
async def on_raw_reaction_add(payload):
	await reactionAdded(bot, payload)

@bot.event
async def on_raw_reaction_remove(payload):
	await reactionRemoved(bot, payload)

@bot.event
async def on_command(ctx):
	timestamp = await getTimestamp()
	print(timestamp + " ⏳ " + Fore.YELLOW + ctx.message.author.name + Style.RESET_ALL + " invoked " + Fore.YELLOW + prefix + ctx.command.name)

@bot.event
async def on_command_completion(ctx):
	timestamp = await getTimestamp()
	print(timestamp + " ✅ " + Fore.GREEN + ctx.message.author.name + Style.RESET_ALL + " invoked " + Fore.GREEN + prefix + ctx.command.name)

for file in os.listdir("./cogs"):
	if file.endswith(".py"):
		bot.load_extension(f'cogs.{file[:-3]}') #[:-3] removes the last 3 chars

# Error handler.
@bot.event
async def on_command_error(ctx, error):
	ignored = (commands.CommandNotFound, )
	error = getattr(error, 'original', error)
	if isinstance(error, discord.ext.commands.errors.ChannelNotFound):
		await sendErrorEmbed(ctx, "I can't find that channel! Make sure you're adding a (valid) Channel element.")
	if isinstance(error, ignored):
		return
	if isinstance(error, discord.ext.commands.CommandNotFound):
		return
	if isinstance(error, discord.ext.commands.DisabledCommand):
		await sendErrorEmbed(ctx, f'{ctx.command} has been disabled.')
	elif isinstance(error, discord.ext.commands.NoPrivateMessage):
		try:
			await sendErrorEmbed(ctx.author, f'{ctx.command} can not be used in Private Messages.')
		except discord.HTTPException:
			pass
	elif isinstance(error, commands.BadArgument):
		if ctx.command.qualified_name == 'tag list':
			await sendErrorEmbed(ctx, "Can't find that member, for whatever reason. Please try again.")
	elif isinstance(error, discord.ext.commands.errors.MissingPermissions):
		print(timestamp + " ❌ " + Fore.RED + "Required permissions missing" + Style.RESET_ALL + "from user: " + ctx.command.name)
		await sendErrorEmbed(ctx, "You're missing the required permissions to run this command!")
	elif isinstance(error, discord.errors.Forbidden):
		print(timestamp + " ❌ " + Fore.RED + "Required permissions missing" + Style.RESET_ALL + " from Reto: " + ctx.command.name)
		#await sendErrorEmbed(ctx, "I'm missing the required permissions to run this command!")
	else:
		timestamp = await getTimestamp()
		print(timestamp + " ❌ " + Fore.RED + "Ignoring exception in command " + Style.RESET_ALL + "{}:".format(ctx.command), file=sys.stderr)
		traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
		nameTraceback = str(error).capitalize()
		formattedTraceback = "\n".join(traceback.format_exception(type(error), error, error.__traceback__))
		await sendErrorEmbed(ctx, nameTraceback + ".\n\n```py\n%s\n```" % formattedTraceback)
	raise error

@bot.event
async def on_ready():
	if os.name == 'nt':
		# Windows
		os.system('cls')
	else:
		# Linux
		os.system('clear')

	# Stop spinner
	spinner.stop()
	
	# Coloured Reto banner
	# Kinda hardcoded, but the alternative wasn't pretty either
	asciiLines = asciiBanner.splitlines()
	print(Style.BRIGHT +Fore.CYAN + asciiLines[0])
	print(Fore.CYAN + asciiLines[1])
	print(Style.BRIGHT + Fore.BLUE + asciiLines[2])
	print(Fore.BLUE + asciiLines[3])
	print(Style.DIM + Fore.BLUE + asciiLines[4])
	print(Style.DIM + Fore.BLUE + asciiLines[5])

	# Get bot info for the startup dashboard
	serverPlural = "server"
	if len(bot.guilds) > 1:
		serverPlural = "servers"
	print ("🟢 " + botname + " is " + Fore.GREEN + "ONLINE" + Style.RESET_ALL + " | " + Fore.BLUE + str(bot.user)
			+ Style.RESET_ALL + " on " + Fore.YELLOW + str(len(bot.guilds)) + Style.RESET_ALL + " " + serverPlural +
			" | v" + Fore.CYAN + botver)
	if debug:
		print ('⚠️ ' + Fore.YELLOW + ' Running on Debug Mode' + Style.RESET_ALL + '. Disable it after you\'re done in json/config.json.')
	print ("🫂  Invite link: " + Fore.BLUE + "https://discord.com/oauth2/authorize?client_id=" + str(bot.user.id) + "&permissions=1342524496&scope=bot")
	
	# Check for updates
	updateSpinner = yaspin(text="Looking for updates...", color="red")
	updateSpinner.start()
	r = requests.get("https://api.github.com/repos/" + gusername + "/" + grepo + "/releases")
	j=r.json()
	if j:
		if not "message" in j:
			if j[0]["tag_name"] != botver:
				updateSpinner.stop()
				print("🛑 [v" + j[0]["tag_name"] + "] " + Fore.RED + "A new version of " + botname + " is available!\n"
						+ Style.RESET_ALL + "   Get it at " + Fore.BLUE + "https://github.com/honiemun/reto-legacy/releases")
			else:
				updateSpinner.text = "You're up to date!"
				await asyncio.sleep(1)
		else:
			updateSpinner.text = "Something went wrong while fetching updates."
			await asyncio.sleep(1)			
	updateSpinner.stop()
	print('\n' + '─' * 25 + " Get started with " + Fore.GREEN + "?setup " + Style.RESET_ALL + '─' * 25 + '\n')

	# Warning for users who've yet to migrate to the new database system. (really, you guys?)
	olddb = TinyDB("json/db.json")
	if ((not db) and (olddb)):
		print("""🛑 It looks like you're using the old database system from v1.5.2
(or earlier!) If that isn't the case, dismiss this message. If you've just
upgraded your """ + botname + """ version, you may need to encrypt your old databases
to the new format before continuing to use """ + botname + """.
More info here: """ + Fore.BLUE + """https://github.com/honiemun/reto-legacy/wiki/Migrating-databases
""")
		print('─' * 75 + '\n')

	#async def on_guild_post():
	#	print("Server count posted successfully")

	# Set bot's activity
	global botactivity
	if not botactivity:
		botactivity = [prefix + 'setup to get started!', 'Hey, bot owner - change the default activities with ' + prefix + 'activity!']
	if botver != "":
		game = discord.Game(botactivity[random.randrange(len(botactivity))] + " | v" + botver)
	else:
		game = discord.Game(botactivity[random.randrange(len(botactivity))])
	await bot.change_presence(activity=game)
	bot.loop.create_task(statusupdates())

@bot.event
async def on_guild_join(guild):
	srv.upsert({'serverid': guild.id, 'heart': 'plus', 'crush': 'minus', 'star': '10', 'global': True}, Query().serverid == guild.id)
	for channel in guild.text_channels:
		if channel.permissions_for(guild.me).send_messages:
			embed=discord.Embed(title="Thank you for inviting " + botname + "!", description="Try using the ?setup command to get started!\nIf any problems arise, [join our Discord server](https://google.com) so we can give you a hand.")
			embed.set_thumbnail(url="https://i.ibb.co/ySfQhDG/reto.png")
			await channel.send(embed=embed)
		break

async def statusupdates():
	while True:
		await asyncio.sleep(60)

		# update the activity list
		activity.clear_cache()
		getactivities = activity.all()
		botactivity = []
		for value in getactivities:
			botactivity.append(value["activity"])
		if not botactivity:
			botactivity = [prefix + 'setup to get started!', 'Hey, bot owner - change the default activities with ' + prefix + 'activity!']
		if botver != "":
			game = discord.Game(botactivity[random.randrange(len(botactivity))] + " | v" + botver)
		else:
			game = discord.Game(botactivity[random.randrange(len(botactivity))])
		await bot.change_presence(activity=game)	

bot.run(bottoken)