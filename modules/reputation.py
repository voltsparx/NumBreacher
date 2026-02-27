def get_reputation_links(parsed):
    number = f"{parsed.country_code}{parsed.national_number}"

    return {
        "800notes": f"https://800notes.com/Phone.aspx/{number}",
        "WhoCalledMe": f"https://whocalledme.com/Phone-Number.aspx/{number}",
        "SpamCalls": f"https://spamcalls.net/en/number/{number}",
    }
