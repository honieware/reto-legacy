# Imports
from tinydb import TinyDB, Query, where
from tinydb.operations import add, subtract, delete
import tinydb_encrypted_jsonstorage as tae

import os.path
from os.path import join as join_path
from os.path import exists

# Dependencies and databases
cfg = TinyDB("json/config.json")
#key = ADD KEY HERE

if not os.path.exists('export/'):
    os.mkdir('export')

databases = {
    "db": TinyDB(encryption_key=key, path=join_path("db/","profile.reto"), storage=tae.EncryptedJSONStorage),
    "srv": TinyDB(encryption_key=key, path=join_path("db/","srv.reto"), storage=tae.EncryptedJSONStorage),
    "activity": TinyDB(encryption_key=key, path=join_path("db/","activity.reto"), storage=tae.EncryptedJSONStorage),
    "post": TinyDB(encryption_key=key, path=join_path("db/","comments.reto"), storage=tae.EncryptedJSONStorage),
    "priv": TinyDB(encryption_key=key, path=join_path("db/","blacklist.reto"), storage=tae.EncryptedJSONStorage),
    "best": TinyDB(encryption_key=key, path=join_path("db/","best.reto"), storage=tae.EncryptedJSONStorage),
    "dm": TinyDB(encryption_key=key, path=join_path("db/","deletables.reto"), storage=tae.EncryptedJSONStorage),
    "customprefix": TinyDB(encryption_key=key, path=join_path("db/","customprefix.reto"), storage=tae.EncryptedJSONStorage),
    "chan": TinyDB(encryption_key=key, path=join_path("db/","channels.reto"), storage=tae.EncryptedJSONStorage)
}

queries = {
    "db": databases["db"].all(),
    "srv": databases["srv"].all(),
    "activity": databases["activity"].all(),
    "post": databases["post"].all(),
    "priv": databases["priv"].all(),
    "best": databases["best"].all(),
    "dm": databases["dm"].all(),
    "customprefix": databases["customprefix"].all(),
    "chan": databases["chan"].all()
}

# Introduction
def yes_or_no(question):
    reply = str(input(question+' (y/n): ')).lower().strip()
    if reply[0] == 'y':
        return True
    if reply[0] == 'n':
        return False
    else:
        return yes_or_no("\nAre you sure you want to proceed? ")	

print("\nWelcome to the Database Decryption tool!\nThis tool is meant for exporting user data to Reto v2, which uses a MongoDB database.")

question = yes_or_no("\nAre you sure you want to proceed?")
if question == False:
	exit()

print("\n\n------------\n\n")

n = 1

# Export
for name, query in queries.items():
    print("✧ Decrypting " + name + " database... (" + str(n) + "/" + str(len(databases)) + ")")

    if query:
        filename = name + ".json"
        filepath = "export/" + filename
        with open(filepath, "a+", encoding="utf-8") as writeJson:
            writeJson.write(str(query).replace("'", "\"").replace("True", "true").replace("False", "false"))
        # os.remove(filepath)
    n += 1

print("\nDone! You can find the .JSON files over at the /export folder.\nPlace the files of this folder in the /export/legacy path, and use the /import command (as a bot admin) in Reto v2 to import this data.")