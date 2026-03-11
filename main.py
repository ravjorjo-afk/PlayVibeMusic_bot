import os
import asyncio
import logging
import yt_dlp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Настройки
API_TOKEN = '8748934991:AAGs8lDc_ZeRPuMHCxKVtYqHBnB0njdJuzU'
DOWNLOAD_PATH = 'downloads'

if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def search_yt(query):
    # Добавили настройки, чтобы поиск был точнее
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'default_search': 'ytsearch5',
        'quiet': True,
        'no_warnings': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        return info['entries']

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(f"Привет, {message.from_user.first_name}! 🎧\nНапиши название песни, и я найду её для тебя.")

@dp.message(F.text & ~F.text.startswith('http'))
async def handle_search(message: types.Message):
    msg = await message.answer("🔎 Ищу варианты...")
    try:
        results = search_yt(message.text)
        builder = InlineKeyboardBuilder()
        
        for entry in results:
            v_id = entry.get('id')
            v_title = entry.get('title', 'Без названия')[:45]
            if v_id:
                # Используем префикс "dl:", чтобы точно передать ID
                builder.row(types.InlineKeyboardButton(text=v_title, callback_data=f"dl:{v_id}"))
        
        if not results:
            await msg.edit_text("Ничего не нашлось 😔")
        else:
            await msg.edit_text("Выбери вариант:", reply_markup=builder.as_markup())
            
    except Exception as e:
        await msg.edit_text(f"Ошибка поиска: {e}")

@dp.callback_query(F.data.startswith("dl:"))
async def download_callback(callback: types.CallbackQuery):
    # Извлекаем ID после двоеточия
    video_id = callback.data.split(":")[1]
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    await callback.message.edit_text("⏳ Начинаю загрузку... Это займет секунд 15.")
    
    # Путь к файлу
    file_path = os.path.join(DOWNLOAD_PATH, f"{video_id}.mp3")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_PATH, f"{video_id}"),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }

    try:
        # Проверяем наличие ffmpeg прямо перед загрузкой
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        audio = types.FSInputFile(file_path)
        await callback.message.answer_audio(audio, caption="Твой вайб готов! 🍉")
        await callback.message.delete()
        
        # Удаляем временный файл
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        await callback.message.answer(f"Ошибка при обработке: {e}\nУбедись, что ffmpeg.exe лежит в папке с main.py")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())