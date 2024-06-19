import requests
from bs4 import BeautifulSoup
import telebot
from telebot import types
import json
# для названий функций
import inspect

# Ваш токен Telegram бота
TOKEN = '6857842585:AAFC_LLP4J2lyWtiQV-rWn7GVnhAplVpT0o'
bot = telebot.TeleBot(TOKEN)

steam_urls = ['https://store.steampowered.com/app/271590/Grand_Theft_Auto_V/',
              'https://store.steampowered.com/app/632470/Disco_Elysium__The_Final_Cut/',
              'https://store.steampowered.com/app/1139900/Ghostrunner/',
              'https://store.steampowered.com/app/2050650/Resident_Evil_4/',
              'https://store.steampowered.com/app/391540/Undertale/',
              'https://store.steampowered.com/app/550/Left_4_Dead_2/',
              'https://store.steampowered.com/app/2124490/SILENT_HILL_2/',
              'https://store.steampowered.com/app/217980/Dishonored/',
              'https://store.steampowered.com/app/22490/Fallout_New_Vegas/',
              'https://store.steampowered.com/app/238010/Deus_Ex_Human_Revolution__Directors_Cut/',
              'https://store.steampowered.com/app/1091500/Cyberpunk_2077/',
              'https://store.steampowered.com/app/292030/_3/',
              'https://store.steampowered.com/app/374320/DARK_SOULS_III/',
              'https://store.steampowered.com/app/1086940/Baldurs_Gate_3/',
              'https://store.steampowered.com/app/1174180/Red_Dead_Redemption_2/',
              'https://store.steampowered.com/app/632470/Disco_Elysium__The_Final_Cut/',
              'https://store.steampowered.com/app/1687950/Persona_5_Royal/',
              'https://store.steampowered.com/app/489830/The_Elder_Scrolls_V_Skyrim_Special_Edition/',
              ]
# ?l=russian
current_game_index = 0


# Обработчик команды /gta
@bot.message_handler(commands=['help'])
def send_game_info(message):
    global current_game_index
    try:
        if current_game_index < len(steam_urls):
            lang_code = message.from_user.language_code if message.from_user.language_code else "en"
            lang_name = get_language_name(lang_code)
            steam_url = f'{steam_urls[current_game_index]}?l={lang_name}'
            # print(message.from_user.language_code)
            # print(lang_name)
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

                markup = types.InlineKeyboardMarkup()
                system_requirements_button = types.InlineKeyboardButton(
                    text="SYSTEM REQUIREMENTS",
                    callback_data=f"system|{current_game_index}"
                )
                markup.add(system_requirements_button)

                # Отправляем информацию в чат Telegram
                bot.send_message(message.chat.id, f"{full_inform}", parse_mode='html',
                                 disable_web_page_preview=True, reply_markup=markup)
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

    cost_game = get_cost_game(soup)

    full_inform = (f"<code >{title}\n</code>"
                   f"{description}\n"
                   f"{rating_on_Steam if rating_on_Steam else ''}"
                   f"{rating_on_Metacritic if rating_on_Metacritic else ''}"
                   f"\n{release_date_info}"
                   f"\n{developer_info}"
                   f"\n{publisher_info}"
                   f"\n{genre}"
                   f"{'\n' + franchise if franchise else ''}"
                   f"{'\n' + title_rating if title_rating else ''}"
                   f"\n{cost_game if cost_game else 'None'}")

    system_requirements = get_system_requirements(soup)
    # !!!!!
    about_game = get_about_this_game(soup)
    platforms = get_platforms(soup)

    save_full_name_to_json(title, description, rating_on_Steam, rating_on_Metacritic, release_date_info, developer_info,
                           publisher_info, genre, franchise, title_rating,cost_game, system_requirements)

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
        formatted_series = None

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

        if len(key_elements) > 1 and len(value_elements) > 5:
            key = key_elements[1].text.strip()
            value0 = value_elements[1].text.strip()
            value1 = soup.find_all('span', {'class': 'responsive_hidden'})[1].text.strip()
            value2 = soup.find_all('span', {'class': 'nonresponsive_hidden responsive_reviewdesc'})[1].text
            value2 = value2.split('<br>')[0].strip()

            rating = f"\n{key} {value0} {value1} {value2}\n"
            return rating
        else:
            return None
    except Exception as e:
        function_name = inspect.currentframe().f_code.co_name
        print(f"Error in {function_name}:\n({e})")
        return None


