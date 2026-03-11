import os
import asyncio
import logging
import yt_dlp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

API_TOKEN = '8748934991:AAGs8lDc_ZeRPuMHCxKVtYqHBnB0njdJuzU'
DOWNLOAD_PATH = 'downloads'

if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ВЕБ-СЕРВЕР ДЛЯ RENDER
async def handle(request):
    return web.Response(text="Бот в порядке!")

async def run_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# ОБНОВЛЕННЫЕ НАСТРОЙКИ ДЛЯ ОБХОДА БАНА
def get_ydl_opts(is_search=False):
    opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        # Эмуляция браузера
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/',
        'nocheckcertificate': True,
        'geo_bypass': True,
    }
    if is_search:
        opts['default_search'] = 'ytsearch5'
        opts['noplaylist'] = True
    return opts

def search_yt(query):
    with yt_dlp.YoutubeDL(get_ydl_opts(is_search=True)) as ydl:
        info = ydl.extract_info(query, download=False)
        return info['entries']

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(f"Привет! 🎧 Напиши название песни.")

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
                builder.row(types.InlineKeyboardButton(text=v_title, callback_data=f"dl:{v_id}"))
        await msg.edit_text("Выбери вариант:", reply_markup=builder.as_markup())
    except Exception as e:
        await msg.edit_text(f"Ошибка поиска: {e}\nПопробуй другое название.")

@dp.callback_query(F.data.startswith("dl:"))
async def download_callback(callback: types.CallbackQuery):
    video_id = callback.data.split(":")[1]
    url = f"https://www.youtube.com/watch?v={video_id}"
    await callback.message.edit_text("⏳ Загружаю музыку...")
    
    file_path_base = os.path.join(DOWNLOAD_PATH, f"{video_id}")
    file_path_mp3 = file_path_base + ".mp3"
    
    ydl_opts = get_ydl_opts()
    ydl_opts['outtmpl'] = file_path_base
    ydl_opts['postprocessors'] = [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        audio = types.FSInputFile(file_path_mp3)
        await callback.message.answer_audio(audio, caption="Твой вайб готов! 🍉")
        await callback.message.delete()
        if os.path.exists(file_path_mp3):
            os.remove(file_path_mp3)
    except Exception as e:
        await callback.message.answer(f"YouTube заблокировал этот трек. Попробуй другой вариант из списка.")

async def main():
    await asyncio.gather(run_web_server(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
