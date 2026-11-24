from rag.chunker import MAX_CHUNK_CHARS, split_into_chunks

SAMPLE = """# Payment terms

## Standard terms
- Pay within 30 days.
- Bank transfer only.

## Reminders
- Reminder every 7 days.
"""


def test_each_section_becomes_one_chunk_with_title_and_heading():
    chunks = split_into_chunks(SAMPLE)

    assert len(chunks) == 2
    assert chunks[0].startswith("Payment terms: Standard terms\n")
    assert "Pay within 30 days." in chunks[0]
    assert chunks[1].startswith("Payment terms: Reminders\n")


def test_a_section_without_text_is_skipped():
    text = "# Title\n\n## Empty section\n\n## Real section\n- Something\n"

    chunks = split_into_chunks(text)

    assert len(chunks) == 1
    assert "Real section" in chunks[0]


def test_text_before_the_first_heading_is_kept_with_the_title():
    text = "# Policy\nThis policy applies to everyone.\n\n## Rules\n- One rule\n"

    chunks = split_into_chunks(text)

    assert chunks[0] == "Policy\nThis policy applies to everyone."


def test_a_long_section_is_split_and_every_piece_keeps_the_heading():
    lines = [f"- Rule number {number} with some extra words to make it longer" for number in range(60)]
    text = "# Big\n\n## Many rules\n" + "\n".join(lines) + "\n"

    chunks = split_into_chunks(text)

    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.startswith("Big: Many rules\n")
        assert len(chunk) <= MAX_CHUNK_CHARS + 100


def test_empty_text_gives_no_chunks():
    assert split_into_chunks("") == []
