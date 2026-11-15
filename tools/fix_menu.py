"""Put the same top menu and the same footer links on all pages. Safe to run again."""
import re
from sitelib import FOOTER, MENU, all_pages, write

FOOTER_TEXT = {"/archive": "All Stories", "/about": "About", "/editorial-policy": "Editorial Policy",
               "/contact": "Contact", "/privacy-policy": "Privacy Policy", "/listen": "Listen"}


def fix(page_html):
    def nav(match):
        indent = match.group(1)
        links = "".join(f'\n{indent}    <a href="{href}">{text}</a>' for href, text in MENU)
        return f'{indent}<nav class="site-nav">{links}\n{indent}</nav>'

    page_html = re.sub(r'([ \t]*)<nav class="site-nav">.*?</nav>', nav, page_html, count=1, flags=re.S)
    links = " &middot; ".join(f'<a href="{h}">{FOOTER_TEXT[h]}</a>' for h in FOOTER)

    def footer(match):
        return re.sub(r'<p>\s*<a href=.*?</p>', f"<p>{links}</p>", match.group(0), count=1, flags=re.S)

    return re.sub(r'<footer class="site-footer">.*?</footer>', footer, page_html, count=1, flags=re.S)


if __name__ == "__main__":
    changed = 0
    for page in all_pages():
        old = page.read_text(encoding="utf-8")
        new = fix(old)
        if new != old:
            write(page, new)
            changed += 1
    print(f"menu and footer: {changed} page(s) changed")
