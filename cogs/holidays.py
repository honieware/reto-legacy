# Import global variables and databases.
from definitions import db, holiday, debug, best, treeroles

# Imports, database definitions and all that kerfuffle.

import discord
from discord.ext import commands, tasks
import asyncio
from tinydb import TinyDB, Query, where
from tinydb.operations import add, subtract, delete
import json
import random
import time

# sharedFunctions
from sharedFunctions import getLocalKarma, treeEnabled, addOrInsertToDatabase

# ----------------------------------------------------------------------------------------------

class Holidays(commands.Cog):
	"""
	Bonus stuff that has to do with the bot's updates, invites, privacy settings, and other extras.
	"""
	def __init__(self, client):
		self.client = client
	
	#------------------------
	# HOLIDAY COMMANDS
	# These will only work if the "holiday" tag on db.json is set to true.
	#------------------------
	@commands.command(description='Take a trip to Reto\'s Holiday Tree, and get gifts for the festivities!')
	async def tree(self, ctx):
		"""Take a trip to Reto\'s Holiday Tree, and get yourself some gifts for the festivities!"""

		# Throw error if the event is over, or if the server doesn't allow for RHT
		if not holiday:
			await sendHolidayError(ctx)
			return
		if not await treeEnabled(ctx.message.guild.id):
			await sendDisabledError(ctx)
			return
		
		# Check if the timeout is over
		if debug:
			timeout = 0
			timeoutOnText = "whenever"
		else:
			timeout = 60 * 5 # two hours
			timeoutOnText = "in five minutes"
		
		# Repeated from the parser because async can be a bitch
		karmaName = await getLocalKarma("name", ctx.message)
		karmaEmoji = await getLocalKarma("emoji", ctx.message)

		server = ctx.message.guild
		openerId = ctx.message.author.id
		
		opener = db.get(Query()['username'] == str(openerId))
		timeToComeBack = time.time()
		if 'lastCheckedTree' in opener:
			timeToComeBack = opener['lastCheckedTree'] + timeout
		
		spendingTitle = "Coming to visit"

		if not 'lastCheckedTree' in opener or time.time() >= timeToComeBack:

			# Calculate how much you'd spend
			priceOfTree = 0
			maxPriceOfTree = 10

			if 'openedGifts' in opener:
				priceOfTree = opener['openedGifts'] if opener['openedGifts'] < maxPriceOfTree else maxPriceOfTree

				openerInDatabase = db.get(Query()['username'] == str(openerId))
				serverKarma = str(ctx.message.guild.id)
				
				if priceOfTree > openerInDatabase.get(serverKarma):
					await sendMoneyError(ctx, karmaName, karmaEmoji, openerInDatabase.get(serverKarma), priceOfTree)
					return
				
				spendingTitle = "Spending " + karmaEmoji + " **x" + str(priceOfTree) + "**"

				# Omit all this if there's a Tree Ticket in your inventory
				if "ticket" in opener and opener["ticket"] > 0:
					priceOfTree = 0
					spendingTitle = "Using 🎫 **x1**"
					addOrInsertToDatabase("ticket", -1, openerId)

				
				db.update(subtract(serverKarma, priceOfTree), where('username') == str(openerId))
			
			# Open the presents
			receivedGifts = openManyGifts(1, [], openerId, server)

			# Update wait time
			db.upsert({'lastCheckedTree': int(time.time())}, where('username') == str(openerId))

			# Create the embed
			giftEmbed = discord.Embed(title=spendingTitle + ", you check on the tree...", color=0x9bf376)
			giftEmbed.set_footer(text="Come back " + timeoutOnText + " for more gifts!")
			
			for receivedGift in receivedGifts:
    				# Should probably be a function, actually
				base = best.get(Query().serverid == str(ctx.message.guild.id))
				bcid = base['channelid']
				bitem = discord.utils.get(ctx.message.guild.channels, id=bcid)
				if bitem:
					bestOf = bitem.mention
				else:
					bestOf = "the Best Of channel"
				
				description = receivedGift["description"].replace('{kn}', karmaName).replace('{ke}', karmaEmoji).replace('{bm}', bestOf)

				# Add a gift to the list
				giftEmbed.add_field(name=receivedGift["emoji"] + "** " + receivedGift["name"] + "**", value="*" + description + "*", inline=False)
			
			# Send the embed
			await ctx.send(embed=giftEmbed)
			
		else:
			await sendTimeoutError(ctx, timeToComeBack)
		
def openGift(openerId, server):
	gifts = getGiftsWithRoles(server)
	giftsByWeight = []

	for gift in gifts:
		giftsByWeight.extend( [gift]*gift["weight"] )
	
	selectedGift = random.choice(giftsByWeight)

	# Update stats
	addOrInsertToDatabase('openedGifts', 1, openerId)
	addOrInsertToDatabase(selectedGift["code"], 1, openerId)

	return selectedGift
	

def openManyGifts(chances, gifts, openerId, server):
    # The possibility to get an extra gift
	repeatedChance = 5
	
	if chances == repeatedChance + 1:
		chances = chances - 1 # Dirty fix so (chances + 5) ends up with 1 -> 5 -> 10, instead of 1 -> 6 -> 11
	
	print("🎁 Trying to get a gift with a chance from 1 to " + str(chances) + "...")

	if (random.randint(1, chances) == 1):
		print("Gift achieved!")
		gifts.append(openGift(openerId, server))
		openManyGifts(chances+repeatedChance, gifts, openerId, server)
	return gifts

def getGiftsWithRoles(server):
	with open('json/gifts.json') as f:
		gifts = json.load(f)

		treeRoleGifts = treeroles.search(Query().serverid == server.id)
		print(treeRoleGifts)

		for roleGift in treeRoleGifts:
			roleToGift = server.get_role(roleGift["id"])

			gifts.append({
				"name": roleToGift.name,
				"code": roleToGift.name.replace(" ", "").lower(),
				"emoji": "👑",
				"description": "A very special **server role** has been added to your profile!",
				"giftable": False,
				"storable": False,
				"weight": roleGift["weight"]
			})

		return gifts

async def sendHolidayError(ctx):
	await ctx.send("🍂 The festivities have passed, and **Reto's Holiday Tree** has withered away.\nThank you for participating!")

async def sendDisabledError(ctx):
	await ctx.send("🚫 **Reto's Holiday Tree** has been disabled on this server.")

async def sendTimeoutError(ctx, timeout):
	await ctx.send("🍂 **Easy there!** The Holiday Tree needs time to rest.\nCheck back <t:" + str(timeout) + ":R> for more gifts!")

async def sendMoneyError(ctx, karmaName, karmaEmoji, currentAmount, requiredAmount):
	await ctx.send("🍂 **Looks like you don't have enough " + karmaName + " to visit!** (Your total: **" + karmaEmoji + " " + str(currentAmount) + "** / Required: **" + karmaEmoji + " " + str(requiredAmount) + "**)\nCome back when you have more " + karmaName + " to spend.")
    

def setup(client):
	client.add_cog(Holidays(client))