def get_rating_on_Metacritic(soup):
    try:
        name_metacritic = soup.find('div', {'class': 'metacritic'})
        if name_metacritic:
            name_metacritic = name_metacritic.text.capitalize()
            value_metacritic = soup.find('div', {'class': 'score'}).text.strip()
            link_metacritic = soup.find('div', {'id': 'game_area_metalink'})
            link_metacritic = link_metacritic.find('a').get('href')
            info_metacritic = f"\n{name_metacritic}: <a href=\"{link_metacritic}\">{value_metacritic}%</a>\n"

            return info_metacritic
        else:
            return None
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
        return None


# ('NoneType' object has no attribute 'get_text')
def get_title_rating(soup):
    try:
        title_rating_name = soup.find('div', {'class': 'game_rating_agency'})
        if title_rating_name:
            title_rating_name = title_rating_name.text.strip()

            title_rating_number_tag = soup.find('div', {'class': 'game_rating_icon'})
            title_rating_number = title_rating_number_tag.text.strip()

            title_rating_number_tag = soup.find('div', {'class': 'game_rating_icon'})
            title_rating_number = title_rating_number_tag.text.strip()

            rating_mapping = {
                '18': '18+',
                '16': '16+',
                '12': '12+',
                '7': '7+',
                '3': '3+',
            }

            rating_key = next(
                (key for key in rating_mapping.keys() if key in title_rating_number_tag.find('img', src=True)['src']),
                None)
            title_rating_number = rating_mapping.get(rating_key, '0+')

            title_rating_descriptors = soup.find('p', {'class': 'descriptorText'})
            if title_rating_descriptors:
                title_rating_descriptors = title_rating_descriptors.get_text(", ", strip=True)
                title_rating_descriptors = f"({title_rating_descriptors})"
            else:
                title_rating_descriptors = ""

            title_rating = (f"{title_rating_name} {title_rating_number} {title_rating_descriptors}")

            return title_rating
        else:
            return None
    except Exception as e:
        function_name = inspect.currentframe().f_code.co_name
        print(f"Error in {function_name}:\n({e})")
        return None


# надо обработать em, b, u, s или strike, sub, sup
# поиск img, br, li переделать в отдельные сообщения img1 и текс после фото это 1 сообщение,img2 и текс после фото это 2 сообщение и т.д.
def get_about_this_game(soup):
    game_area_description = soup.find('div', {'id': 'game_area_description'})

    if game_area_description:
        print(game_area_description)

        for h2_tag in game_area_description.find_all('h2'):
            h2_tag.string = f"\033[1m{h2_tag.get_text(strip=True).upper()}\033[0m"

        for strong_tag in game_area_description.find_all('strong'):
            strong_tag.string = f"\033[1m{strong_tag.get_text(strip=True)} \033[0m"

        for i_tag in game_area_description.find_all('i'):
            i_tag.string = f"\033[3m{i_tag.get_text(strip=True)}\033[0m"

        for li_tag in game_area_description.find_all('li'):
            li_tag.string = f"\u2022 {li_tag.get_text(strip=True)}\n"

        about_game_text = game_area_description.get_text("\n", strip=True)
        print(about_game_text)
        return about_game_text
    return None


