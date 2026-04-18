#!/usr/bin/env python3
"""Reusable script to assemble a regenerated thin post.
Usage: python assemble_thin_post.py <slug>

Reads the existing post and its -content.html file,
replaces the body content while preserving header, images,
share buttons, related posts, and navigation.
"""
import sys
import re
from pathlib import Path

base = Path('sessions/mystery_history/project/mystery-history-web/src')
posts_dir = base / 'posts'

slug = sys.argv[1]
post_file = posts_dir / f'{slug}.html'
content_file = posts_dir / f'{slug}-content.html'

if not post_file.exists():
    print(f'ERROR: Post file not found: {post_file}')
    sys.exit(1)

if not content_file.exists():
    print(f'ERROR: Content file not found: {content_file}')
    sys.exit(1)

html = post_file.read_text(encoding='utf-8')
new_content = content_file.read_text(encoding='utf-8')

# 1. Extract prefix (before article)
article_start = html.find('<article class="post-content">')
prefix = html[:article_start]

# 2. Extract header block
header_start = html.find('<header class="post-header">', article_start)
header_end = html.find('</header>', header_start) + len('</header>')
header = html[header_start:header_end]

# 3. Extract inline images from old post
inline_img_blocks = []
for m in re.finditer(r'<img[^>]*src="([^"]*inline[^"]*\.webp)"[^>]*alt="([^"]+)"', html, re.DOTALL):
    inline_img_blocks.append({'src': m.group(1), 'alt': m.group(2)})

print(f'Found {len(inline_img_blocks)} inline images')
for img in inline_img_blocks:
    print(f'  {img["src"]} -> {img["alt"]}')

# Replace inline image placeholders
for i, img in enumerate(inline_img_blocks, 1):
    img_tag = f'<img src="../{img["src"]}"
     alt="{img["alt"]}"
     class="inline-image">'
    new_content = new_content.replace(f'<!-- INLINE IMAGE {i} -->', img_tag)

remaining = new_content.count('INLINE IMAGE')
print(f'Remaining inline image placeholders: {remaining}')

# 4. Extract suffix (share buttons through navigation)
share_start = html.find('<div class="share-buttons">')
post_nav_start = html.find('<nav class="post-navigation">')
if share_start > 0 and post_nav_start > 0:
    post_nav_end = html.find('</nav>', post_nav_start) + len('</nav>')
    suffix_content = html[share_start:post_nav_end]
    print(f'Suffix content: {len(suffix_content)} chars')
else:
    print('WARNING: Could not find share buttons or navigation!')
    suffix_content = ''

# 5. Get page suffix (after </article>)
article_end_pos = html.find('</article>') + len('</article>')
page_suffix = html[article_end_pos:]

# 6. Assemble
new_post = (
    prefix +
    '<article class="post-content">
' +
    header + '
' +
    new_content + '
' +
    suffix_content + '
' +
    '</article>' +
    page_suffix
)

# Verify key elements
required = {
    'article tag': '<article class="post-content">',
    'header block': '<header class="post-header">',
    'hero image': 'hero.webp',
    'h1 title': '<h1 class="post-title">',
    'share buttons': '<div class="share-buttons">',
    'related posts': '<div class="related-posts">',
    'footer': '<footer class="site-footer">',
    'amazon link': 'amazon.com/dp',
    'references section': 'post-sources',
}

all_pass = True
for name, marker in required.items():
    if marker not in new_post:
        print(f'FAIL: {name}')
        all_pass = False

fun_fact_count = new_post.count('class="fun-fact"')
if fun_fact_count < 3:
    print(f'FAIL: Only {fun_fact_count} fun-fact boxes (need 3+)')
    all_pass = False

if not all_pass:
    print('ASSEMBLY FAILED - not writing file')
    sys.exit(1)

# Write new post
post_file.write_text(new_post, encoding='utf-8')
print(f'New post written: {len(new_post)} chars')

# Verify word count
article_match = re.search(r'<article class="post-content">(.*?)</article>', new_post, re.DOTALL)
if article_match:
    text = re.sub(r'<[^>]+>', ' ', article_match.group(1))
    text = re.sub(r'\s+', ' ', text).strip()
    wc = len(text.split())
    print(f'Word count: {wc}')

# Clean up content file
content_file.unlink()
print(f'Content file removed')
