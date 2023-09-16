import aiofiles
from PIL import Image, ImageDraw, ImageFont
import io


async def generate_profile_stats_for_worker(telegram_id, balance, profit, warnings, payment_method):
    # Открываем изображение
    async with aiofiles.open('software programming.png', mode='rb') as image_file:
        image_data = await image_file.read()

    image = Image.open(io.BytesIO(image_data))

    # Создаем объект ImageDraw для рисования на изображении
    draw = ImageDraw.Draw(image)

    # Задаем шрифт (Montserrat)
    font = ImageFont.truetype('Montserrat-VariableFont_wght.ttf', size=96)

    # Задаем координаты и текст, который вы хотите добавить
    text = "0"
    x, y = 165, 330  # Координаты, где будет размещен текст

    # Указываем цвет текста (в данном случае, белый)
    text_color = (0, 0, 0)

    # Добавляем текст на изображение
    draw.text((x - 40, y), balance, font=font, fill=text_color)
    draw.text((x - 40, y + 275), profit, font=font, fill=text_color)
    draw.text((x, y + 275 * 2), warnings, font=font, fill=text_color)
    draw.text((x - 12, (y + 275 * 3) + 40), payment_method.split(' ')[1], font=ImageFont.truetype('Montserrat-VariableFont_wght.ttf', size=36), fill=text_color)

    # Сохраняем измененное изображение
    async with aiofiles.open(f'{telegram_id}.png', mode='wb') as output_file:
        await output_file.write(image.tobytes())

    # Закрываем изображение
    image.close()