def get_cost_game(soup):
    try:
        if (panel_cost := soup.find('div', {'class': 'game_purchase_action'})):
            print(f"\033[94m{panel_cost}\033[0m")
            if (cost_game := panel_cost.find('div', {'class': 'game_purchase_price price'})):
                cost_game = cost_game.text.strip()
                print(f"\033[92mPrice: {cost_game}\033[0m")

            elif (discount_original_price := panel_cost.find('div', {'class': 'discount_original_price'})):
                if (special_offer := soup.find('p', {'class': 'game_purchase_discount_countdown'})):
                    special_offer = special_offer.text.strip()
                    print(special_offer)

                discount_original_price = discount_original_price.text.strip()
                print("\033[9m" + discount_original_price + "\033[0m")
                discount_original_price = f"<s>{discount_original_price}</s>"

                discount_percentage = panel_cost.find('div', {'class': 'discount_pct'})
                discount_percentage = discount_percentage.text.strip()
                print(discount_percentage)

                discount_final_price = panel_cost.find('div', {'class': 'discount_final_price'})
                discount_final_price = discount_final_price.text.strip()
                print(discount_final_price)
                discount_final_price = f"<b><u>{discount_final_price}</u></b>"

                cost_game = (f"{special_offer + '\n' if special_offer else ''}"
                             f"{discount_final_price}   ({discount_percentage} |{discount_original_price}|)")

            elif (panel_cost.find('div', {'id': 'demoGameBtn'})):
                # Найти тег 'a' внутри 'div'
                a_tag = panel_cost.find('a')

                # Получить атрибут 'href'
                href = a_tag.get('href')

                # Извлечь текст из атрибута 'href'
                text = href.split(',')[1].strip().replace('"', '')

                print(f"\033[7m{text}\033[0m")  # Выведет: Resident Evil 4 Chainsaw Demo

                if (next_panel_cost := panel_cost.find_next('div', {'class': 'game_purchase_action'})):
                    if (next_cost_game := next_panel_cost.find('div', {'class': 'game_purchase_price price'})):
                        next_cost_game = next_cost_game.text.strip()
                        print(f"\033[6mPrice: {next_cost_game}\033[0m")

                    elif (discount_original_price := next_panel_cost.find('div', {'class': 'discount_original_price'})):
                        if (special_offer := soup.find('p', {'class': 'game_purchase_discount_countdown'})):
                            special_offer = special_offer.text.strip()
                            print(special_offer)

                        discount_original_price = discount_original_price.text.strip()
                        print("\033[9m" + discount_original_price + "\033[0m")

                        discount_percentage = next_panel_cost.find('div', {'class': 'discount_pct'})
                        discount_percentage = discount_percentage.text.strip()
                        print(discount_percentage)

                        discount_final_price = next_panel_cost.find('div', {'class': 'discount_final_price'})
                        discount_final_price = discount_final_price.text.strip()
                        print(discount_final_price)

                cost_game = (f"{text}"
                             f"{'\n' + special_offer if special_offer else ""}"
                             f"{'\n' + next_cost_game if next_cost_game else ''} "
                             f"{'\n' + discount_final_price if discount_final_price else ''}   ({discount_percentage if discount_percentage else ''}   {discount_original_price if discount_original_price else ''})")

            elif (discount_final_price := soup.find('div', {'class': 'discount_final_price'})):
                discount_final_price = discount_final_price.text.strip()
                cost_game = discount_final_price

            if (cost_game):
                return cost_game

            #         else:
            #             print("\033[93mError: No information about price\033[0m")
            #     else:
            #         print("\033[93mNo information about price\033[0m")
            else:
                print("\033[93mNo prices\033[0m")
        else:
            print("\033[93mNo price\033[0m")

            '''
            # Цена со скидкой во время распродаж

            game_area_description = soup.find('div', {'class': 'discount_final_price'})
            if game_area_description:
                # СПЕЦИАЛЬНОЕ ПРЕДЛОЖЕНИЕ!
                cost_game_text3 = soup.find('p', {'class': 'game_purchase_discount_countdown'})
                print(cost_game_text3)
                if cost_game_text3:
                    cost_game_text3 = cost_game_text3.text
                    special_offer = cost_game_text3.split('!')[0].strip() + "!"
                    print(special_offer)
                else:
                    print("\033[91mNo game_purchase_discount_countdown\033[0m")

                    cost_game_text1 = soup.find('div', {'class': 'discount_original_price'})
                    if cost_game_text1:
                        cost_game_text1 = cost_game_text1.text
                        print("\033[9m" + cost_game_text1 + "\033[0m")

                        cost_game_text2 = soup.find('div', {'class': 'discount_pct'}).text
                        print(cost_game_text2)

                        cost_game_text = game_area_description.text
                        print(cost_game_text)
                    else:
                        print("\033[93mNo game area description\033[0m")
            '''
        return None
    except Exception as e:
        function_name = inspect.currentframe().f_code.co_name
        print(f"Error in {function_name}:\n({e})")
        return None


