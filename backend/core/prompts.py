from typing import Optional, Literal
from backend.models.schemas import LabMeta

DocType = Literal["referat","article_ru","article_en","article_ru_en","lab"]

def _section_template(doc_type: str, lab_meta: Optional[LabMeta]) -> list[dict]:
    if doc_type == "article_en":
        return [
            {"title": "Abstract"},
            {"title": "Keywords"},
            {"title": "Introduction"},
            {"title": "Main Body", "sub": ["Background","Methods","Results","Discussion"]},
            {"title": "Conclusion"},
            {"title": "References"},
        ]
    if doc_type == "article_ru":
        return [
            {"title": "Аннотация"},
            {"title": "Ключевые слова"},
            {"title": "Введение"},
            {"title": "Основная часть", "sub": ["Предпосылки","Методы","Результаты","Обсуждение"]},
            {"title": "Заключение"},
            {"title": "Список литературы"},
        ]
    if doc_type == "article_ru_en":
        return [
            {"title": "Abstract / Аннотация"},
            {"title": "Keywords / Ключевые слова"},
            {"title": "Введение"},
            {"title": "Основная часть", "sub": ["История/Предпосылки","Методы","Результаты","Обсуждение"]},
            {"title": "Заключение"},
            {"title": "Список литературы / References"},
        ]
    if doc_type == "lab":
        return [
            {"title": "Титульный лист"},
            {"title": "Цель работы"},
            {"title": "Оборудование и ПО"},
            {"title": "Теоретические сведения"},
            {"title": "Ход работы", "sub": ["Постановка эксперимента","Выполнение"]},
            {"title": "Результаты"},
            {"title": "Анализ и обсуждение"},
            {"title": "Заключение"},
            {"title": "Список источников"},
        ]
    return [
        {"title": "Введение"},
        {"title": "Основная часть", "sub": ["1. Теоретическая часть","2. Практическая часть"]},
        {"title": "Заключение"},
        {"title": "Список литературы"},
    ]

def estimate_words(page_target: int, line_spacing: float, font_size: int) -> int:
    base = 380
    factor = 1.0
    if line_spacing >= 1.5:
        factor *= 1.18
    if font_size >= 14:
        factor *= 1.12
    return max(320, int(base * factor * page_target))

def build_prompt(doc_type: str, topic: str, locale: str, style: str, depth: int,
                 requirements: Optional[str], lab_meta: Optional[LabMeta],
                 page_target: int, line_spacing: float = 1.15, font_size: int = 12) -> str:
    words_target = estimate_words(page_target, line_spacing, font_size)
    templ = _section_template(doc_type, lab_meta)

    lab_lines = []
    if lab_meta:
        if lab_meta.discipline: lab_lines.append(f"discipline: {lab_meta.discipline}")
        if lab_meta.variant: lab_lines.append(f"variant: {lab_meta.variant}")
        if lab_meta.goal: lab_lines.append(f"goal: {lab_meta.goal}")
        if lab_meta.equipment: lab_lines.append(f"equipment: {lab_meta.equipment}")
    lab_info = "; ".join(lab_lines) if lab_lines else ""
    extra = f"Additional requirements: {requirements}" if requirements else ""

    distribution = {"intro": 0.15, "main": 0.70, "outro": 0.15}
    intro_w = int(words_target * distribution["intro"])
    main_w = int(words_target * distribution["main"])
    outro_w = int(words_target * distribution["outro"])

    return (
        "You are an academic writer that outputs STRICT JSON only. No markdown, no code fences, no comments.\n\n"
        f"Context:\n"
        f"- Language: {locale}\n"
        f"- Style: {style}\n"
        f"- Topic: {topic}\n"
        f"- Target length: ~{words_target} words (±10%)\n"
        f"- Section budget guideline:\n"
        f"  - Introduction ≈ {intro_w} words\n"
        f"  - Main body ≈ {main_w} words\n"
        f"  - Conclusion ≈ {outro_w} words\n"
        f"- Max outline depth: {depth}\n"
        f"- {extra}\n"
        f"- {('Lab meta: ' + lab_info) if lab_info else ''}\n\n"
        f"Follow this exact section template (order and titles must match). For items with 'sub', create child sections with those exact titles:\n"
        f"{templ}\n\n"
        "Output JSON schema:\n"
        "{\n"
        '  "title": "string",\n'
        '  "paragraphs": [],\n'
        '  "subsections": []\n'
        "}\n\n"
        "Rules:\n"
        "- Under-generation is not allowed: expand with concise definitions, short examples, brief explanations until the word budget is met.\n"
        "- No markdown markers (#, *, -, 1.). Plain text sentences only.\n"
        "- No inline citations; references only as individual paragraphs in the final references section, formatted like: [1] Автор. Название. Год.\n"
        "- For 'Keywords'/'Ключевые слова', use one paragraph with comma-separated keywords.\n"
        "- For lab, integrate goal and equipment into respective sections.\n\n"
        "Respond with JSON only."
    )
