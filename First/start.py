import requests
from bs4 import BeautifulSoup
import telebot
import json
# для названий функций
import inspect

# Ваш токен Telegram бота
TOKEN = '6857842585:AAFC_LLP4J2lyWtiQV-rWn7GVnhAplVpT0o'
bot = telebot.TeleBot(TOKEN)

steam_urls = ['https://store.steampowered.com/app/2124490/SILENT_HILL_2/',
              'https://store.steampowered.com/app/217980/Dishonored/',
              'https://store.steampowered.com/app/22490/Fallout_New_Vegas/',
              'https://store.steampowered.com/app/238010/Deus_Ex_Human_Revolution__Directors_Cut/',
              'https://store.steampowered.com/app/632470/Disco_Elysium__The_Final_Cut/',
              'https://store.steampowered.com/app/271590/Grand_Theft_Auto_V/',
              'https://store.steampowered.com/app/1091500/Cyberpunk_2077/',
              'https://store.steampowered.com/app/292030/_3/',
              'https://store.steampowered.com/app/374320/DARK_SOULS_III/',
              'https://store.steampowered.com/app/1086940/Baldurs_Gate_3/',
              'https://store.steampowered.com/app/1174180/Red_Dead_Redemption_2/',
              'https://store.steampowered.com/app/632470/Disco_Elysium__The_Final_Cut/',
              'https://store.steampowered.com/app/2050650/Resident_Evil_4/',
              'https://store.steampowered.com/app/1687950/Persona_5_Royal/',
              'https://store.steampowered.com/app/489830/The_Elder_Scrolls_V_Skyrim_Special_Edition/',
              'https://store.steampowered.com/app/550/Left_4_Dead_2/',
              'https://store.steampowered.com/app/391540/Undertale/',
              ]
current_game_index = 0


# Обработчик команды /gta
@bot.message_handler(commands=['help'])
def send_game_info(message):
    global current_game_index
    try:
        if current_game_index < len(steam_urls):
            lang_code = message.from_user.language_code if message.from_user.language_code else "en"
            lang_name = get_language_name(lang_code)
            # ?l=russian
            steam_url = f'{steam_urls[current_game_index]}?l={lang_name}'
            print(steam_url)

            # Запрашиваем страницу игры
            response = requests.get(steam_url)

            print(current_game_index + 1, len(steam_urls))
            if response.status_code == 200:
                # Используем BeautifulSoup для парсинга HTML
                soup = BeautifulSoup(response.text, 'html.parser')

                # image_url = soup.find('img', {'class': 'game_header_image_full'}).get('src')
                # # Отправляем изображение в чат Telegram
                # bot.send_photo(message.chat.id, image_url, caption="Название игры: <b>Some Game</b>", parse_mode='html')

                full_inform = get_full_inform(soup)

                # Отправляем информацию в чат Telegram
                bot.send_message(message.chat.id, f"{full_inform}", parse_mode='html',
                                 disable_web_page_preview=True)
                current_game_index += 1
            else:
                bot.send_message(message.chat.id, f"Error: {response.status_code}")
        else:
            bot.send_message(message.chat.id, "The END.")
    except Exception as e:
        function_name = inspect.currentframe().f_code.co_name
        print(f"Error in {function_name}:\n({e})")
        bot.reply_to(message, f"An error occurred: {str(e)}")


def get_full_inform(soup):
    # Извлекаем нужную информацию (например, название игры)
    title = soup.find('div', {'class': 'apphub_AppName'}).text.strip()
    description = soup.find('div', {'class': 'game_description_snippet'}).text.strip()

    rating_on_Steam = get_game_rating_on_Steam(soup)

    rating_on_Metacritic = get_rating_on_Metacritic(soup)

    # release_date_info = get_release_date(soup)

    developer_info, publisher_info, release_date_info = get_developer_and_publisher_and_release_info(soup)

    genre, franchise = get_genre_and_franchise_on_Steam(soup)

    title_rating = get_title_rating(soup)

    full_inform = (f"<code >{title}\n</code>"
                   f"{description}\n"
                   f"{rating_on_Steam}"
                   f"{rating_on_Metacritic}"
                   f"\n{release_date_info}"
                   f"\n{developer_info}"
                   f"\n{publisher_info}"
                   f"\n{genre}"
                   f"\n{franchise}"
                   f"\n{title_rating}")

    return full_inform


def get_language_name(code):
    language_names = {
        'ru': 'russian',
        'ua': 'ukrainian',
        'en': 'english',
        # Добавьте другие языки при необходимости
    }
    # Преобразовываем код языка в его полное название
    return language_names.get(code.lower(), code)


