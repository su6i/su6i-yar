from src.core.database import USER_LANG
import re

LANG_ALIASES = {
    "fa": "fa", "persian": "fa", "farsi": "fa",
    "en": "en", "english": "en",
    "fr": "fr", "french": "fr",
    "ko": "ko", "korean": "ko"
}

MESSAGES = {
    "fa": {
        "welcome": (
            "👋 **سلام {name}!**\n"
            "به **سوشییار**، دستیار هوشمند خود خوش آمدید.\n\n"
            "━━━━━━━━━━━━━━\n"
            "🔻 از منوی زیر استفاده کنید یا لینک بفرستید"
        ),
        "btn_status": "📊 وضعیت",
        "btn_help": "🆘 راهنما",
        "btn_dl": "📥 دانلودر",
        "btn_fc": "🧠 هوش مصنوعی",
        "btn_stop": "🛑 توقف ربات",
        "btn_voice": "🔊 تبدیل صوت",
        "btn_lang_fa": "🇮🇷 فارسی",
        "btn_lang_en": "🇺🇸 English",
        "btn_lang_fr": "🇫🇷 Français",
        "btn_lang_ko": "🇰🇷 한국어",
        "status_fmt": (
            "📊 **وضعیت سیستم**\n"
            "━━━━━━━━━━━━━━\n"
            "📥 **دانلودر:**       {dl}\n"
            "🧠 **فکت‌چک هوشمند:** {fc}\n"
            "━━━━━━━━━━━━━━\n"
            "🔻 برای تغییر از دکمه‌های زیر استفاده کنید"
        ),
        "dl_on": "✅ فعال",
        "dl_off": "❌ غیرفعال",
        "fc_on": "✅ فعال",
        "fc_off": "❌ غیرفعال",
        "action_dl": "📥 وضعیت دانلود: {state}",
        "action_fc": "🧠 وضعیت راستی‌آزمایی: {state}",
        "access_denied": "⛔ شما دسترسی به این ربات ندارید.",
        "limit_reached": "⛔ سقف درخواست روزانه شما تمام شد ({remaining} از {limit}).",
        "limit_remaining_count": "باقی‌مانده",
        "analyzing": "🧠 در حال راستی‌آزمایی...",
        "user_type_admin": "👑 ادمین",
        "user_type_member": "✅ عضو",
        "user_type_free": "🆓 رایگان",
        "status_label_user": "کاربر",
        "status_label_type": "نوع",
        "status_label_quota": "سهمیه امروز",
        "irrelevant_msg": "⚠️ این محتوا به نظر می‌رسد سیاسی، عقیدتی یا اجتماعی باشد. من فقط ادعاهای دقیق علمی، پزشکی و آماری را بررسی می‌کنم.",
        "btn_price": "💰 قیمت ارز و طلا",
        "menu_closed": "❌ منو بسته شد. برای باز کردن /start بزنید",
        "price_loading": "⏳ در حال دریافت قیمت‌های لحظه‌ای از tgju.org...",
        "price_error": "❌ خطا در دریافت قیمت‌ها از tgju.org. لطفاً دوباره تلاش کنید.",
        "price_msg": (
            "💰 **قیمت لحظه‌ای بازار (tgju.org)**\n"
            "━━━━━━━━━━━━━━\n"
            "🇺🇸 **دلار:** `{usd_tm}` تومان\n"
            "🇪🇺 **یورو:** `{eur_tm}` تومان\n"
            "🟡 **طلا ۱۸ عیار:** `{gold18_tm}` تومان\n"
            "**حباب طلای ۱۸:** `{diff_tm}`\n"
            "━━━━━━━━━━━━━━\n"
            "🌐 **انس جهانی:** `{ons}`$\n\n"
            "**طلای ۱۸ جهانی:**\n"
            "`{theoretical_tm}` تومان"
        ),
        "help_msg": (
            "📚 **راهنمای کامل قابلیت‌های ربات**\n"
            "━━━━━━━━━━━━━━\n\n"
            "📥 **دانلودر اینستاگرام**\n"
            "لینک پست یا ریلز را بفرستید تا خودکار دانلود شود.\n"
            "▫️ اگر دانلود خودکار خاموش بود:\n"
            "`/dl [لینک]`\n\n"
            "🧠 **راستی‌آزمایی هوشمند** (`/check`)\n"
            "بررسی درستی ادعا یا تحلیل متن:\n"
            "▫️ ریپلای به پیام:\n"
            "`/check`\n"
            "▫️ یا مستقیم:\n"
            "`/check [متن شما]`\n\n"
            "🎓 **آموزش زبان** (`/learn`)\n"
            "یادگیری کلمات با تصویر و تلفظ:\n"
            "▫️ مستقیم:\n"
            "`/learn [کلمه یا جمله]`\n"
            "▫️ ریپلای روی کلمه:\n"
            "`/learn`\n\n"
            "🔊 **تبدیل متن به صوت** (`/voice`)\n"
            "▫️ خواندن متن پیام (ریپلای):\n"
            "`/voice`\n"
            "▫️ خواندن متن دلخواه:\n"
            "`/voice [متن]`\n"
            "▫️ ترجمه و خواندن (مثلاً به انگلیسی):\n"
            "`/voice en [متن]`\n"
            "*(زبان‌ها: fa, en, fr, ko)*\n\n"
            "📊 **وضعیت و سهمیه**\n"
            "مشاهده اعتبار باقی‌مانده:\n"
            "`/status`\n\n"
            "💰 **نرخ ارز و طلا**\n"
            "قیمت لحظه‌ای دلار، یورو و طلا:\n"
            "`/price`\n\n"
            "📄 **جزئیات تحلیل**\n"
            "اگر توضیحات بیشتر خواستید، روی نتیجه تحلیل ریپلای کنید:\n"
            "`/detail`\n\n"
            "🎂 **تولد** (`/birthday`)\n"
            "ثبت و تبریک تولد:\n"
            "▫️ افزودن (ریپلای روی کاربر یا آیدی):\n"
            "`/birthday add [تاریخ]`\n"
            "▫️ تبریک دستی:\n"
            "`/birthday wish [نام] [تاریخ]`\n"
            "▫️ چک کردن لیست:\n"
            "`/birthday check`\n\n"
            "🛠 **ابزارهای amir** (`/amir`)\n"
            "▫️ QR code از هر متنی:\n"
            "`/qr [متن یا لینک]`\n"
            "▫️ رمز عبور امن:\n"
            "`/pass [طول — پیش‌فرض ۱۶]`\n"
            "▫️ آب‌وهوا:\n"
            "`/weather [شهر]`\n"
            "▫️ تبدیل یه عکس به PDF:\n"
            "عکس بفرستید + کپشن `pdf` یا `a4`\n"
            "▫️ هر دو طرف کارت ملی روی یه صفحه A4:\n"
            "دو عکس رو **باهم** (آلبوم) انتخاب کنید + کپشن `کارت ملی`\n\n"
            "━━━━━━━━━━━━━━"
        )
    },
    "en": {
        "welcome": "👋 **Hello {name}!**\nWelcome to **Su6i Yar**.",
        "dl_on": "✅ Active", "dl_off": "❌ Inactive",
        "fc_on": "✅ Active", "fc_off": "❌ Inactive",
        "action_dl": "📥 Download status: {state}",
        "action_fc": "🧠 AI status: {state}",
        "access_denied": "⛔ Access Denied.",
        "limit_reached": "⛔ Daily limit reached.",
        "limit_remaining_count": "remaining",
        "analyzing": "🧠 Analyzing...",
        "user_type_admin": "👑 Admin", "user_type_member": "✅ Member", "user_type_free": "🆓 Free",
        "status_label_user": "User", "status_label_type": "Type", "status_label_quota": "Quota",
        "irrelevant_msg": "⚠️ Irrelevant content."
    },
    "fr": {
        "welcome": "👋 **Bonjour {name}!**",
        "dl_on": "✅ Actif", "dl_off": "❌ Inactif",
        "action_dl": "📥 Téléchargement: {state}",
        "action_fc": "🧠 IA: {state}",
        "access_denied": "⛔ Accès refusé.",
        "limit_reached": "⛔ Limite atteinte.",
        "limit_remaining_count": "restant",
        "analyzing": "🧠 Analyse...",
        "irrelevant_msg": "⚠️ Contenu non pertinent."
    },
    "ko": {
        "welcome": "👋 **안녕하세요 {name}!**",
        "dl_on": "✅ 활성화", "dl_off": "❌ 비활성화",
        "action_dl": "📥 다운로드: {state}",
        "action_fc": "🧠 AI: {state}",
        "access_denied": "⛔ 접근 거부됨.",
        "limit_reached": "⛔ 한도 초과.",
        "limit_remaining_count": "남음",
        "analyzing": "🧠 분석 중...",
        "irrelevant_msg": "⚠️ 관련 없는 콘텐츠."
    }
}

