import discord
from discord.ui import Button, View
from discord.utils import get
from yt_dlp import YoutubeDL
from googleapiclient.discovery import build
import asyncio
import os
from mutagen.mp3 import MP3
import requests
import json
import time

TOKEN ='TOKEN' #디스코드 봇 토큰
API_KEY = 'API_KEY' #구글 api 키키
music_dir = './music'
admin_id = 788053153391575040
channel_id = 1136967222363963462
embed_message = None
music_count = 0
message_count1 = 0
message_count2 = 0
music_list = []
url_list = []

client = discord.Client(intents=discord.Intents.all())

class MusicQueue:
    def __init__(self):
        self.queue = []

    def add_to_queue(self, title):
        self.queue.append(title)

    def get_next_title(self):
        return self.queue.pop(0) if self.queue else None

music_queue = MusicQueue()

@client.event
async def on_ready():
    global embed_message
    global button_callbacks
    global message_count1
    global message_count2
    message_counts2 = 0
    channel = client.get_channel(channel_id)

    if message_count1 == 0:
        message_count1 += 1
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Music🎵"))
        async def button_callback(interaction):
            member = interaction.guild.get_member(interaction.user.id)
            if member.voice is None:
                await interaction.response.send_message(embed=red3, ephemeral=True)
            else:
                await interaction.response.send_message(embed=red1, ephemeral=True)
        button_callbacks = [button_callback]*4
        map_buttons_to_callbacks(button_list1, button_callbacks)
        view = View(timeout=None)
        add_buttons_to_view(view, button_list1)
        embed_message = await channel.send(embed=blue1, view=view)
    else:
        async def button_callback(interaction):
            member = interaction.guild.get_member(interaction.user.id)
            if member.voice is None:
                await interaction.response.send_message(embed=red3, ephemeral=True)
            else:
                await interaction.response.send_message(embed=red1, ephemeral=True)
        async def _button_callback(interaction):
            await interaction.response.defer()
            await embed_message.delete()
            await asyncio.sleep(1)
            if os.path.exists(music_dir):
                for file in os.scandir(music_dir):
                    os.remove(file)
                    print(file)
            await client.close()
        button_callbacks.append(_button_callback)
        map_buttons_to_callbacks(button_list2, button_callbacks)
        view = View(timeout=None)
        add_buttons_to_view(view, button_list2)
        await embed_message.edit(embed=blue1, view=view)

@client.event
async def on_message(message):
    global music_count
    if message.author == client.user:
        return

    if message.channel.id == channel_id:
        global embed_message
        global url
        global message_count2
        if message.author.voice is None:
            await message.channel.purge(limit=1)
            embed = await message.channel.send(embed=red2)
            await asyncio.sleep(6)
            await embed.delete()
        else:
            if message_count2 == 0:
                asyncio.run_coroutine_threadsafe(embed_message.edit(embed=blue2), client.loop)
            await message.channel.purge(limit=1)

            voice_channel = message.author.voice.channel

            if message.guild.voice_client is None:
                await voice_channel.connect()
            else:
                await message.guild.voice_client.move_to(voice_channel)

            title = message.content
            url = get_music_url(title)
            url_list.append(url)
            dl_music(title, url)
            music_queue.add_to_queue(title)

            vc = discord.utils.get(client.voice_clients, guild=message.guild)

        def play_next(_):
            global music_count
            next_title = music_queue.get_next_title()
            
            if next_title is not None:
                
                info = get_music_info(next_title, url_list[music_count])
                embed = info_embed(info, url_list[music_count])
                asyncio.run_coroutine_threadsafe(embed_message.edit(embed=embed), client.loop)
                music_count += 1
                source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f'{music_dir}/{next_title}.mp3'))
                vc.play(source, after=play_next)
            else:
                asyncio.run_coroutine_threadsafe(on_ready(), client.loop)

        if not vc.is_playing() and not vc.is_paused():
            message_count2 += 1
            next_title = music_queue.get_next_title()
            if next_title is not None:
                async def button_callback1(interaction):
                    await interaction.response.defer()
                    if vc and vc.is_playing():
                        vc.stop()
                async def button_callback2(interaction):
                    message_count2 = 0
                    await vc.disconnect()
                    await on_ready()
                    await interaction.response.defer()
                    embed = await interaction.channel.send(embed=green1(interaction.user), reference=interaction.message)
                    await asyncio.sleep(6)
                    await embed.delete()
                async def button_callback3(interaction):
                    await interaction.response.defer()
                    if vc and vc.is_playing():
                        vc.pause()
                    else:
                        vc.resume()
                async def button_callback4(interaction):
                    await interaction.response.defer()
                    if vc and vc.is_paused():
                        vc.resume()
                async def button_callback5(interaction):
                    await interaction.response.defer()
                    await message.channel.purge(limit=1)
                    await vc.disconnect()
                    await asyncio.sleep(1)
                    if os.path.exists(music_dir):
                        for file in os.scandir(music_dir):
                            os.remove(file)
                            print(file)
                    await client.close()
                button_callbacks = [button_callback1, button_callback2, button_callback3, button_callback4, button_callback5]
                map_buttons_to_callbacks(button_list2, button_callbacks)
                view = View(timeout=None)
                add_buttons_to_view(view, button_list2)

                info = get_music_info(next_title, url_list[music_count])
                embed = info_embed(info, url_list[music_count])
                asyncio.run_coroutine_threadsafe(embed_message.edit(embed=embed, view=view), client.loop)
                music_count += 1
                source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f'{music_dir}/{next_title}.mp3'))
                vc.play(source, after=play_next)

