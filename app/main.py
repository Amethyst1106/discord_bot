from datetime import datetime, timezone, timedelta
import os
import sys
import google.generativeai as genai
import discord
from discord import app_commands
from discord.ext import tasks

import ai, search
from tools import form_question, to_discord_file
from server import server_thread
from search import fetch_html
import db

from logging import getLogger
logger = getLogger(__name__)

# Gemini APIの設定
genai.configure(api_key=os.environ["GEMINI_TOKEN"])

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
super_model_name = "gemini-1.5-pro-exp-0801"
flash_model_name = "gemini-1.5-flash-latest"

nomal_AIs = {}
super_AIs = {}
flash_AIs = {}
AIs_dic = {"flash" : flash_AIs, "super" : super_AIs, "nomal" : nomal_AIs}
models_choice = [app_commands.Choice(name = model,  value = model)  for model  in AIs_dic.keys()]
prompt_actions = ["reset", "show", "add", "delete"]
prompt_choice = [app_commands.Choice(name = action, value = action) for action in prompt_actions]
config_actions = ["show", "set"]
config_choice = [app_commands.Choice(name = action, value = action) for action in config_actions]
schedule_actions = ["add", "show", "delete"]
schedule_choice = [app_commands.Choice(name = action, value = action) for action in schedule_actions]
proseka_AI = ai.ProsekaAI()

# botの設定
intents = discord.Intents.none()  #スラッシュコマンド以外受け取らない
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# タイマーの設定
sql = "SELECT * FROM SCHEDULE"
schedule_datas = db.select(sql)
schedules = {data["timestamp"]:data for data in schedule_datas}
td = timedelta(hours=9)
tz = timezone(td)

@client.event
async def on_ready():
    await tree.sync()
    global nomal_AIs, super_AIs, flash_AIs
    for guild in client.guilds:
        nomal_AIs[guild.id] = ai.ChatAI(guild_id=guild.id, version=nomal_model_name, name = "通常モデル")
        super_AIs[guild.id] = ai.ChatAI(guild_id=guild.id, version=super_model_name, name = "上位モデル")
        flash_AIs[guild.id] = ai.ChatAI(guild_id=guild.id, version=flash_model_name, name = "高速モデル")
    loop.start()
    logger.error('{0.user} がログインしたよ'.format(client))

@client.event
#接続が切れたとき
async def on_disconnect():
    logger.error("接続が切断されました")

# 60秒に一回ループ
@tasks.loop(seconds=60)
async def loop():
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
    if now in schedules:
        schedule = schedules[now]
        channel  = await client.fetch_channel(int(schedule["channel_id"]))
        send_text = f'【スケジュール機能】\n<@{schedule["mention"]}>\n{now}\n{schedule["event"]}'
        await channel.send(send_text)  


#------------------------------スラッシュコマンド------------------------------------
#回答
@tree.command(name="chat", description="送った内容に返答してくれます")
@app_commands.choices(model = models_choice)
async def chat(interaction: discord.Interaction, 
                text: str, 
                file: discord.Attachment = None,
                model: str = "flash"):
    await interaction.response.defer()
    guild_id = interaction.guild_id
    chat_ai = AIs_dic[model][guild_id]
    result, text_file = await chat_ai.return_answer(interaction, text, file)
    files = []
    if text_file is not None:
        files.append(text_file)
    if file is not None:
        files.append(await to_discord_file(file))

    if files != []:
        await interaction.followup.send(result, files=files)
    else:
        await interaction.followup.send(result)

#履歴をリセット
@tree.command(name="reset_history", description="記憶をリセットします")
@app_commands.choices(model = models_choice)
async def reset_history(interaction: discord.Interaction, model: str = "flash"):
    await interaction.response.defer()
    guild_id = interaction.guild_id
    chat_ai = AIs_dic[model][guild_id]
    result = chat_ai.reset_history()
    await interaction.followup.send(result)

#プロンプト
@tree.command(name="prompt", description="命令についてのコマンド")
@app_commands.choices(model = models_choice, action = prompt_choice)
async def prompt(interaction: discord.Interaction, action:str, prompt: str =  "", index: int = 0 , model: str = "flash"):
    await interaction.response.defer()
    guild_id = interaction.guild_id
    chat_ai = AIs_dic[model][guild_id]
    if   action == "reset":
        result = chat_ai.reset_prompt()
    elif action == "show":
        result = await chat_ai.show_prompt()
    elif action == "add":
        result = chat_ai.add_prompt(prompt)
    elif action == "delete":
        result = chat_ai.delete_prompt(index)
    await interaction.followup.send(result)

