import google.generativeai as genai
from tools import form_question
from logging import getLogger

logger = getLogger(__name__)

class ChatAI:
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

    def __init__(self, 
                guild_id, 
                version = "gemini-1.0-pro-latest",
                name = "通常モデル",
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
    def return_answer(self, interaction, text):
        self.loging_info()
        logger.error("質問受付")
        logger.error("質問 : " + text)
        name = interaction.user.display_name
        i = 0
        result = ""
        while(result == ""):
            try:
                limit_prompt = str(2000 - i) + "文字以内で答えて。" if i > 0 else ""
                prompt = "。\n".join(self.prompt) \
                        + "。" if self.prompt != [] else ""
                text = limit_prompt + prompt + text
                response = self.chat_ai.send_message(text)
                result = form_question(name, text) + "【回答】\n" + response.text

                if len(result) > 2000:
                    i += 100
                    result = ""  # 2000文字超えるとdiscord側のエラーになるので再トライ

            except genai.types.StopCandidateException as e:
                result = form_question(name, text) + str(e) + " により回答不能です。"
            except Exception as e:
                logger.error(e)
                result = form_question(name, text) + str(type(e)) + "が発生しました。"
            logger.error("result : " + str(len(result)) + "文字")
        logger.error("回答完了\n")
        return result

    # 履歴とコンフィグをリセット
    def reset_history(self):
        self.chat_ai = self.model.start_chat(history=[])
        self.temperature = None
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
        result = self.name + f"コンフィグを\ntemperature : {temperature}\nに設定しました。"
        self.loging_info(result)
        return f"{self.name} : {result}"
    
    # コンフィグを見る
    def show_config(self):
        result = f"temperature = {self.temperature}"
        return f"{self.name} : {result}"
    
    # プロンプトを追加
    def add_prompt(self, str):
        self.prompt.append(str)
        self.loging_info()
        result = f"命令\n「{str}」\nを追加しました。"
        self.loging_info(result)
        return f"{self.name} : {result}"
    
    # プロンプトを消す
    def delete_prompt(self, index):
        self.loging_info()
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
    def show_prompt(self):
        result = "命令一覧 : " \
                + str([f"{x} : {self.prompt}" for x in range(len(self.prompt))])
        return result
    
    # ログ出力用
    def loging_info(self, text = ""):
        logger.error(self.name)
        if text != "":
            logger.error(text + "\n")