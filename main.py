import os, asyncio, logging, yt_dlp, random
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

async def handle(request): return web.Response(text="Bot is Active")
async def run_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()

def get_ydl_opts(v_id=None):
    opts = {
        # 'best' — это ключ. Если 'bestaudio' нет, он возьмет видео и вырежет звук.
        'format': 'bestaudio/best', 
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'cookiefile': 'cookies.txt', # Твой файл со скрина
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'extractor_args': {'youtube': {'player_client': ['android', 'web'], 'skip': ['hls', 'dash']}},
    }
    if v_id:
        opts['outtmpl'] = os.path.join(DOWNLOAD_PATH, f"{v_id}")
        opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        opts['default_search'] = 'ytsearch5'
        opts['noplaylist'] = True
    return opts

@dp.message(Command("start"))
async def start(m: types.Message): await m.answer("🎧 Бот на связи и видит Cookies! Кидай название.")

@dp.message(F.text & ~F.text.startswith('/'))
async def search(m: types.Message):
    msg = await m.answer("🔎 Ищу варианты...")
    try:
        # Небольшая пауза, чтобы YouTube не злился
        await asyncio.sleep(random.uniform(1, 2))
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            res = ydl.extract_info(m.text, download=False).get('entries', [])
        if not res: return await msg.edit_text("Ничего не нашел. Перепроверь куки!")
        
        kb = InlineKeyboardBuilder()
        for e in res:
            kb.row(types.InlineKeyboardButton(text=e.get('title')[:45], callback_data=f"dl:{e['id']}"))
        await msg.edit_text("Выбери трек:", reply_markup=kb.as_markup())
    except Exception as e:
        logging.error(f"Search error: {e}")
        await msg.edit_text("Ошибка поиска. YouTube вредничает, попробуй еще раз.")

@dp.callback_query(F.data.startswith("dl:"))
async def dl(c: types.CallbackQuery):
    v_id = c.data.split(":")[1]
    await c.message.edit_text("📥 Начинаю загрузку... Это может занять время.")
    f_p = os.path.join(DOWNLOAD_PATH, f"{v_id}.mp3")
    
    try:
        # Используем универсальные настройки
        with yt_dlp.YoutubeDL(get_ydl_opts(v_id)) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={v_id}"])
        
        await c.message.answer_audio(types.FSInputFile(f_p), caption="Твой вайб! 🍉")
        await c.message.delete()
    except Exception as e:
        logging.error(f"DL error: {e}")
        await c.message.answer("Не удалось скачать именно этот формат. Попробуй другой вариант из списка.")
    finally:
        if os.path.exists(f_p): os.remove(f_p)

async def main():
    # УБИВАЕМ TelegramConflictError со скринов
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.gather(run_web_server(), dp.start_polling(bot))

if __name__ == "__main__": asyncio.run(main())
