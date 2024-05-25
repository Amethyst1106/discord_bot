import requests
from bs4 import BeautifulSoup as bs
import re


def get_wikipedia_url(word):
    url = "https://ja.wikipedia.org/wiki/" + word
    return url

def get_wikipedia_text(word):
    url = get_wikipedia_url(word)
    response = requests.get(url)
    if response.status_code != 200:
        return False
    
    soup = bs(response.content, "html.parser")
    div = soup.find("div", class_="mw-content-ltr mw-parser-output")
    paragraphs = div.find_all("p")
    paragraphs_text = [paragraph.get_text() for paragraph in paragraphs]
    text = "\n".join(paragraphs_text)
    text = re.sub(r'\[.*?\]', '', text)
    return text

print(get_wikipedia_text("ミラノ風ドリア"))