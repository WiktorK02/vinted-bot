import requests
import time
import os
import random
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone

class TelegramBot:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}/"

    def send_message(self, text):
        url = f"{self.base_url}sendMessage"
        params = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        try:
            response = requests.post(url, params=params, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"Błąd wysyłania wiadomości Telegram: {e}")

    def send_offer(self, offer):
        message = self.format_offer_message(offer)
        self.send_message(message)

    @staticmethod
    def format_offer_message(offer):
        return (
            f"<b>🎮 Nowa oferta Nintendo Switch 🎮</b>\n\n"
            f"<b>📌 Tytuł:</b> {offer.title}\n"
            f"<b>💰 Cena:</b> {offer.price}\n"
            f"<b>📅 Data dodania:</b> {offer.date}\n\n"
            f"<a href='{offer.url}'>🔗 Zobacz ofertę</a>"
        )

class Requester:
    def __init__(self):
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.85 Safari/537.36"
        ]
        self.MAX_RETRIES = 3
        self.last_locale = None
        self.create_new_session()

    def create_new_session(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "X-Requested-With": "XMLHttpRequest",
            "Connection": "keep-alive"
        }
        self.session.headers.update(self.headers)

    def set_locale(self, locale):
        self.last_locale = locale
        self.headers["Host"] = locale
        self.headers["Referer"] = f"https://{locale}/catalog?page={random.randint(1,3)}"
        try:
            self.session.get(f"https://{locale}/", timeout=10)
        except Exception as e:
            print(f"Cookie error: {e}")

    def get(self, url, params=None):
        for tried in range(1, self.MAX_RETRIES + 1):
            try:
                response = self.session.get(url, params=params, timeout=15)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                self.create_new_session()
                wait_time = random.randint(10, 30)
                print(f"Retrying ({tried}/{self.MAX_RETRIES}) after {wait_time}s...")
                time.sleep(wait_time)
                if tried == self.MAX_RETRIES:
                    raise Exception(f"Failed after {self.MAX_RETRIES} attempts: {str(e)}")

class Item:
    def __init__(self, data):
        self.id = data["id"]
        self.title = data["title"]
        self.price = f"{data['price']['amount']} {data['price']['currency_code']}"
        self.url = data["url"]
        self.date = datetime.fromtimestamp(
            data["photo"]["high_resolution"]["timestamp"], tz=timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_vinted_offers(search_url, num_items=10):
    requester = Requester()
    parsed_url = urlparse(search_url)
    locale = parsed_url.netloc
    requester.set_locale(locale)

    api_url = f"https://{locale}/api/v2/catalog/items"
    query_params = parse_qs(parsed_url.query)
    params = {
        "page": 1,
        "per_page": num_items,
        "order": "newest_first"
    }
    params.update(query_params)

    try:
        response = requester.get(api_url, params=params)
        return [Item(item) for item in response.json().get("items", [])[:num_items]]
    except Exception as e:
        print(f"Error: {e}")
        return []

def main_loop(search_url, interval=60):
    bot = TelegramBot(
        token="7164037349:AAGrbjgmKyCereONOOOvYzlkQvv6_aTwNk0",
        chat_id="7495057991"
    )

    seen_ids = set()

    try:
        bot.send_message("🚀 Bot started! Monitoring for new Nintendo Switch offers...")

        while True:
            print(f"\n🔄 Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            offers = get_vinted_offers(search_url)
            new_offers = [offer for offer in offers if offer.id not in seen_ids]
            seen_ids.update(offer.id for offer in offers)

            if new_offers:
                print(f"\n🌟 Found {len(new_offers)} new offers")
                for offer in new_offers:
                    bot.send_offer(offer)

            sleep_time = random.uniform(interval - 10, interval + 10)
            print(f"⏳ Waiting {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        bot.send_message("🛑 Bot stopped!")
        print("\n🛑 Monitoring stopped")

if __name__ == "__main__":
    main_loop(
        search_url=(
            "https://www.vinted.pl/catalog?"
            "search_text=nintendo&"
            "status_ids[]=3&status_ids[]=4&status_ids[]=7&"
            "catalog[]=3025"
        ),
        interval=60
    )
