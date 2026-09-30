"""Offline href/src and HTML fragment checks for the two static build outputs.

This is a CI test utility, not a general HTML validator or network crawler.
"""
import argparse
import posixpath
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlsplit

ORIGIN = 'https://static-site.invalid'
URL_TRIM_CHARACTERS = ''.join(chr(codepoint) for codepoint in range(0x21))


class Page(HTMLParser):
    # Older supported 3.12 versions only recognize script/style by default.
    # Text decoding is immaterial here: only element attributes are inspected.
    CDATA_CONTENT_ELEMENTS = ('script', 'style', 'xmp', 'iframe', 'noembed',
                             'noframes', 'textarea', 'title')

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.fragments = set()
        self.template_depth = 0
        self.has_base = False
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attributes):
        if self.template_depth:
            if tag == 'template':
                self.template_depth += 1
            return
        attrs = {}
        for name, value in attributes:
            attrs.setdefault(name, value)
        if tag == 'base':
            self.has_base = True
        if attrs.get('id'):
            self.fragments.add(attrs['id'])
        if tag == 'a' and attrs.get('name'):
            self.fragments.add(attrs['name'])
        for name in ('href', 'src'):
            if attrs.get(name) is not None:
                self.links.append(attrs[name])
        if tag == 'template':
            self.template_depth = 1

    def handle_endtag(self, tag):
        if tag == 'template' and self.template_depth:
            self.template_depth -= 1


def check_site(output, base):
    root = Path(output).resolve()
    if not base.startswith('/') or not base.endswith('/'):
        raise ValueError('hosting base must start and end with /')
    pages = {}
    for file in sorted(root.rglob('*.html')):
        if not file.resolve().is_relative_to(root):
            raise ValueError('HTML file outside output')
        pages[file.resolve()] = Page(file.read_text(encoding='utf-8'))
    if not pages:
        raise ValueError('no HTML pages found')
    errors = []
    checked = 0
    for file, page in pages.items():
        relative = file.relative_to(root).as_posix()
        route = relative.removesuffix('index.html') if file.name == 'index.html' else relative
        document_url = ORIGIN + base + quote(route, safe='/')
        if page.has_base:
            errors.append(f'{relative}: unsupported_base_element')
            continue
        for link in page.links:
            try:
                parsed = urlsplit(urljoin(document_url, link.strip(URL_TRIM_CHARACTERS)))
                if parsed.scheme not in ('http', 'https') or parsed.netloc != 'static-site.invalid':
                    continue
                checked += 1
                decoded = unquote(parsed.path, errors='strict')
                if '\\' in decoded or '\x00' in decoded:
                    raise ValueError('ambiguous local path')
                path = '/' + posixpath.normpath(decoded).lstrip('/')
                if base != '/' and path != base.rstrip('/') and not path.startswith(base):
                    errors.append(f'{relative} -> {link}: outside_base')
                    continue
                local = '' if path == base.rstrip('/') else path[len(base):]
                target = (root / local).resolve()
                if not target.is_relative_to(root):
                    errors.append(f'{relative} -> {link}: outside_output')
                    continue
                if decoded.endswith('/') and not target.is_dir():
                    errors.append(f'{relative} -> {link}: missing_directory')
                    continue
                if target.is_dir():
                    target = (target / 'index.html').resolve()
                if not target.is_relative_to(root) or not target.is_file():
                    errors.append(f'{relative} -> {link}: missing_target')
                    continue
                fragment = unquote(parsed.fragment, errors='strict')
                if fragment and target.suffix == '.html':
                    destination = pages.get(target)
                    if destination is None:
                        errors.append(f'{relative} -> {link}: unchecked_html_target')
                    elif fragment not in destination.fragments and fragment.lower() != 'top':
                        errors.append(f'{relative} -> {link}: missing_fragment')
            except (ValueError, UnicodeError):
                errors.append(f'{relative} -> {link}: invalid_local_url')
    return len(pages), checked, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--base', required=True)
    args = parser.parse_args()
    try:
        pages, links, errors = check_site(args.output, args.base)
    except (OSError, ValueError, UnicodeError) as error:
        print(f'link check refused: {error}')
        return 1
    print(f'Checked {links} local href/src URLs across {pages} HTML pages under {args.base}')
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
