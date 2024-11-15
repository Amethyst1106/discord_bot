﻿import os
import sys
from datetime import datetime, timedelta, timezone
from logging import getLogger

import ai
import db
import discord
import google.generativeai as genai
import search
from discord import app_commands
from discord.ext import tasks
from search import fetch_html
from server import server_thread
from tools import form_question, to_discord_file

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

# Geminiモデルの設定
flash_model_name = "gemini-1.5-flash-latest"
super_model_name = "gemini-1.5-pro-latest"
exp_model_name   = "gemini-exp-1114"

flash_AIs = {}
super_AIs = {}
exp_AIs   = {}
AIs_dic = {"flash" : flash_AIs, "super" : super_AIs, "exp" : exp_AIs}
default_AI_key = "exp"

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
td = timedelta(hours=9)
tz = timezone(td)
schedule_table_name = "Schedule"
delete_rule = f"time_stamp < \'{datetime.now(tz).strftime('%Y-%m-%d %H:%M')}\'"
db.delete_by_rule(schedule_table_name, delete_rule)
schedule_datas = db.select_all(schedule_table_name)
schedules = {data["time_stamp"]:data for data in schedule_datas}
add_schedules = []

is_ready = False

@client.event
async def on_ready():
    global is_ready
    if not is_ready:
        await tree.sync()
        global super_AIs, flash_AIs, exp_AIs
        for guild in client.guilds:
            flash_AIs[guild.id] = ai.ChatAI(guild_id=guild.id, version=flash_model_name, name = "高速モデル")
            super_AIs[guild.id] = ai.ChatAI(guild_id=guild.id, version=super_model_name, name = "上位モデル")
            exp_AIs[guild.id]   = ai.ChatAI(guild_id=guild.id, version=exp_model_name  , name = "試験モデル")
        loop.start()
        logger.error('{0.user} がログインしたよ'.format(client))
        is_ready = True

@client.event
#接続が切れたとき
async def on_disconnect():
    logger.error("接続が切断されました")

# 60秒に一回ループ
@tasks.loop(seconds=60)
async def loop():
    now_str = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
    now     = datetime.strptime(now_str, "%Y-%m-%d %H:%M")
    if now in schedules:
        schedule = schedules[now]
        channel  = await client.fetch_channel(int(schedule["channel_id"]))
        send_text = f'【スケジュール機能】\n{schedule["mention"]}\n{now_str}\n{schedule["event"]}'
        await channel.send(send_text)
        schedules.pop(now)


#------------------------------スラッシュコマンド------------------------------------
#回答
@tree.command(name="chat", description="送った内容に返答してくれます")
@app_commands.choices(model = models_choice)
async def chat(interaction: discord.Interaction, 
                text: str, 
                file: discord.Attachment = None,
                model: str = default_AI_key):
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
async def reset_history(interaction: discord.Interaction, model: str = default_AI_key):
    await interaction.response.defer()
    guild_id = interaction.guild_id
    chat_ai = AIs_dic[model][guild_id]
    result = chat_ai.reset_history()
    await interaction.followup.send(result)

#プロンプト
@tree.command(name="prompt", description="命令についてのコマンド")
@app_commands.choices(model = models_choice, action = prompt_choice)
async def prompt(interaction: discord.Interaction, action:str, prompt: str =  "", index: int = 0 , model: str = default_AI_key):
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
                        action:str, temperature: float = None, model: str = default_AI_key):
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
    chat_ai = AIs_dic[default_AI_key][guild_id]
    search_result = search.get_wikipedia_text(word)
    page_title = search_result[0]
    name = interaction.user.display_name
    if page_title:
        try:
            summary = await chat_ai.get_summary(search_result[1], order, length)
            summary = summary.replace("。", "。\n").replace("\n\n\n", "\n\n")
            result = form_question(name, f"{word}" + (f"\n{order}" if order else ""))\
                    + f"項目名：{page_title}\n"\
                    + f"<{search_result[2]}>\n"\
                    + summary
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
    chat_ai = AIs_dic[default_AI_key][guild_id]
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
@app_commands.describe(date="YYYY-MM-DD (デフォルト:今日)", time="HH:MM", event="内容", mention = "デフォルト:送信者")
@app_commands.choices(action = schedule_choice)
async def schedule(interaction: discord.Interaction,
                        action:str, date: str = "",
                        time: str = "", event: str = "", mention: str = ""):
    await interaction.response.defer()
    
    if action == "add":
        date = datetime.now(tz).strftime("%Y-%m-%d") if date == "" else ""
        if not("" in (date, time, event)):
            mention = f"<@{str(interaction.user.id)}>" if mention == "" else mention
            time_stamp_str = date + " " + time
            time_stamp     = datetime.strptime(time_stamp_str, "%Y-%m-%d %H:%M")
            schedule = {
            "time_stamp"  : time_stamp,
            "event"      : event,
            "guild_id"   : str(interaction.guild_id),
            "channel_id" : str(interaction.channel_id),
            "mention"    : mention
            }
            schedules[time_stamp] = schedule
            add_schedules.append(schedule)
            result = f"{time_stamp_str}\n{event}"
        else:
            result = "必要事項を入力してください。"
        result = "【スケジュール登録】\n" + result

    elif action == "show":
        guild_schedules = []
        for time_stamp in sorted(schedules.keys()):
            if str(interaction.guild_id) == schedules[time_stamp]["guild_id"]:
                guild_schedules.append(time_stamp.strftime("%Y-%m-%d %H:%M") + "\n" + schedules[time_stamp]["event"])
        result = "\n\n".join(guild_schedules) if guild_schedules != [] else "スケジュールがありません"
        result = "【スケジュール一覧】\n" + result
        
    elif action == "delete":
        try:
            if not("" in (date, time)):
                time_stamp_str = date + " " + time
                time_stamp     = datetime.strptime(time_stamp_str, "%Y-%m-%d %H:%M")
                delete_rule    = f"time_stamp = \'{time_stamp}\'"
                db.delete_by_rule("Schedule", delete_rule)
                result = f"{time_stamp_str}\n{schedules[time_stamp]['event']}"
                schedules.pop(time_stamp)
            else:
                result = "日付を入力してください。"
        except Exception as e:
            result = e + "が発生しました。"
        result = "【スケジュール削除】\n" + result
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
    
finally:
    for schedule in add_schedules:
        db.insert_dic(schedule_table_name, schedule)