def dl_music(title, url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'music/'+title,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)

def get_music_url(q):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    request = youtube.search().list(
        part='snippet',
        maxResults=1,
        q=q
    )
    response = request.execute()
    video = response['items'][0]
    return f'https://www.youtube.com/watch?v={video["id"]["videoId"]}'

def get_music_info(title, url):
    response = json.loads(requests.get(f'https://www.youtube.com/oembed?url={url}').text)
    tit = response['title']
    thu = response['thumbnail_url']
    sec = MP3(f'{music_dir}/{title}.mp3').info.length
    min = int(sec) // 60
    sec %= 60
    len = f"{min}분 {int(sec)}초"
    return [tit, thu, len]

def map_buttons_to_callbacks(buttons, callbacks):
    for button, callback in zip(buttons, callbacks):
        button.callback = callback
def add_buttons_to_view(view, buttons):
    for button in buttons:
        view.add_item(button)

def info_embed(info, url):
    return discord.Embed(
        title=info[0],
        url=url,
        description=info[2],
        color=0x1E8FFF
    ).set_image(url=info[1])

button1 = Button(label="▷|", style = discord.ButtonStyle.grey)
button2 = Button(label="■", style = discord.ButtonStyle.grey)
button3 = Button(label="▶❚❚", style = discord.ButtonStyle.grey)
button4 = Button(label="≣", style = discord.ButtonStyle.grey)
button5 = Button(label="⭘", style = discord.ButtonStyle.grey)
button_list1 = [button1, button2, button3, button4]
button_list2 = [button1, button2, button3, button4, button5]
button_callbacks = []

red1 = discord.Embed(
    title='현재 재생 중인 곡이 없어요.',
    color=0xE00000
)
red2 = discord.Embed(
    title='이 명령어를 사용하려면 음성채널에 있어야 해요.',
    color=0xE00000
)
red3 = discord.Embed(
    title='**이 버튼을 사용하려면 음성채널에 있어야 해요!**',
    color=0xE00000
)
def green1(interaction_user):
    return discord.Embed(
        title='음악을 정지했어요.',
        color=0x57F288
    ).set_footer(
        text=interaction_user.name,
        icon_url=interaction_user.avatar.url
    )
blue1 = discord.Embed(
    title='현재 재생중인 곡이 없습니다.',
    description='',
    color=0x1E8FFF
).set_image(url='https://ifh.cc/g/CL81a5.jpg')
blue2 = discord.Embed(
    title='잠시만 기다려주세요..',
    color=0x1E8FFF
)

client.run(TOKEN)