# コンフィグ
@tree.command(name="config", description="コンフィグについてのコマンド")
@app_commands.choices(model = models_choice, action = config_choice)
async def config(interaction: discord.Interaction,
                        action:str, temperature: float = None, model: str = "flash"):
    await interaction.response.defer()
    guild_id = interaction.guild_id
    chat_ai = AIs_dic[model][guild_id]
    if action == "set":
        result = chat_ai.set_config(temperature)
    elif action == "show":
        result = await chat_ai.show_config()
    await interaction.followup.send(result)

# Wikipediaの記事を要約
@tree.command(name="wikipedia", description="Wikipediaの項目について要約します")
async def wikipedia(interaction: discord.Interaction, word: str, order: str = "", length: int = 300):
    await interaction.response.defer()
    guild_id = interaction.guild_id
    chat_ai = AIs_dic["flash"][guild_id]
    search_result = search.get_wikipedia_text(word)
    page_title = search_result[0]
    name = interaction.user.display_name
    if page_title:
        try:
            result = form_question(name, f"{word}" + (f"\n{order}" if order else ""))\
                    + f"項目名：{page_title}\n"\
                    + f"<{search_result[2]}>\n"\
                    + await chat_ai.get_summary(search_result[1], order, length)
        except genai.types.StopCandidateException as e:
            result = form_question(name, word)\
                    + f"項目名：{page_title}\n" + f"<{search_result[2]}>\n"\
                    + str(e) + " により回答不能です。"
        except Exception as e:
            logger.error(e)
            result = form_question(name, word)\
                    + f"項目名：{page_title}\n" + f"<{search_result[2]}>\n"\
                    + str(type(e)) + "が発生しました。"
    else:
        result = form_question(name, f"{word}" + (f"\n{order}" if order else ""))\
                + search_result[1]
    await interaction.followup.send(result)


# URL先のページを要約
@tree.command(name="summarize", description="URL先のページを要約します")
async def summarize(interaction: discord.Interaction, url: str, order: str = "", length: int = 300):
    await interaction.response.defer()
    name = interaction.user.display_name
    guild_id = interaction.guild_id
    chat_ai = AIs_dic["flash"][guild_id]
    try:
        html = await fetch_html(url)
        summary = await chat_ai.get_summary(html, order, length)
        result = form_question(name, f"<{url}>" + (f"\n{order}" if order else ""))\
                    + summary
    except Exception as e:
        logger.error(e)
        result = form_question(name, f"<{url}>" + (f"\n{order}" if order else ""))\
                + str(type(e)) + "が発生しました。"
        
    await interaction.followup.send(result)
    

# プロセカ
@tree.command(name="proseka", description="プロセカ曲の難易度を返します")
@app_commands.choices(reset = [app_commands.Choice(name = "reset", value = "reset")])
async def proseka(interaction: discord.Interaction, music_name: str, reset: str = ""):
    await interaction.response.defer()
    if reset == "reset":
        result = await proseka_AI.reset_history()
    else:
        try:
            result = await proseka_AI.return_level(music_name)
        except Exception as e:
            logger.error(e)
            result = str(type(e)) + "が発生しました。"
            
    await interaction.followup.send(result)
    await proseka_AI.reset_history()

# スケジュール
@tree.command(name="schedule", description="スケジュールのコマンド")
@app_commands.describe(date="YYYY-MM-DD", time="HH:MM")
@app_commands.choices(action = schedule_choice)
async def schedule(interaction: discord.Interaction,
                        action:str, date: str = "", time: str = "", event: str = "", mention: str = ""):
    await interaction.response.defer()

    if action == "add":
        if not("" in (date, time, event)):
            mention = str(interaction.user.id) if mention == "" else mention
            timestamp = date + " " + time
            schedule = {
            "timestamp"  : timestamp,
            "event"      : event,
            "guild_id"   : str(interaction.guild_id),
            "channel_id" : str(interaction.channel_id),
            "mention"    : mention
            }
            schedules[timestamp] = schedule
            db.insert("SCHEDULE", schedule)
            result = f"{timestamp}\n{event}\nスケジュールを登録しました"
        else:
            result = "必要事項を入力してください。"

    elif action == "show":
        guild_schedules = []
        for timestamp in schedules:
            if str(interaction.guild_id) == schedules[timestamp]["guild_id"]:
                guild_schedules.append(timestamp + "\n" + schedules[timestamp]["event"])
        result = "\n\n".join(guild_schedules)

    elif action == "delete":
        result = "未実装"

    await interaction.followup.send(result)

# stop
@tree.command(name = "stop", description="管理用コマンド")
async def stop(interaction: discord.Interaction, password: str):
    if password == os.environ["STOP_PASSWORD"]:
        await interaction.response.send_message("botを停止します。")
        client.close()
        sys.exit()

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
except discord.errors.ConnectionClosed as e:
    if e.code == 1000:
        logger.error("再接続中・・・")
    else:
        raise e