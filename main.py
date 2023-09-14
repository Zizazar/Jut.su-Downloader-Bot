from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
import youtube_dl
import telebot
from telebot import types
import os
TOKEN = ''
bot = telebot.TeleBot(TOKEN)

IsSearch = True
anime_url = ''
Seasons = ()

curr_season = ''
curr_ep = ''
#----Парсинг Сезонов и серий-----
def sort_seasons(mass):
    if type(mass) != list:
        raise ValueError
    output = {1:[]}
    season = 1
    data = []
    films = []
    for item in mass:
        if "фильм" not in item:
            data.append(int(item.split(" ")[0]))
        else:
            films.append(int(item.split(" ")[0]))
    for i in range(len(data)):
        output[season].append(data[i])
        try:
            if data[i] > data[i+1]:
                season += 1
                output[season] = []
        except:
            pass
    return output,films

def search_anime(input):
    driver = webdriver.Chrome('C:/chromedriver.exe')
    driver.get('https://jut.su')
    search = driver.find_element(By.XPATH, '//*[@id="search_b"]/form/input[2]')
    search.send_keys(input)
    driver.find_element(By.XPATH, '//*[@id="search_b"]/form/input[3]').click()
    global anime_url
    anime_url = driver.current_url
    AniName = driver.find_element(By.CLASS_NAME, 'anime_padding_for_title').text
    AniAdditional = driver.find_element(By.CLASS_NAME,'under_video_additional').text

    elem_episodes = driver.find_elements(By.XPATH, '//*[@id="dle-content"]/div/div[2]/a')
    raw_seasons = []
    for i in elem_episodes:
        raw_seasons.append(i.text)
    driver.quit()
    global Seasons
    Seasons = sort_seasons(raw_seasons)
    driver.quit()
    lenEpisodes = 0
    for ep in range(len(Seasons[0])):
        lenEpisodes += len(Seasons[0][ep+1])
    print(Seasons)
    out_message = {
        'name': AniName[9:AniName.find(' все серии')],
        'seasons': len(Seasons[0]),
        'episodes': lenEpisodes,
        'films': len(Seasons[1]),
        'additional': AniAdditional,
        'link': anime_url
    }
    print(out_message)
    return out_message

def download_anime(url):
    driver = webdriver.Chrome('C:/chromedriver.exe')
    driver.get(url)
    driver.find_element(By.ID, 'wap_player_use_old').click()    #переключение на старый плеер
    video_url = driver.find_element(By.ID, 'wap_player_3').get_attribute('data-player')  #извлечение ссылки на видео
    driver.quit()
    ydl_opts = {'outtmpl': 'tmp/video.mp4'}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:     #Скачивание видео
        ydl.download([video_url])

@bot.message_handler(commands=['start', 'help'])
def tg_send_welcome(message):
    bot.send_message(message.chat.id, "Бот запущен для загрузки аниме пришлите ссылку или название")

@bot.message_handler(content_types='text')
def tg_anime_search(message):
    global IsSearch
    if IsSearch:
        bot.send_message(message.chat.id, "Поиск")
        print(message.text)
        AnimeData = search_anime(message.text)
        formated_message = f'''<u>Результаты поиска:</u>
Название: <b>{AnimeData["name"]}</b>
Сезоны: {AnimeData['seasons']}
Серии: {AnimeData['episodes']}
Фильмы: {AnimeData['films']}
{AnimeData['additional']}'''
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton("Смотреть на jutsu", url=AnimeData["link"])
        button2 = types.InlineKeyboardButton("Смотреть в Телеграме", callback_data= 'watch')
        markup.add(button1, button2)
        bot.edit_message_text(formated_message, message.chat.id, message.id +1, parse_mode='HTML', reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: True)
    def answer(call):
        if call.data == 'watch':
            
            mesg = bot.send_message(message.chat.id, f'Напишите номер сезона от 1 до {len(Seasons[0])}')
                
            global IsSearch
            IsSearch = False
            
            bot.register_next_step_handler(mesg, WhatchInTelegram_step_2)
    
    def WhatchInTelegram_step_2(message):
        global curr_season
        curr_season = message.text
        eps = len(Seasons[0][int(curr_season)])

        mesg = bot.send_message(message.chat.id, f'Напишите номер серии от 1 до {eps}')

        bot.register_next_step_handler(mesg, WhatchInTelegram_step_3)
        
    def WhatchInTelegram_step_3(message):
        global curr_ep
        curr_ep = message.text
        mesg = bot.send_message(message.chat.id, f'<b>Скачиваю</b> сезон: {curr_season} серия: {curr_ep}', parse_mode='HTML')
        if len(Seasons[0]) == 1:
            dl_url = f'{anime_url}/episode-{curr_ep}.html'
        else:
            dl_url = f'{anime_url}/season-{curr_season}/episode-{curr_ep}.html'
        '''if film != 0:
            dl_url = f'{anime_url}/film-{film}.html'''
        print(dl_url)
        os.remove('tmp/video.mp4')
        download_anime(dl_url)
        bot.send_video(message.chat.id, open('tmp/video.mp4', 'rb'), timeout=20000)
        
        global IsSearch
        IsSearch = True
        
bot.polling(timeout=10, none_stop=True)

