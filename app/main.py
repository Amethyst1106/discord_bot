import os
from io import BytesIO
from server import server_thread
import discord
import google.generativeai as genai
import requests
from discord import app_commands
from PIL import Image

import ai, search
from tools import form_question

from logging import getLogger
logger = getLogger(__name__)

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
AIs_dic = {"nomal" : nomal_AIs, "super" : super_AIs, "flash" : flash_AIs}
choice_list = [app_commands.Choice(name=model, value=model) for model in AIs_dic.keys()]

# botの設定
intents = discord.Intents.none()  #スラッシュコマンド以外受け取らない
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    global nomal_AIs, super_AIs, flash_AIs
    for guild in client.guilds:
        nomal_AIs[guild.id] = ai.ChatAI(guild_id=guild.id, version=nomal_model_name, name = "通常モデル")
        super_AIs[guild.id] = ai.ChatAI(guild_id=guild.id, version=super_model_name, name = "上位モデル")
        flash_AIs[guild.id] = ai.ChatAI(guild_id=guild.id, version=flash_model_name, name = "高速モデル")
    logger.error('{0.user} がログインしたよ'.format(client))

#接続が切れたとき
async def on_disconnect():
    logger.error("再接続中・・・")


#------------------------------スラッシュコマンド------------------------------------
#回答
@tree.command(name="chat", description="送った内容に返答してくれます")
@app_commands.choices(model = choice_list)
async def chat(interaction: discord.Interaction, text: str, model: str = "nomal"):
    await interaction.response.defer()
    guild_id = interaction.guild_id
    chat_ai = AIs_dic[model][guild_id]
    result = chat_ai.return_answer(interaction, text)
    await interaction.followup.send(result)

#履歴をリセット
@tree.command(name="reset_history", description="記憶をリセットします")
@app_commands.choices(model = choice_list)
async def reset_history(interaction: discord.Interaction, model: str = "nomal"):
    await interaction.response.defer()
    guild_id = interaction.guild_id
    chat_ai = AIs_dic[model][guild_id]
    result = chat_ai.reset_history()
    await interaction.followup.send(result)

#プロンプトをリセット
@tree.command(name="reset_prompt", description="命令をリセットします")
@app_commands.choices(model = choice_list)
async def reset_prompt_nomal(interaction: discord.Interaction, model: str = "nomal"):
    await interaction.response.defer()
    guild_id = interaction.guild_id
    chat_ai = AIs_dic[model][guild_id]
    result = chat_ai.reset_prompt()
    await interaction.followup.send(result)

#プロンプトを追加
@tree.command(name="add_prompt", description="命令を追加します")
@app_commands.choices(model = choice_list)
async def add_prompt(interaction: discord.Interaction, prompt: str, model: str = "nomal"):
    await interaction.response.defer()
    guild_id = interaction.guild_id
    chat_ai = AIs_dic[model][guild_id]
    result = chat_ai.add_prompt(prompt)
    await interaction.followup.send(result)

#プロンプトを見る
@tree.command(name="show_prompt", description="命令を表示します")
@app_commands.choices(model = choice_list)
async def show_prompt(interaction: discord.Interaction, model: str = "nomal"):
    await interaction.response.defer()
    guild_id = interaction.guild_id
    chat_ai = AIs_dic[model][guild_id]
    result = chat_ai.show_prompt()
    await interaction.followup.send(result)

#プロンプトを消す
@tree.command(name="delete_prompt", description="命令を削除します")
@app_commands.choices(model = choice_list)
async def delete_prompt(interaction: discord.Interaction, index: int, model: str = "nomal"):
    await interaction.response.defer()
    guild_id = interaction.guild_id
    chat_ai = AIs_dic[model][guild_id]
    result = chat_ai.delete_prompt(index)
    await interaction.followup.send(result)

# コンフィグを変更する
@tree.command(name="set_config", description="コンフィグを設定します。")
@app_commands.choices(model = choice_list)
async def set_config(interaction: discord.Interaction,
                        temperature: float = None, model: str = "nomal"):
    await interaction.response.defer()
    guild_id = interaction.guild_id
    chat_ai = AIs_dic[model][guild_id]
    result = chat_ai.set_config(temperature)
    await interaction.followup.send(result)

# コンフィグを見る
@tree.command(name="show_config", description="コンフィグを表示します")
@app_commands.choices(model = choice_list)
async def show_config(interaction: discord.Interaction, model: str = "nomal"):
    await interaction.response.defer()
    guild_id = interaction.guild_id
    chat_ai = AIs_dic[model][guild_id]
    result = chat_ai.show_config()
    await interaction.followup.send(result)

# Wikipediaの記事を要約
@tree.command(name="wikipedia", description="Wikipediaの項目について要約します")
async def wikipedia(interaction: discord.Interaction, word: str, order: str = "", length: int = 300):
    await interaction.response.defer()
    guild_id = interaction.guild_id
    chat_ai = AIs_dic["flash"][guild_id]
    search_result = search.get_wikipedia_text(word)
    if search_result[0]:
        result = form_question(interaction.user.display_name, word)\
                + f"項目名：{search_result[0]}\n"\
                + f"<{search_result[2]}>\n"\
                + chat_ai.get_summary(search_result[0], search_result[1], order, length)
    else:
        result = form_question(interaction.user.display_name, word)\
                + search_result[1]
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


#------------------------------bot動作------------------------------------
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