def get_msg(key, user_id=None):
    """Retrieve localized message based on User ID"""
    lang = "fa"
    if user_id and user_id in USER_LANG:
        lang = USER_LANG[user_id]
        
    return MESSAGES.get(lang, MESSAGES["fa"]).get(key, key)

def extract_text(response) -> str:
    """Safely extract text from LangChain response, handling both string and list content."""
    if not response:
        return ""
    
    # Handle string input directly
    if isinstance(response, str):
        return response.strip()
        
    # Handle LangChain Message object or similar
    if hasattr(response, 'content'):
        content = response.content
    else:
        content = str(response)

    if isinstance(content, list):
        # Handle list-based content (Multimodal/Grounding parts from Gemini)
        return "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in content]).strip()
    
    return str(content).strip()

def clean_text_strict(text: str) -> str:
    """
    Strict cleaning for Persian TTS as requested:
    - Replace meaningful emojis with text.
    - Keep only letters, spaces, and basic punctuation.
    - Remove numbers, other emojis, and styling symbols.
    """
    if not text:
        return ""
        
    import re
    # 0. Semantic Emoji Mapping
    emoji_map = {
        "✅": "تأیید شده", "❌": "رد شده", "⛔": "غیرمجاز", "⚠️": "هشدار",
        "🧠": "تحلیل", "💡": "نتیجه", "📄": "منبع", "🔍": "بررسی",
        "📊": "آمار", "📈": "روند", "📉": "روند نزولی", "🆔": "شناسه",
        "👤": "کاربر", "🟢": "فعال", "🔴": "غیرفعال",
    }
    
    for emoji_char, text_replacement in emoji_map.items():
        text = text.replace(emoji_char, f" {text_replacement} ")

    # 1. Handle Titles/Headers (Markdown bold) -> Add period for pause
    text = re.sub(r'\*\*(.*?)\*\*', r' . . . \1 . . . ', text)
    
    # 2. Convert colons in headers to full stops/pauses
    text = re.sub(r'(^|\n)(.*?):', r'\1\2 . . . ', text)
    
    # 3. Remove URLs
    text = re.sub(r'http\S+', 'لینک', text)
    
    # 4. Remove all other non-word chars (except Persian/English chars and basic punctuation)
    # Keeping Arabic/Persian range + English + basic punctuation
    text = re.sub(r'[^\w\s\.\,\?\!\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]', ' ', text)
    
    # 5. Collapse spaces and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_link_from_text(entities, text_content):
    """Helper to find URL in entities or regex"""
    if not text_content: return None
    
    if entities:
        for entity in entities:
            if entity.type == 'text_link': # Hyperlink
                return entity.url
            elif entity.type == 'url': # Raw Link
                return text_content[entity.offset:entity.offset + entity.length]
    
    # Fallback: Regex Search
    found = re.search(r'(https?://\S+)', text_content)
    if found:
        return found.group(1)
    return None

