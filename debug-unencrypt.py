# Imports
from tinydb import TinyDB, Query, where
from tinydb.operations import add, subtract, delete
import tinydb_encrypted_jsonstorage as tae
import re
import sys

import os.path
from os.path import join as join_path
from os.path import exists

# Dependencies and databases
cfg = TinyDB("json/config.json")
key = "" # Bring your own Encryption Key.

if not os.path.exists('export/'):
    os.mkdir('export')

filename = "post.json"
filepath = "export/" + filename

print("\nDatabase Debugging Tool")

question = input("\nInput the line to seek: ")
if question == False:
	exit()

with open(filepath, "r", encoding="utf-8") as readJson:
    data = readJson.read()
    debugQuery = data[int(question):]
    print(debugQuery[:200])