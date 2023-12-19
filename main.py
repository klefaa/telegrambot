import os
from io import BytesIO

import requests
import telebot
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
from telebot import types

load_dotenv()

bot = telebot.TeleBot(os.getenv('TOKEN_BOT'))


@bot.message_handler(commands=["start"])
def start(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    strings = ["котик", "собачка", "лисичка", "уточка", "фильм", "погода пермь", "генератор предсказаний (да/нет)"]
    for s in strings:
        markup.add(s)
    bot.send_message(m.chat.id,
                     'Привет 👋, меня зовут thegreatestbot')

    bot.send_message(m.chat.id,
                     'Я могу:\n' +
                     '1) Выдать фото случайного котика\n' +
                     '2) Выдать фото или видео случайной собачки\n' +
                     '3) Выдать фото случайной лисы\n' +
                     '4) Выдать фото случайной утки\n' +
                     '5) Выдать случайный фильм, информация о котором есть на Кинопоиске\n' +
                     '6) Выдать прогноз погоды\n' +
                     '7) Ответить на интересующий тебя вопрос гифкой Да/Нет\n' +
                     '8) Отправь мне картинку и я превращу ее в текст',
                     reply_markup=markup)


@bot.message_handler(commands=["cat"])
def cat(m):
    api_url = "https://api.thecatapi.com/v1/images/search"
    response = requests.get(api_url)
    if response.status_code != 200:
        return bot.send_message(m.chat.id, "простите, сайтик с котиками упал и спить(")
    data = response.json()
    if not data:
        return bot.send_message(m.chat.id, "котик спить, поэтому он не пришел(")
    response = requests.get(data[0]["url"])
    if response.status_code != 200:
        return bot.send_message(m.chat.id, "котик спить, поэтому он не пришел(")
    bot.send_photo(m.chat.id, response.content)


def compress_image(image_url, max_size=2 * 1024 * 1024):
    response = requests.get(image_url)
    if response.status_code != 200:
        return None
    data = response.content
    size = len(data)
    if size > max_size:
        img = Image.open(BytesIO(data))
        img.thumbnail((800, 600))
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        return buffer.getvalue()
    return data


def send_image_or_video(m, url):
    if "mp4" in url:
        response = requests.get(url)
        if response.status_code == 200:
            bot.send_video(m.chat.id, response.content)
    else:
        compressed_image = compress_image(url)
        if compressed_image:
            bot.send_photo(m.chat.id, compressed_image)
        else:
            bot.send_message(m.chat.id, "Не удалось загрузить изображение.")


@bot.message_handler(commands=["dog"])
def dog(m):
    api_url = "https://random.dog/woof.json"
    response = requests.get(api_url)
    if response.status_code != 200:
        return bot.send_message(m.chat.id, "простите, сайтик с песиками упал и спит(")
    data = response.json()
    if not data:
        return bot.send_message(m.chat.id, "песик спит, поэтому он не пришел(")
    send_image_or_video(m, data["url"])

@bot.message_handler(commands=["film"])
def film(m):
    header = {
        "X-API-KEY": os.getenv('TOKEN_FILM')
    }
    response = requests.get("https://api.kinopoisk.dev/v1.3/movie/random", headers=header)

    if response.status_code != 200:
        return bot.send_message(m.chat.id, "простите, сайтик с фильмами упал(")

    data = response.json()

    if not data:
        return bot.send_message(m.chat.id, "фильмы умерли")

    name = data["name"]
    description = data.get("description", "отсутствует")
    rating_kp = data["rating"].get("kp", "отсутствует")
    rating_imdb = data["rating"].get("imdb", "отсутствует")
    genres = ", ".join([i["name"] for i in data.get("genres", [])])
    try:
        trailers = "\n".join([i["url"] for i in data["videos"].get("trailers", [])])
    except Exception:
        trailers = "нетю"
    poster_url = data["poster"]["url"]

    bot.send_photo(m.chat.id, poster_url, caption=f"""
Название: {name}

Описание: {description}

Рейтинг Кинопоиска: {rating_kp}
Рейтинг IMDB: {rating_imdb}
Жанры: {genres}
Трейлеры: 
{trailers}
    """)


@bot.message_handler(commands=["description"])
def description(m, res=False):
    bot.send_message(m.chat.id, """
    Бот создан Кокоулиной Мариной в некоммерческих целях
    """)


def edit_num(n):
    return int(n * 10) / 10


@bot.message_handler(commands=["weather"])
def weather(message):
    try:
        city = message.text.split(" ", 1)[1]
        api_url = "http://api.openweathermap.org/geo/1.0/direct?q=" + city + "&appid=" + os.getenv('TOKEN_OPENWEATHER')
        response = requests.get(api_url)
        if response.status_code != 200:
            return bot.send_message(message.chat.id, "простите, сайтик с погодой усталь")
        response = response.json()
        lat = response[0]["lat"]
        lon = response[0]["lon"]
        api_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&" \
                  f"appid={os.getenv('TOKEN_OPENWEATHER')}&cnt=1"
        response = requests.get(api_url)
        if response.status_code != 200:
            return bot.send_message(message.chat.id, "простите, сайтик с погодой усталь")
        response = response.json()
        temp = edit_num(response["main"]["temp"] - 273.15)
        feels_like = edit_num(response["main"]["feels_like"] - 273.15)
        min_temp = edit_num(response["main"]["temp_min"] - 273.15)
        max_temp = edit_num(response["main"]["temp_max"] - 273.15)
        wind_speed = edit_num(response["wind"]["speed"])
        if temp < -20:
            ans = "сидим дома, там холодно и страшно("
        elif temp < 0:
            ans = "холодно но неочень.."
        elif temp < 10:
            ans = "на улице прохладно"
        elif temp < 20:
            ans = "на улице нормик погода"
        elif temp < 30:
            ans = "где вентилятор?"
        else:
            ans = "переезжаем в холодильник"
        bot.send_message(message.chat.id, f"""
    {ans}
температура сейчас: {temp}
ощущается как: {feels_like}
минимальная температура: {min_temp}
максимальная температура: {max_temp}
скорость ветра: {wind_speed}
        """)
    except Exception:
        bot.send_message(message.chat.id, f"Команда должна содержать город")


@bot.message_handler(commands=["help"])
def description(m, res=False):
    bot.send_message(m.chat.id, """
Макарони бот умеет:
/help - список команд
/description - описание бота
/cat - фотография случайного котика
/dog - фотография случайной собачки
/fox - фотография случайной лисы
/duck - фотография случайной утки
/film - случайный фильм
/weather "название города" - данные о погоде в данный момент в указанном городе 
/yesno - предсказание да/нет
""")


@bot.message_handler(commands=["yesno"])
def joke(message):
    response = requests.get("https://yesno.wtf/api")
    if response.status_code != 200:
        return bot.send_message(message.chat.id, "кончились хиханьки хаханьки")
    gif_response = requests.get(response.json()["image"])
    if gif_response.status_code != 200:
        return bot.send_message(message.chat.id, "кончились хиханьки хаханьки")
    bot.send_document(message.chat.id, ("gif.gif", gif_response.content))


@bot.message_handler(commands=["fox"])
def fox(message):
    response = requests.get("https://randomfox.ca/floof/")
    if response.status_code != 200:
        return bot.send_message(message.chat.id, "кончились лисички сестрички")
    response = requests.get(response.json()["image"])
    if response.status_code != 200:
        return bot.send_message(message.chat.id, "кончились лисички сестрички")
    bot.send_photo(message.chat.id, response.content)


@bot.message_handler(commands=["duck"])
def duck(message):
    response = requests.get("https://random-d.uk/api/random")
    if response.status_code != 200:
        return bot.send_message(message.chat.id, "кончились уточки")
    response = requests.get(response.json()["url"])
    if response.status_code != 200:
        return bot.send_message(message.chat.id, "кончились уточки")
    bot.send_photo(message.chat.id, response.content)


# Пример использования:
# send_gif(message, bot)


# Получение сообщений от юзера
@bot.message_handler(content_types=["text"])
def handle_text(message):
    answer = "Используй одну из доступных команд /help или отправь картинку"
    if message.text.strip().lower() == "котик":
        cat(message)
        return
    elif message.text.strip().lower() == "фильм":
        film(message)
        return
    elif message.text.strip().lower() == "собачка":
        dog(message)
        return
    elif message.text.strip().lower() == "лисичка":
        fox(message)
        return
    elif message.text.strip().lower() == "уточка":
        duck(message)
        return
    elif message.text.strip().lower() == "генератор предсказаний (да/нет)":
        joke(message)
        return
    elif message.text.strip().lower().find("погода ") == 0:
        weather(message)
        return
    bot.send_message(message.chat.id, answer)


@bot.message_handler(content_types=["document"])
def handle_document(message):
    if message.document.mime_type.startswith('image'):
        file_info = bot.get_file(message.document.file_id)
        file = bot.download_file(file_info.file_path)

        image = Image.open(BytesIO(file))

        if 'exif' in image.info:
            exif = image.info['exif']
            image = Image.open(BytesIO(file))
            image = image.rotate(0, expand=True)
            image = Image.open(BytesIO(file))
            image = image.rotate(90, expand=True)
            image = Image.open(BytesIO(file))
            image = image.rotate(180, expand=True)
            image = Image.open(BytesIO(file))
            image = image.rotate(270, expand=True)

        new_width = image.width // 2
        new_height = image.height // 2
        image = image.resize((new_width, new_height))

        # Конвертируйте изображение в ASCII-арт
        ascii_image = img_redactor(image)
        ascii_image.save("ascii_art.png", "PNG")
        with open("ascii_art.png", "rb") as doc_file:
            bot.send_document(message.chat.id, doc_file)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, отправьте изображение в качестве файла.")


@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    photo = message.photo[-1]
    file_info = bot.get_file(photo.file_id)
    file = bot.download_file(file_info.file_path)
    image = Image.open(BytesIO(file))
    ascii_image = img_redactor(image)
    ascii_image.save("ascii_art.png", "PNG")
    with open("ascii_art.png", "rb") as doc_file:
        bot.send_document(message.chat.id, doc_file)
        bot.send_photo(message.chat.id, ascii_image)


def img_redactor(image):
    def pixel_to_ascii(pixel):
        grayscale = 0.2126 * pixel[0] + 0.7152 * pixel[1] + 0.0722 * pixel[2]
        index = int((grayscale / 255) * (len(ASCII_CHARS) - 1))
        return ASCII_CHARS[index]

    ASCII_CHARS = ".:!/r(l1Z4H9W8$@"
    ORIGINAL_WIDTH, ORIGINAL_HEIGHT = image.size

    new_width = ORIGINAL_WIDTH // 4
    new_height = ORIGINAL_HEIGHT // 4

    resized_image = image.resize((new_width, new_height))

    ascii_text = ""
    char_width = 8
    char_height = 8

    for i in range(new_height):
        for j in range(new_width):
            pixel = resized_image.getpixel((j, i))
            ascii_text += pixel_to_ascii(pixel)
        ascii_text += "\n"

    image_width = char_width * len(ascii_text.split('\n')[0])
    image_height = char_height * len(ascii_text.split('\n'))

    ascii_image = Image.new('RGB', (image_width, image_height), (0, 0, 0))
    draw = ImageDraw.Draw(ascii_image)
    font = ImageFont.load_default()

    lines = ascii_text.split('\n')
    for i, line in enumerate(lines):
        for j, char in enumerate(line):
            draw.text((j * char_width, i * char_height), char, (255, 255, 255), font=font)

    return ascii_image


if __name__ == "__main__":
    bot.polling(none_stop=True, interval=0)
