from datetime import date


def format_amount(amount):
    return f"{amount:,.2f}"


def format_date(date_text):
    parsed_date = date.fromisoformat(date_text)
    return parsed_date.strftime("%d %b %Y")