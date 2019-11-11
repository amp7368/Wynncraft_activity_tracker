from datetime import datetime, timedelta
import discord
from json import loads
from json.decoder import JSONDecodeError
from aiohttp import client_exceptions
import traceback
import urllib.request
import urllib.error
import asyncio
import time

PREFIX = "$"
MOJANG_REQUESTS_PER = 450
MOJANG_MINUTES = 10
players_today = dict()
last_updated = [time.time()]
client = discord.Client(max_messages=100)
requests = list()
with open('config.txt') as file:
    p = 0
    for line in file:
        line = line.split("#")[0].strip()
        if p == 0:
            inactivity_bot_id = int(line)
        elif p == 1:
            login = line
        elif p == 2:
            line = line.split(",")
            color = discord.colour.Color.from_rgb(int(line[0]), int(line[1]), int(line[2]))
        elif p == 3:
            debug_person = int(line)
        else:
            break
        p += 1


def strip():
    '''
    removes all requests that were more than MOJANG_MINUTES ago
    :return:
    '''
    for request in requests.copy():
        if request < time.time() - MOJANG_MINUTES * 60:
            requests.remove(request)


@client.event
async def on_message(message):
    '''
    on any message in my discord servers,
    see if a command was said and execute the corresponding command
    :param message:
    :return:
    '''
    try:
        strip()
        if len(players_today) == 0:
            last_updated[0] = time.time()
        if time.time() - last_updated[0] > 24 * 60 * 60:
            for p in list(players_today.keys()):
                players_today.__delitem__(p)
        if message.author.id == inactivity_bot_id or not message.content.startswith(PREFIX):
            return
        if message.content.lower().startswith(PREFIX + 'inactivity'):
            await on_command_inactivity(message)
        elif message.content.lower().startswith(PREFIX + "help"):
            await on_command_help(message)
        elif message.content.lower().startswith(PREFIX + "info"):
            await on_command_info(message)
        elif message.content.lower().startswith(PREFIX + "player_inactivity"):
            await on_command_player_inactivity(message)
        elif message.content.lower().startswith(PREFIX + "player_stats"):
            await on_command_player_stats(message)
    except:
        try:
            await send_trace()
        except:
            pass


async def send_trace():
    string = traceback.format_exc()
    traceback.print_exc()
    msgs = list()
    while True:
        if len(string) < 1998:
            msgs.append(string)
            break
        else:
            msgs.append(str(string[:1998]))
            string = string[1997:]
    for i in msgs:
        try:
            await client.get_user(debug_person).send(i)
        except client_exceptions.ClientOSError:
            await asyncio.sleep(1)
            continue


async def on_command_player_inactivity(message):
    '''
    create an inactivity report for a single player
    :param message: the message that the user sent
    :return:
    '''
    msgs = message.content.split(" ")
    if len(msgs) != 2:
        await correct_command_player_inactivity(message.channel)
    name = msgs[1]
    if name in players_today:
        player = players_today[name]
    else:
        try:
            name = get_uuid(name, time.time() - 60)[0]
        except:
            return
        player = fetch_login(name)
    tim = time_inactive(time.time(), player)
    string = "```ml\n" + '|    ' + "{:<30}".format(" Member") + '|  ' + "{:<23}".format(
        "Time Inactive") + '|' + '\n' + \
             ('+-----' + '-' * 29 + '+' + '-' * 25 + '+\n') + \
             '|    ' + "{:<30}".format(msgs[1]) + '|  ' + "{:<23}".format(
        str(tim) + " Days") + '|' + '\n' + ('+-----' + '-' * 29 + '+' + '-' * 25 + '+\n```')

    try:
        await message.channel.send(string)
    except client_exceptions.ClientOSError:
        pass


async def on_command_player_stats(message):
    '''
    send a report of statistics for a player
    :param message: the message that the user sent
    :return:
    '''
    msgs = message.content.split(" ")
    if len(msgs) != 2:
        await correct_command_player_inactivity(message.channel)
    name = msgs[1]
    try:
        if name in players_today:
            player = players_today[name]
        else:
            try:
                name = get_uuid(name, time.time() - 60)[0]
            except:
                return
            player = fetch_login(name)
    except:
        try:
            await message.channel.send("Failed to get player statistics for " + msgs[1])
        except client_exceptions.ClientOSError:
            pass
        finally:
            return
    tim = time_inactive(time.time(), player)
    player = player['data'][0]
    embed = (discord.Embed(color=color, description=
    "__**" + msgs[1] + '**__\n\n'
                       "**Guild:** " + player['guild']['name'] + '\n' +
    "**Chests Opened:** " + str(player['global']['chestsFound']) + '\n' +
    "**Blocks Walked:** " + str(player['global']['blocksWalked']) + '\n' +
    "**Mobs Killed:** " + str(player['global']['mobsKilled']) + '\n' +
    "**Total Logins:** " + str(player['global']['logins']) + '\n' +
    "**Total Playtime:** " + str(player['meta']['playtime']) + '\n' +
    "**Days Since Last Login:** " + str(tim) + '\n'))
    try:
        await message.channel.send(embed=embed)
    except client_exceptions.ClientOSError:
        pass


