﻿import json
from logging import getLogger

import discord
import google.generativeai as genai
from search import fetch_html
from tools import form_question, get_image_file, upload_file

logger = getLogger(__name__)

default_safety_settings = [{
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

class ChatAI:
    def __init__(self, 
                guild_id = None, 
                version = "gemini-1.5-flash-latest",
                name = "高速モデル",
                temperature = None,
                safety_settings = default_safety_settings,
                history = []):
        self.guild_id = guild_id
        self.name = name
        self.version = version
        self.default_model = genai.GenerativeModel(version)
        config = genai.GenerationConfig(temperature = temperature)
        self.model = genai.GenerativeModel(version, 
                                            safety_settings=safety_settings,
                                            generation_config = config)
        self.chat_ai = self.model.start_chat(history=history)
        self.safety_settings = safety_settings
        self.prompt = []
        self.history = history
        self.temperature = None


    # 回答
    async def return_answer(self, interaction, text, file = None):
        self.loging_info()
        logger.error("質問受付")
        logger.error("質問 : " + text)
        name = interaction.user.display_name
        text_file = None
        result = ""
        try:
            content, formed_text = await self._form_content(text, file, self.prompt)
            response = await self.chat_ai.send_message_async(content)
            result = form_question(name, formed_text) + f"【回答({self.name})】\n" + response.text
            # 2000文字超えるとdiscord側のエラーになるのでtextに
            if len(result) > 2000:
                with open("response.txt", "w", encoding="utf-8") as response_file:
                    response_file.write(result[2000:])
                text_file = discord.File("response.txt")
                result = result[:2000]

        except genai.types.StopCandidateException as e:
            result = form_question(name, text) + str(e) + " により回答不能です。"
        except Exception as e:
            logger.error(e)
            result = form_question(name, text) + str(type(e)) + "が発生しました。"
        logger.error("result : " + str(len(result)) + "文字")
        logger.error("回答完了\n")
        return result, text_file


    # 入力コンテンツの整形
    async def _form_content(self, text, file = None, prompt = []):
        prompt_text = "。\n".join(prompt) + "。\n" if prompt != [] else ""
        formed_text = prompt_text + text
        content = [formed_text]
        if file is not None:
            if "text" in file.content_type or "json" in file.content_type:
                file_content = await file.read()
                file_text    = file_content.decode('utf-8')
                content.append(file_text)
            elif "image" in file.content_type:
                image_file = await get_image_file(file)
                content.append(image_file)
            elif "video" in file.content_type or "audio" in file.content_type:
                uploaded_file = await upload_file(file)
                content.append(uploaded_file)
            
        return content, formed_text


    # 履歴をリセット
    def reset_history(self):
        self.chat_ai = self.model.start_chat(history=[])
        result = "記憶をリセットしました。"
        self.loging_info(result)
        return f"{self.name} : {result}"


    # コンフィグを変更
    def set_config(self, temperature):
        config = genai.GenerationConfig(temperature = temperature)
        self.model = genai.GenerativeModel(self.version, 
                                            safety_settings = self.safety_settings,
                                            generation_config = config)
        self.temperature = temperature
        self.chat_ai = self.model.start_chat(history=self.chat_ai.history)
        result = f"コンフィグを\ntemperature : {temperature}\nに設定しました。"
        self.loging_info(result)
        return f"{self.name} : {result}"
    
    # コンフィグを見る
    async def show_config(self):
        result = f"temperature = {self.temperature}"
        result += f"\nmodel_name = {self.chat_ai.model.model_name}"
        return f"{self.name} : {result}"
    

    # プロンプトを追加
    def add_prompt(self, prompt):
        self.prompt.append(prompt)
        result = f"命令\n「{prompt}」\nを追加しました。"
        self.loging_info(result)
        return f"{self.name} : {result}"
    

    # プロンプトを消す
    def delete_prompt(self, index):
        try:
            deleted_prompt = self.prompt.pop(index)
            result = f"命令\n「{deleted_prompt}」\nを削除しました。"
        except Exception as e:
            result = str(type(e)) + "が発生しました。"
        self.loging_info(result)
        return f"{self.name} : {result}"


    # プロンプトをリセット
    def reset_prompt(self):
        self.prompt = []
        result = "命令をリセットしました。"
        self.loging_info(result)
        return result
    

    # プロンプトを見る
    async def show_prompt(self):
        result = "命令一覧\n" \
                + "\n".join([f"{x} : {self.prompt[x]}" for x in range(len(self.prompt))])
        return result
    

    # ログ出力用
    def loging_info(self, text = ""):
        logger.error(self.name)
        if text != "":
            logger.error(text + "\n")


    # 要約
    async def get_summary(self, text, order, length):
        logger.error(f"summary" + (f"\n{order}" if order else ""))
        prompt = f"以下の文を、{length}文字程度で要約して。{order}。\n" + text
        response = await self.chat_ai.send_message_async(prompt)
        try:
            result = response.text
            logger.error("result : " + str(len(result)) + "文字")
            logger.error("回答完了\n")
        except genai.types.StopCandidateException as e:
            result = text + "\n\n" + str(e) + " により回答不能です。"
        except Exception as e:
            logger.error(e)
            result = text + "\n\n" + str(type(e)) + "が発生しました。"
        return result



# プロセカ用
class ProsekaAI(ChatAI):
    def __init__(self,
                guild_id = None, 
                version = "gemini-1.5-flash-latest",
                name = "プロセカモデル",
                temperature = None,
                safety_settings = default_safety_settings,
                history = []):
        super().__init__(guild_id, version, name, temperature, safety_settings, history)
        self.all_music_page = ""
        self.master_level_page = ""
        self.have_page = False
    
    # プロセカ用
    async def return_level(self, music_name):
        if not self.have_page:
            await self.base_history()
        logger.error("プロセカ受付")
        logger.error("曲名 : " + music_name + "\n")
        master_prompt = f"表から、{music_name}のレベルと判定についてと、説明。"
        response = await self.chat_ai.send_message_async(master_prompt)
        result = "曲名 : " + music_name + "\n\n" + response.text
        return result
    
    async def reset_history(self):
        result = super().reset_history()
        await self.base_history()
        return result

    async def base_history(self):
        # self.all_music_page = await fetch_html("https://pjsekai.com/?aad6ee23b0", ["thead", "tbody"])
        self.master_level_page = await fetch_html("https://pjsekai.com/?aa95a0f97c", ["thead", "tbody"])
        page_prompt = "以降はこの表の内容をもとに答えてください。"\
                        + "ここから表\n" + self.master_level_page
        await self.chat_ai.send_message_async(page_prompt)
        self.have_page = True