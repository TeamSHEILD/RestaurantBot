import discord
from discord.ext import commands
import datetime
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
import requests
import trivia

client = MongoClient(config.mongo_client)
db = client['siri']

class User(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.prefix = 'r!'


    @commands.command(aliases=['User', 'Profile', 'profile'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def user(self, ctx, user:discord.User=None):
        if not user:
            user = ctx.author
        post = db.market.find_one({"owner": int(user.id)})
        if post:
            embed = discord.Embed(colour=0xa82021, description=str(user))
            embed.set_author(icon_url=user.avatar_url_as(format='png'), name="User Stats")
            embed.set_thumbnail(url=user.avatar_url_as(format='png'))
            embed.add_field(name="Restaurant", value=post['name'])
            embed.add_field(name="Money", value="$" + str(post['money']))
            await ctx.send(embed=embed)
        else:
            await ctx.send("This user doesn't have a restaurant")

    @commands.command(aliases=['Balance', 'bal'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def balance(self, ctx, user:discord.User=None):
        if not user:
            user = ctx.author
        post = db.market.find_one({"owner": int(user.id)})
        if post:
            bal = format(post['money'], ",d")
            await ctx.send(f"**{user.name}**'s balance is **${bal}**.")
        else:
            await ctx.send("This user doesn't have a restaurant")

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

        elif not posts['money'] >= count:
            await ctx.send(f"You don't have enough money.")

        elif posts_user is None:
            await ctx.send(f"**{user.name}** doesn't have a restaurant.")

        elif not posts is None:
            await self.add_money(user=user.id, count=count)
            await self.take_money(user=ctx.author.id, count=count)
            await ctx.send(f"{user.mention}, **{ctx.message.author}** has donated **${count}** to you.")
        else:
            await ctx.send("You don't have a restaurant. Create one by doing `r!start`.")

    @commands.command(pass_context=True, aliases=['Daily'])
    @commands.cooldown(1,86400, commands.BucketType.user)
    async def daily(self, ctx):
        posts = db.market.find_one({"owner": ctx.author.id})
        patrons = db.utility.find_one({"utility": "patrons"})
        if posts:
            ri = random.randint(1,11)
            rci = random.randint(150, 250)
            if ctx.author.id in patrons['bronze']:
                rci *= 1.2
                rci = round(rci)
            elif ctx.author.id in patrons['silver']:
                rci *= 1.4
                rci = round(rci)
            elif ctx.author.id in patrons['gold']:
                rci *= 1.6
                rci = round(rci)
            elif ctx.author.id in patrons['diamond']:
                rci *= 1.7
                rci = round(rci)
            if 'worker' in data:
                if data['worker']:
                    rci = rci - 50
            else:
                pass
            chest = [f'{rci} Cash']
            #if ri == 10:
                #chest.append('x1.1 EXP boost for 24 hours (No use yet.)')
                #db.market.update_one({"owner": ctx.author}, {"$push":{"inventory": {"boost": {"type":"experience", "multiply":1.1, "time":24}}}})
            #else:
                #pass
            await self.add_money(user=ctx.author.id, count=rci)
            embed = discord.Embed(colour=0xa82021, description="\n".join(chest) + "\n\nWant even more money? Vote for me on [Discord Bot List](https://top.gg/bot/648065060559781889), and do `r!votereward` to receive another chest.")
            embed.set_thumbnail(url="http://pixelartmaker.com/art/f6d46bd306aacfd.png")
            embed.set_footer(text="Come back in 24 hours!")
            await ctx.send(embed=embed, content=f"{ctx.author.mention}, you opened your daily chest and received...")
        else:
            await ctx.send("You don't have a restaurant. Create one by doing `r!start`.")

    @commands.command(aliases=['Inventory', 'inv'])
    async def inventory(self, ctx, page=1):
        post = db.market.find_one({"owner": ctx.author.id})
        if post:
            embed = discord.Embed(colour=0xa82021)
            embed.set_author(icon_url=ctx.author.avatar_url_as(format='png'), name="Your Inventory")
            names = []
            items_per_page = 12
            pages = math.ceil(len(post['inventory']) / 12)
            start = (page - 1) * 12
            end = start + 12
            for x in post['inventory'][start:end]:
                if 'colour' in x:
                    names.append(f"<:ColourIcon:659418340703469584> {x['colour']['colour']} ({x['colour']['rarity']})")
                elif 'banner' in x:
                    names.append(f"<:BannerIcon:657457820295495699> {x['banner']['name']} ({x['banner']['rarity']}) [[View]]({x['banner']['url']})")
                else:#if 'boost' in x:
                    pass#names.append(f"<:EarningsBoost:651474110022418433> {x['boost']['name']} ({x['banner']['rarity']}) [[View]]({x['banner']['url']})")
            if names:
                embed.description = "\n".join(names)
            else:
                embed.description = "Nothing to see here."
            np = page+1
            embed.set_footer(text=f"Page {page} of {pages} | r!inventory {np} to see the next page")
            await ctx.send(embed=embed)
        else:
            await ctx.send("You don't have a restaurant! Create one with `r!start`.")

    @commands.command(aliases=['Dine', 'Eat', 'eat'])
    @commands.cooldown(1,30, commands.BucketType.user)
    async def dine(self, ctx, *, restaurant=None):
        post = db.market.find_one({"owner":ctx.author.id})
        def nc(m):
            return m.author == ctx.message.author
        if not restaurant:
            self.bot.get_command("dine").reset_cooldown(ctx)
            await ctx.send("You didn't include a restaurant! Example: `r!dine @lukee#0420` or `r!dine McDonalds`.")
        if ctx.message.mentions:
            if len(ctx.message.mentions) >= 2:
                res = db.market.find_one({"owner":ctx.message.mentions[0].id})
            else:
                res = db.market.find_one({"owner":ctx.message.mentions[0].id})
        elif db.market.find_one({"name": restaurant}):
            res = db.market.find_one({"name": restaurant})
        else:
            res = None
        if res['owner'] == ctx.author.id:
            self.bot.get_command("dine").reset_cooldown(ctx)
            await ctx.send("You can't dine in at your own restaurant.")
        elif res:
            items = []
            for x in res['items']:
                items.append(x['name'])
            li = ', '.join(items)
            embed = discord.Embed(colour=0xa82021, description=f"Welcome to {res['name']}!\n\nWhich item would you like to order?\n\n**Menu**: {li}")
            embed.set_footer(text='You have 90 seconds to respond with a menu item.')
            cmsg = await ctx.send(embed=embed)
            chi = await self.bot.wait_for('message', check=nc, timeout=90)
            await cmsg.delete()
            try:
                await chi.delete()
            except:
                pass
            newi = []
            for x in res['items']:
                if x['name'] == chi.content:
                    newi.append(x)
            if chi.content in items:
                item = newi[0]
                if post['money'] >= item['price']:
                    rxp = round(1.2*item['price'])
                    await self.take_money(ctx.author.id, item['price'])
                    c = await self.add_exp(ctx.author.id, rxp)
                    await ctx.send(f"You've ordered a {item['name']} from {res['name']} for ${item['price']}. You've earned {c} EXP for dining in.")
                    await self.add_money(res['owner'], round(item['price']/1.8))
                    await self.add_sold(res['owner'], item['name'])
                else:
                    self.bot.get_command("dine").reset_cooldown(ctx)
                    await ctx.send("You don't have enough money for this.")
            else:
                self.bot.get_command("dine").reset_cooldown(ctx)
                await ctx.send("That item is not on the menu.")
        else:
            self.bot.get_command("dine").reset_cooldown(ctx)
            await ctx.send("I couldn't find that restaurant. Try tagging the owner instead.")

    @commands.command(aliases=['Use'])
    @commands.cooldown(1,10, commands.BucketType.user)
    async def use(self, ctx, *, item):
        post = db.market.find_one({"owner": ctx.author.id})
        item = item.lower().replace("(uncommon", "").replace("(common)", "").replace("uncommon", "").replace("common", "")
        w = True
        if post:
            w = []
            for x in post['inventory']:
                if 'colour' in x:
                    if w:
                        pass
                    elif x['colour']['colour'].lower() == item.lower():
                        await asyncio.sleep(1)
                        db.market.update_one({"owner": ctx.author.id}, {"$set": {"colour": x['colour']['hex']}})
                        w.append(1)
                    else:
                        pass
                elif 'banner' in x:
                    if w:
                        pass
                    elif x['banner']['name'].lower() == item.lower():
                        await asyncio.sleep(1)
                        db.market.update_one({"owner": ctx.author.id}, {"$set": {"banner": x['banner']['url']}})
                        w.append(1)
                    else:
                        pass
                else:#if 'boost' in x:
                    pass#names.append()
            if not w:
                await ctx.send("I could not find that in your inventory. Please only include the item name.")
            else:
                await ctx.send("Item used successfully.")
        else:
            await ctx.send("You don't have a restaurant! Create one with `r!start`.")

    @commands.command(aliases=['Se2ll'])
    async def se2ll(self, ctx, *, item):
        post = db.market.find_one({"owner": ctx.author.id})
        item = item.lower().replace("(uncommon", "").replace("(common)", "").replace("uncommon", "").replace("common", "")
        w = True
        if post:
            for x in post['inventory']:
                if 'colour' in x:
                    if x['colour']['colour'].lower() == item:
                        await asyncio.sleep(1)
                        db.market.update_one({"owner": ctx.author.id}, {"$set": {"colour": None}})
                elif 'banner' in x:
                    if x['banner']['name'].lower() == item:
                        await asyncio.sleep(1)
                        db.market.delete_one({"owner": ctx.author.id}, {"$set": {"banner": None}})
                else:#if 'boost' in x:
                    w = False#names.append()
            if not w:
                await ctx.send("I could not find that in your inventory. Please only include the item name.")
            else:
                await ctx.send("Item sold successfully for")
        else:
            await ctx.send("You don't have a restaurant! Create one with `r!start`.")

    @commands.command(pass_context=True, aliases=['Votereward'])
    @commands.cooldown(1, 43200, commands.BucketType.user)
    async def votereward(self, ctx): #http://pixelartmaker.com/art/f697739d6ed8a4b.png
        posts = db.market.find_one({"owner": ctx.author.id})
        rci = random.randint(50,100)
        r = requests.get(f"https://discordbots.org/api/bots/648065060559781889/check?userId={ctx.author.id}", headers={"Authorization": config.dbl_token}).json()
        if posts:
            if r['voted'] == 1:
                await self.add_money(user=ctx.author.id, count=rci)
                embed = discord.Embed(colour=0x7289da, description=f"{rci} Cash")
                embed.set_thumbnail(url="http://pixelartmaker.com/art/f697739d6ed8a4b.png")
                embed.set_footer(text="Thanks for upvoting! Come back in 12 hours!")
                await ctx.send(embed=embed, content=f"{ctx.author.mention}, you opened your DBL chest and received...")
            else:
                await ctx.send("You haven't upvoted! Upvote here: <https://top.gg/bot/648065060559781889/vote>")
                self.bot.get_command("votereward").reset_cooldown(ctx)
        else:
            await ctx.send("You don't have a restaurant. Create one by doing `r!start`.")

    @commands.command(aliases=['Trivia'])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def trivia(self, ctx):
        post = db.market.find_one({"owner": ctx.author.id})
        if not post:
            await ctx.send("You don't have a restaurant! Create one with `r!start`.")
        else:
            embed = discord.Embed(colour=0xa82021)
            question = rnd(trivia.questions)
            letters = ["a", "b", "c", "d"]
            cn = 0
            desc = ""
            choices = []
            for x in question['answers']:
                cn += 1
                if cn == 1:
                    choices.append({"a":question['answers'][0], "letter": "a"})
                elif cn == 2:
                    choices.append({"b":question['answers'][1], "letter": "b"})
                elif cn == 3:
                    choices.append({"c":question['answers'][2], "letter": "c"})
                else:
                    choices.append({"d":question['answers'][3], "letter": "d"})
            opt = []
            for x in choices:
                letter = x['letter']
                opt.append(f":regional_indicator_{x['letter']}: {x[letter]}")
            answers = "\n".join(opt)
            embed.description = question['question'] + "\n\n" + answers
            embed.set_footer(text="You have 90 seconds to respond with the correct letter.")
            await ctx.send(embed=embed)
            cl = None
            for x in choices:
                letter = x['letter']
                if x[letter] == question['correct']:
                    cl = x['letter']
            b = time.perf_counter()
            msg = await self.bot.wait_for('message', check=lambda x: x.author == ctx.author)
            a = time.perf_counter()
            tt = a-b
            if msg.content.lower() == cl or msg.content.lower() == question['correct'].lower():
                if tt <= 5:
                    await ctx.send("You've answered correctly in under 5 seconds. You've been awarded $10.")
                    await self.add_money(ctx.author.id, 10)
                elif tt <= 10:
                    await ctx.send("You've answered correctly in under 10 seconds. You've been awarded $8.")
                    await self.add_money(ctx.author.id, 8)
                else:
                    await ctx.send("You've answered correctly. You've been awarded $5.")
                    await self.add_money(ctx.author.id, 5)
            else:
                await ctx.send("You've answered incorrectly. You've been awarded $2 for your efforts.")
                await self.add_money(ctx.author.id, 2)



    @commands.command(aliases=['Beg'])
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def beg(self, ctx):
        numb = random.randint(1,5)
        post = db.market.find_one({"owner": ctx.author.id})
        if not post:
            await ctx.send("You don't have a restaurant! Create one with `r!start`.")
        elif numb == 1 or numb == 2:
            await ctx.send("The Bank of Restaria denied your request.")
        else:
            grant = numb*5
            await ctx.send(f"The Bank of Restaria granted you ${grant} for your restaurant.")
            await self.add_money(ctx.author.id, grant)

    @commands.command(aliases=['Donate'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def donation(self, ctx):
        embed = discord.Embed(colour=0xa82021, title="Donate", description="Want to support restaurant AND receive awesome rewards? To donate now or view information on rewards, click [here](https://www.patreon.com/join/paixlukee).")
        await ctx.send(embed=embed)

    @commands.command(pass_context=True, aliases=['Weekly'])
    @commands.cooldown(1,604800, commands.BucketType.user)
    async def weekly(self, ctx):
        posts = db.market.find_one({"owner": ctx.author.id})
        patrons = db.utility.find_one({"utility": "patrons"})
        if posts:
            rci = random.randint(1000, 1700)
            if ctx.author.id in patrons['silver'] or ctx.author.id in patrons['gold'] or ctx.author.id in patrons['diamond']:
                chest = [f'{rci} Cash']
                await self.add_money(user=ctx.author.id, count=rci)
                embed = discord.Embed(colour=0xa82021, description="\n".join(chest) + "\n\nP.S. Thanks for supporting me!")
                embed.set_thumbnail(url="http://pixelartmaker.com/art/134b1292dc645e7.png")
                embed.set_footer(text="Come back in 1 week!")
                await ctx.send(embed=embed, content=f"{ctx.author.mention}, you opened your patron weekly chest and received...")
            else:
                await ctx.send("You must be a silver+ patron to use this command! For more information on restaurant patronage, do `r!donate`.")
                self.bot.get_command("weekly").reset_cooldown(ctx)
        else:
            await ctx.send("You don't have a restaurant. Create one by doing `r!start`.")
            self.bot.get_command("weekly").reset_cooldown(ctx)

    @commands.command(aliases=['Work'])
    @commands.cooldown(1, 480, commands.BucketType.user)
    async def work(self, ctx):
        posts = db.utility.find_one({"utility": "res"})
        patrons = db.utility.find_one({"utility": "patrons"})
        user = db.market.find_one({"owner": ctx.author.id})
        now = datetime.datetime.now()
        db.market.update_one({"owner": ctx.author.id}, {"$set":{"laststock": now.strftime("%d/%m/%Y %H:%M")}})
        if user:
            if ctx.author.id in patrons['bronze']:
                ml = 1.2
            elif ctx.author.id in patrons['silver']:
                ml = 1.4
            elif ctx.author.id in patrons['gold']:
                ml = 1.6
            elif ctx.author.id in patrons['diamond']:
                ml = 1.7
            else:
                ml = 1
            country = str(user['country'])
            rm = rnd(posts['resp'])['text']
            count = 0
            r1 = rnd(food.food[country])
            r2 = rnd(food.food[country])
            r3 = rnd(food.food[country])
            r4 = rnd(food.food[country])
            if 'happy' in rm or 'refused' in rm:
                msg = str(rm).replace("ITEM", r1['name'])
            elif 'ITEM' in rm and not 'ITEM2' in rm:
                count = r1['price']
                count *= ml
                count = round(count)
                msg = str(rm).replace("ITEM", r1['name']).replace("COUNT", "$" + str(count))
                await self.add_money(user=ctx.author.id, count=count)
                await self.add_sold(user=ctx.author.id, sold=r1['name'])
            elif 'ITEM2' in rm and not 'ITEM4' in rm:
                count = r1['price']+r2['price']+r3['price']
                count *= ml
                count = round(count)
                msg = str(rm).replace("ITEM3", r3['name']).replace("ITEM2", r2['name']).replace("ITEM", r1['name']).replace("COUNT", "$" + str(count))
                await self.add_money(user=ctx.author.id, count=count)
                await self.add_sold(user=ctx.author.id, sold=r1['name'])
                await self.add_sold(user=ctx.author.id, sold=r2['name'])
                await self.add_sold(user=ctx.author.id, sold=r3['name'])
            else:
                count = r1['price']+r2['price']+r3['price']+r4['price']
                count *= ml
                count = round(count)
                msg = str(rm).replace("ITEM4", r4['name']).replace("ITEM3", r3['name']).replace("ITEM2", r2['name']).replace("ITEM", r1['name']).replace("COUNT", "$" + str(count))
                await self.add_money(user=ctx.author.id, count=count)
                await self.add_sold(user=ctx.author.id, sold=r1['name'])
                await self.add_sold(user=ctx.author.id, sold=r2['name'])
                await self.add_sold(user=ctx.author.id, sold=r3['name'])
                await self.add_sold(user=ctx.author.id, sold=r4['name'])
            if 'TIP2' in rm:
                tpct = random.randint(8,10)
                tpct *= ml
                tpct = round(tpct)
                if 'worker' in user:
                    if user['worker']:
                        wn = user['worker_name']
                        tpct = tpct + round(tpct*user['worker'][wn][1]['tips'])
                msg = msg.replace("TIP2", "$" + str(tpct))
                await self.add_money(user=ctx.author.id, count=tpct)
            elif 'TIP' in rm:
                tpc = random.randint(2,4)
                tpc *= ml
                tpc = round(tpc)
                if 'worker' in user:
                    if user['worker']:
                        wn = user['worker_name']
                        tpc = tpc + round(tpc*user['worker'][wn][1]['tips'])
                msg = msg.replace("TIP", "$" + str(tpc))
                await self.add_money(user=ctx.author.id, count=tpc)
            if r1['name'].endswith('s') or r1['name'].endswith('gna'):
                nn = r1['name']
            else:
                if r1['name'].startswith(("a", "e", "i", "o", "u")):
                    nn = "an " + r1['name']
                else:
                    nn = "a " + r1['name']
            msg = msg.replace(r1['name'], nn)
            await ctx.send(f"{ctx.author.mention}, {msg}")
        else:
            await ctx.send("You don't have a restaurant. Create one with `r!start`.")


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

    async def add_exp(self, user, count):
        data = db.market.find_one({"owner": user})
        bal = data['exp']
        if 'worker' in data:
            if data['worker']:
                wn = data['worker_name']
                count = count + round(count*data['worker'][wn][0]['exp'])
        exp = int(bal) + count
        db.market.update_one({"owner": user}, {"$set":{"exp": exp}})
        return count
        #if exp <= 500:
            #db.market.update_one({"owner": user.id}, {"$push": {"inventory":{"banner": {"name": "Lovely Hearts", "url": "http://paixlukee.ml/m/AEJSB.jpg", 'rarity': 'Legendary'}}}})
            #await bot.get_user(user).send("Congrats! You've hit 500 EXP with your restaurant! As a gift, the **Legendary** Lovely Hearts banner has been added to your inventory.")

    async def add_sold(self, user, sold):
        item = sold
        data = db.market.find_one({"owner": user})
        it = None
        for x in data['items']:
            if x['name'] == item:
                it = x
        bal = it['sold']
        tc = int(bal) + 1
        db.market.update_one({"owner": user}, {"$pull":{"items": {"name": item, "price": it['price'], "stock": it['stock'], "sold": bal}}})
        db.market.update_one({"owner": user}, {"$push":{"items": {"name": item, "price": it['price'], "stock": it['stock'], "sold": tc}}})


def setup(bot):
    bot.add_cog(User(bot))
