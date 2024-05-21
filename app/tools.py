from discord import integrations
import google.generativeai as genai
from logging import getLogger
import logging

logger = getLogger(__name__)
logger.setLevel(logging.INFO)

# 質問の整形
def form_question(name, text):
    return "from : " + name + "\n" + text + "\n\n"


def init_AI(guild_id, model, AIs, prompts, configs, default_config):
    if guild_id not in AIs:
        AIs[guild_id] = model.start_chat(history=[])
    if guild_id not in prompts:
        prompts[guild_id] = []
    if guild_id not in configs:
        configs[guild_id] = default_config


# 回答
async def return_answer(interaction, text, model, AIs, prompts, configs,
                        default_config):
    # チャンネルにAIがなければ作る
    guild_id = interaction.guild_id
    init_AI(guild_id, model, AIs, prompts, configs, default_config)
    ai = AIs[guild_id]
    logger.error("質問受付")
    logger.error("質問 : " + text)

    name = interaction.user.display_name
    i = 0
    result = ""
    while (result == ""):
        try:
            limit_prompt = str(2000 - i) + "文字以内で答えて。" if i > 0 else ""
            prompt = "。\n".join(prompts[guild_id]) \
                    + "。" if prompts[guild_id] != [] else ""
            text = limit_prompt + prompt + text
            response = ai.send_message(text)
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
    return result


# 記憶リセット
async def reset_history(interaction, model, AIs, name):
    AIs[interaction.guild_id] = model.start_chat(history=[])
    logger.error(name + "モデル記憶リセット\n\n")
