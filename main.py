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

async def handle(request): return web.Response(text="Bot is Live")
async def run_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()

def get_ydl_opts(is_search=False):
    return {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'cookiefile': 'cookies.txt',
        # ГЛАВНОЕ: Эмуляция клиента iOS, его меньше банят за поиск
        'extractor_args': {'youtube': {'player_client': ['ios'], 'skip': ['hls', 'dash']}},
        'default_search': 'ytsearch5' if is_search else None,
        'noplaylist': True,
        'user_agent': 'com.google.ios.youtube/19.29.1 (iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X;)'
    }

@dp.message(Command("start"))
async def start(m: types.Message): await m.answer("🎧 Жду название песни!")

@dp.message(F.text & ~F.text.startswith('/'))
async def handle_search(m: types.Message):
    msg = await m.answer("🔎 Ищу...")
    try:
        with yt_dlp.YoutubeDL(get_ydl_opts(is_search=True)) as ydl:
            res = ydl.extract_info(m.text, download=False).get('entries', [])
        if not res: return await msg.edit_text("Ничего не нашел.")
        kb = InlineKeyboardBuilder()
        for e in res: kb.row(types.InlineKeyboardButton(text=e.get('title', 'Track')[:45], callback_data=f"dl:{e['id']}"))
        await msg.edit_text("Выбери:", reply_markup=kb.as_markup())
    except: await msg.edit_text("Ошибка поиска. Попробуй другое слово.")

@dp.callback_query(F.data.startswith("dl:"))
async def dl(c: types.CallbackQuery):
    v_id = c.data.split(":")[1]
    url = f"https://www.youtube.com/watch?v={v_id}"
    await c.message.edit_text("⏳ Качаю...")
    f_p = os.path.join(DOWNLOAD_PATH, f"{v_id}")
    opts = get_ydl_opts()
    opts.update({'outtmpl': f_p, 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]})
    try:
        with yt_dlp.YoutubeDL(opts) as ydl: ydl.download([url])
        await c.message.answer_audio(types.FSInputFile(f_p + ".mp3"), caption="Готово! 🍉")
        await c.message.delete()
    except: await c.message.answer("Ошибка скачивания.")
    finally:
        if os.path.exists(f_p + ".mp3"): os.remove(f_p + ".mp3")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.gather(run_web_server(), dp.start_polling(bot))

if __name__ == "__main__": asyncio.run(main())
