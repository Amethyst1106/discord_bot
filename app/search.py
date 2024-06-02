from bs4 import BeautifulSoup as bs
import aiohttp
import wikipedia
wikipedia.set_lang("ja")

async def fetch_html(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
            return html

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