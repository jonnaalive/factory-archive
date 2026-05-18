"""Markdown factory report → HTML converter with dark theme."""
import re
import sys
from pathlib import Path

TEMPLATE_HEAD = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — Factory</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.8;
            color: #e0e0e0;
            background: #0a0a0a;
        }}
        .nav {{ padding: 16px 24px; border-bottom: 1px solid #1a1a1a; }}
        .nav a {{ color: #888; text-decoration: none; font-size: 0.9rem; }}
        .nav a:hover {{ color: #fff; }}
        .container {{ max-width: 780px; margin: 0 auto; padding: 48px 24px 100px; }}
        h1 {{ font-size: 1.9rem; font-weight: 700; line-height: 1.3; margin-bottom: 32px; color: #fff; }}
        h2 {{ font-size: 1.4rem; font-weight: 700; margin-top: 56px; margin-bottom: 20px; color: #fff; padding-bottom: 8px; border-bottom: 1px solid #333; }}
        h3 {{ font-size: 1.15rem; font-weight: 600; margin-top: 36px; margin-bottom: 14px; color: #ddd; }}
        h4 {{ font-size: 1rem; font-weight: 600; margin-top: 28px; margin-bottom: 10px; color: #ccc; }}
        p {{ margin-bottom: 16px; font-size: 1rem; color: #bbb; }}
        strong {{ color: #fff; font-weight: 600; }}
        em {{ color: #aaa; font-style: italic; }}
        ul, ol {{ margin: 12px 0 16px 24px; color: #bbb; }}
        li {{ margin-bottom: 6px; font-size: 0.95rem; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0 28px; font-size: 0.88rem; overflow-x: auto; display: block; }}
        th {{ background: #1a1a1a; color: #fff; padding: 10px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #333; white-space: nowrap; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #1a1a1a; color: #bbb; }}
        tr:hover td {{ background: #111; }}
        pre {{ background: #111; border: 1px solid #222; border-radius: 8px; padding: 16px 20px; margin: 16px 0 24px; overflow-x: auto; font-size: 0.85rem; line-height: 1.6; color: #ccc; font-family: 'JetBrains Mono', 'Fira Code', monospace; }}
        code {{ background: #1a1a1a; padding: 2px 6px; border-radius: 4px; font-size: 0.88rem; color: #ddd; font-family: 'JetBrains Mono', 'Fira Code', monospace; }}
        pre code {{ background: none; padding: 0; }}
        blockquote {{ border-left: 3px solid #444; padding: 12px 20px; margin: 16px 0; background: #111; border-radius: 0 8px 8px 0; color: #aaa; font-style: italic; }}
        hr {{ border: none; border-top: 1px solid #222; margin: 48px 0; }}
        .meta-bar {{ display: flex; gap: 10px; margin-bottom: 28px; flex-wrap: wrap; }}
        .meta-chip {{ font-size: 0.78rem; padding: 4px 10px; border-radius: 20px; background: #1a1a1a; border: 1px solid #333; color: #aaa; }}
        .disclaimer {{ margin-top: 48px; padding: 16px; background: #111; border: 1px solid #222; border-radius: 8px; font-size: 0.82rem; color: #666; }}
        @media (max-width: 600px) {{
            .container {{ padding: 28px 16px 60px; }}
            h1 {{ font-size: 1.5rem; }}
            table {{ font-size: 0.78rem; }}
            th, td {{ padding: 8px 8px; }}
        }}
    </style>
</head>
<body>
    <div class="nav"><a href="index.html">&larr; Factory 홈</a></div>
    <div class="container">
"""

TEMPLATE_TAIL = """
        <div class="disclaimer">본 글은 공개 정보 기반의 투자 참고 자료이며, 투자 권유가 아닙니다.</div>
    </div>
</body>
</html>
"""


def parse_frontmatter(text):
    """Extract title from YAML frontmatter."""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    title = ""
    body = text
    if match:
        fm = match.group(1)
        body = text[match.end():]
        t = re.search(r'title:\s*["\']?(.*?)["\']?\s*$', fm, re.MULTILINE)
        if t:
            title = t.group(1)
    return title, body


def md_to_html(md_text):
    """Convert markdown body to HTML."""
    lines = md_text.split('\n')
    html_parts = []
    in_table = False
    in_code = False
    in_list = False
    list_type = None
    code_buf = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Code block
        if line.strip().startswith('```'):
            if not in_code:
                in_code = True
                code_buf = []
            else:
                in_code = False
                html_parts.append('<pre><code>' + escape_html('\n'.join(code_buf)) + '</code></pre>')
            i += 1
            continue

        if in_code:
            code_buf.append(line)
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^---+\s*$', line):
            if in_list:
                html_parts.append(f'</{list_type}>')
                in_list = False
            html_parts.append('<hr>')
            i += 1
            continue

        # Headers
        h_match = re.match(r'^(#{1,4})\s+(.*)', line)
        if h_match:
            if in_list:
                html_parts.append(f'</{list_type}>')
                in_list = False
            level = len(h_match.group(1))
            content = inline_format(h_match.group(2))
            html_parts.append(f'<h{level}>{content}</h{level}>')
            i += 1
            continue

        # Table
        if '|' in line and line.strip().startswith('|'):
            if in_list:
                html_parts.append(f'</{list_type}>')
                in_list = False
            if not in_table:
                in_table = True
                html_parts.append('<table>')
                cells = [c.strip() for c in line.strip().strip('|').split('|')]
                html_parts.append('<tr>' + ''.join(f'<th>{inline_format(c)}</th>' for c in cells) + '</tr>')
                # Skip separator line
                if i + 1 < len(lines) and re.match(r'^\|[\s\-:|]+\|', lines[i+1]):
                    i += 1
            else:
                cells = [c.strip() for c in line.strip().strip('|').split('|')]
                html_parts.append('<tr>' + ''.join(f'<td>{inline_format(c)}</td>' for c in cells) + '</tr>')
            i += 1
            continue
        elif in_table:
            in_table = False
            html_parts.append('</table>')

        # Blockquote
        if line.strip().startswith('>'):
            if in_list:
                html_parts.append(f'</{list_type}>')
                in_list = False
            content = inline_format(line.strip()[1:].strip())
            html_parts.append(f'<blockquote>{content}</blockquote>')
            i += 1
            continue

        # Unordered list
        ul_match = re.match(r'^(\s*)[-*]\s+(.*)', line)
        if ul_match:
            if not in_list or list_type != 'ul':
                if in_list:
                    html_parts.append(f'</{list_type}>')
                html_parts.append('<ul>')
                in_list = True
                list_type = 'ul'
            html_parts.append(f'<li>{inline_format(ul_match.group(2))}</li>')
            i += 1
            continue

        # Ordered list
        ol_match = re.match(r'^(\s*)\d+[.)]\s+(.*)', line)
        if ol_match:
            if not in_list or list_type != 'ol':
                if in_list:
                    html_parts.append(f'</{list_type}>')
                html_parts.append('<ol>')
                in_list = True
                list_type = 'ol'
            html_parts.append(f'<li>{inline_format(ol_match.group(2))}</li>')
            i += 1
            continue

        # Close list if needed
        if in_list and line.strip() == '':
            html_parts.append(f'</{list_type}>')
            in_list = False
            i += 1
            continue

        # Paragraph
        if line.strip():
            if in_list:
                html_parts.append(f'</{list_type}>')
                in_list = False
            html_parts.append(f'<p>{inline_format(line.strip())}</p>')

        i += 1

    if in_list:
        html_parts.append(f'</{list_type}>')
    if in_table:
        html_parts.append('</table>')

    return '\n'.join(html_parts)


def inline_format(text):
    """Apply inline formatting (bold, italic, code, links)."""
    text = escape_html(text)
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Inline code
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    # Links
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" style="color:#7bb8f0">\1</a>', text)
    return text


def escape_html(text):
    """Escape HTML special chars (but not already-processed markdown)."""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def convert_file(input_path, output_path):
    """Convert a markdown file to HTML."""
    md = Path(input_path).read_text(encoding='utf-8')
    title, body = parse_frontmatter(md)
    if not title:
        title = Path(input_path).stem

    html_body = md_to_html(body)

    # Extract tags for meta bar
    tags_match = re.search(r'tags:\s*\[(.*?)\]', md)
    tags = []
    if tags_match:
        tags = [t.strip().strip('"\'') for t in tags_match.group(1).split(',')]

    meta_html = ''
    if tags:
        chips = ''.join(f'<span class="meta-chip">{t}</span>' for t in tags[:6])
        meta_html = f'<div class="meta-bar">{chips}</div>'

    full_html = TEMPLATE_HEAD.format(title=title) + meta_html + f'<h1>{escape_html(title)}</h1>\n' + html_body + TEMPLATE_TAIL

    Path(output_path).write_text(full_html, encoding='utf-8')
    print(f"OK: {input_path} -> {output_path}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python convert.py <input.md> <output.html>")
        sys.exit(1)
    convert_file(sys.argv[1], sys.argv[2])
