import os
from io import BytesIO
from server import server_thread

import discord
import google.generativeai as genai
import requests
from discord import app_commands
from PIL import Image

import ai
from tools import form_question, return_answer, init_AI, reset_history

from logging import getLogger
import logging

logger = getLogger(__name__)
logger.setLevel(logging.INFO)

# Gemini APIの設定
genai.configure(api_key=os.environ['GEMINI_TOKEN'])

safety_settings = [{
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_NONE"
}, {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_NONE"
}, {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_NONE"
}, {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_NONE"
}]
default_config = genai.GenerationConfig(temperature=0.7)

# Geminiモデルの設定
nomal_model_name = "gemini-1.0-pro-latest"
super_model_name = "gemini-1.5-pro-latest"
flash_model_name = "gemini-1.5-flash-latest"
image_model = genai.GenerativeModel("gemini-pro-vision",
                                    safety_settings=safety_settings)

nomal_AIs = {}
super_AIs = {}
flash_AIs = {}

# botの設定
intents = discord.Intents.none()  #スラッシュコマンド以外受け取らない
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    global nomal_AIs, super_AIs, flash_AIs
    for guild in client.guilds:
        nomal_AIs[guild.id] = ai.ChatAI(guild_id=guild.id, version=nomal_model_name)
        super_AIs[guild.id] = ai.ChatAI(guild_id=guild.id, version=super_model_name, name = "上位モデル : ")
        flash_AIs[guild.id] = ai.ChatAI(guild_id=guild.id, version=flash_model_name, name = "高速モデル : ")
    logger.error('{0.user} がログインしたよ'.format(client))
    

#------------------------------nomal------------------------------------
#回答
@tree.command(name="chat", description="送った内容に返答してくれます")
async def return_nomal_answer(interaction: discord.Interaction, text: str):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = nomal_AIs[guild_id].return_answer(interaction, text)
    await interaction.followup.send(result)

