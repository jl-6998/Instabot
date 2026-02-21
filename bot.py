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
BIN_API = "https://data.handyapi.com/bin/{}"

# Disguise the bot as a real web browser
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

# --- Massive Translation Dictionary (Every Country Faker/IBAN Supports) ---
COUNTRY_NAMES = {
    "afghanistan": "af", "albania": "al", "algeria": "dz", "andorra": "ad", "argentina": "ar", 
    "armenia": "am", "australia": "au", "austria": "at", "azerbaijan": "az", "bahrain": "bh", 
    "bangladesh": "bd", "belarus": "by", "belgium": "be", "bolivia": "bo", "bosnia": "ba", 
    "brazil": "br", "bulgaria": "bg", "canada": "ca", "chile": "cl", "china": "cn", 
    "colombia": "co", "costa rica": "cr", "croatia": "hr", "cuba": "cu", "cyprus": "cy", 
    "czechia": "cz", "czech republic": "cz", "denmark": "dk", "dominican republic": "do", 
    "ecuador": "ec", "egypt": "eg", "el salvador": "sv", "estonia": "ee", "faroe islands": "fo", 
    "finland": "fi", "france": "fr", "georgia": "ge", "germany": "de", "ghana": "gh", 
    "gibraltar": "gi", "greece": "gr", "greenland": "gl", "guatemala": "gt", "honduras": "hn", 
    "hungary": "hu", "iceland": "is", "india": "in", "indonesia": "id", "iran": "ir", 
    "iraq": "iq", "ireland": "ie", "israel": "il", "italy": "it", "japan": "jp", 
    "jordan": "jo", "kazakhstan": "kz", "kenya": "ke", "kosovo": "xk", "kuwait": "kw", 
    "latvia": "lv", "lebanon": "lb", "libya": "ly", "liechtenstein": "li", "lithuania": "lt", 
    "luxembourg": "lu", "malaysia": "my", "malta": "mt", "mauritania": "mr", "mauritius": "mu", 
    "mexico": "mx", "moldova": "md", "monaco": "mc", "montenegro": "me", "morocco": "ma", 
    "nepal": "np", "netherlands": "nl", "new zealand": "nz", "nicaragua": "ni", "nigeria": "ng", 
    "north macedonia": "mk", "norway": "no", "oman": "om", "pakistan": "pk", "palestine": "ps", 
    "paraguay": "py", "peru": "pe", "philippines": "ph", "poland": "pl", "portugal": "pt", 
    "qatar": "qa", "romania": "ro", "russia": "ru", "san marino": "sm", "saudi arabia": "sa", 
    "serbia": "rs", "singapore": "sg", "slovakia": "sk", "slovenia": "si", "south africa": "za", 
    "south korea": "kr", "korea": "kr", "spain": "es", "sri lanka": "lk", "sweden": "se", 
    "switzerland": "ch", "syria": "sy", "taiwan": "tw", "thailand": "th", "tunisia": "tn", 
    "turkey": "tr", "uae": "ae", "united arab emirates": "ae", "uk": "gb", "united kingdom": "gb", 
    "ukraine": "ua", "uruguay": "uy", "us": "us", "usa": "us", "united states": "us", 
    "venezuela": "ve", "vietnam": "vn"
}