def get_system_requirements(soup):
    try:
        list_system_requirements = soup.find('div', {'class': 'sysreq_contents'})
        if not list_system_requirements:
            print("System requirements section not found.")
            return None

        system_requirements = {}

        os_sections = list_system_requirements.find_all('div', {'class': 'game_area_sys_req'})

        for section in os_sections:
            os_type = section['data-os']
            requirements = {
                'minimum': {},
                'recommended': {}
            }

            left_col = section.find('div', {'class': 'game_area_sys_req_leftCol'})
            right_col = section.find('div', {'class': 'game_area_sys_req_rightCol'})

            if left_col:
                min_title = left_col.find('strong')
                if min_title and ('Минимальные' in min_title.text or 'Minimum' in min_title.text):
                    min_list = min_title.find_next_sibling('ul', {'class': 'bb_ul'})
                    for li in min_list.find_all('li'):
                        key_value = li.get_text().split(':', 1)
                        if len(key_value) == 2:
                            key, value = key_value
                            requirements['minimum'][key.strip()] = value.strip()

            if right_col:
                rec_title = right_col.find('strong')
                if rec_title and ('Recommended' in rec_title.text or 'Рекомендованные' in rec_title.text):
                    rec_list = rec_title.find_next_sibling('ul', {'class': 'bb_ul'})
                    for li in rec_list.find_all('li'):
                        key_value = li.get_text().split(':', 1)
                        if len(key_value) == 2:
                            key, value = key_value
                            requirements['recommended'][key.strip()] = value.strip()

            system_requirements[os_type] = requirements
            print(os_type)
            print(requirements)

        return system_requirements



    except Exception as e:
        function_name = inspect.currentframe().f_code.co_name
        print(f"Error in {function_name}:\n({e})")
        return None


def get_platforms(soup):
    platform_icons = {
        "win": "Windows",
        "mac": "Mac",
        "linux": "Linux"
    }

    game_platforms = soup.find('div', {'class': 'game_area_purchase_platform'})
    if game_platforms:
        platform_tags = game_platforms.find_all('span', {'class': 'platform_img'})
        if platform_tags:

            platforms = []
            for platform_tag in platform_tags:
                platform_class = platform_tag['class'][1]
                platform_name = platform_icons.get(platform_class)
                if platform_name:
                    platforms.append(platform_name)

            print("Поддерживаемые платформы:", ', '.join(platforms))
        else:
            print("\033[93mNot platform!!!\033[0m")
    else:
        print("\033[93mNo platforms\033[0m")
    return None


@bot.callback_query_handler(func=lambda call: call.data.startswith("system|"))
def send_system_requirements(call):
    try:
        parts = call.data.split("|")
        if len(parts) == 2:
            game_index = int(parts[1])
            print(parts)

            steam_url = f'{steam_urls[game_index]}'
            response = requests.get(steam_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                system_requirements = get_system_requirements(soup)

                formatted_requirements = format_requirements(system_requirements)

                bot.send_message(call.message.chat.id, f"System Requirements:\n{formatted_requirements}", parse_mode='html')
            else:
                bot.send_message(call.message.chat.id, "Invalid callback data format")
        # steam_url = f'{steam_urls[current_game_index - 1]}'
        # response = requests.get(steam_url)
        # if response.status_code == 200:
        #     soup = BeautifulSoup(response.text, 'html.parser')
        #     system_requirements = get_system_requirements(soup)
        #     bot.send_message(call.message.chat.id, f"System Requirements:\n{system_requirements}", parse_mode='html')
        # else:
        #     bot.send_message(call.message.chat.id, f"Error: {response.status_code}")
    except Exception as e:
        function_name = inspect.currentframe().f_code.co_name
        print(f"Error in {function_name}:\n({e})")
        bot.reply_to(call.message, f"An error occurred: {str(e)}")


def format_requirements(requirements):
    formatted_text = ""
    for platform, reqs in requirements.items():
        formatted_text += f"<b>{platform.upper()}</b>\n\n"
        for level, specs in reqs.items():
            formatted_text += f"<i>{level.capitalize()}:</i>\n"
            for key, value in specs.items():
                formatted_text += f"<b>{key}</b>: {value}\n"
            formatted_text += "\n"
    return formatted_text

def save_full_name_to_json(title, description, rating_on_Steam, rating_on_Metacritic, release_date_info, developer_info,
                           publisher_info, genre, franchise, title_rating, cost_game, system_requirements):
    try:
        with open("full_info.json", "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        data = {}

    if title not in data:
        data[title] = {
            "full_name": title,
            "description": description,
            "rating_on_Steam": rating_on_Steam,
            "rating_on_Metacritic": rating_on_Metacritic,
            "release_date_info": release_date_info,
            "developer_info": developer_info,
            "publisher_info": publisher_info,
            "genre": genre,
            "franchise": franchise,
            "title_rating": title_rating,
            "cost_game": cost_game,
            "system_requirements": system_requirements
        }

        with open("full_info.json", "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)


# Запускаем бота
if __name__ == '__main__':
    bot.polling(none_stop=True)
