from io import BytesIO

from PIL import Image

from app.photo_quality import check_photo


def image_bytes(size=(800, 800), color=(100, 120, 140)):
    image = Image.new("RGB", size, color)
    output = BytesIO()
    image.save(output, "JPEG")
    return output.getvalue()


def test_rejects_small_photo():
    result = check_photo(image_bytes((320, 320)))
    assert not result.accepted
    assert "۶۴۰" in result.reason


def test_rejects_invalid_file():
    assert not check_photo(b"not an image").accepted