# --- Faker Locale Map (Every Locale Supported by Python Faker) ---
LOCALE_MAP = {
    'ar': 'es_AR', 'am': 'hy_AM', 'au': 'en_AU', 'at': 'de_AT', 'az': 'az_AZ', 
    'bd': 'bn_BD', 'be': 'nl_BE', 'bg': 'bg_BG', 'bo': 'es_BO', 'br': 'pt_BR', 
    'by': 'be_BY', 'ca': 'en_CA', 'ch': 'de_CH', 'cl': 'es_CL', 'cn': 'zh_CN', 
    'co': 'es_CO', 'cr': 'es_CR', 'cu': 'es_CU', 'cz': 'cs_CZ', 'de': 'de_DE', 
    'dk': 'da_DK', 'do': 'es_DO', 'ec': 'es_EC', 'ee': 'et_EE', 'eg': 'ar_EG', 
    'es': 'es_ES', 'fi': 'fi_FI', 'fr': 'fr_FR', 'gb': 'en_GB', 'ge': 'ka_GE', 
    'gh': 'en_GH', 'gr': 'el_GR', 'gt': 'es_GT', 'hn': 'es_HN', 'hr': 'hr_HR', 
    'hu': 'hu_HU', 'id': 'id_ID', 'ie': 'en_IE', 'il': 'he_IL', 'in': 'en_IN', 
    'ir': 'fa_IR', 'it': 'it_IT', 'jp': 'ja_JP', 'ke': 'en_KE', 'kr': 'ko_KR', 
    'lt': 'lt_LT', 'lv': 'lv_LV', 'mt': 'en_MT', 'mx': 'es_MX', 'my': 'ms_MY', 
    'ng': 'en_NG', 'ni': 'es_NI', 'nl': 'nl_NL', 'no': 'no_NO', 'np': 'ne_NP', 
    'nz': 'en_NZ', 'pe': 'es_PE', 'ph': 'en_PH', 'pk': 'ur_PK', 'pl': 'pl_PL', 
    'pt': 'pt_PT', 'py': 'es_PY', 'ro': 'ro_RO', 'rs': 'sr_RS', 'ru': 'ru_RU', 
    'sa': 'ar_SA', 'se': 'sv_SE', 'sg': 'en_SG', 'si': 'sl_SI', 'sk': 'sk_SK', 
    'sv': 'es_SV', 'th': 'th_TH', 'tr': 'tr_TR', 'tw': 'zh_TW', 'ua': 'uk_UA', 
    'us': 'en_US', 'uy': 'es_UY', 've': 'es_VE', 'vn': 'vi_VN', 'za': 'en_ZA'
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
        except:
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
        await update.message.reply_text(f"⚠️ **Error generating offline address:** `{str(e)}`", parse_mode="Markdown")

async def gen_iban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ **Usage:** `/iban <COUNTRY>`\nExample: `/iban germany`", parse_mode="Markdown")
        return
    
    user_input = " ".join(context.args).lower()
    country_code = COUNTRY_NAMES.get(user_input, user_input).upper()

    try:
        # 1. Fetch random valid IBAN from an online generator to ensure perfect validity
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://www.iban-generator.com/api/generate?country={country_code}", headers=HTTP_HEADERS, timeout=10.0)
            iban_str = resp.json().get("iban")
            
            if not iban_str:
                raise ValueError("API did not return an IBAN.")
                
        # 2. Slice it cleanly using Schwifty offline
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
    except Exception as e:
        await update.message.reply_text(f"❌ **'{country_code}' is invalid, does not use the IBAN system, or API failed.**", parse_mode="Markdown")

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
            # FIX: Safely parse the complex nested dictionary Mail.tm uses for Domains
            domain_resp = await client.get("https://api.mail.tm/domains", headers=HTTP_HEADERS, timeout=10.0)
            domain_data = domain_resp.json()
            
            # Extract domain string dynamically depending on their API version
            if 'hydra:member' in domain_data:
                domain = domain_data['hydra:member'][0]['domain']
            elif type(domain_data) is list:
                domain = domain_data[0]['domain']
            else:
                domain = "vjuum.com" # Reliable static fallback domain
                
            username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            address = f"{username}@{domain}"
            password = f"{username}SecretPass123!"
            
            payload = {"address": address, "password": password}
            acc_resp = await client.post("https://api.mail.tm/accounts", json=payload, headers=HTTP_HEADERS, timeout=10.0)
            
            if acc_resp.status_code in [200, 201]:
                msg = (
                    f"📧 **Temporary Email Generated** ✅\n\n"
                    f"📫 **Address:** `{address}`\n\n"
                    f"👇 *To check for new messages, copy the address and send:*\n"
                    f"`/inbox {address}`"
                )
                await update.message.reply_text(msg, parse_mode="Markdown")
            else:
                await update.message.reply_text(f"❌ **Failed to register email.** API Code: {acc_resp.status_code}", parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"⚠️ **Email Server Error:** `{str(e)}`", parse_mode="Markdown")

async def check_inbox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ **Usage:** `/inbox <email_address>`", parse_mode="Markdown")
        return

    address = context.args[0]
    if "@" not in address:
        await update.message.reply_text("❌ **Invalid email format.**", parse_mode="Markdown")
        return

    username = address.split("@")[0]
    password = f"{username}SecretPass123!"

    async with httpx.AsyncClient() as client:
        try:
            # Authenticate
            token_resp = await client.post("https://api.mail.tm/token", json={"address": address, "password": password}, headers=HTTP_HEADERS, timeout=10.0)
            if token_resp.status_code != 200:
                await update.message.reply_text("❌ **Could not authenticate. Make sure the address was generated by this bot.**", parse_mode="Markdown")
                return
                
            token = token_resp.json()['token']
            auth_headers = {**HTTP_HEADERS, "Authorization": f"Bearer {token}"}
            
            # Fetch Inbox
            msg_resp = await client.get("https://api.mail.tm/messages", headers=auth_headers, timeout=10.0)
            if msg_resp.status_code == 200:
                messages = msg_resp.json().get('hydra:member', [])
                if not messages:
                    await update.message.reply_text("📭 **Inbox is currently empty.**\nWait a few seconds and try again.", parse_mode="Markdown")
                    return

                latest_msg_id = messages[0]['id']
                read_resp = await client.get(f"https://api.mail.tm/messages/{latest_msg_id}", headers=auth_headers, timeout=10.0)

                if read_resp.status_code == 200:
                    msg_data = read_resp.json()
                    sender = msg_data.get('from', {}).get('address', 'Unknown')
                    subject = msg_data.get('subject', 'No Subject')
                    text_body = msg_data.get('text', 'No Content available.')[:1000] 

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
            await update.message.reply_text(f"⚠️ **Inbox Checking Error:** `{str(e)}`", parse_mode="Markdown")

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
