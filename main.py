import os, asyncio, logging, yt_dlp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

API_TOKEN = '8748934991:AAGs8lDc_ZeRPuMHCxKVtYqHBnB0njdJuzU'
DOWNLOAD_PATH = 'downloads'
if not os.path.exists(DOWNLOAD_PATH): os.makedirs(DOWNLOAD_PATH)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

async def handle(request): return web.Response(text="Bot is running!")
async def run_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()

def get_ydl_opts(is_search=False):
    opts = {
        # 'best' позволяет скачать любое видео/аудио, если 'bestaudio' недоступно
        'format': 'bestaudio/best', 
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'cookiefile': 'cookies.txt', # ИСПОЛЬЗУЕМ ТВОЙ ФАЙЛ
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }
    if is_search:
        opts['default_search'] = 'ytsearch5'
        opts['noplaylist'] = True
    return opts

@dp.message(Command("start"))
async def start(m: types.Message): await m.answer("🎧 Бот авторизован! Пришли название.")

@dp.message(F.text & ~F.text.startswith('/'))
async def handle_search(m: types.Message):
    msg = await m.answer("🔎 Ищу варианты...")
    try:
        with yt_dlp.YoutubeDL(get_ydl_opts(is_search=True)) as ydl:
            res = ydl.extract_info(m.text, download=False).get('entries', [])
        if not res: return await msg.edit_text("Ничего не найдено. Обнови куки!")
        
        builder = InlineKeyboardBuilder()
        for e in res:
            builder.row(types.InlineKeyboardButton(text=e.get('title', 'Track')[:45], callback_data=f"dl:{e['id']}"))
        await msg.edit_text("Выбери вариант:", reply_markup=builder.as_markup())
    except Exception as e:
        await msg.edit_text(f"Ошибка поиска. Попробуй через 10 секунд.")

@dp.callback_query(F.data.startswith("dl:"))
async def download_callback(c: types.CallbackQuery):
    v_id = c.data.split(":")[1]
    url = f"https://www.youtube.com/watch?v={v_id}"
    await c.message.edit_text("⏳ Загружаю...")
    
    f_base = os.path.join(DOWNLOAD_PATH, f"{v_id}")
    f_mp3 = f_base + ".mp3"
    
    opts = get_ydl_opts()
    opts.update({'outtmpl': f_base, 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]})

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        await c.message.answer_audio(types.FSInputFile(f_mp3), caption="Твой трек! 🍉")
        await c.message.delete()
        if os.path.exists(f_mp3): os.remove(f_mp3)
    except Exception as e:
        await c.message.answer("YouTube отклонил запрос даже с куками. Попробуй другой вариант.")

async def main():
    # Решаем проблему Conflict (скриншоты 2 и 4)
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.gather(run_web_server(), dp.start_polling(bot))

if __name__ == "__main__": asyncio.run(main())
