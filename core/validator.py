import phonenumbers
from phonenumbers import NumberParseException

def validate_number(number):
    if not number or not number.strip():
        return False, None

    try:
        parsed = phonenumbers.parse(number)
        return phonenumbers.is_valid_number(parsed), parsed
    except NumberParseException:
        return False, None
