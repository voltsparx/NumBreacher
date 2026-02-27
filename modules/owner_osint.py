import html
import re
from collections import Counter
from urllib.parse import quote_plus

import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

NAME_PATTERN = re.compile(r"\b[A-Z][a-z]{2,}(?: [A-Z][a-z]{2,}){1,2}\b")
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
DUCK_RESULT_TITLE_PATTERN = re.compile(
    r'<a[^>]*class="result__a"[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL
)

STOPWORDS = {
    "truecaller",
    "telegram",
    "whatsapp",
    "facebook",
    "google",
    "search",
    "number",
    "phone",
    "caller",
    "unknown",
    "mobile",
    "contact",
    "lookup",
    "directory",
}

OWNER_CACHE = {}


def _clean_html(value):
    without_tags = HTML_TAG_PATTERN.sub(" ", value)
    text = html.unescape(without_tags)
    return " ".join(text.split())


def _extract_candidate_names(text):
    names = []
    for candidate in NAME_PATTERN.findall(text):
        if _is_likely_name(candidate):
            names.append(candidate)
    return names


def _is_likely_name(candidate):
    words = candidate.split()
    if len(words) < 2:
        return False

    lowered_words = {word.lower() for word in words}
    return lowered_words.isdisjoint(STOPWORDS)


def lookup_owner_name(parsed, timeout=4):
    number = f"{parsed.country_code}{parsed.national_number}"

    if number in OWNER_CACHE:
        return OWNER_CACHE[number]

    query_variants = [
        f"\"{number}\" \"Truecaller\"",
        f"\"{number}\" \"phone owner\"",
    ]

    votes = Counter()
    source_urls = []
    failed_queries = 0

    for query in query_variants:
        url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        source_urls.append(url)

        try:
            response = requests.get(url, headers=HEADERS, timeout=timeout)
            response.raise_for_status()
        except requests.RequestException:
            failed_queries += 1
            continue

        titles = DUCK_RESULT_TITLE_PATTERN.findall(response.text)
        for raw_title in titles[:10]:
            title = _clean_html(raw_title)
            for candidate_name in _extract_candidate_names(title):
                votes[candidate_name] += 1

    if not votes:
        notes = "No reliable owner name discovered in indexed public snippets."
        if failed_queries == len(query_variants):
            notes = "Owner lookup sources were unavailable."

        result = {
            "name": "Unknown",
            "confidence": "Low",
            "method": "DuckDuckGo search-snippet heuristic",
            "notes": notes,
            "sources": source_urls,
            "candidates": [],
        }
        OWNER_CACHE[number] = result
        return result

    top_candidates = [name for name, _ in votes.most_common(3)]
    best_name, score = votes.most_common(1)[0]

    if score >= 3:
        confidence = "High"
    elif score >= 2:
        confidence = "Medium"
    else:
        confidence = "Low"

    result = {
        "name": best_name,
        "confidence": confidence,
        "method": "DuckDuckGo search-snippet heuristic",
        "notes": "Heuristic guess from public indexed pages. Verify manually.",
        "sources": source_urls,
        "candidates": top_candidates,
    }
    OWNER_CACHE[number] = result
    return result