def get_genre_and_franchise_on_Steam(soup):
    # Извлекаем нужную информацию
    details_block = soup.find('div', {'id': 'genresAndManufacturer'})

    details_quantity = details_block.find_all('b')
    # Ищем пятый тег <b> (Серия игр)
    if len(details_quantity) > 5:
        series_tag = details_quantity[4]
        series_text = series_tag.find_next('a').get_text(strip=True)
        formatted_series = f"{series_tag.text} {series_text}"
    else:
        print("Тег 'Серия игр' не найден.")
        formatted_series = ""

    # Ищем второй тег <b> (Жанр)
    genre_name = details_quantity[1]

    # Извлекаем текст из тега <span>
    # genre_value = ', '.join(a.get_text(strip=True) for a in genre_name.find_next('span').find_all('a'))
    genre_value = genre_name.find_next('span').find_all('a')
    genre_value = ', '.join(str(tag) for tag in genre_value)
    # Форматируем и выводим результат
    formatted_genre = f"{genre_name.text} {genre_value}"

    return formatted_genre, formatted_series


def get_game_rating_on_Steam(soup):
    try:
        key_elements = soup.find_all('div', {'class': 'subtitle column all'})
        value_elements = soup.find_all('span', {'class': 'game_review_summary'})

        if len(key_elements) > 1 and len(value_elements) > 1:
            key = key_elements[1].text.strip()
            value0 = value_elements[1].text.strip()
            value1 = soup.find_all('span', {'class': 'responsive_hidden'})[1].text.strip()
            value2 = soup.find_all('span', {'class': 'nonresponsive_hidden responsive_reviewdesc'})[1].text
            value2 = value2.split('<br>')[0].strip()

            rating = f"\n{key} {value0} {value1} {value2}\n"
            return rating
        else:
            return ""
    except Exception as e:
        function_name = inspect.currentframe().f_code.co_name
        print(f"Error in {function_name}:\n({e})")
        return None


def get_rating_on_Metacritic(soup):
    try:
        name_metacritic = soup.find('div', {'class': 'metacritic'})
        if name_metacritic:
            name_metacritic = name_metacritic.text.capitalize()
            value_metacritic = soup.find('div', {'class': 'score high'}).text.strip()
            link_metacritic = soup.find('div', {'id': 'game_area_metalink'})
            link_metacritic = link_metacritic.find('a').get('href')
            info_metacritic = f"\n{name_metacritic}: <a href=\"{link_metacritic}\">{value_metacritic}%</a>\n"

            return info_metacritic
        else:
            return ""
    except Exception as e:
        function_name = inspect.currentframe().f_code.co_name
        print(f"Error in {function_name}:\n({e})")
        return None


# def get_release_date(soup):
#     date_elements = soup.find('div', {'class': 'release_date'})
#     date_key = date_elements.find('div', {'class': 'subtitle column'}).text.strip()
#     date_value = date_elements.find('div', {'class': 'date'}).text.strip()
#
#     date_info = f"{date_key} {date_value}"
#
#     return date_info


def get_developer_and_publisher_and_release_info(soup, label_class='grid_label', content_class='grid_content'):
    name_elements = soup.find_all('div', {'class': label_class})
    values_elements = soup.find_all('div', {'class': content_class})

    if name_elements and values_elements:
        developer_label = name_elements[0].text.strip()
        publisher_label = name_elements[1].text.strip()

        developer_link = values_elements[0].find('a')
        publisher_link = values_elements[1].find('a')

        date_of_release_name = name_elements[2].text
        date_of_release_value = soup.find('div', {'class': 'grid_content grid_date'}).text.strip()
        date_of_release = f"{date_of_release_name}: {date_of_release_value}"

        developer_info = f'{developer_label} {developer_link}'
        publisher_info = f'{publisher_label} {publisher_link}'

        return developer_info, publisher_info, date_of_release
    else:
        return ""


# ('NoneType' object has no attribute 'get_text')
def get_title_rating(soup):
    try:
        title_rating_name = soup.find('div', {'class': 'game_rating_agency'})
        if title_rating_name:
            title_rating_name = title_rating_name.text.strip()

            title_rating_number_tag = soup.find('div', {'class': 'game_rating_icon'})
            title_rating_number = title_rating_number_tag.text.strip()
            if '18' in title_rating_number_tag.find('img', src=True)['src']:
                title_rating_number = '18+'
            elif '16' in title_rating_number_tag.find('img', src=True)['src']:
                title_rating_number = '16+'
            elif '12' in title_rating_number_tag.find('img', src=True)['src']:
                title_rating_number = '12+'
            elif '7' in title_rating_number_tag.find('img', src=True)['src']:
                title_rating_number = '7+'
            elif '3' in title_rating_number_tag.find('img', src=True)['src']:
                title_rating_number = '3+'
            else:
                title_rating_number = '0+'

            title_rating_descriptors = soup.find('p', {'class': 'descriptorText'})
            if title_rating_descriptors:
                title_rating_descriptors = title_rating_descriptors.get_text(", ", strip=True)
                title_rating_descriptors = f"({title_rating_descriptors})"
            else:
                title_rating_descriptors = ""

            title_rating = (f"{title_rating_name} {title_rating_number} {title_rating_descriptors}")

            return title_rating
        else:
            return ""
    except Exception as e:
        function_name = inspect.currentframe().f_code.co_name
        print(f"Error in {function_name}:\n({e})")
        return None


# Запускаем бота
if __name__ == '__main__':
    bot.polling()
