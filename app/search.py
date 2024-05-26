import wikipedia
wikipedia.set_lang("ja")

def get_wikipedia_text(word):
    search_list = wikipedia.search(word)
    try:
        if search_list:
            result = get_formed_result(search_list[0])
        else:
            result = []
    except wikipedia.DisambiguationError as e:
        first_option = e.options[0]
        try:
            result = get_formed_result(first_option)
        except Exception as e:
            return f"エラーが発生しました: {e}"
    return result

def get_formed_result(word):
    page = wikipedia.page(word)
    text = page.content.split("\n\n\n== 符号位置")[0].split("\n\n\n== 脚注")[0]
    return [word, text]