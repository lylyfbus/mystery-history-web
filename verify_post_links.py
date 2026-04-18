#!/usr/bin/env python3
"""Verify external links in a post."""
import sys
import re
import urllib.request
import urllib.error
import ssl
from pathlib import Path

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

slug = sys.argv[1]
base = Path('sessions/mystery_history/project/mystery-history-web/src')
post_file = base / 'posts' / f'{slug}.html'
html = post_file.read_text(encoding='utf-8')

links = re.findall(r'href="(https?://[^"]+)"', html)
skip = ['twitter.com', 'facebook.com', 'reddit.com', 'pinterest.com', 'pastmysteries.com']
external = list(dict.fromkeys([l for l in links if not any(d in l for d in skip) and not l.startswith('/')]))

print(f'Checking {len(external)} links...')
bad = []
for url in external:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'})
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        print(f'  OK {resp.status}: {url[:80]}')
    except urllib.error.HTTPError as e:
        bad.append({'url': url, 'status': e.code})
        print(f'  FAIL {e.code}: {url[:80]}')
    except Exception as e:
        bad.append({'url': url, 'status': str(e)[:80]})
        print(f'  ERROR: {url[:80]} -> {str(e)[:80]}')

print(f'
Good: {len(external) - len(bad)}, Bad: {len(bad)}')
if bad:
    print('BAD LINKS:')
    for r in bad:
        print(f'  {r["status"]} - {r["url"]}')
    sys.exit(1)
else:
    print('All links OK!')
