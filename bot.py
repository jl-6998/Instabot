import logging
import random
import string
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import httpx
from faker import Faker
import schwifty
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# APIs & Token
TOKEN = "8312222553:AAEdCJK6ZiJRpkoqWXbooXNYNSTLnP0YmO0"
# Switched to HandyAPI because Binlist blocks Render servers
BIN_API = "https://data.handyapi.com/bin/{}"

# Disguise the bot as a real web browser to bypass Cloudflare API blocks
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# --- Translation Dictionary for Full Country Names ---
COUNTRY_NAMES = {
    "nepal": "np", "united states": "us", "usa": "us", "uk": "gb", 
    "united kingdom": "gb", "germany": "de", "france": "fr", "spain": "es", 
    "italy": "it", "india": "in", "bangladesh": "bd", "canada": "ca", 
    "australia": "au", "brazil": "br", "russia": "ru", "japan": "jp", 
    "china": "cn", "mexico": "mx", "netherlands": "nl", "switzerland": "ch", 
    "sweden": "se", "norway": "no", "denmark": "dk", "finland": "fi", 
    "poland": "pl", "turkey": "tr", "greece": "gr", "argentina": "ar", 
    "colombia": "co", "peru": "pe", "korea": "kr", "indonesia": "id", 
    "malaysia": "my", "philippines": "ph", "thailand": "th", "vietnam": "vn", 
    "egypt": "eg", "saudi arabia": "sa", "uae": "ae", "israel": "il", 
    "portugal": "pt", "austria": "at", "hungary": "hu", "belgium": "be", 
    "pakistan": "pk", "singapore": "sg", "sri lanka": "lk", "south africa": "za"
}

# Faker Locale Map (Now includes Nepal explicitly)
LOCALE_MAP = {
    'us': 'en_US', 'gb': 'en_GB', 'uk': 'en_GB', 'ca': 'en_CA', 'au': 'en_AU',
    'de': 'de_DE', 'fr': 'fr_FR', 'it': 'it_IT', 'es': 'es_ES', 'bd': 'bn_BD',
    'in': 'en_IN', 'ru': 'ru_RU', 'br': 'pt_BR', 'jp': 'ja_JP', 'cn': 'zh_CN',
    'mx': 'es_MX', 'za': 'en_ZA', 'nl': 'nl_NL', 'ch': 'de_CH', 'se': 'sv_SE',
    'no': 'no_NO', 'dk': 'da_DK', 'fi': 'fi_FI', 'pl': 'pl_PL', 'cz': 'cs_CZ',
    'ro': 'ro_RO', 'tr': 'tr_TR', 'gr': 'el_GR', 'ar': 'es_AR', 'co': 'es_CO',
    'cl': 'es_CL', 'pe': 'es_PE', 've': 'es_VE', 'kr': 'ko_KR', 'tw': 'zh_TW',
    'id': 'id_ID', 'my': 'ms_MY', 'ph': 'en_PH', 'th': 'th_TH', 'vn': 'vi_VN',
    'eg': 'ar_EG', 'sa': 'ar_SA', 'ae': 'ar_AE', 'il': 'he_IL', 'pt': 'pt_PT',
    'at': 'de_AT', 'hu': 'hu_HU', 'bg': 'bg_BG', 'hr': 'hr_HR', 'sk': 'sk_SK',
    'ua': 'uk_UA', 'ie': 'en_IE', 'ng': 'en_NG', 'ke': 'en_KE', 'nz': 'en_NZ',
    'be': 'nl_BE', 'pk': 'en_PK', 'sg': 'en_SG', 'lk': 'en_LK', 'np': 'ne_NP'
}

# --- Helper Functions ---

def luhn_check(card_num: str) -> bool:
    if not card_num.isdigit(): return False
    digits = [int(x) for x in card_num]
    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9: digits[i] -= 9
    return sum(digits) % 10 == 0

def generate_dot_trick_email(base_name: str) -> str:
    clean_name = "".join(c for c in base_name.lower() if c.isalpha()) or "testuser"
    dotted_name = clean_name[0]
    for char in clean_name[1:]:
        if random.choice([True, False]): dotted_name += "."
        dotted_name += char
    return f"{dotted_name}@gmail.com"

