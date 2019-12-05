import discord
from discord.ext import commands
import datetime
import requests
import random
import math
import time
from discord.ext.commands import errors, converter
from random import randint, choice as rnd
import aiohttp
import asyncio
import json
import os
import config
from pymongo import MongoClient
import pymongo
import string
import food

client = MongoClient(config.mongo_client)
db = client['siri']

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.prefix = 'r!'

        
    @commands.command(aliases=['User', 'Profile', 'profile'])
    async def user(self, ctx, user:discord.User=None):
        if not user:
            user = ctx.author
        post = db.market.find_one({"owner": int(user.id)})
        embed = discord.Embed(colour=0xa82021, description=str(user))
        embed.set_author(icon_url=user.avatar_url_as(format='png'), name="User Stats")
        embed.set_thumbnail(url=user.avatar_url_as(format='png'))
        embed.add_field(name="Restaurant", value=post['name'])
        embed.add_field(name="Money", value="$" + str(post['money']))
        await ctx.send(embed=embed)
        
    @commands.command(aliases=['Balance', 'bal'])
    async def balance(self, ctx, user:discord.User=None):
        if not user:
            user = ctx.author
        post = db.market.find_one({"owner": int(user.id)})
        await ctx.send(f"**{user.name}**'s balance is **${post['money']}**.")
                       
    @commands.command(pass_context=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def donate(self, ctx, user: discord.User=None, count:int=None):
        posts_user = db.market.find_one({"owner": user.id})
        posts = db.market.find_one({"owner": ctx.author.id})                          

        if ctx.author == user:
            await ctx.send("You cannot donate money to yourself!")
                       
        elif not count or not user:
            await ctx.send("You must include both the user and the amount of money. Example: `r!donate @lukee#0420 25`")

        elif count < 0:
            await ctx.send(f"You can't donate under **$1**.")

        elif posts['money'] < count:
            await ctx.send(f"You don't have enough money.")

        elif posts_user is None:
            await ctx.send(f"**{user.name}** doesn't have an account.")

        elif not posts is None:
            await self.add_money(user=user.id, count=count)
            await self.take_money(user=ctx.author.id, count=count)
            await ctx.send(f"{user.mention}, **{ctx.message.author}** has donated **${count}** to you.")
        else:
            await ctx.send("You don't have an account. Create one by doing `r!start`.") 
                       
    @commands.command(pass_context=True, aliases=['Daily'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def daily(self, ctx):
        posts = db.market.find_one({"owner": ctx.author.id})                          
        count = 200   
        if posts:
            await self.add_money(user=ctx.author.id, count=count)
            await ctx.send(f"{ctx.author.mention}, you've received your daily **${count}**.")
        else:
            await ctx.send("You don't have an account. Create one by doing `r!start`.") 
                       
    @commands.command(aliases=['Work'])
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def work(self, ctx):
        posts = db.utility.find_one({"utility": "res"})
        user = db.market.find_one({"owner": ctx.author.id})
        country = str(user['country'])
        rm = rnd(posts['resp'])
        count = 0
        r1 = rnd(food.food[country])
        r2 = rnd(food.food[country])
        r3 = rnd(food.food[country])
        r4 = rnd(food.food[country])
        if 'ITEM' in rm and not 'ITEM2' in rm:
            count = r1['money']
            msg = str(rm).replace("ITEM", r1).replace("COUNT", count)
            await self.add_money(user=ctx.author.id, count=count)
        elif 'ITEM2' in rm and not 'ITEM4' in rm:
            count = r1['money']+r2['money']+r3['money']
            msg = str(rm).replace("ITEM", r1).replace("ITEM2", r2).replace("ITEM3", r3).replace("COUNT", count)
            await self.add_money(user=ctx.author.id, count=count)
        else:
            count = r1['money']+r2['money']+r3['money']+r4['money']
            msg = str(rm).replace("ITEM", r1).replace("ITEM2", r2).replace("ITEM3", r3).replace("ITEM4", r4).replace("COUNT", count)
            await self.add_money(user=ctx.author.id, count=count)
        if 'TIP' in rm and not 'TIP2' in rm:
            tpc = random.randint(2,4)
            msg = msg.replace("TIP", tpc)
            await self.add_money(user=ctx.author.id, count=tpc)
        else:
            tpc = random.randint(8,10)
            msg = msg.replace("TIP", tpc)
            await self.add_money(user=ctx.author.id, count=tpc)
                       
        await ctx.send(embed=f"{ctx.author.mention}, {msg}")
        

    async def add_money(self, user:int, count):
        data = db.market.find_one({"owner": user})
        bal = data['money']
        money = int(bal) + count
        db.market.update_one({"owner": user}, {"$set":{"money": money}})

    async def take_money(self, user:int, count:int):
        data = db.market.find_one({"owner": user})
        bal = data['money']
        money = int(bal) - count
        db.market.update_one({"owner": user}, {"$set":{"money": money}})
                    

def setup(bot):
    bot.add_cog(Shop(bot))
