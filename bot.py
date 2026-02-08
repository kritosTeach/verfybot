import os
import sqlite3
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

# تهيئة قاعدة البيانات
def init_db():
    conn = sqlite3.connect('/tmp/emails.db' if 'RENDER' in os.environ else 'emails.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS emails
                 (email TEXT PRIMARY KEY, 
                  user_id INTEGER,
                  username TEXT,
                  description TEXT,
                  date TEXT DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()
    print("✅ قاعدة بيانات الإيميلات جاهزة")

# التحقق من صحة الإيميل
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# التحقق من وجود الإيميل
def check_email(email):
    db_path = '/tmp/emails.db' if 'RENDER' in os.environ else 'emails.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT email, user_id, username, description, date FROM emails WHERE email=?", (email,))
    result = c.fetchone()
    conn.close()
    return result

# حجز الإيميل مع الوصف
def reserve_email(email, user_id, username, description):
    db_path = '/tmp/emails.db' if 'RENDER' in os.environ else 'emails.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO emails (email, user_id, username, description) VALUES (8322471161:AAEwthafhAceZSx-dAqHfO8Pzpegf9ppNEc)", 
                 (email, user_id, username, description))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    finally:
        conn.close()
    return success

# حذف الإيميل
def delete_email_from_db(email, user_id):
    db_path = '/tmp/emails.db' if 'RENDER' in os.environ else 'emails.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM emails WHERE email=? AND user_id=?", (email, user_id))
    deleted = c.rowcount
    conn.commit()
    conn.close()
    return deleted > 0

# أمر /start
async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    await update.message.reply_text(
        f'📧 مرحباً {user.first_name}!\n\n'
        'أنا بوت حجز الإيميلات مع الوصف\n\n'
        '🔹 /reserve <إيميل> <وصف> - لحجز إيميل مع وصف\n'
        '🔹 /check <إيميل> - للتحقق من إيميل\n'
        '🔹 /my_emails - لعرض إيميلاتي مع زر الحذف\n'
        '🔹 /search <نص> - للبحث عن إيميلات\n'
        '🔹 /stats - لإحصائيات البوت\n'
        '🔹 /help - للمساعدة'
    )

# أمر /reserve لحجز إيميل مع وصف
async def reserve(update: Update, context: CallbackContext):
    user = update.effective_user
    
    if not context.args:
        await update.message.reply_text(
            '❌ الرجاء إدخال إيميل ووصف\n'
            '📝 مثال: /reserve example@gmail.com هذا وصف للإيميل'
        )
        return
    
    # نأخذ أول كلمة كإيميل والباقي كوصف
    email = context.args[0].strip().lower()
    description = ' '.join(context.args[1:]) if len(context.args) > 1 else "لا يوجد وصف"
    
    # التحقق من صحة الإيميل
    if not is_valid_email(email):
        await update.message.reply_text(
            '❌ صيغة الإيميل غير صحيحة\n'
            '📝 مثال صحيح: username@domain.com\n'
            '🔹 يجب أن يحتوي على @ ونقطة\n'
            '🔹 يجب أن يكون اسم النطاق صحيحاً'
        )
        return
    
    # التحقق من أن الإيميل غير محجوز
    if check_email(email):
        await update.message.reply_text(f'❌ الإيميل {email} محجوز بالفعل')
        return
    
    # حجز الإيميل
    if reserve_email(email, user.id, user.username, description):
        await update.message.reply_text(
            f'✅ تم حجز الإيميل بنجاح\n'
            f'📧 {email}\n'
            f'📝 الوصف: {description}\n'
            f'👤 بواسطة: @{user.username or user.first_name}'
        )
    else:
        await update.message.reply_text('❌ فشل في حجز الإيميل')

# أمر /check للتحقق من الإيميل
async def check(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text('❌ الرجاء إدخال إيميل\nمثال: /check example@gmail.com')
        return
    
    email = ' '.join(context.args).strip().lower()
    
    # التحقق من صحة الإيميل أولاً
    if not is_valid_email(email):
        await update.message.reply_text('❌ صيغة الإيميل غير صحيحة')
        return
    
    result = check_email(email)
    
    if result:
        email_addr, user_id, username, description, date = result
        response = (
            f'📌 **معلومات الإيميل:**\n'
            f'📧 {email_addr}\n'
            f'📝 **الوصف:** {description}\n'
            f'👤 **المستخدم:** {username or "غير معروف"}\n'
            f'🆔 **ID:** {user_id}\n'
            f'📅 **تاريخ الحجز:** {date}'
        )
        await update.message.reply_text(response, parse_mode='Markdown')
    else:
        await update.message.reply_text(f'✅ الإيميل {email} متاح للحجز')

# أمر /my_emails لعرض الإيميلات مع زر الحذف
async def my_emails(update: Update, context: CallbackContext):
    user = update.effective_user
    
    db_path = '/tmp/emails.db' if 'RENDER' in os.environ else 'emails.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT email, description, date FROM emails WHERE user_id=? ORDER BY date DESC", (user.id,))
    emails = c.fetchall()
    conn.close()
    
    if emails:
        # إنشاء لوحة مفاتيح مع أزرار الحذف
        keyboard = []
        
        for email, description, date in emails:
            # إضافة زر الحذف لكل إيميل
            keyboard.append([
                InlineKeyboardButton(
                    f"🗑️ حذف {email}",
                    callback_data=f"delete_{email}"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # إعداد قائمة الإيميلات
        response = "📧 **إيميلاتك المحجوزة:**\n\n"
        for i, (email, description, date) in enumerate(emails, 1):
            response += f"{i}. **{email}**\n"
            response += f"   📝 {description}\n"
            response += f"   📅 {date}\n\n"
        
        response += f"📊 **الإجمالي:** {len(emails)} إيميل\n"
        response += "🔽 **اضغط على الزر لحذف الإيميل**"
        
        await update.message.reply_text(response, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text("📭 ليس لديك إيميلات محجوزة بعد")

# معالجة زر الحذف
async def delete_button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    callback_data = query.data
    
    # التحقق من أن البيانات تحتوي على delete_
    if callback_data.startswith("delete_"):
        email = callback_data.replace("delete_", "")
        
        # حذف الإيميل من قاعدة البيانات
        if delete_email_from_db(email, user_id):
            # تحديث الرسالة
            await query.edit_message_text(
                f"✅ تم حذف الإيميل: {email}\n"
                f"🔄 يتم تحديث القائمة..."
            )
            
            # إعادة عرض الإيميلات المتبقية
            db_path = '/tmp/emails.db' if 'RENDER' in os.environ else 'emails.db'
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT email, description, date FROM emails WHERE user_id=? ORDER BY date DESC", (user_id,))
            emails = c.fetchall()
            conn.close()
            
            if emails:
                # إنشاء لوحة مفاتيح جديدة
                keyboard = []
                
                for email, description, date in emails:
                    keyboard.append([
                        InlineKeyboardButton(
                            f"🗑️ حذف {email}",
                            callback_data=f"delete_{email}"
                        )
                    ])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # إعداد قائمة الإيميلات المحدثة
                response = "📧 **إيميلاتك المحجوزة:**\n\n"
                for i, (email, description, date) in enumerate(emails, 1):
                    response += f"{i}. **{email}**\n"
                    response += f"   📝 {description}\n"
                    response += f"   📅 {date}\n\n"
                
                response += f"📊 **الإجمالي:** {len(emails)} إيميل\n"
                response += "🔽 **اضغط على الزر لحذف الإيميل**"
                
                await query.edit_message_text(response, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await query.edit_message_text("✅ تم حذف جميع الإيميلات\n📭 ليس لديك إيميلات محجوزة حالياً")
        else:
            await query.edit_message_text(
                f"❌ فشل في حذف الإيميل: {email}\n"
                f"⚠️ ربما الإيميل غير موجود أو ليس لديك صلاحية لحذفه"
            )

# أمر /reeserv (بديل لـ /reserve)
async def reeserv(update: Update, context: CallbackContext):
    await reserve(update, context)

# أمر /help
async def help_command(update: Update, context: CallbackContext):
    help_text = """
📚 **أوامر بوت حجز الإيميلات:**

🔹 /start - بدء البوت
🔹 /reserve <إيميل> <وصف> - لحجز إيميل مع وصف
🔹 /check <إيميل> - التحقق من حالة إيميل
🔹 /my_emails - عرض إيميلاتك مع زر الحذف
🔹 /help - عرض هذه الرسالة

📝 **صيغة الإيميل الصحيحة:**
- مثال: username@domain.com
- يجب أن يحتوي على @ ونقطة

⚠️ **ملاحظات:**
- الحجز دائم حتى تقوم بحذفه
- كل مستخدم يمكنه حذف إيميلاته فقط
"""
    await update.message.reply_text(help_text)

# الدالة الرئيسية
def main():
    # التوكن من متغير البيئة في Render
    TOKEN = os.environ.get("8322471161:AAEwthafhAceZSx-dAqHfO8Pzpegf9ppNEc")
    
    if not TOKEN:
        print("❌ TELEGRAM_TOKEN غير موجود!")
        print("🔹 في Render، اذهب إلى Environment → Add Environment Variable")
        print("🔹 أضف: Key=TELEGRAM_TOKEN, Value=توكنك")
        return
    
    # التحقق من صحة التوكن
    if ":" not in TOKEN or not TOKEN.split(":")[0].isdigit():
        print("❌ التوكن غير صحيح!")
        print("📌 التوكن يجب أن يكون بهذا الشكل: 123456789:ABCdef...")
        return
    
    try:
        # تهيئة قاعدة البيانات
        init_db()
        
        # إنشاء التطبيق
        print(f"🔹 جاري إنشاء التطبيق مع التوكن: {TOKEN[:10]}...")
        app = Application.builder().token(TOKEN).build()
        
        # إضافة الأوامر
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("reserve", reserve))
        app.add_handler(CommandHandler("reeserv", reeserv))
        app.add_handler(CommandHandler("check", check))
        app.add_handler(CommandHandler("my_emails", my_emails))
        app.add_handler(CommandHandler("help", help_command))
        
        # إضافة معالج لزر الحذف
        app.add_handler(CallbackQueryHandler(delete_button_callback, pattern=r'^delete_'))
        
        # بدء البوت
        print("✅" * 50)
        print("🤖 بوت حجز الإيميلات يعمل بنجاح!")
        print(f"📧 البوت ID: {TOKEN.split(':')[0]}")
        print(f"🌍 البيئة: {'Render' if 'RENDER' in os.environ else 'Local'}")
        print("✅" * 50)
        
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        print("❌" * 50)
        print(f"خطأ في تشغيل البوت: {type(e).__name__}")
        print(f"التفاصيل: {e}")
        print("❌" * 50)
        raise

if __name__ == '__main__':
    main()