def get_flag(country_code: str) -> str:
    """Generates a flag emoji from a 2-letter country code."""
    if not country_code or len(country_code) != 2: return "🌍"
    return ''.join(chr(ord(c.upper()) + 127397) for c in country_code)

def to_bold_sans(text: str) -> str:
    bold_text = ""
    for char in text:
        if 'A' <= char <= 'Z': bold_text += chr(ord(char) - 65 + 120276)
        elif 'a' <= char <= 'z': bold_text += chr(ord(char) - 97 + 120302)
        else: bold_text += char
    return bold_text

# --- Dummy Web Server to keep Render Happy ---

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

# --- Command Handlers ---

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu_text = (
        "🤖 **BOT COMMANDS MENU** 🤖\n\n"
        "💳 **BIN Info**\n"
        "├ Command : `/bin {6-digit}`\n"
        "└ Example : `/bin 412236`\n\n"
        "🔐 **CC Generator**\n"
        "├ Command : `/gen BIN|MM|YYYY|CVV`\n"
        "└ Example : `/gen 412236xxxx|xx|2025|xxx`\n\n"
        "ℹ️ **IBAN Generator**\n"
        "├ Command : `/iban COUNTRY_NAME`\n"
        "└ Example : `/iban germany`\n\n"
        "📍 **Fake Address**\n"
        "├ Command : `/fake {country}`\n"
        "├ Example : `/fake nepal`\n"
        "└ Example : `/fake us`\n\n"
        "📧 **Temp Mail**\n"
        "├ Command : `/email`\n"
        "└ Command : `/inbox {email_address}`\n\n"
        "👤 **Profile Info**\n"
        "└ Command : `/me`\n\n"
        "📌 **Menu**\n"
        "└ Command : `/menu`"
    )
    await update.message.reply_text(menu_text, parse_mode="Markdown")

