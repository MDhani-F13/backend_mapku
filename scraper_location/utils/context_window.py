# scraper_location/utils/context_window.py

def extract_context_window(sentence: str, locs: list, window: int = 3) -> str:
    """
    Potong kalimat di sekitar LOC valid.
    Ambil window N token sebelum & sesudah setiap LOC.
    Gabungkan snippet, dedup token.
    """
    words = sentence.split()
    indices = []

    for loc in locs:
        loc_tokens = loc.split()
        for i in range(len(words) - len(loc_tokens) + 1):
            if words[i:i+len(loc_tokens)] == loc_tokens:
                indices.append((i, i + len(loc_tokens) - 1))

    snippets = []
    for start, end in indices:
        w_start = max(0, start - window)
        w_end = min(len(words), end + 1 + window)
        snippets.append(words[w_start:w_end])

    # Gabung semua snippet ➜ flatten ➜ dedup urut
    context_words = []
    for snip in snippets:
        for w in snip:
            if w not in context_words:
                context_words.append(w)

    return ' '.join(context_words)
