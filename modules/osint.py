def get_osint_links(parsed):
    country_code = str(parsed.country_code)
    national_number = str(parsed.national_number)
    num = country_code + national_number

    return {
        "Truecaller": f"https://www.truecaller.com/search/{country_code}/{national_number}",
        "Google": f"https://www.google.com/search?q={num}",
        "GoogleExact": f"https://www.google.com/search?q=%22{num}%22",
        "Bing": f"https://www.bing.com/search?q=%22{num}%22",
        "Facebook": f"https://www.facebook.com/search/top/?q={num}",
        "LinkedIn": f"https://www.linkedin.com/search/results/all/?keywords={num}",
        "WhatsApp": f"https://wa.me/{num}",
        "Telegram": f"https://t.me/{num}",
    }
