import re


PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize_digits(value: str) -> str:
    return value.translate(PERSIAN_DIGITS).strip()


def normalize_national_id(value: str) -> str:
    return re.sub(r"\D", "", normalize_digits(value))


def is_valid_national_id(value: str) -> bool:
    code = normalize_national_id(value)
    if len(code) != 10 or len(set(code)) == 1:
        return False
    check = int(code[-1])
    total = sum(int(code[i]) * (10 - i) for i in range(9)) % 11
    expected = total if total < 2 else 11 - total
    return check == expected


def normalize_phone(value: str) -> str:
    phone = re.sub(r"\D", "", normalize_digits(value))
    if phone.startswith("0098"):
        phone = "0" + phone[4:]
    elif phone.startswith("98"):
        phone = "0" + phone[2:]
    return phone


def is_valid_mobile(value: str) -> bool:
    return bool(re.fullmatch(r"09\d{9}", normalize_phone(value)))


def clean_name(value: str) -> str:
    return " ".join(value.strip().split())


def is_valid_name(value: str) -> bool:
    value = clean_name(value)
    return 2 <= len(value) <= 100 and bool(re.fullmatch(r"[آ-یءئؤإأۀة\s\-]+", value))
