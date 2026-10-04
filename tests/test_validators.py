from app.validators import is_valid_mobile, is_valid_national_id, normalize_phone


def test_valid_national_id_accepts_persian_digits():
    assert is_valid_national_id("۰۰۱۳۵۴۷۵۴۲")


def test_national_id_rejects_repeated_digits():
    assert not is_valid_national_id("۱۱۱۱۱۱۱۱۱۱")


def test_phone_normalization():
    assert normalize_phone("+98 913 123 4567") == "09131234567"
    assert is_valid_mobile("۰۹۱۳۱۲۳۴۵۶۷")
