#!/usr/bin/env python3

import discord
from imgurpython import ImgurClient
import json
import random

with open('creds.json') as f:
    creds = json.loads(f.read())

DISCORD_TOKEN = creds['discord']['token']
DISCORD_CLIENT = discord.Client()

IMGUR_CLIENT_ID = creds['imgur']['client_id']
IMGUR_CLIENT_SECRET = creds['imgur']['client_secret']
IMGUR_CLIENT = ImgurClient(IMGUR_CLIENT_ID, IMGUR_CLIENT_SECRET)


def random_corgi_imgur():
    rpage = random.randint(0, 99)
    corgi = random.choice(IMGUR_CLIENT.gallery_search('corgi', page=rpage))
    if corgi.is_album:
        corgi = random.choice(IMGUR_CLIENT.get_album_images(corgi.id))
    return corgi.link


@DISCORD_CLIENT.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == DISCORD_CLIENT.user:
        return

    if message.content.startswith('$corgi'):
        # corgi image
        msg = random_corgi_imgur()
        await message.channel.send(msg)

    elif 'corg' in message.content:
        msg = 'corgi!'
        await message.channel.send(msg)


@DISCORD_CLIENT.event
async def on_ready():
    print('Logged in as')
    print(DISCORD_CLIENT.user.name)
    print(DISCORD_CLIENT.user.id)
    print('------')


if __name__ == '__main__':
    DISCORD_CLIENT.run(DISCORD_TOKEN)
