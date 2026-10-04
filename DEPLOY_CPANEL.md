# استقرار روی cPanel با MySQL

این راهنما مخصوص هاستی است که قابلیت **Setup Python App / Python Selector**، نسخه Python 3.11 یا جدیدتر و دسترسی Terminal یا SSH داشته باشد.

اگر این گزینه در cPanel وجود ندارد، این پروژه روی آن هاست اجرا نمی‌شود و باید از شرکت میزبان درخواست فعال‌سازی Passenger Python کنید یا VPS تهیه کنید.

## 1. پیش‌نیازها

از پشتیبانی هاست کتبی بپرسید:

- آیا Setup Python App و Passenger فعال است؟
- آیا Python 3.11 یا جدیدتر موجود است؟
- آیا نصب پکیج با pip مجاز است؟
- آیا برنامه Python می‌تواند درخواست POST از اینترنت دریافت کند؟
- سقف فضای دیسک و حجم فایل چقدر است؟
- آیا AutoSSL برای زیردامنه فعال می‌شود؟

## 2. ساخت زیردامنه

در Domains یک زیردامنه مانند `nobat.example.ir` بسازید و AutoSSL را برای آن فعال کنید. برنامه بله به HTTPS معتبر نیاز دارد.

## 3. ساخت MySQL

در MySQL Databases:

1. یک database بسازید، مثلاً `kosar_booking`.
2. یک user بسازید، مثلاً `kosar_app`، با رمز قوی و URL-safe.
3. کاربر را با ALL PRIVILEGES به database اضافه کنید.
4. نام کامل database و user معمولاً پیشوند حساب cPanel دارد؛ همان نام کامل را استفاده کنید.
5. Collation دیتابیس را `utf8mb4_unicode_ci` قرار دهید.

## 4. بارگذاری فایل‌ها

فایل ZIP پروژه را در مسیری بیرون از `public_html`، مثلاً `/home/USER/kosar-app` استخراج کنید. فایل `.env` و پوشه `storage` نباید در دسترس مستقیم وب باشند.

## 5. ایجاد Python App

در Setup Python App:

- Python version: 3.11 یا جدیدتر
- Application root: `kosar-app`
- Application URL: زیردامنه ساخته‌شده
- Startup file: `passenger_wsgi.py`
- Entry point: `application`

پس از ساخت، دستور فعال‌سازی virtualenv را که cPanel نمایش می‌دهد در Terminal اجرا کنید. سپس:

```bash
cd ~/kosar-app
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 6. تنظیم اسرار

از `.env.cpanel.example` یک فایل `.env` بسازید و مقادیر واقعی را وارد کنید. توکن و رمزها را در Git یا گفت‌وگو منتشر نکنید.

نمونه DATABASE_URL:

```text
mysql+pymysql://cpuser_kosarapp:StrongPass123@localhost/cpuser_kosarbooking?charset=utf8mb4
```

اگر رمز دارای `@`، `:`، `/`، `#` یا `%` باشد باید URL-encode شود؛ برای ساده‌شدن استقرار، رمز بسیار قوی ولی متشکل از حروف، اعداد، خط تیره و زیرخط انتخاب کنید.

تولید APP_SECRET:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

تولید ENCRYPTION_KEY:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 7. ساخت جدول‌ها

```bash
cd ~/kosar-app
python scripts/check_production_config.py
python scripts/init_db.py
```

پیام موفقیت باید نمایش داده شود.

## 8. مجوز پوشه عکس‌ها

```bash
mkdir -p storage/photos
chmod 750 storage storage/photos
```

## 9. راه‌اندازی مجدد Passenger

در Setup Python App روی Restart کلیک کنید. اگر چنین دکمه‌ای نبود:

```bash
mkdir -p tmp
touch tmp/restart.txt
```

## 10. آزمایش

این نشانی‌ها را بررسی کنید:

- صفحه اصلی: `https://nobat.example.ir/`
- سلامت برنامه: `https://nobat.example.ir/health`
- پنل: `https://nobat.example.ir/admin`

پاسخ health باید شامل `"ok": true` باشد. یک نوبت کاملاً آزمایشی ثبت و سپس فایل CSV پنل را امتحان کنید.

## 11. پشتیبان‌گیری

حداقل روزانه از MySQL و پوشه خصوصی `storage/photos` نسخه پشتیبان رمزگذاری‌شده تهیه کنید. دسترسی فایل‌های عکس را از مرورگر عمومی مسدود نگه دارید.

## 12. اتصال بله

فقط پس از درست‌بودن HTTPS و تست کامل، توکن بازو در متغیر `BALE_BOT_TOKEN` قرار می‌گیرد و Webhook ثبت می‌شود. این بخش در مرحله بعد پروژه تکمیل خواهد شد.
