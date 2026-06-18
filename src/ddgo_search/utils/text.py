"""Text parsing and clean up utilities."""


def clean_markdown(content: str) -> str:
    """Clean markdown text by removing duplicate blank lines & trailing space."""
    if not content:
        return ""

    # Collapse three or more consecutive newlines into exactly two
    lines = content.split("\n")
    cleaned_lines = []
    blank_count = 0

    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            blank_count += 1
            if blank_count <= 1:
                cleaned_lines.append("")
        else:
            blank_count = 0
            cleaned_lines.append(stripped)

    return "\n".join(cleaned_lines).strip()
