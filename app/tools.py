import discord
import google.generativeai as genai
from PIL import Image
import aiohttp
from io import BytesIO
import asyncio

# 質問の整形
def form_question(name, text):
    return "from : " + name + "\n" + text + "\n\n"

# 画像のファイルとembedを取得
async def get_files_and_embed(file = None):
    embed = None
    files = []
    if file is not None and "image" in file.content_type :
        embed = discord.Embed(title="送信ファイル", color=0xff0000)
        embed.set_image(url=file.url)
        image_file = await get_image_file(file)
        files.append(image_file)
    return files, embed

# 画像の処理
async def get_image_file(image):
    async with aiohttp.ClientSession() as session:
        async with session.get(image.url) as response:
            data = await response.read()
            image_file = Image.open(BytesIO(data))
    return image_file


# 送信可能なファイルにする
async def to_discord_file(file):
    file_data = await file.read()
    discord_file = discord.File(BytesIO(file_data), filename=file.filename)
    return discord_file

# 動画・音声の処理
async def upload_file(file):
    file_bytes = await file.read()
    file_name = "temp_video.mp4" if "video" in file.content_type\
            else "temp_audio.mp3"
    
    # 一時ファイルに保存
    with open(file_name, "wb") as temp_file:
        temp_file.write(file_bytes)
    
    # アップロード
    uploaded_file = await wait_for_processed(file_name)
    return uploaded_file

# アップロード完了を待つ関数
async def wait_for_processed(file_name):
    uploaded_file = genai.upload_file(file_name)
    await asyncio.sleep(4)
    uploaded_file = genai.get_file(uploaded_file.name)
    return uploaded_file