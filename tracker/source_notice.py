"""Recognize the pilot's literal, unconditional footer notice in Astro source.

This is a conservative source check, not an Astro evaluator or a CSS visibility
audit. Unfamiliar markup requires review instead of supplying release evidence.
"""
from html.parser import HTMLParser
import re


def _complete_tag_expressions(source: str) -> bool:
    """Refuse markup/truncated JavaScript before HTMLParser can invent tags."""
    if '<' in source[1:]:
        return False
    depth = 0
    quote = None
    escaped = False
    for char in source:
        if quote is not None:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in "'\"":
            quote = char
        elif depth and char in '`/<>':
            return False  # Template literals, regex/comments and JSX need review.
        elif char == '{':
            depth += 1
        elif char == '}':
            if not depth:
                return False
            depth -= 1
    return depth == 0 and quote is None


class _FooterNotice(HTMLParser):
    VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
    TEXT_CONTAINERS = {'html','body','footer','div','p','span','a','strong','em','b','i',
                       'small','s','u','abbr','cite','code','pre','nav','ul','ol','li',
                       'section','article','h1','h2','h3','h4','h5','h6'}
    BLOCKS = {'footer','div','p','nav','ul','ol','li','section','article','pre',
              'h1','h2','h3','h4','h5','h6'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.uncertain = False
        self.footers = 0
        self.closed_footers = 0
        self.parts = []
        self.document_elements = {'html':0, 'body':0}

    def _in_footer(self):
        return any(tag == 'footer' for tag, _ in self.stack)

    def handle_starttag(self, tag, attrs):
        path = [name for name, _ in self.stack]
        names = [name for name, _ in attrs]
        # Browsers consume everything after plaintext, including closing tags.
        # HTMLParser handling varies by version and treats /> as self-closing.
        if tag == 'plaintext':
            self.uncertain = True
        if not _complete_tag_expressions(self.get_starttag_text()):
            self.uncertain = True
        if tag in self.document_elements:
            self.document_elements[tag] += 1
            expected_path = [] if tag == 'html' else ['html']
            if self.document_elements[tag] != 1 or path != expected_path:
                self.uncertain = True
        # Uppercase names may be Astro components. Dynamic/replacement attributes
        # or explicit hiding on a notice ancestor are not unconditional proof.
        unsafe = (not self.get_starttag_text().startswith('<'+tag)
                  or tag not in self.TEXT_CONTAINERS
                  or len(names) != len(set(names)))
        for name, value in attrs:
            if (name in {'hidden','inert','style','popover'} or ':' in name
                    or any(char in name + (value or '') for char in '{}')
                    or name == 'aria-hidden' and (value or '').strip().lower() != 'false'):
                unsafe = True
        if tag == 'footer':
            self.footers += 1
            if path != ['html','body']:
                self.uncertain = True
        if self._in_footer() and (tag in self.BLOCKS or unsafe or tag == 'br'):
            self.parts.append(' ')
        if tag not in self.VOID:
            self.stack.append((tag, unsafe))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1][0] != tag:
            self.uncertain = True
            return
        if self._in_footer() and (tag in self.BLOCKS or self.stack[-1][1]):
            self.parts.append(' ')
        self.stack.pop()
        if tag == 'footer':
            self.closed_footers += 1

    def handle_data(self, data):
        # Ignore only complete property lookups outside the footer (e.g. {title}).
        # Complex/unbalanced expressions anywhere can contain fake closing tags
        # that HTMLParser would otherwise mistake for real document structure.
        literal = data if self._in_footer() else re.sub(
            r'\{\s*[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*\s*\}', '', data)
        if any(char in literal for char in '{}'):
            self.uncertain = True
        if self._in_footer() and not any(unsafe for _, unsafe in self.stack):
            self.parts.append(data)


def public_footer_notice(layout: str, notice: str) -> bool:
    source = re.sub(r'\A---\r?\n.*?\r?\n---(?:\r?\n|$)', '', layout,
                    count=1, flags=re.DOTALL)
    parser = _FooterNotice()
    parser.feed(source)
    parser.close()
    text = ' '.join(''.join(parser.parts).split())
    return (not parser.uncertain and not parser.stack and parser.footers == 1
            and parser.closed_footers == 1 and ' '.join(notice.split()) in text)
