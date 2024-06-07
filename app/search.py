from bs4 import BeautifulSoup as bs
import aiohttp
import wikipedia
wikipedia.set_lang("ja")
from logging import getLogger
import re

logger = getLogger(__name__)

# URLからhtml(body)を返す
async def fetch_html(url, tags = ["body"]):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.read()
            try:
                charset = get_charset(content)
                html = content.decode(encoding=charset, errors='ignore')
                bodys = [b.get_text(separator=" ") for b in bs(html, "html.parser").findAll(tags)]
                body = "".join(bodys)
                return body if len(body) > 30 else html
            except UnicodeDecodeError as e:
                err = e
            if err:
                raise err
            return None

# wordに近い項目の全文を返す
def get_wikipedia_text(word):
    search_list = wikipedia.search(word)
    try:
        if search_list:
            result = get_formed_result(search_list[0])
        else:
            result = [False, "その項目はありません"]
    except wikipedia.DisambiguationError as e:
        first_option = e.options[0]
        result = get_formed_result(first_option)
        
    except wikipedia.WikipediaException as e:
        result = [False, "Wikipediaが忙しいらしいので、再トライしてください"]
    except Exception as e:
        result = [False, str(e) + "が発生しました。"]
    return result

def get_formed_result(word):
    page = wikipedia.page(word)
    text = page.content.split("\n\n\n== 符号位置")[0].split("\n\n\n== 脚注")[0]
    return [word, text, page.url]

# contentからcharsetを取り出す
def get_charset(content):
    # first_htmlからcharsetを抽出
    first_html = content.decode(encoding="utf-8", errors='ignore')
    charset_pattern = re.compile(r'<meta.*?charset=(.*?)[\s\'"\/>]')
    charset = charset_pattern.search(first_html).group(1)
    if charset == "x-sjis":
        charset = "sjis"
    return charset