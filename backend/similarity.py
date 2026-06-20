"""
Модуль определения похожести библиографических ссылок.
Изолирован специально, чтобы можно было менять алгоритм,
не трогая остальной backend. Безопасно удалить весь файл
и вызов check_duplicates() в app.py — система продолжит работать.
"""

import re

STOP_WORDS = {
    'vol', 'no', 'pp', 'p', 'ed', 'eds', 'trans', 'transl',
    'in', 'and', 'the', 'of', 'a', 'an', 'on', 'at', 'as',
    'i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii',
    'press', 'publishers', 'publishing', 'university', 'co',
    'london', 'new', 'york', 'oxford', 'cambridge', 'paris', 'berlin'
}


def _tokenize(text):
    text = text.lower()
    words = re.findall(r"[a-zа-яё']+|\d{4}", text)
    return [w for w in words if w not in STOP_WORDS and len(w) > 1]


def _jaccard(set_a, set_b):
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union else 0.0


def _extract_year(text):
    match = re.search(r'\b(1[5-9]\d{2}|20\d{2})\b', text)
    return match.group(1) if match else None


def _extract_first_word(text):
    words = re.findall(r"[A-Za-zА-Яа-яЁё']+", text)
    return words[0].lower() if words else None


def similarity_score(text_a, text_b):
    """
    Возвращает (score 0..1, причина).
    score — комбинация пересечения слов + бонусы за совпадение
    года и первого слова (обычно фамилия автора).
    """
    tokens_a = set(_tokenize(text_a))
    tokens_b = set(_tokenize(text_b))

    base = _jaccard(tokens_a, tokens_b)

    year_a = _extract_year(text_a)
    year_b = _extract_year(text_b)
    year_match = (year_a is not None and year_a == year_b)

    author_a = _extract_first_word(text_a)
    author_b = _extract_first_word(text_b)
    author_match = (author_a is not None and author_a == author_b)

    score = base
    if year_match:
        score += 0.15
    if author_match:
        score += 0.15

    score = min(score, 1.0)
    return score


def check_duplicates(new_citation, existing_sources, threshold=0.45, max_results=3):
    """
    existing_sources: список dict с ключами 'id', 'citation', 'short_name'
    Возвращает список похожих источников, отсортированный по убыванию score.
    """
    results = []
    for src in existing_sources:
        score = similarity_score(new_citation, src['citation'])
        if score >= threshold:
            results.append({
                'id': src['id'],
                'short_name': src['short_name'],
                'citation': src['citation'],
                'score': round(score * 100)
            })

    results.sort(key=lambda r: r['score'], reverse=True)
    return results[:max_results]
