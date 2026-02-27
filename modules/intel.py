from phonenumbers import PhoneNumberFormat, PhoneNumberType, format_number, number_type

LINE_TYPE_MAP = {
    PhoneNumberType.FIXED_LINE: "FIXED_LINE",
    PhoneNumberType.MOBILE: "MOBILE",
    PhoneNumberType.FIXED_LINE_OR_MOBILE: "FIXED_LINE_OR_MOBILE",
    PhoneNumberType.TOLL_FREE: "TOLL_FREE",
    PhoneNumberType.PREMIUM_RATE: "PREMIUM_RATE",
    PhoneNumberType.SHARED_COST: "SHARED_COST",
    PhoneNumberType.VOIP: "VOIP",
    PhoneNumberType.PERSONAL_NUMBER: "PERSONAL_NUMBER",
    PhoneNumberType.PAGER: "PAGER",
    PhoneNumberType.UAN: "UAN",
    PhoneNumberType.VOICEMAIL: "VOICEMAIL",
    PhoneNumberType.UNKNOWN: "UNKNOWN",
}


def get_line_type(parsed):
    try:
        return LINE_TYPE_MAP.get(number_type(parsed), "UNKNOWN")
    except Exception:
        return "UNKNOWN"


def get_number_formats(parsed):
    formats = {}
    try:
        formats["E164"] = format_number(parsed, PhoneNumberFormat.E164)
        formats["International"] = format_number(parsed, PhoneNumberFormat.INTERNATIONAL)
        formats["National"] = format_number(parsed, PhoneNumberFormat.NATIONAL)
        formats["RFC3966"] = format_number(parsed, PhoneNumberFormat.RFC3966)
    except Exception:
        return {}
    return formats