import html

def smart_split(text, header="", max_len=1024, overflow_prefix="... ادامه در پیام بعدی"):
    """
    Split text into two parts: a caption (max_len) and overflow_text.
    Uses HTML formatting for stability.
    Returns (final_caption_html, overflow_raw_text)
    """
    if not text:
        return header, ""
        
    # Split by paragraphs
    paragraphs = text.split('\n\n')
    current_caption_raw = ""
    overflow_text_raw = ""
    overflow_started = False
    
    for para in paragraphs:
        if overflow_started:
            overflow_text_raw += ("\n\n" if overflow_text_raw else "") + para
        else:
            potential = (current_caption_raw + "\n\n" if current_caption_raw else "") + para
            
            # Test length with HTML escaping
            test_caption_html = header + "\n\n" + html.escape(potential) + "\n\n<i>" + html.escape(overflow_prefix) + "</i>"
            
            if len(test_caption_html) <= max_len:
                current_caption_raw = potential
            else:
                if not current_caption_raw:
                    # Hard split if first paragraph is too long
                    allowed = max_len - len(header) - len(overflow_prefix) - 30
                    current_caption_raw = para[:allowed]
                    overflow_text_raw = para[allowed:]
                    overflow_started = True
                else:
                    overflow_started = True
                    overflow_text_raw = para
                    
    final_caption_html = header + (("\n\n" + html.escape(current_caption_raw)) if current_caption_raw else "")
    if overflow_text_raw:
        final_caption_html += "\n\n<i>" + html.escape(overflow_prefix) + "</i>"
        
    return final_caption_html, overflow_text_raw
