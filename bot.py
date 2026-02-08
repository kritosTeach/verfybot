import os
import sys
import sqlite3
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

# ... (الوظائف كلها تبقى نفسها) ...

def main():
    # طريقة 1: التوكن مباشرة (أحذف هاد التعليق واستعمل التوكن الحقيقي)
    # TOKEN = "ضع_توكن_بوتك_هنا"
    
    # طريقة 2: من متغير بيئة
    TOKEN = os.environ.get("7544040053:AAE4jEeMnpoI3L7Fc_s0yTe6F8gkuvD5-Ug")
    
    # طريقة 3: من ملف .env
    # from dotenv import load_dotenv
    # load_dotenv()
    # TOKEN = os.environ.get("TELEGRAM_TOKEN")
    
    # التحقق من التوكن
    if not TOKEN or TOKEN == "ضع_توكن_بوتك_هنا":
        print("❌" * 50)
        print("❌ خطأ: التوكن غير صحيح!")
        print("❌" * 50)
        print("\n🔹 إليك خطوات الحل:")
        print("1. اذهب إلى @BotFather في تلغرام")
        print("2. أرسل /mybots")
        print("3. إختر البوت الخاص بك")
        print("4. إضغط على API Token")
        print("5. إنسخ التوكن")
        print("\n🔹 ثم:")
        print("- إما ضع التوكن مباشرة في الكود (سطر 372)")
        print("- أو أضف متغير بيئة TELEGRAM_TOKEN في Railway")
        print("\nمتغير البيئة في Railway:")
        print("1. اذهب إلى Settings → Variables")
        print("2. أضف: Name=TELEGRAM_TOKEN, Value=توكنك")
        print("3. إضغط Add ثم Redeploy")
        return
    
    # التحقق من صحة التوكن (يجب أن يحتوي على : ويبدأ بأرقام)
    if ":" not in TOKEN or not TOKEN.split(":")[0].isdigit():
        print(f"❌ التوكن غير صحيح: {TOKEN[:20]}...")
        print("📌 التوكن الصحيح يجب أن يكون بهذا الشكل: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz123456")
        return
    
    try:
        # تهيئة قاعدة البيانات
        init_db()
        
        # إنشاء التطبيق
        print("🔹 محاولة إنشاء التطبيق...")
        app = Application.builder().token(TOKEN).build()
        
        # إضافة الأوامر
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("reserve", reserve))
        app.add_handler(CommandHandler("reeserv", reeserv))
        app.add_handler(CommandHandler("check", check))
        app.add_handler(CommandHandler("my_emails", my_emails))
        app.add_handler(CommandHandler("search", search))
        app.add_handler(CommandHandler("stats", stats))
        app.add_handler(CommandHandler("help", help_command))
        
        # إضافة معالج لزر الحذف
        app.add_handler(CallbackQueryHandler(delete_button_callback, pattern=r'^delete_'))
        
        # بدء البوت
        print("✅" * 50)
        print("🤖 بوت حجز الإيميلات يعمل بنجاح!")
        print(f"📧 البوت: {TOKEN.split(':')[0]}")
        print("📁 قاعدة البيانات: emails.db")
        print("✅" * 50)
        
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        print("❌" * 50)
        print(f"❌ خطأ في تشغيل البوت: {type(e).__name__}")
        print(f"❌ التفاصيل: {e}")
        print("❌" * 50)
        
        # معلومات إضافية للإصلاح
        if "token" in str(e).lower() or "authorized" in str(e).lower():
            print("\n🔹 المشكلة في التوكن:")
            print("- تأكد من أن التوكن صحيح")
            print("- حاول إنشاء بوت جديد من @BotFather")
            print("- تأكد من أنك لم تستعمل التوكن في مكان آخر")
        
        if "timed out" in str(e).lower():
            print("\n🔹 مشكلة في الاتصال:")
            print("- تأكد من أن Railway يسمح باتصالات الصادرة")
            print("- حاول تغيير المنطقة (Region) في Railway")
        
        # إعادة رفع الخطأ للرؤية في اللوغات
        raise

if __name__ == '__main__':
    main()
