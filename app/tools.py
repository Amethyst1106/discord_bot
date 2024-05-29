import discord
from PIL import Image
import aiohttp
from io import BytesIO
from pydub import AudioSegment
import requests

# 質問の整形
def form_question(name, text):
    return "from : " + name + "\n" + text + "\n\n"

#画像と音声のファイルとembedを取得
async def get_files_and_embed(image = None, audio = None):
    embed = None
    files = []
    if not(image is None and audio is None):
        embed = discord.Embed(title="送信ファイル", color=0xff0000)
    if image is not None:
        embed.set_image(url=image.url)
        image_file = await get_image_file(image)
        files.append(image_file)
    if audio is not None:
        embed.add_field(name="音声ファイル", value=f"[ダウンロードリンク]({audio.url})", inline=False)
        audio_file = await get_audio_file(audio)
        files.append(audio_file)
    return files, embed

# 画像の処理
async def get_image_file(image):
    data = requests.get(image.url)
    async with aiohttp.ClientSession() as session:
        async with session.get(image.url) as response:
            data = await response.read()
            image_file = Image.open(BytesIO(data))
    return image_file

# 音声の処理
async def get_audio_file(audio):
    data = requests.get(audio.url)
    async with aiohttp.ClientSession() as session:
        async with session.get(audio.url) as response:
            data = await response.read()
            audio_file = AudioSegment.from_file(BytesIO(data))
    return audio_file