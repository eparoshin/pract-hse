import telebot
import wikipediaapi
import requests
from copy import deepcopy

bot = telebot.TeleBot('token')
headers = {
    'x-rapidapi-key': "key",
    'x-rapidapi-host': "bing-image-search1.p.rapidapi.com"
}
url = "https://bing-image-search1.p.rapidapi.com/images/search"

url_g_0 = 'https://google-search3.p.rapidapi.com/api/v1/search/q='
url_g_1 = '+site:ru.wikipedia.org&num=10'

headers_g = {
    'x-rapidapi-key': "key",
    'x-rapidapi-host': "google-search3.p.rapidapi.com"
}


class NotFoundException(Exception):
    def __init__(self):
        pass


class Anwser:
    def __init__(self, request):
        self.req = request

    def get_wiki_link(self): #Поиск точного названия статьи из википедии
        gogl_req = deepcopy(self.req)
        gogl_req.replace(' ', '+')
        gogl_req = url_g_0 + gogl_req + url_g_1
        response_g = requests.request("GET", gogl_req, headers=headers_g)
        rj = response_g.json()
        try:
            return rj['results'][0]['title']
        except IndexError:
            raise NotFoundException

    def get_wiki_summary(self, language):
        wiki = wikipediaapi.Wikipedia(language)
        wiki_title = self.get_wiki_link()
        end = wiki_title.rfind('—')
        wiki_title = wiki_title[0:end - 1]
        self.req = wiki_title
        current_page = wiki.page(wiki_title)
        if current_page.exists():
            flag = False  # проверяю, что статья из википедии относиться к категории связанной с музыкой.(Без этого не
            # работает к примеру поиск группы "Звери")
            for category in current_page.categories:
                if category.find('музыка') != -1 or category.find('Музыка') != -1:
                    flag = True
                    break
            if flag:
                return current_page.summary
            else:
                self.req = self.req + ' (группа)'
                current_page = wiki.page(self.req)
                if current_page.exists():
                    return current_page.summary
                else:
                    raise NotFoundException
        else:
            raise NotFoundException

    def get_image(self):
        querystring = {"q": self.req+'(music)'}
        response = requests.request("GET", url, headers=headers, params=querystring)
        data = response.json()
        return data['value'][0]['thumbnailUrl']


@bot.message_handler(commands=['start', 'new'])
def send_info(message):
    group_name = bot.send_message(message.chat.id, 'Привет. Пожалуйста введи название музыкального исполнителя, '
                                                   'чтобы я мог найти информацию о нем.')
    bot.register_next_step_handler(group_name, result)


def result(message):
    an = Anwser(message.text)
    try:
        text = an.get_wiki_summary('ru')
        image = an.get_image()
        bot.send_photo(message.chat.id, image)
        if len(text) > 4096:
            bot.send_message(message.chat.id, text[0:(text[0:4096].rfind('.') + 1)])
        else:
            bot.send_message(message.chat.id, text)
    except NotFoundException:
        bot.send_message(message.chat.id, 'Исполнитель не найден')


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)


bot.polling()
