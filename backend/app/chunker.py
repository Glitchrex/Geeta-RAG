SEPARATORS = ("\n\n", "\n", ". ", " ") 

def split_text(text: str, max_chars: int, separators: tuple[str, ...] = SEPARATORS) -> list[str]:
    
    """ Split text into pieces of at most max_chars, cutting at the most natural boundary. """
    if len(text) <= max_chars:
        return [text]

    if not separators:
        return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]

    sep, finer = separators[0], separators[1:]
    pieces : list[str] = []
    current = ""

    for part in text.split(sep):
        candidate = f"{current}{sep}{part}" if current else part
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            pieces.append(current)
        if len(part) > max_chars:
            pieces.extend(split_text(part, max_chars, finer))
            current = ""
        else:
            current = part

    if current:
        pieces.append(current)
    return pieces

def chunk_text(text: str, max_chars: int, overlap: int = 0) -> list[str]:
    """ Split text into pieces of at most max_chars, with optional overlap. """
    pieces = [p.strip() for p in split_text(text, max_chars) if p.strip()]
    chunks = []
    for i, piece in enumerate(pieces):
        if i == 0 or overlap == 0:
            chunks.append(piece)
            continue
        tail = pieces[i - 1][-overlap:]
        tail = tail[tail.find(" ") + 1:]
        chunks.append(f"{tail} {piece}")
    return chunks