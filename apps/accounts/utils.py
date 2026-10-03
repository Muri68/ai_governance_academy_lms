import phonenumbers
from phonenumbers import geocoder


# Map ISO alpha-2 → emoji flag
# (Regional Indicator Symbols: A=🇦, B=🇧, ...)
def _flag_from_iso(iso_code: str) -> str:
    if not iso_code or len(iso_code) != 2:
        return '🌐'
    iso = iso_code.upper()
    return chr(0x1F1E6 + ord(iso[0]) - ord('A')) + chr(0x1F1E6 + ord(iso[1]) - ord('A'))


def get_country_flag(phone: str) -> str:
    """
    Given an E.164 phone string like '+447911123456',
    return its country flag emoji. Returns 🌐 if unknown.
    """
    if not phone:
        return '🌐'
    try:
        parsed = phonenumbers.parse(phone, None)
        region = phonenumbers.region_code_for_number(parsed)
        return _flag_from_iso(region)
    except phonenumbers.NumberParseException:
        return '🌐'


def get_country_name(phone: str) -> str:
    """Return human-readable country name, e.g. 'United Kingdom'."""
    if not phone:
        return ''
    try:
        parsed = phonenumbers.parse(phone, None)
        return geocoder.country_name_for_number(parsed, "en") or ''
    except phonenumbers.NumberParseException:
        return ''


def split_phone(phone: str):
    """
    Split an E.164 phone into (country_calling_code, national_number).
    E.g. '+447911123456' → ('+44', '7911123456')
    """
    if not phone:
        return ('', '')
    try:
        parsed = phonenumbers.parse(phone, None)
        cc = f"+{parsed.country_code}"
        national = str(parsed.national_number)
        return (cc, national)
    except phonenumbers.NumberParseException:
        return ('', phone)