async def on_command_help(message):
    '''
    Send a help command in the channel the message was sent
    :param message: the message that the user sent
    '''
    try:
        await message.channel.send(embed=discord.Embed(color=color, description=
        "**" + PREFIX + "help** - shows a list of commands\n" +
        "**" + PREFIX + "info** - shows basic info about the bot\n" +
        "**" + PREFIX + "inacitivty <guild name>** - sends an inacitivty report for the given guild\n" +
        "**" + PREFIX + "player_inactivity <player_name> - sends and inactivity report for the given player"))
    except client_exceptions.ClientOSError:
        pass


async def on_command_info(message):
    '''
    Send an info command in the channel the message was sent
    :param message: the message that the user sent
    :return:
    '''
    try:
        await message.channel.send(embed=discord.Embed(color=color, description=
        "__**CloverBot**__\n" +
        "**Author: ** appleptr16#5054\n" +
        "**CloverBot's discord:** <https://discord.gg/XEyUWu9>\n" +
        "**Release Version:** 1.0\n" +
        "**Testing status** - Alpha (expect bugs)\n" +
        "**Server count:** " + str(len(client.guilds)) + '\n' +
        "**bot invite below**\n" +
        "<https://bit.ly/2MICTec>"))
    except client_exceptions.ClientOSError:
        pass


async def on_command_inactivity(message):
    '''
    Start the inactivity procedure
    because a person inputed that they wanted an inactivity report
    :param message: the message that the user sent
    :return:
    '''
    try:
        msg = message.content.split(" ")

        if len(msg) < 2:
            await correct_command_inacitivity(message.channel)

        string = ''
        for i in msg[1:]:
            string += i + "%20"
        data = fetch_members(string.strip('%20'))
        msgs = await make_message_inactivity(data, message.channel)
        try:
            for m in msgs:
                await message.channel.send(m)
        except client_exceptions.ClientOSError:
            return
    except:
        traceback.print_exc()
        try:
            await message.channel.send("Try again 30 minutes from now")
        except client_exceptions.ClientOSError:
            pass
        return


async def correct_command_player_inactivity(channel):
    '''
    sends the correct usage of the !player_inactivity command
    :param channel: the channel the message should be sent in
    :return:
    '''
    try:
        a = await channel.send("!player_inactivity <player name>")
        del a
    except client_exceptions.ClientOSError:
        pass


async def correct_command_inacitivity(channel):
    '''
    sends the correct usage of the !inactivity command
    :param channel: the channel the message should be sent in
    :return:
    '''
    try:
        a = await channel.send("!inactivity <guild name>")
        del a
    except client_exceptions.ClientOSError:
        pass


def get_uuid(username, time_stamp):
    '''
    get either the uuid or username of the username given
    :param username: the username we are trying to find
    :param time_stamp: the current time
    :return:
    '''
    while len(requests) >= MOJANG_REQUESTS_PER - 1:
        asyncio.sleep(10)
        strip()
    try:
        url = loads(urllib.request.urlopen(
            'https://api.mojang.com/users/profiles/minecraft/' + username + '?at=' + str(int(time.time()))).readline())
        requests.append(time.time())
        uuid = url['id']
        return str(uuid[:9]) + '-' + str(uuid[9:14]) + '-' + str(uuid[14:19]) + '-' + str(uuid[19:24]) + '-' + str(
            uuid[24:]), url['name']
    except JSONDecodeError:
        print("0", username)
        try:
            fetch_login(username)
            return username, username
        except urllib.error.HTTPError:
            print("-1", username)
            while len(requests) >= MOJANG_REQUESTS_PER - 1:
                asyncio.sleep(10)
                strip()
            url = loads(urllib.request.urlopen(
                'https://api.mojang.com/users/profiles/minecraft/' + username + '?at=0').readline())
            requests.append(time.time())
            uuid = url['id']
            return str(uuid[:9]) + '-' + str(uuid[9:14]) + '-' + str(uuid[14:19]) + '-' + str(uuid[19:24]) + '-' + str(
                uuid[24:]), url['name']


