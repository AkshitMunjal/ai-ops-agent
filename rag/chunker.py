MAX_CHUNK_CHARS = 1200


def read_sections(text):
    """Return the document title and a list of (heading, body) pairs."""
    title = ""
    sections = []
    current_heading = ""
    current_lines = []

    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("## "):
            sections.append((current_heading, current_lines))
            current_heading = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    sections.append((current_heading, current_lines))
    return title, sections


def split_long_lines(lines, max_chars):
    """Group lines into pieces that are not longer than max_chars."""
    pieces = []
    current_piece = []
    current_length = 0

    for line in lines:
        line_length = len(line) + 1

        if current_piece and current_length + line_length > max_chars:
            pieces.append("\n".join(current_piece))
            current_piece = []
            current_length = 0

        current_piece.append(line)
        current_length += line_length

    if current_piece:
        pieces.append("\n".join(current_piece))

    return pieces


def make_chunk_text(title, heading, body):
    if heading:
        first_line = f"{title}: {heading}"
    else:
        first_line = title

    return f"{first_line}\n{body}"


def split_into_chunks(text):
    """Split one document into chunks. Each chunk starts with its title and heading."""
    title, sections = read_sections(text)
    chunks = []

    for heading, lines in sections:
        body_lines = [line for line in lines if line.strip() != ""]

        if not body_lines:
            continue

        for piece in split_long_lines(body_lines, MAX_CHUNK_CHARS):
            chunks.append(make_chunk_text(title, heading, piece))

    return chunks
