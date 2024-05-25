import wikipedia
wikipedia.set_lang("ja")

def get_wikipedia_text(word):
    search_list = wikipedia.search(word)
    if search_list:
        page = wikipedia.page(search_list[0])
        text = page.content.split("\n\n\n== 符号位置")[0].split("\n\n\n== 脚注")[0]
        return [search_list[0], text]
    else:
        return []

print(get_wikipedia_text("ミラノ風ドリア"))