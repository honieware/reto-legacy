import discord
from discord.ext import commands
import asyncio
import pyfiglet
from tinydb import TinyDB, Query, where
from tinydb.operations import add, subtract
import aiohttp        
import aiofiles
import os.path
import os
import json
import random
from datetime import datetime

# new encryption method (1.6)!
import tinydb_encrypted_jsonstorage as tae
from os.path import join as join_path
key = "P4lcFx$V8wg#0F46!Z!#D$bo*u%kHoH9d*iKHD5kKIXp4p6*%J@1IZTyeQpY7iKL"

# Unencrypted! This NEEDS to be editable by a simple text editor.
cfg = TinyDB("json/config.json")

olddb = TinyDB("json/db.json")
oldsrv = TinyDB('json/server.json')
oldactivity = TinyDB('json/activity.json')
oldcustomprefix = TinyDB('json/prefix.json')
oldbest = TinyDB('json/bestname.json')
oldpost = TinyDB('json/comments.json')
oldpriv = TinyDB('json/blacklist.json')
olddm = TinyDB('json/deletables.json')
oldchan = TinyDB('json/channels.json')

newdb = TinyDB(encryption_key=key, path=join_path("db/","profile.reto"), storage=tae.EncryptedJSONStorage)
#newcfg = TinyDB(encryption_key=key, path=join_path("db/","cfg.reto"), storage=tae.EncryptedJSONStorage)
newsrv = TinyDB(encryption_key=key, path=join_path("db/","srv.reto"), storage=tae.EncryptedJSONStorage)
newactivity = TinyDB(encryption_key=key, path=join_path("db/","activity.reto"), storage=tae.EncryptedJSONStorage)
newcustomprefix = TinyDB(encryption_key=key, path=join_path("db/","customprefix.reto"), storage=tae.EncryptedJSONStorage)
newbest = TinyDB(encryption_key=key, path=join_path("db/","best.reto"), storage=tae.EncryptedJSONStorage)
newpost = TinyDB(encryption_key=key, path=join_path("db/","comments.reto"), storage=tae.EncryptedJSONStorage)
newpriv = TinyDB(encryption_key=key, path=join_path("db/","blacklist.reto"), storage=tae.EncryptedJSONStorage)
newdm = TinyDB(encryption_key=key, path=join_path("db/","deletables.reto"), storage=tae.EncryptedJSONStorage)
newchan = TinyDB(encryption_key=key, path=join_path("db/","channels.reto"), storage=tae.EncryptedJSONStorage)

for c in cfg:
	bottoken = c['bottoken']
	botname = c['botname']
	support = c['support']
	botver = c['botver']
	prefix = c['prefix']

def yes_or_no(question):
    reply = str(input(question+' (y/n): ')).lower().strip()
    if reply[0] == 'y':
        return True
    if reply[0] == 'n':
        return False
    else:
        return yes_or_no("\nAre you sure you want to proceed? ")	

def update_database(olddb, newdb, dbname, withtimestamp):
	if not (newdb):
		i = 0
		for dbelement in olddb:
			i = i + 1
			if withtimestamp == True:
				curdate = str(datetime.now())
				dbelement['timestamp'] = curdate
			newdb.insert(dbelement)
			print("Taking care of the " + dbname + " database... (" + str(i) + "/" + str(len(olddb)) + ")", end="\r")
		print("The " + dbname + " database has been encrypted!                   ")


print("\n\nHello, and welcome to the Reto 1.6 Update!\nThis update adds ENCRYPTION, so the owner of the bot can't read the messages sent, amongst other things.\nThis means that the previously open databases need to be manually migrated.\nThis script hopefully helps smoothen out the process!")
print("\n\nDo note that this will only INSERT, not UPSERT values into the new encrypted files.\nThis will lead to duplicated values, so we will only run this code if the DB is completely empty.\nNeed to run this again? Delete the .reto files at the /db directory!\nAdditionally, this may take a little while. Sit back, have a cup of tea - or a beer, if that's more your thing.")

question = yes_or_no("\nAre you sure you want to proceed?")
if question == False:
	exit()

# DB MIGRATION

print("\n\n------------\n\n")

# I struggled for about an hour trying to find a more optimized way to do this.
# (Function-saving in dictionaries is a pain.)
# Luckily this runs OUTSIDE of Reto, so I can hard-code this a tiny bit.
# Future employers, please don't look at this. You may just have a heart attack. <3

update_database(olddb,newdb,"DB/PROFILE", False)
#update_database(oldcfg,newcfg,"CONFIGS", False)
update_database(oldsrv,newsrv,"SERVER", False)
update_database(oldactivity,newactivity,"ACTIVITY", False),
update_database(oldcustomprefix,newcustomprefix,"CUSTOM PREFIX", False)
update_database(oldbest,newbest,"BEST-OF NAMES", False)
update_database(oldpriv,newpriv,"PRIVACY BLACKLIST", False)
update_database(oldchan,newchan,"CHANNEL SETTINGS", False)
update_database(oldpost,newpost,"COMMENTS", True)