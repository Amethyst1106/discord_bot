from bs4 import BeautifulSoup as bs
import aiohttp
import wikipedia
wikipedia.set_lang("ja")
from logging import getLogger

logger = getLogger(__name__)

async def fetch_html(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            encodings = ["utf-8", "shift_jis", "iso-8859-1", "euc-jp", "gb2312", "big5"]
            for encoding in encodings:
                try:
                    html = await response.text(encoding=encoding)
                    bodys = str(bs(html, "html.parser").findAll('body'))
                    body = "\n".join(bodys)
                    return body
                except UnicodeDecodeError as e:
                    err = e
                    continue
            if err:
                raise err
            return None

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