async def bin_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ **Usage:** `/bin <6-digit BIN>`", parse_mode="Markdown")
        return
    bin_val = context.args[0][:8]
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(BIN_API.format(bin_val), headers=HTTP_HEADERS, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                if data.get("Status") == "SUCCESS":
                    country_name = data.get('Country', {}).get('Name', 'UNKNOWN')
                    country_code = data.get('Country', {}).get('A2', '')
                    msg = (
                        f"🏦 𝗕𝗜𝗡 𝗟𝗼𝗼𝗸𝘂𝗽 𝗥𝗲𝘀𝘂𝗹𝘁 🔍\n\n"
                        f"🔢 𝗕𝗶𝗻 ⇾ `{bin_val}`\n"
                        f"🟢 𝗦𝘁𝗮𝘁𝘂𝘀 ⇾ ✅ SUCCESS\n"
                        f"💳 𝗦𝗰𝗵𝗲𝗺𝗲 ⇾ {data.get('Scheme', 'UNKNOWN').upper()}\n"
                        f"🏷️ 𝗧𝘆𝗽𝗲 ⇾ {data.get('Type', 'UNKNOWN').upper()}\n"
                        f"🏛️ 𝗜𝘀𝘀𝘂𝗲𝗿/𝗕𝗮𝗻𝗸 ⇾ {data.get('Issuer', 'UNKNOWN').upper()}\n"
                        f"💎 𝗧𝗶𝗲𝗿 ⇾ {data.get('CardTier', 'UNKNOWN').upper()}\n"
                        f"🌍 𝗖𝗼𝘂𝗻𝘁𝗿𝘆 ⇾ {country_name} {get_flag(country_code)}\n"
                        f"🛡️ 𝗟𝘂𝗵𝗻 ⇾ {luhn_check(bin_val + '0000000000')}"
                    )
                    await update.message.reply_text(msg, parse_mode="Markdown")
                else:
                    await update.message.reply_text("❌ **BIN not found.**", parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ **API rate-limited.**", parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text("⚠️ **Connection error to lookup service.**", parse_mode="Markdown")

async def gen_cc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ **Usage:** `/gen <BIN>`\nExample: `/gen 46272919`", parse_mode="Markdown")
        return
    base_bin = context.args[0].split('|')[0].replace('x', '').replace('X', '')
    if len(base_bin) < 6:
        await update.message.reply_text("❌ Please provide at least a 6-digit BIN.")
        return

    generated_cards = []
    for _ in range(10):
        card_num = base_bin + "".join(random.choices(string.digits, k=max(0, 16 - len(base_bin))))
        mm = str(random.randint(1, 12)).zfill(2)
        yyyy = str(random.randint(2025, 2035))
        cvv = "".join(random.choices(string.digits, k=3))
        generated_cards.append(f"`{card_num}|{mm}|{yyyy}|{cvv}`")

    info_str, bank_str, country_str = "Unknown", "Unknown", "Unknown"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(BIN_API.format(base_bin[:8]), headers=HTTP_HEADERS, timeout=8.0)
            if resp.status_code == 200:
                d = resp.json()
                if d.get("Status") == "SUCCESS":
                    info_str = f"{d.get('Scheme', '').upper()} - {d.get('Type', '').upper()}".strip(" -") or "Unknown"
                    bank_str = d.get('Issuer', 'Unknown')
                    c_name = d.get('Country', {}).get('Name', 'Unknown')
                    c_code = d.get('Country', {}).get('A2', '')
                    country_str = f"{c_name} {get_flag(c_code)}".strip()
        except: pass

    msg = (
        f"⚙️ 𝗕𝗜𝗡 ⇾ `{base_bin}`\n"
        f"🔢 𝗔𝗺𝗼𝘂𝗻𝘁 ⇾ 10\n\n"
        f"{chr(10).join(generated_cards)}\n\n"
        f"ℹ️ 𝗜𝗻𝗳𝗼: {info_str}\n"
        f"🏦 𝗕𝗮𝗻𝗸: {bank_str}\n"
        f"🌍 𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country_str}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def fake_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ **Usage:** `/fake <COUNTRY>`\nExample: `/fake nepal`", parse_mode="Markdown")
        return
    
    user_input = " ".join(context.args).lower()
    
    # Check if they typed a full country name (like "nepal" -> "np")
    country_code = COUNTRY_NAMES.get(user_input, user_input)
    
    locale = LOCALE_MAP.get(country_code, 'en_US')
    raw_country_name = user_input.upper() if country_code in LOCALE_MAP else "UNITED STATES (Fallback)"
    
    display_country = to_bold_sans(raw_country_name)
    flag_emoji = get_flag(country_code) if country_code in LOCALE_MAP else "🇺🇸"

    try:
        fake = Faker(locale)
        full_name = fake.name()
        state = getattr(fake, 'administrative_unit', getattr(fake, 'state', lambda: "N/A"))()
        
        msg = (
            f"📍 {display_country} 𝗔𝗱𝗱𝗿𝗲𝘀𝘀 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗼𝗿 {flag_emoji}\n\n"
            f"👤 𝗙𝘂𝗹𝗹 𝗡𝗮𝗺𝗲: `{full_name}`\n"
            f"🏠 𝗦𝘁𝗿𝗲𝗲𝘁 𝗔𝗱𝗱𝗿𝗲𝘀𝘀: `{fake.street_address()}`\n"
            f"🏙️ 𝗖𝗶𝘁𝘆/𝗧𝗼𝘄𝗻/𝗩𝗶𝗹𝗹𝗮𝗴𝗲: `{fake.city()}`\n"
            f"🗺️ 𝗦𝘁𝗮𝘁𝗲/𝗣𝗿𝗼𝘃𝗶𝗻𝗰𝗲/𝗥𝗲𝗴𝗶𝗼𝗻: `{state}`\n"
            f"📮 𝗣𝗼𝘀𝘁𝗮𝗹 𝗖𝗼𝗱𝗲: `{fake.postcode()}`\n"
            f"📞 𝗣𝗵𝗼𝗻𝗲 𝗡𝘂𝗺𝗯𝗲𝗿: `{fake.phone_number()}`\n"
            f"🌍 𝗖𝗼𝘂𝗻𝘁𝗿𝘆: `{fake.current_country()}`\n"
            f"📧 𝗧𝗲𝗺𝗽𝗼𝗿𝗮𝗿𝘆 𝗘𝗺𝗮𝗶𝗹: `{generate_dot_trick_email(full_name.replace(' ', ''))}`"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text("⚠️ **Error generating offline address.**", parse_mode="Markdown")

async def gen_iban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ **Usage:** `/iban <COUNTRY>`\nExample: `/iban germany`", parse_mode="Markdown")
        return
    
    user_input = " ".join(context.args).lower()
    country_code = COUNTRY_NAMES.get(user_input, user_input).upper()
    locale = LOCALE_MAP.get(country_code.lower())

    if not locale:
        await update.message.reply_text("❌ **Country not mapped or supported for IBAN.**", parse_mode="Markdown")
        return

    try:
        # Faker creates the valid raw IBAN string, Schwifty parses the details cleanly
        fake = Faker(locale)
        iban_str = fake.iban()
        iban_obj = schwifty.IBAN(iban_str)
        flag = get_flag(country_code)
        
        msg = (
            f"🌍 **IBAN Details** 🏦\n\n"
            f"🏳️ Country: {country_code} {flag}\n"
            f"🔢 IBAN: `{iban_str}`\n"
            f"📏 Length: {len(iban_str)}\n\n"
            f"🏛️ Bank Code: `{iban_obj.bank_code or 'N/A'}`\n"
            f"💳 Account Number: `{iban_obj.account_code or 'N/A'}`\n"
            f"✅ Check Digits: `{iban_obj.checksum}`\n"
            f"📝 BBAN: `{iban_obj.bban}`"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
    except AttributeError:
        await update.message.reply_text("❌ **This specific country's banking system does not support automatic IBAN generation.**", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text("⚠️ **Error parsing IBAN data.**", parse_mode="Markdown")

async def profile_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    username = f"@{user.username}" if user.username else "No Username"
    await update.message.reply_text(
        f"👤 **Your Profile** ℹ️\n"
        f"📛 Name: `{user.full_name}`\n"
        f"🔗 Username: `{username}`\n"
        f"🆔 ID: `{user.id}`", 
        parse_mode="Markdown"
    )

async def gen_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1", headers=HTTP_HEADERS, timeout=10.0)
            if resp.status_code == 200:
                email = resp.json()[0]
                msg = (
                    f"📧 **Temporary Email Generated** ✅\n\n"
                    f"📫 **Address:** `{email}`\n\n"
                    f"👇 *To check for new messages, copy the address and send:*\n"
                    f"`/inbox {email}`"
                )
                await update.message.reply_text(msg, parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ **Failed to generate email.**", parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text("⚠️ **Connection error to email server.**", parse_mode="Markdown")

async def check_inbox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ **Usage:** `/inbox <email_address>`", parse_mode="Markdown")
        return

    email = context.args[0]
    if "@" not in email:
        await update.message.reply_text("❌ **Invalid email format.**", parse_mode="Markdown")
        return

    login, domain = email.split("@")
    async with httpx.AsyncClient() as client:
        try:
            url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}"
            resp = await client.get(url, headers=HTTP_HEADERS, timeout=10.0)
            
            if resp.status_code == 200:
                messages = resp.json()
                if not messages:
                    await update.message.reply_text("📭 **Inbox is currently empty.**\nWait a few seconds and try again.", parse_mode="Markdown")
                    return

                latest_msg_id = messages[0]['id']
                read_url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={login}&domain={domain}&id={latest_msg_id}"
                read_resp = await client.get(read_url, headers=HTTP_HEADERS, timeout=10.0)

                if read_resp.status_code == 200:
                    msg_data = read_resp.json()
                    sender = msg_data.get('from', 'Unknown')
                    subject = msg_data.get('subject', 'No Subject')
                    text_body = msg_data.get('textBody', 'No Content available.')[:1000] 

                    output = (
                        f"📬 **New Message Received!**\n\n"
                        f"👤 **From:** `{sender}`\n"
                        f"📝 **Subject:** `{subject}`\n\n"
                        f"📄 **Message:**\n`{text_body}`"
                    )
                    await update.message.reply_text(output, parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ **Could not reach inbox.**", parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text("⚠️ **Connection error while checking inbox.**", parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 **Welcome!** Send `/menu` to see available commands.", parse_mode="Markdown")

def main():
    threading.Thread(target=keep_alive, daemon=True).start()

    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("bin", bin_info))
    application.add_handler(CommandHandler("gen", gen_cc))
    application.add_handler(CommandHandler("iban", gen_iban))
    application.add_handler(CommandHandler("fake", fake_address))
    application.add_handler(CommandHandler("me", profile_info))
    application.add_handler(CommandHandler("email", gen_email))
    application.add_handler(CommandHandler("inbox", check_inbox))

    print("Bot is polling and ready to go! 🚀")
    application.run_polling()

if __name__ == "__main__":
    main()
