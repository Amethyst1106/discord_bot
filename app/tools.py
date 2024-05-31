import discord
from PIL import Image
import aiohttp
from io import BytesIO

# 質問の整形
def form_question(name, text):
    return "from : " + name + "\n" + text + "\n\n"

#画像のファイルとembedを取得
async def get_files_and_embed(image = None):
    embed = None
    files = []
    if not(image is None):
        embed = discord.Embed(title="送信ファイル", color=0xff0000)
    if image is not None:
        embed.set_image(url=image.url)
        image_file = await get_image_file(image)
        files.append(image_file)
    return files, embed

# 画像の処理
async def get_image_file(image):
    async with aiohttp.ClientSession() as session:
        async with session.get(image.url) as response:
            data = await response.read()
            image_file = Image.open(BytesIO(data))
    return image_file