import asyncio
import feedparser
from datetime import datetime, timezone
from telegram import Bot
from telegram.error import RetryAfter, TimedOut
import html  # HTML karakter referanslarını dönüştürmek için gerekli

# Doğrudan token ve kanal ID'si koy
TOKEN = '7153022938:AAElT2olwhCa700qfAL4HFrI7JYL9eDw_N0'  # Token'in burada
CHANNEL_ID = '@haberolog'  # Kanal ID'si burada

# RSS feed URL'si
RSS_FEED_URL = 'https://www.ensonhaber.com/rss/ensonhaber.xml'

# Son kontrol edilen haberin tarihini tutacak değişken
last_checked_date = None

async def send_news_with_image(bot, entry):
    # Başlık ve özetin HTML karakter referanslarını çözüyoruz
    title = html.unescape(entry.title.upper())
    summary = html.unescape(entry.summary)
    
    # Resim URL'sini kontrol et
    image_url = entry.media_content[0]['url'] if 'media_content' in entry and entry.media_content else None
    
    news_text = f"*{title}*\n\n{summary}"
    
    try:
        if image_url:
            # Resimli mesaj gönder
            await bot.send_photo(chat_id=CHANNEL_ID, photo=image_url, caption=news_text, parse_mode='Markdown')
        else:
            # Resimsiz mesaj gönder
            await bot.send_message(chat_id=CHANNEL_ID, text=news_text, parse_mode='Markdown')
        print(f"Haber gönderildi: {title}")
    except Exception as e:
        print(f"Haber gönderilirken hata oluştu: {str(e)}")

async def send_initial_news(bot):
    global last_checked_date
    feed = feedparser.parse(RSS_FEED_URL)
    
    # Son 3 haberi al
    last_3_entries = feed.entries[:3]
    
    for entry in reversed(last_3_entries):
        pub_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z').replace(tzinfo=timezone.utc)
        await send_news_with_image(bot, entry)
    
    # Son kontrol edilen tarihi güncelle
    if last_3_entries:
        last_checked_date = datetime.strptime(last_3_entries[0].published, '%a, %d %b %Y %H:%M:%S %z').replace(tzinfo=timezone.utc)
        print(f"Bot başlatıldı. Son kontrol edilen tarih: {last_checked_date}")
    else:
        print("RSS beslemesinde haber bulunamadı.")

async def send_news():
    global last_checked_date
    bot = Bot(TOKEN)
    
    # Başlangıçta son 3 haberi gönder
    await send_initial_news(bot)
    
    while True:
        try:
            feed = feedparser.parse(RSS_FEED_URL)
            
            for entry in reversed(feed.entries):
                pub_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z').replace(tzinfo=timezone.utc)
                
                if last_checked_date is None or pub_date > last_checked_date:
                    await send_news_with_image(bot, entry)
                    last_checked_date = pub_date
            
            # 60 saniye bekle
            await asyncio.sleep(60)
        except RetryAfter as e:
            print(f"Flood control. Bekleniyor: {e.retry_after} saniye")
            await asyncio.sleep(e.retry_after)
        except TimedOut:
            print("Zaman aşımı. Yeniden deneniyor...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Genel hata oluştu: {str(e)}")
            await asyncio.sleep(60)

if __name__ == '__main__':
    asyncio.run(send_news())
