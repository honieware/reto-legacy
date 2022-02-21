# Import global variables and databases.
from definitions import botname

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

# sharedFunctions
from sharedFunctions import printLeaderboard, createLeaderboardEmbed, getProfile, sendErrorEmbed

# ----------------------------------------------------------------------------------------------

class Help(commands.Cog):
    """
    How to get support, find out about the bot's commands and more.
    """
    def __init__(self, client):
        self.client = client
        client.remove_command('help')


    @commands.command(pass_context=True)
    @commands.has_permissions(add_reactions=True,embed_links=True)
    async def help(self,ctx,*cog):
        """Gets all cogs and commands of mine."""
        if not cog:
            """Cog listing.  What more?"""
            halp=discord.Embed(title=botname + "'s Commands",
                               description="Use `?help *category*` to find out more about each command!\n_(Don't know where to start? Use ?setup to get everything going!)_\nIf you're in need of assistance, [join our support server](https://discord.gg/RAwfrty)!")
            cogs_desc = ''
            for x in self.client.cogs:
                if (x != "Reaction") and (x != "Management"):
                    halp.add_field(name=x,value=self.client.cogs[x].__doc__,inline=True)
            cmds_desc = ''
            for y in self.client.walk_commands():
                if not y.cog_name and not y.hidden:
                    cmds_desc += ('{} - {}'.format(y.name,y.help)+'\n')
            await ctx.message.add_reaction(emoji='✉')
            await ctx.message.author.send('',embed=halp)
        else:
            """Helps me remind you if you pass too many args."""
            if len(cog) > 1:
                halp = discord.Embed(title='Error!',description='That is too many a category!',color=discord.Color.red())
                await ctx.message.author.send('',embed=halp)
            else:
                splice = cog[0]
                cog = splice[0].upper() + splice[1:].lower()
                #printing commands of cog
                """Command listing within a cog."""
                found = False
                #finding Cog
                for x in self.client.cogs:
                    #for y in cog:
                    if x == cog: 
                        #making title
                        halp=discord.Embed(title=cog+' - Commands',description=self.client.cogs[cog].__doc__, color=discord.Color.green())
                        for c in self.client.get_cog(cog).get_commands():
                            if not c.hidden: #if cog not hidden
                                halp.add_field(name=c.name,value=c.help,inline=False)
                        found = True
                if not found:
                    """Reminds you if that cog doesn't exist."""
                    halp = discord.Embed(title='Error!',description='Is "'+cog[0]+'" a valid category?',color=discord.Color.red())
                else:
                    await ctx.message.add_reaction(emoji='✉')
                await ctx.message.author.send('',embed=halp)
        
def setup(client):
    client.add_cog(Help(client))