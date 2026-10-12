Cooler Control - پروژه کنترل کولر با Kivy
========================================

فایل‌ها:
- main.py: نقطه ورود، چهار صفحه و منطق ارسال/نمایش داده
- cooler.kv: طراحی رابط کاربری
- bluetooth_manager.py: Bluetooth Classic SPP و خواندن خطی
- time_picker.py: انتخاب ساعت و دقیقه با Spinner
- numeric_keypad.py: صفحه‌کلید عددی مستقل
- buildozer.spec: تنظیمات ساخت APK
- requirements.txt: وابستگی‌های پایتون
- assets/icon.png: آیکون نمونه

ساخت APK:
1) روی Linux یا WSL2 یک محیط Buildozer آماده کنید.
2) وارد پوشه پروژه شوید.
3) دستورهای زیر را اجرا کنید:
   pip install buildozer
   buildozer android debug
4) فایل APK معمولاً در پوشه bin ساخته می‌شود.

نکته‌های مهم اندروید:
- ابتدا HC-05 را از تنظیمات Android جفت کنید (PIN معمولاً 1234 یا 0000 است، بسته به ماژول).
- سپس در صفحه Settings دستگاه را انتخاب و Connect کنید.
- نسخه‌های جدید Android ممکن است مجوز Nearby devices / Bluetooth را هنگام اجرا بخواهند. برای انتشار نهایی، مجوزهای runtime را متناسب با نسخه Android هدف مدیریت کنید.
- buildozer.spec از API 33 استفاده می‌کند؛ پشتیبانی مجوزهای runtime باید قبل از انتشار روی گوشی واقعی آزمایش شود.
- KivyMD 1.2.0 سبک Material 2 دارد، نه پیاده‌سازی کامل Material 3.

پروتکل:
ثابت‌ها: 1, 2, 3, 4, T, t, s, hFA, hEN
پویا: S + HHMM، ON + HHMM، OFF + HHMM
هر فرمان دقیقاً با LF یعنی \n پایان می‌یابد.

توجه:
برنامه فقط پاسخ‌هایی را که آردوینو واقعاً می‌فرستد می‌تواند نشان دهد. برای نمایش دما، رطوبت و وضعیت، فریمور آردوینو باید خطوطی مانند
Temp: 28.5 C
Humidity: 45.0 %
Time: 14:30
Mode: Auto
Pump: ON
Motor: Slow
Timer: ON
را ارسال کند.
