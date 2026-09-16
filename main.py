import os
import json
import subprocess
from telegram import Update
from telegram.request import HTTPXRequest
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = '8765516812:AAGnhYjAYr36Es580De4ojn8oHZ7HyRXDnw'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أرسل لي أي فيديو (سواء كـ فيديو عادي أو كـ ملف Document) وسأقوم بفحصه واستخراج معلومات الـ HDR والدقة.")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("جاري تحميل الملف واستخراج التفاصيل...")
    
    document = update.message.document
    video = update.message.video

    if video:
        file_obj = await video.get_file()
    elif document:
        file_obj = await document.get_file()
    else:
        await msg.edit_text("يرجى إرسال ملف فيديو.")
        return

    file_path = "temp_video.mp4"
    await file_obj.download_to_drive(file_path)

    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', '-show_format', file_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        data = json.loads(result.stdout)

        video_stream = next((s for s in data.get('streams', []) if s.get('codec_type') == 'video'), None)

        if not video_stream:
            await msg.edit_text("لم يتم العثور على مسار فيديو صالح داخل هذا الملف.")
            return

        pix_fmt = video_stream.get('pix_fmt', 'غير معروف')
        color_space = video_stream.get('color_space', 'غير معروف')
        color_transfer = video_stream.get('color_transfer', 'غير معروف')
        width = video_stream.get('width', 'غير معروف')
        height = video_stream.get('height', 'غير معروف')
        codec = video_stream.get('codec_name', 'غير معروف')
        
        hdr_keywords = ['hdr', '10bit', 'bt2020', 'arib-std-b67', 'smpte2084', 'yuv420p10le']
        is_hdr = "نعم (HDR)" if any(k in f"{pix_fmt} {color_space} {color_transfer}".lower() for k in hdr_keywords) else "لا (SDR - 8bit)"

        report = (
            f"🎬 **تفاصيل الفيديو:**\n\n"
            f"🔹 **الدقة:** {width}x{height}\n"
            f"🔹 **الترميز (Codec):** {codec}\n"
            f"🔹 **صيغة البكسل (Pixel Format):** {pix_fmt}\n"
            f"🔹 **مساحة الألوان (Color Space):** {color_space}\n"
            f"🔹 **منحنى التحويل (Transfer):** {color_transfer}\n\n"
            f"✨ **دعم الـ HDR:** {is_hdr}"
        )

        await msg.edit_text(report, parse_mode="Markdown")

    except Exception as e:
        await msg.edit_text(f"حدث خطأ أثناء تحليل الفيديو: {str(e)}")
    
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0)
    
    app = ApplicationBuilder().token(TOKEN).request(request).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL, handle_video))
    
    print("البوت يعمل الآن...")
    app.run_polling()
