from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageFilter, ImageStat, UnidentifiedImageError


@dataclass
class PhotoCheck:
    accepted: bool
    reason: str = ""
    width: int = 0
    height: int = 0


def check_photo(data: bytes) -> PhotoCheck:
    if len(data) > 10 * 1024 * 1024:
        return PhotoCheck(False, "حجم تصویر نباید بیشتر از ۱۰ مگابایت باشد.")
    try:
        image = Image.open(BytesIO(data))
        image.verify()
        image = Image.open(BytesIO(data)).convert("RGB")
    except (UnidentifiedImageError, OSError):
        return PhotoCheck(False, "فایل ارسالی یک تصویر معتبر نیست.")

    width, height = image.size
    if width < 640 or height < 640:
        return PhotoCheck(False, "ابعاد تصویر باید حداقل ۶۴۰ در ۶۴۰ پیکسل باشد.", width, height)

    preview = image.copy()
    preview.thumbnail((800, 800))
    gray = preview.convert("L")
    brightness = ImageStat.Stat(gray).mean[0]
    if brightness < 40:
        return PhotoCheck(False, "نور تصویر بسیار کم است؛ لطفاً در محیط روشن عکس بگیرید.", width, height)
    if brightness > 225:
        return PhotoCheck(False, "نور تصویر بیش از حد زیاد است.", width, height)

    edges = gray.filter(ImageFilter.FIND_EDGES)
    sharpness = ImageStat.Stat(edges).var[0]
    if sharpness < 45:
        return PhotoCheck(False, "تصویر تار است؛ دوربین را ثابت نگه دارید و دوباره عکس بگیرید.", width, height)

    return PhotoCheck(True, width=width, height=height)
