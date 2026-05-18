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
        .nav {{
            position: sticky; top: 0; z-index: 100;
            padding: 12px 24px;
            background: rgba(10,10,10,0.9);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid #1a1a1a;
            display: flex; align-items: center; gap: 16px;
        }}
        .nav a {{ color: #888; text-decoration: none; font-size: 0.85rem; transition: color 0.15s; }}
        .nav a:hover {{ color: #fff; }}
        .nav-title {{ color: #555; font-size: 0.8rem; margin-left: auto; }}
        .layout {{ display: flex; max-width: 1100px; margin: 0 auto; }}
        .toc {{
            position: sticky; top: 56px;
            width: 220px; min-width: 220px;
            height: calc(100vh - 56px);
            overflow-y: auto;
            padding: 32px 16px 32px 24px;
            border-right: 1px solid #141414;
        }}
        .toc::-webkit-scrollbar {{ width: 3px; }}
        .toc::-webkit-scrollbar-thumb {{ background: #333; border-radius: 3px; }}
        .toc-title {{ font-size: 0.7rem; font-weight: 600; color: #444; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 16px; }}
        .toc a {{
            display: block; padding: 5px 0;
            font-size: 0.78rem; color: #555;
            text-decoration: none; transition: color 0.15s;
            border-left: 2px solid transparent;
            padding-left: 10px; margin-left: -10px;
        }}
        .toc a:hover {{ color: #ccc; }}
        .toc a.active {{ color: #fff; border-left-color: #fff; }}
        .toc a.h3 {{ padding-left: 20px; font-size: 0.73rem; }}
        .container {{
            flex: 1; min-width: 0;
            padding: 48px 48px 100px;
        }}
        h1 {{ font-size: 1.8rem; font-weight: 700; line-height: 1.3; margin-bottom: 32px; color: #fff; }}
        h2 {{
            font-size: 1.3rem; font-weight: 700;
            margin-top: 56px; margin-bottom: 20px; color: #fff;
            padding-bottom: 8px; border-bottom: 1px solid #222;
            scroll-margin-top: 72px;
        }}
        h3 {{ font-size: 1.1rem; font-weight: 600; margin-top: 36px; margin-bottom: 14px; color: #ddd; scroll-margin-top: 72px; }}
        h4 {{ font-size: 0.95rem; font-weight: 600; margin-top: 28px; margin-bottom: 10px; color: #ccc; }}
        p {{ margin-bottom: 14px; font-size: 0.95rem; color: #bbb; }}
        strong {{ color: #fff; font-weight: 600; }}
        em {{ color: #aaa; font-style: italic; }}
        ul, ol {{ margin: 10px 0 14px 24px; color: #bbb; }}
        li {{ margin-bottom: 5px; font-size: 0.9rem; }}
        table {{
            width: 100%; border-collapse: collapse;
            margin: 16px 0 24px; font-size: 0.82rem;
            display: block; overflow-x: auto;
        }}
        th {{
            background: #141414; color: #ddd;
            padding: 10px 12px; text-align: left;
            font-weight: 600; border-bottom: 2px solid #222;
            white-space: nowrap; position: sticky; top: 0;
        }}
        td {{ padding: 9px 12px; border-bottom: 1px solid #161616; color: #aaa; }}
        tr:hover td {{ background: #0f0f0f; color: #ddd; }}
        pre {{
            background: #0e0e0e; border: 1px solid #1a1a1a;
            border-radius: 10px; padding: 18px 20px;
            margin: 14px 0 22px; overflow-x: auto;
            font-size: 0.8rem; line-height: 1.7; color: #bbb;
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
        }}
        code {{
            background: #161616; padding: 2px 7px;
            border-radius: 5px; font-size: 0.82rem; color: #ddd;
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
        }}
        pre code {{ background: none; padding: 0; }}
        blockquote {{
            border-left: 3px solid #333; padding: 14px 20px;
            margin: 14px 0; background: #0e0e0e;
            border-radius: 0 10px 10px 0; color: #999;
            font-style: italic; font-size: 0.9rem;
        }}
        hr {{ border: none; border-top: 1px solid #1a1a1a; margin: 48px 0; }}
        .meta-bar {{ display: flex; gap: 8px; margin-bottom: 28px; flex-wrap: wrap; }}
        .meta-chip {{
            font-size: 0.72rem; padding: 4px 10px;
            border-radius: 20px; background: #141414;
            border: 1px solid #222; color: #888;
        }}
        .disclaimer {{
            margin-top: 48px; padding: 14px 16px;
            background: #0e0e0e; border: 1px solid #1a1a1a;
            border-radius: 10px; font-size: 0.78rem; color: #555;
        }}
        .back-top {{
            position: fixed; bottom: 24px; right: 24px;
            width: 40px; height: 40px;
            background: #1a1a1a; border: 1px solid #333;
            border-radius: 50%; color: #888;
            display: flex; align-items: center; justify-content: center;
            cursor: pointer; opacity: 0; transition: opacity 0.3s;
            font-size: 1.1rem; text-decoration: none;
        }}
        .back-top.show {{ opacity: 1; }}
        .back-top:hover {{ background: #333; color: #fff; }}
        @media (max-width: 900px) {{
            .toc {{ display: none; }}
            .container {{ padding: 32px 20px 80px; }}
        }}
        @media (max-width: 600px) {{
            .container {{ padding: 24px 16px 60px; }}
            h1 {{ font-size: 1.4rem; }}
            h2 {{ font-size: 1.1rem; }}
            table {{ font-size: 0.75rem; }}
            th, td {{ padding: 7px 8px; }}
        }}
    </style>
</head>
<body>
    <div class="nav">
        <a href="index.html">&larr; Factory</a>
        <span class="nav-title">{title}</span>
    </div>
    <div class="layout">
        <nav class="toc" id="toc"><div class="toc-title">목차</div></nav>
        <div class="container">
"""

TEMPLATE_TAIL = """
        <div class="disclaimer">본 글은 공개 정보 기반의 투자 참고 자료이며, 투자 권유가 아닙니다.</div>
        </div>
    </div>
    <a href="#" class="back-top" id="backTop">&uarr;</a>
    <script>
        // TOC generation
        const toc = document.getElementById('toc');
        const headings = document.querySelectorAll('h2, h3');
        headings.forEach((h, i) => {
            h.id = 'section-' + i;
            const a = document.createElement('a');
            a.href = '#section-' + i;
            a.textContent = h.textContent;
            if (h.tagName === 'H3') a.classList.add('h3');
            toc.appendChild(a);
        });

        // Active TOC highlight
        const tocLinks = toc.querySelectorAll('a');
        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    tocLinks.forEach(l => l.classList.remove('active'));
                    const id = entry.target.id;
                    const link = toc.querySelector('a[href="#' + id + '"]');
                    if (link) link.classList.add('active');
                }
            });
        }, { rootMargin: '-80px 0px -70% 0px' });
        headings.forEach(h => observer.observe(h));

        // Back to top
        const backTop = document.getElementById('backTop');
        window.addEventListener('scroll', () => {
            backTop.classList.toggle('show', window.scrollY > 400);
        });
    </script>
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
