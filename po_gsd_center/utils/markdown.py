try:
    from markdown_it import MarkdownIt
    _md = MarkdownIt()

    def render_md(text: str) -> str:
        if not text:
            return ""
        return _md.render(text)

except ImportError:
    import re

    def render_md(text: str) -> str:
        if not text:
            return ""
        # Minimal fallback renderer
        html = text
        html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
        html = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html)
        html = re.sub(r"\*(.+?)\*", r"<i>\1</i>", html)
        html = re.sub(r"`(.+?)`", r"<code>\1</code>", html)
        html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
        html = html.replace("\n\n", "<br><br>")
        return html


def strip_md(text: str) -> str:
    """Return plain text with markdown syntax stripped."""
    import re
    text = re.sub(r"#{1,6}\s*", "", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"^[-*+]\s+", "", text, flags=re.MULTILINE)
    return text.strip()
