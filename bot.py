import logging
import random
import string
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
BIN_API = "https://lookup.binlist.net/{}"

# Faker Locale Map (70+ Countries)
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
    'be': 'nl_BE', 'pk': 'en_PK', 'sg': 'en_SG', 'lk': 'en_LK'
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
    if len(country_code) != 2: return ""
    return ''.join(chr(ord(c.upper()) + 127397) for c in country_code)

def to_bold_sans(text: str) -> str:
    """Converts standard text into 𝗯𝗼𝗹𝗱 𝘀𝗮𝗻𝘀-𝘀𝗲𝗿𝗶𝗳 Unicode."""
    bold_text = ""
    for char in text:
        if 'A' <= char <= 'Z': bold_text += chr(ord(char) - 65 + 120276)
        elif 'a' <= char <= 'z': bold_text += chr(ord(char) - 97 + 120302)
        else: bold_text += char
    return bold_text

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
        "├ Command : `/iban COUNTRY_CODE`\n"
        "└ Example : `/iban de`\n\n"
        "📍 **Fake Address**\n"
        "├ Command : `/fake {country_code}`\n"
        "├ Example : `/fake gb`\n"
        "└ Example : `/fake us`\n\n"
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
            response = await client.get(BIN_API.format(bin_val), timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                msg = (
                    f"🏦 𝗕𝗜𝗡 𝗟𝗼𝗼𝗸𝘂𝗽 𝗥𝗲𝘀𝘂𝗹𝘁 🔍\n\n"
                    f"🔢 𝗕𝗶𝗻 ⇾ `{bin_val}`\n"
                    f"🟢 𝗦𝘁𝗮𝘁𝘂𝘀 ⇾ ✅ SUCCESS\n"
                    f"💳 𝗦𝗰𝗵𝗲𝗺𝗲 ⇾ {data.get('scheme', 'UNKNOWN').upper()}\n"
                    f"🏷️ 𝗧𝘆𝗽𝗲 ⇾ {data.get('type', 'UNKNOWN').upper()}\n"
                    f"🏛️ 𝗜𝘀𝘀𝘂𝗲𝗿/𝗕𝗮𝗻𝗸 ⇾ {data.get('bank', {}).get('name', 'UNKNOWN').upper()}\n"
                    f"💎 𝗧𝗶𝗲𝗿 ⇾ {data.get('brand', 'UNKNOWN').upper()}\n"
                    f"🌍 𝗖𝗼𝘂𝗻𝘁𝗿𝘆 ⇾ {data.get('country', {}).get('name', 'UNKNOWN')} {data.get('country', {}).get('emoji', '')}\n"
                    f"🛡️ 𝗟𝘂𝗵𝗻 ⇾ {luhn_check(bin_val + '0000000000')}"
                )
                await update.message.reply_text(msg, parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ **BIN not found or API rate-limited.**", parse_mode="Markdown")
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
            resp = await client.get(BIN_API.format(base_bin[:8]), timeout=8.0)
            if resp.status_code == 200:
                d = resp.json()
                info_str = f"{d.get('scheme', '').upper()} - {d.get('type', '').upper()}".strip(" -") or "Unknown"
                bank_str = d.get('bank', {}).get('name', 'Unknown')
                country_str = f"{d.get('country', {}).get('name', 'Unknown')} {d.get('country', {}).get('emoji', '')}".strip()
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
        await update.message.reply_text("⚠️ **Usage:** `/fake <COUNTRY_CODE>`\nExample: `/fake bd`", parse_mode="Markdown")
        return
    
    country_code = context.args[0].lower()
    locale = LOCALE_MAP.get(country_code, 'en_US')
    raw_country_name = country_code.upper() if country_code in LOCALE_MAP else "UNITED STATES (Fallback)"
    
    # Format country nicely (e.g. 𝗙𝗥𝗔𝗡𝗖𝗘) and get the emoji flag
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
        await update.message.reply_text("⚠️ **Usage:** `/iban <COUNTRY_CODE>`\nExample: `/iban de`", parse_mode="Markdown")
        return
    
    country_code = context.args[0].upper()
    try:
        iban_obj = schwifty.IBAN.generate(country_code)
        iban_str = str(iban_obj)
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
    except ValueError:
        await update.message.reply_text(f"❌ **'{country_code}' is invalid or does not use the IBAN system.**", parse_mode="Markdown")

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 **Welcome!** Send `/menu` to see available commands.", parse_mode="Markdown")

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("bin", bin_info))
    application.add_handler(CommandHandler("gen", gen_cc))
    application.add_handler(CommandHandler("iban", gen_iban))
    application.add_handler(CommandHandler("fake", fake_address))
    application.add_handler(CommandHandler("me", profile_info))

    print("Bot is polling and ready to go! 🚀")
    application.run_polling()

if __name__ == "__main__":
    main()
