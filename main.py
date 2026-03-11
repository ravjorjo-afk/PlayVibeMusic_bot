import os
import asyncio
import logging
import yt_dlp
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# Токен твоего бота
API_TOKEN = '8748934991:AAGs8lDc_ZeRPuMHCxKVtYqHBnB0njdJuzU'
DOWNLOAD_PATH = 'downloads'

if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Веб-сервер для поддержания жизни на Render
async def handle(request):
    return web.Response(text="Bot is running with Cookies!")

async def run_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# Функция настроек с подключением COOKIES
def get_ydl_opts(is_search=False):
    opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'cookiefile': 'cookies.txt',  # Твой файл с авторизацией
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }
    if is_search:
        opts['default_search'] = 'ytsearch5'
        opts['noplaylist'] = True
    return opts

def search_yt(query):
    with yt_dlp.YoutubeDL(get_ydl_opts(is_search=True)) as ydl:
        info = ydl.extract_info(query, download=False)
        return info.get('entries', [])

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("🎧 Бот авторизован и готов! Какую песню ищем?")

@dp.message(F.text & ~F.text.startswith('http'))
async def handle_search(message: types.Message):
    msg = await message.answer("🔎 Минутку, ищу в базе...")
    try:
        results = search_yt(message.text)
        builder = InlineKeyboardBuilder()
        for entry in results:
            v_id = entry.get('id')
            v_title = entry.get('title', 'Track')[:45]
            if v_id:
                builder.row(types.InlineKeyboardButton(text=v_title, callback_data=f"dl:{v_id}"))
        if not results:
            await msg.edit_text("Ничего не нашел. Попробуй другое название.")
        else:
            await msg.edit_text("Выбери лучший вариант:", reply_markup=builder.as_markup())
    except Exception as e:
        await msg.edit_text(f"Ошибка поиска: {e}")

@dp.callback_query(F.data.startswith("dl:"))
async def download_callback(callback: types.CallbackQuery):
    video_id = callback.data.split(":")[1]
    url = f"https://www.youtube.com/watch?v={video_id}"
    await callback.message.edit_text("⏳ Начинаю загрузку... Это может занять до 30 секунд.")
    
    file_path_base = os.path.join(DOWNLOAD_PATH, f"{video_id}")
    file_mp3 = file_path_base + ".mp3"
    
    ydl_opts = get_ydl_opts()
    ydl_opts['outtmpl'] = file_path_base
    ydl_opts['postprocessors'] = [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }]

    try:
        # Небольшая пауза, чтобы не спамить запросами
        await asyncio.sleep(random.uniform(2, 4))
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        audio = types.FSInputFile(file_mp3)
        await callback.message.answer_audio(audio, caption="Приятного прослушивания! 🍉")
        await callback.message.delete()
        
        if os.path.exists(file_mp3):
            os.remove(file_mp3)
    except Exception as e:
        await callback.message.answer(f"YouTube всё равно блокирует этот файл. Попробуй другое видео из списка.")
        logging.error(f"Error: {e}")

async def main():
    # Очистка очереди обновлений, чтобы не было конфликтов
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.gather(run_web_server(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