async def make_message_inactivity(guild_data, channel):
    '''
    Make a list of messages to be sent of the guilds inactivity report
    :param guild_data: the guild data from the API
    :param channel: the channel to send the messages
    :return: the list of messages of the inactivity report
    '''
    try:
        time_now = guild_data['request']['timestamp']
    except KeyError:
        return ['Not a guild']
    except:
        return ['Failed to get the inactivity list']
    try:
        progress_message = await channel.send('```' + '_' * 100 + '```')
    except client_exceptions.ClientOSError:
        return
    messages = list()

    string_message = '```ml\n'
    string_message += '|    ' + "{:<30}".format(guild_data['name'] + " Members") + '|  ' + "{:<23}".format(
        "Rank") + '|  ' + "{:<23}".format("Time Inactive") + '|' + '\n'
    string_message += ('+-----' + '-' * 29 + '+' + '-' * 25 + '+' + '-' * 25 + '+\n')
    times = dict()
    i = 0
    length = len(guild_data['members'])
    for member in guild_data['members']:
        prog = int(i / length * 100)
        try:
            await progress_message.edit(content=('```' + '=' * prog) + ('_' * (100 - prog)) + '```')
        except (discord.errors.NotFound, discord.errors.Forbidden, client_exceptions.ClientOSError):
            pass

        try:
            if member['name'] in players_today:
                player = players_today[member['name']]
                tim = time_inactive(time_now, player)
            else:
                uuid = member['uuid']
                player = fetch_login(uuid)
                tim = time_inactive(time_now, player)
                players_today[member['name']] = player
            string = "{:<30}".format(member['name']) + '|  ' + "{:<23}".format(
                member['rank'].lower()) + '|  ' + "{:<23}".format(str(tim) + " Days") + '|' + '\n'
        except:  # if anything goes wrong ignore it
            traceback.print_exc()
            tim = -1
            string = "Unavailable \n"

        if tim in times:
            times[tim].append(string)
        else:
            times[tim] = [string]
        i += 1
    try:
        await channel.delete_messages([progress_message])
    except:
        pass
    member_number = 0
    pg = 0
    for t in sorted(times.keys()):
        for i in range(len(times[t])):
            string_message += "{:<5}".format('| ' + str(member_number + 1) + ".") + times[t][i]
            if pg == 14:
                messages.append(string_message + '```')
                string_message = '```ml\n'
                pg = 0
            if pg % 5 == 4:
                string_message += ('+-----' + '-' * 29 + '+' + '-' * 25 + '+' + '-' * 25 + '+\n')
            pg += 1
            member_number += 1
    if string_message != '```ml\n':
        messages.append(string_message + '```')
    return messages


def time_inactive(time_now, player_info):
    '''
    determine how long
    :param time_now: the current time
    :param player_info: the player's information that we are meant to find the time since login for
    :return: how many days the player has been inactive
    '''
    login_time = player_info['data'][0]['meta']['lastJoin']
    login_time = datetime(int(login_time[:4]), int(login_time[5:7]), int(login_time[8:10]), int(login_time[11:13]),
                          int(login_time[14:16]), int(login_time[17:19]))
    time_now = datetime.fromtimestamp(time_now)
    difference = time_now - login_time + timedelta(hours=5)
    return difference.days


def fetch_members(guild_name):
    '''
    get the information for the guild from the API
    :param guild_name: the guild name of which we want the members
    :return: the read JSON API
    '''

    return loads(urllib.request.urlopen(
        'https://api.wynncraft.com/public_api.php?action=guildStats&command=' + guild_name).readline())


def fetch_login(name):
    '''
    get the information for the player from the API
    :param name: the player username
    :return: the read JSON API for the player
    '''
    return loads(urllib.request.urlopen(
        'https://api.wynncraft.com/v2/player/' + name + '/stats').readline())


def client_runner():
    '''
    start the bot
    :return: never
    '''
    while True:
        try:
            client.run(login)
            print("Wow")
        except MemoryError:
            print("ME")
        except Exception as e:
            print(e)
        except:
            pass
        asyncio.sleep(5)


if __name__ == "__main__":
    while True:
        try:
            client_runner()
        except:
            pass
