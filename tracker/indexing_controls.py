"""Recognize the pilot's static repository safeguards; uncertainty needs review.

These checks do not establish live headers, crawlability, or an Astro expression's
runtime value. Unrecognized configurations are deliberately not proof of an
intact pilot control.
"""
from html.parser import HTMLParser
import re


def _has_noindex(value: str) -> bool:
    return 'noindex' in {token.strip().lower() for token in value.split(',')}


class _HeadMeta(HTMLParser):
    VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.path = []
        self.closed = False
        self.uncertain = False
        self.robots = 0
        self.noindex = False

    def handle_starttag(self, tag, attrs):
        if self.closed:
            return
        if tag in {'html','head','meta'} and not self.get_starttag_text().startswith('<'+tag):
            self.uncertain = True  # Uppercase Astro component names are not literal HTML.
        if tag == 'head' and self.path != ['html']:
            self.uncertain = True
        names = [name for name, _ in attrs]
        if tag in {'html','head'} and any(name.startswith('set:') or '{' in name for name in names):
            self.uncertain = True
        values = dict(attrs)
        if tag == 'meta' and self.path == ['html','head'] and (values.get('name') or '').strip().lower() == 'robots':
            self.robots += 1
            if len(names) != len(set(names)) or any('{' in name for name in names):
                self.uncertain = True
            content = values.get('content') or ''
            self.noindex = _has_noindex(content) and not any(char in content for char in '{}')
        if tag not in self.VOID:
            self.path.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if self.closed:
            return
        if not self.path or self.path[-1] != tag:
            self.uncertain = True
        else:
            self.path.pop()
        if tag == 'head':
            self.closed = True

    def handle_data(self, data):
        # An Astro conditional surrounding the head/meta is not unconditional proof.
        if not self.closed and self.path in ([], ['html'], ['html','head']) and data.strip():
            self.uncertain = True


def pilot_meta_noindex(layout: str) -> bool:
    source = re.sub(r'\A---\r?\n.*?\r?\n---(?:\r?\n|$)', '', layout, count=1, flags=re.DOTALL)
    parser = _HeadMeta()
    parser.feed(source)
    parser.close()
    return parser.closed and not parser.uncertain and parser.robots == 1 and parser.noindex


def pilot_robots_disallow_all(robots: str) -> bool:
    """Recognize the canonical wildcard group, with no agent/allow exceptions."""
    directives = []
    for raw in robots.splitlines():
        line = raw.split('#',1)[0].strip()
        if not line:
            continue
        name, separator, value = line.partition(':')
        if not separator:
            return False
        directives.append((name.strip().lower(),value.strip()))
    return directives == [('user-agent','*'),('disallow','/')]


def pilot_header_noindex(headers: str) -> bool:
    """Recognize an unqualified noindex directive under only a global path rule."""
    scope = None
    found = False
    for raw in headers.splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if not raw[0].isspace():
            if line != '/*':
                return False
            scope = line
            continue
        name, separator, value = line.partition(':')
        if scope != '/*' or not separator or '#' in line:
            return False
        if name.strip().lower() == 'x-robots-tag':
            if ':' in value or not _has_noindex(value):
                return False
            found = True
    return found