#履歴をリセット
@tree.command(name="reset_history", description="通常モデルの記憶をリセットします")
async def reset_history_nomal(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = nomal_AIs[guild_id].reset_history()
    await interaction.followup.send(result)

#プロンプトをリセット
@tree.command(name="reset_prompt", description="命令をリセットします")
async def reset_prompt_nomal(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = nomal_AIs[guild_id].reset_prompt()
    await interaction.followup.send(result)

#プロンプトを追加
@tree.command(name="add_prompt", description="命令を追加します")
async def add_prompt_nomal(interaction: discord.Interaction, prompt: str):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = nomal_AIs[guild_id].add_prompt(prompt)
    await interaction.followup.send(result)

#プロンプトを見る
@tree.command(name="show_prompt", description="命令を表示します")
async def show_prompt_nomal(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = nomal_AIs[guild_id].show_prompt()
    await interaction.followup.send(result)

#プロンプトを消す
@tree.command(name="delete_prompt", description="命令を削除します")
async def delete_prompt_nomal(interaction: discord.Interaction, index: int):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = nomal_AIs[guild_id].delete_prompt(index)
    await interaction.followup.send(result)

# コンフィグを変更する
@tree.command(name="set_config", description="コンフィグを設定します。")
async def set_config_nomal(interaction: discord.Interaction,
                        temperature: float = None):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = nomal_AIs[guild_id].set_config(temperature)
    await interaction.followup.send(result)

#コンフィグを見る
@tree.command(name="show_config", description="コンフィグを表示します")
async def show_config_nomal(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = nomal_AIs[guild_id].show_config()
    await interaction.followup.send(result)


#------------------------------super------------------------------------
#回答
@tree.command(name="super_chat", description="上位モデルが返答してくれます")
async def return_super_answer(interaction: discord.Interaction, text: str):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = super_AIs[guild_id].return_answer(interaction, text)
    await interaction.followup.send(result)

#履歴をリセット
@tree.command(name="reset_history_super", description="上位モデルの記憶をリセットします")
async def reset_history_super(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = super_AIs[guild_id].reset_history()
    await interaction.followup.send(result)

#プロンプトをリセット
@tree.command(name="reset_prompt_super", description="上位モデルの命令をリセットします")
async def reset_prompt_super(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = super_AIs[guild_id].reset_prompt()
    await interaction.followup.send(result)

#プロンプトを追加
@tree.command(name="add_prompt_super", description="上位モデルの命令を追加します")
async def add_prompt_super(interaction: discord.Interaction, prompt: str):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = super_AIs[guild_id].add_prompt(prompt)
    await interaction.followup.send(result)

#プロンプトを見る
@tree.command(name="show_prompt_super", description="上位モデルの命令を表示します")
async def show_prompt_super(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = super_AIs[guild_id].show_prompt()
    await interaction.followup.send(result)

#プロンプトを消す
@tree.command(name="delete_prompt_super", description="上位モデルの命令を削除します")
async def delete_prompt_super(interaction: discord.Interaction, index: int):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = super_AIs[guild_id].delete_prompt(index)
    await interaction.followup.send(result)

# コンフィグを変更する
@tree.command(name="set_config_super", description="上位モデルのコンフィグを設定します。")
async def set_config_super(interaction: discord.Interaction,
                        temperature: float = None):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = super_AIs[guild_id].set_config(temperature)
    await interaction.followup.send(result)

#コンフィグを見る
@tree.command(name="show_config_super", description="上位モデルのコンフィグを表示します")
async def show_config_super(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = super_AIs[guild_id].show_config()
    await interaction.followup.send(result)


#------------------------------flash------------------------------------
#回答
@tree.command(name="flash_chat", description="flashモデルが送った内容に返答してくれます")
async def return_flash_answer(interaction: discord.Interaction, text: str):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = flash_AIs[guild_id].return_answer(interaction, text)
    await interaction.followup.send(result)

#履歴をリセット
@tree.command(name="reset_history_flash", description="flashモデルの記憶をリセットします")
async def reset_history_flash(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = flash_AIs[guild_id].reset_history()
    await interaction.followup.send(result)

#プロンプトをリセット
@tree.command(name="reset_prompt_flash", description="flashモデルの命令をリセットします")
async def reset_prompt_flash(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = flash_AIs[guild_id].reset_prompt()
    await interaction.followup.send(result)

#プロンプトを追加
@tree.command(name="add_prompt_flash", description="flashモデルの命令を追加します")
async def add_prompt_flash(interaction: discord.Interaction, prompt: str):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = flash_AIs[guild_id].add_prompt(prompt)
    await interaction.followup.send(result)

#プロンプトを見る
@tree.command(name="show_prompt_flash", description="flashモデルの命令を表示します")
async def show_prompt_flash(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = flash_AIs[guild_id].show_prompt()
    await interaction.followup.send(result)

#プロンプトを消す
@tree.command(name="delete_prompt_flash", description="flashモデルの命令を削除します")
async def delete_prompt_flash(interaction: discord.Interaction, index: int):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = flash_AIs[guild_id].delete_prompt(index)
    await interaction.followup.send(result)

# コンフィグを変更する
@tree.command(name="set_config_flash", description="flashモデルのコンフィグを設定します。")
async def set_config_flash(interaction: discord.Interaction,
                        temperature: float = None):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = flash_AIs[guild_id].set_config(temperature)
    await interaction.followup.send(result)

#コンフィグを見る
@tree.command(name="show_config_flash", description="flashモデルのコンフィグを表示します")
async def show_config_flash(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    await interaction.response.defer()
    result = flash_AIs[guild_id].show_config()
    await interaction.followup.send(result)


#------------------------------image------------------------------------
# 画像モデルの回答
@tree.command(name="image_chat", description="画像を読み取って回答してくれます")
async def return_image_answer(interaction: discord.Interaction,
                                image: discord.Attachment,
                                text: str = ""):
    logger.error("質問受付")
    await interaction.response.defer()
    name = interaction.user.display_name
    text = "日本語で回答して。" + text
    embed = None
    try:
        logger.error("質問 : " + text)
        embed = discord.Embed(title="画像", color=0xff0000)
        embed.set_image(url=image.url)

        data = requests.get(image.url)
        image_file = Image.open(BytesIO(data.content))
        response = image_model.generate_content([text, image_file])
        result = form_question(name, text) + "【回答】\n" + response.text
    except genai.types.StopCandidateException as e:
        result = form_question(name, text) + str(e) + " により回答不能です。"
    except Exception as e:
        logger.error(e)
        result = form_question(name, text) + str(type(e)) + "が発生しました。"

    if embed is None:
        await interaction.followup.send(result)
    else:
        await interaction.followup.send(result, embed=embed)
    logger.error("回答完了\n")

# Koyeb用 サーバー立ち上げ
server_thread()

# botの作動
try:
    bot_token = os.getenv("DISCORD_BOT_TOKEN") or ""
    if bot_token == "":
        raise Exception("DiscordBotのトークンがないよ")
    client.run(bot_token)
except discord.HTTPException as e:
    if e.status == 429:
        logger.error("レート上限だよ")
    elif e.status == 400:
        logger.error("送ろうとした文が2000文字を超えてたよ")
    else:
        raise e
