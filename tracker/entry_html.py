"""Bounded non-rendering HTML inspection. No fetching, DOM execution or approval.

The scope deliberately includes body navigation/footer and collapsed/hidden text.
It excludes script/style content; media and linked/dynamically loaded text are not
read. Strict interior balancing can reject browser-repairable HTML. A completed
document may have the observed inert script trailer and one redundant closing
body/html pair; out-of-body prose and elements are never silently discarded.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser

MAX_HTML = 1_048_576
MAX_TEXT = 65_536
MAX_NODES = 30_000
MAX_DEPTH = 128
SCOPE = 'html-body-text-links-v1'
VOID = frozenset('area base br col embed hr img input link meta param source track wbr'.split())
BLOCK = frozenset('address article aside blockquote br dd details div dl dt fieldset figcaption figure footer form h1 h2 h3 h4 h5 h6 header hr li main nav ol p pre section summary table tbody td th thead tr ul'.split())
CONTROL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff\ud800-\udfff]')

class SourceExtractionError(ValueError):
    """Only fixed machine codes are exposed; never embed source payloads."""


def require(condition: object, code: str = 'invalid_source_extraction') -> None:
    if not condition:
        raise SourceExtractionError(code)


def clean_text(value: object, maximum: int = MAX_TEXT, *, empty: bool = False) -> str:
    require(isinstance(value, str) and len(value) <= maximum, 'invalid_source_text')
    require(not CONTROL.search(value) and (empty or value.strip()), 'invalid_source_text')
    return value


def normalized(value: str) -> str:
    return re.sub(r'[\t\n\r \u00a0]+', ' ', value).strip()


class _BodyParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.body_count = self.closed_bodies = self.nodes = 0
        self.closed_html = 0
        self.redundant_ends: list[str] = []
        self.blocks: list[str] = []
        self.buffer: list[str] = []
        self.links: list[str] = []
        self.headings: list[str] = []
        self.heading: list[str] | None = None
        self.text_size = 0

    def active(self) -> bool:
        return 'body' in self.stack and not any(t in self.stack for t in ('script', 'style'))

    def flush(self) -> None:
        text = normalized(''.join(self.buffer))
        if text:
            self.blocks.append(text)
        self.buffer.clear()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.nodes += 1
        require(self.nodes <= MAX_NODES, 'html_too_complex')
        require(len(attrs) == len({k for k, _ in attrs}), 'ambiguous_html')
        require(tag != 'base', 'unsupported_document_base')
        if self.active():
            require(tag not in ('del', 'ins', 's', 'strike'), 'annotated_source_text')
        if self.closed_bodies:
            # NPS emits scripts after its first complete document. They remain
            # outside this non-rendering scope; no new visible element is allowed.
            require(not self.redundant_ends and tag in ('script', 'style')
                    and self.stack in ([], ['html']), 'content_outside_body')
        if tag == 'body':
            self.body_count += 1
            require(self.body_count == 1 and 'head' not in self.stack, 'body_ambiguous')
        if self.active() and tag in BLOCK:
            self.flush()
        if tag not in VOID:
            self.stack.append(tag)
            require(len(self.stack) <= MAX_DEPTH, 'html_too_deep')
        if self.active() and tag == 'h1':
            require(self.heading is None, 'heading_ambiguous')
            self.heading = []
        if self.active() and tag == 'a':
            href = dict(attrs).get('href')
            if href is not None:
                # Retained only as private comparison text; never followed or rendered as a link.
                self.links.append(clean_text(href, 2048, empty=True))
                require(len(self.links) <= 2048, 'html_too_complex')

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID:
            return
        if not self.stack and self.closed_bodies == self.closed_html == 1:
            # Only the exact redundant closing pair observed in the NPS envelope.
            # This cannot close a missing/misnested element within the document.
            expected = 'body' if not self.redundant_ends else 'html'
            require(len(self.redundant_ends) < 2 and tag == expected, 'ambiguous_html')
            self.redundant_ends.append(tag)
            return
        require(bool(self.stack) and self.stack[-1] == tag, 'ambiguous_html')
        if self.active():
            if tag == 'h1':
                require(self.heading is not None, 'heading_ambiguous')
                self.headings.append(normalized(''.join(self.heading)))
                self.heading = None
            if tag in BLOCK or tag == 'body':
                self.flush()
        self.stack.pop()
        if tag == 'body':
            self.closed_bodies += 1
        if tag == 'html':
            self.closed_html += 1

    def handle_data(self, data: str) -> None:
        if not self.active() and not any(t in self.stack for t in ('head', 'script', 'style')):
            require(not data.strip(), 'content_outside_body')
        if self.active():
            clean_text(data, MAX_TEXT, empty=True)
            self.text_size += len(data)
            require(self.text_size <= MAX_TEXT, 'source_context_too_large')
            self.buffer.append(data)
            if self.heading is not None:
                self.heading.append(data)


def inspect_html(html: object, expected_heading: str) -> dict:
    """Return normalized body blocks and raw anchor targets; reject ambiguous input."""
    clean_text(html, MAX_HTML)
    require(len(html.encode('utf-8')) <= MAX_HTML, 'source_html_too_large')
    clean_text(expected_heading, 256)
    parser = _BodyParser()
    try:
        parser.feed(html)
        parser.close()
    except SourceExtractionError:
        raise
    except Exception:
        raise SourceExtractionError('ambiguous_html') from None
    require(parser.body_count == parser.closed_bodies == 1 and not parser.stack, 'body_ambiguous')
    require(parser.redundant_ends in ([], ['body', 'html']), 'ambiguous_html')
    require(parser.headings.count(expected_heading) == 1, 'heading_ambiguous')
    text = '\n'.join(parser.blocks)
    clean_text(text)
    return {'scope': SCOPE, 'text': text, 'h1': parser.headings, 'links': parser.links}
