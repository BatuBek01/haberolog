import os
import asyncio
from flask import Flask
from telegram import Bot
import feedparser
from datetime import datetime, timezone
import html

app = Flask(__name__)

# Bot token ve kanal ID'sini çevre değişkenlerinden al
TOKEN = os.getenv('TELEGRAM_TOKEN')  # Render'da çevre değişkeni ayarlayın
CHANNEL_ID = os.getenv('CHANNEL_ID')

# RSS feed URL'si
RSS_FEED_URL = 'https://www.ensonhaber.com/rss/ensonhaber.xml'

last_checked_date = None

async def send_news_with_image(bot, entry):
    title = html.unescape(entry.title.upper())
    summary = html.unescape(entry.summary)

    image_url = entry.media_content[0]['url'] if 'media_content' in entry and entry.media_content else None

    news_text = f"*{title}*\n\n{summary}"

    try:
        if image_url:
            await bot.send_photo(chat_id=CHANNEL_ID, photo=image_url, caption=news_text, parse_mode='Markdown')
        else:
            await bot.send_message(chat_id=CHANNEL_ID, text=news_text, parse_mode='Markdown')
        print(f"Haber gönderildi: {title}")
    except Exception as e:
        print(f"Haber gönderilirken hata oluştu: {str(e)}")

async def send_initial_news(bot):
    global last_checked_date
    feed = feedparser.parse(RSS_FEED_URL)

    last_3_entries = feed.entries[:3]

    for entry in reversed(last_3_entries):
        pub_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z').replace(tzinfo=timezone.utc)
        await send_news_with_image(bot, entry)

    if last_3_entries:
        last_checked_date = datetime.strptime(last_3_entries[0].published, '%a, %d %b %Y %H:%M:%S %z').replace(tzinfo=timezone.utc)
        print(f"Bot başlatıldı. Son kontrol edilen tarih: {last_checked_date}")
    else:
        print("RSS beslemesinde haber bulunamadı.")

async def send_news():
    global last_checked_date
    bot = Bot(TOKEN)

    await send_initial_news(bot)

    while True:
        try:
            feed = feedparser.parse(RSS_FEED_URL)

            for entry in reversed(feed.entries):
                pub_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z').replace(tzinfo=timezone.utc)

                if last_checked_date is None or pub_date > last_checked_date:
                    await send_news_with_image(bot, entry)
                    last_checked_date = pub_date

            await asyncio.sleep(60)
        except Exception as e:
            print(f"Genel hata oluştu: {str(e)}")
            await asyncio.sleep(60)

@app.route('/')
def index():
    return "Telegram Bot is running!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))

    # Botu asyncio kullanarak arka planda çalıştır
    loop = asyncio.get_event_loop()
    loop.create_task(send_news())

    # Flask sunucusunu başlat
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
