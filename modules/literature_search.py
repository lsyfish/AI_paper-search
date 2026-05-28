# -*- coding: utf-8 -*-
"""
联网文献检索模块 - 对接多个学术开放 API

支持数据源：
  - Semantic Scholar（综合，免费无 Key）
  - PubMed（医学/生命科学，NIH 免费接口）
  - CrossRef（综合，DOI 权威数据，免费）
  - arXiv（理工/CS/AI 预印本，免费）
"""

import json
import re
import ssl
import threading
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Callable, Dict, List, Optional

SOURCE_SEMANTIC_SCHOLAR = 'Semantic Scholar'
SOURCE_PUBMED = 'PubMed'
SOURCE_CROSSREF = 'CrossRef'
SOURCE_ARXIV = 'arXiv'

DEFAULT_TIMEOUT = 15
MAX_RESULTS_PER_SOURCE = 10

_SOURCE_BADGES = {
    SOURCE_SEMANTIC_SCHOLAR: '[SS]',
    SOURCE_PUBMED: '[PM]',
    SOURCE_CROSSREF: '[CR]',
    SOURCE_ARXIV: '[arXiv]',
}


# ─── HTTP helper ────────────────────────────────────────────

def _http_get(url: str, *, timeout: int = DEFAULT_TIMEOUT) -> str:
    req = urllib.request.Request(url, headers={
        'User-Agent': (
            'Mozilla/5.0 (compatible; PaperLabLiteratureSearch/1.0; '
            'mailto:noreply@example.com)'
        ),
        'Accept': 'application/json, application/atom+xml, */*',
    })
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
        return resp.read().decode('utf-8', errors='replace')


def _safe_text(value) -> str:
    if value is None:
        return ''
    if isinstance(value, list):
        return '; '.join(str(v) for v in value if v)
    return str(value).strip()


def _truncate(text: str, max_len: int = 500) -> str:
    text = str(text or '').strip()
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + '…'


def _strip_html(text: str) -> str:
    return re.sub(r'<[^>]+>', '', str(text or '')).strip()


# ─── Semantic Scholar ────────────────────────────────────────

def search_semantic_scholar(
    query: str, limit: int = MAX_RESULTS_PER_SOURCE
) -> List[Dict]:
    encoded = urllib.parse.quote(query.strip())
    fields = (
        'title,authors,year,abstract,externalIds,'
        'venue,journal,publicationTypes,citationCount'
    )
    url = (
        f'https://api.semanticscholar.org/graph/v1/paper/search'
        f'?query={encoded}&limit={limit}&fields={fields}'
    )
    raw = _http_get(url)
    payload = json.loads(raw)
    results = []
    for item in payload.get('data') or []:
        authors = [
            a.get('name', '')
            for a in (item.get('authors') or [])
        ]
        ext = item.get('externalIds') or {}
        doi = ext.get('DOI', '')
        arxiv_id = ext.get('ArXiv', '')
        journal_info = item.get('journal')
        if isinstance(journal_info, dict):
            journal = journal_info.get('name', '') or item.get('venue', '')
        else:
            journal = item.get('venue', '')
        url_val = (
            f'https://arxiv.org/abs/{arxiv_id}' if arxiv_id
            else (f'https://doi.org/{doi}' if doi else '')
        )
        results.append({
            'source': SOURCE_SEMANTIC_SCHOLAR,
            'title': _safe_text(item.get('title')),
            'authors': authors,
            'year': str(item.get('year') or ''),
            'abstract': _truncate(item.get('abstract') or ''),
            'journal': _safe_text(journal),
            'doi': _safe_text(doi),
            'url': url_val,
            'citation_count': int(item.get('citationCount') or 0),
            'volume': '',
            'issue': '',
            'pages': '',
        })
    return results


# ─── PubMed ──────────────────────────────────────────────────

def search_pubmed(
    query: str, limit: int = MAX_RESULTS_PER_SOURCE
) -> List[Dict]:
    encoded = urllib.parse.quote(query.strip())
    search_url = (
        f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
        f'?db=pubmed&term={encoded}&retmax={limit}&retmode=json'
    )
    search_raw = _http_get(search_url)
    id_list = (
        (json.loads(search_raw).get('esearchresult') or {}).get('idlist') or []
    )
    if not id_list:
        return []

    ids = ','.join(id_list[:limit])
    summary_url = (
        f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi'
        f'?db=pubmed&id={ids}&retmode=json'
    )
    summary_raw = _http_get(summary_url)
    result_map = json.loads(summary_raw).get('result') or {}
    uids = result_map.get('uids') or id_list

    results = []
    for uid in uids:
        item = result_map.get(str(uid)) or {}
        if not item or not item.get('title'):
            continue
        authors = [
            a.get('name', '')
            for a in (item.get('authors') or [])
        ]
        pub_date = str(item.get('pubdate') or '')
        year = pub_date[:4] if len(pub_date) >= 4 else ''
        results.append({
            'source': SOURCE_PUBMED,
            'title': _safe_text(item.get('title', '').rstrip('.')),
            'authors': authors,
            'year': year,
            'abstract': '',
            'journal': _safe_text(item.get('source')),
            'doi': '',
            'url': f'https://pubmed.ncbi.nlm.nih.gov/{uid}/',
            'citation_count': 0,
            'volume': _safe_text(item.get('volume')),
            'issue': _safe_text(item.get('issue')),
            'pages': _safe_text(item.get('pages')),
        })
    return results


# ─── CrossRef ────────────────────────────────────────────────

def search_crossref(
    query: str, limit: int = MAX_RESULTS_PER_SOURCE
) -> List[Dict]:
    encoded = urllib.parse.quote(query.strip())
    fields = 'DOI,title,author,published,container-title,volume,issue,page,abstract,type'
    url = (
        f'https://api.crossref.org/works'
        f'?query={encoded}&rows={limit}&select={fields}'
        f'&mailto=paperlab@example.com'
    )
    raw = _http_get(url)
    items = (json.loads(raw).get('message') or {}).get('items') or []
    results = []
    for item in items:
        titles = item.get('title') or []
        title = titles[0] if titles else ''
        if not title:
            continue
        authors = []
        for a in item.get('author') or []:
            family = str(a.get('family') or '').strip()
            given = str(a.get('given') or '').strip()
            if family:
                authors.append(f'{family}, {given}' if given else family)
        pub = (
            item.get('published')
            or item.get('published-print')
            or item.get('published-online')
            or {}
        )
        date_parts = pub.get('date-parts') or [[]]
        year = str(date_parts[0][0]) if date_parts and date_parts[0] else ''
        journals = item.get('container-title') or []
        journal = journals[0] if journals else ''
        doi = _safe_text(item.get('DOI'))
        abstract = _strip_html(item.get('abstract', ''))
        results.append({
            'source': SOURCE_CROSSREF,
            'title': _safe_text(title),
            'authors': authors,
            'year': year,
            'abstract': _truncate(abstract),
            'journal': _safe_text(journal),
            'doi': doi,
            'url': f'https://doi.org/{doi}' if doi else '',
            'citation_count': 0,
            'volume': _safe_text(item.get('volume')),
            'issue': _safe_text(item.get('issue')),
            'pages': _safe_text(item.get('page')),
        })
    return results


# ─── arXiv ───────────────────────────────────────────────────

def search_arxiv(
    query: str, limit: int = MAX_RESULTS_PER_SOURCE
) -> List[Dict]:
    encoded = urllib.parse.quote(query.strip())
    url = (
        f'https://export.arxiv.org/api/query'
        f'?search_query=all:{encoded}&start=0&max_results={limit}'
    )
    raw = _http_get(url)
    ns = {
        'atom': 'http://www.w3.org/2005/Atom',
        'arxiv': 'http://arxiv.org/schemas/atom',
    }
    root = ET.fromstring(raw)
    results = []
    for entry in root.findall('atom:entry', ns):
        title_el = entry.find('atom:title', ns)
        title = (
            title_el.text.strip().replace('\n', ' ')
            if title_el is not None else ''
        )
        if not title:
            continue
        authors = []
        for author_el in entry.findall('atom:author', ns):
            name_el = author_el.find('atom:name', ns)
            if name_el is not None and name_el.text:
                authors.append(name_el.text.strip())
        summary_el = entry.find('atom:summary', ns)
        abstract = (
            summary_el.text.strip().replace('\n', ' ')
            if summary_el is not None else ''
        )
        published_el = entry.find('atom:published', ns)
        year = ''
        if published_el is not None and published_el.text:
            year = published_el.text[:4]
        id_el = entry.find('atom:id', ns)
        arxiv_id = ''
        if id_el is not None and id_el.text:
            arxiv_id = id_el.text.strip().split('/')[-1]
        doi_el = entry.find('arxiv:doi', ns)
        doi = doi_el.text.strip() if doi_el is not None else ''
        results.append({
            'source': SOURCE_ARXIV,
            'title': title,
            'authors': authors,
            'year': year,
            'abstract': _truncate(abstract),
            'journal': 'arXiv',
            'doi': doi,
            'url': f'https://arxiv.org/abs/{arxiv_id}' if arxiv_id else '',
            'citation_count': 0,
            'volume': '',
            'issue': '',
            'pages': '',
        })
    return results


# ─── Citation Formatter ──────────────────────────────────────

def _fmt_authors_gbt(authors: List[str], max_n: int = 3) -> str:
    if not authors:
        return ''
    shown = authors[:max_n]
    result = ', '.join(shown)
    if len(authors) > max_n:
        result += ', 等'
    return result


def _fmt_authors_apa(authors: List[str], max_n: int = 7) -> str:
    if not authors:
        return ''
    formatted = []
    for author in authors[:max_n]:
        if ',' in author:
            parts = author.split(',', 1)
            family = parts[0].strip()
            given = parts[1].strip()
            initials = '. '.join(w[0] for w in given.split() if w) + '.' if given else ''
            formatted.append(f'{family}, {initials}' if initials else family)
        else:
            formatted.append(author)
    if len(authors) > max_n:
        return ', '.join(formatted) + ', et al.'
    if len(formatted) == 1:
        return formatted[0]
    return ', '.join(formatted[:-1]) + ', & ' + formatted[-1]


def _fmt_authors_mla(authors: List[str]) -> str:
    if not authors:
        return ''
    if len(authors) == 1:
        return authors[0]
    if len(authors) == 2:
        return f'{authors[0]}, and {authors[1]}'
    return f'{authors[0]}, et al'


def format_reference(paper: Dict, style: str) -> str:
    """Format a paper dict as a citation string for the given style."""
    title = paper.get('title', '')
    authors = paper.get('authors') or []
    year = paper.get('year', '')
    journal = paper.get('journal', '')
    volume = paper.get('volume', '')
    issue = paper.get('issue', '')
    pages = paper.get('pages', '')
    doi = paper.get('doi', '')
    style = str(style or 'GB/T 7714').strip()

    if style in ('GB/T 7714', 'IEEE'):
        a = _fmt_authors_gbt(authors)
        ref = (f'{a}. ' if a else '') + title
        if journal:
            ref += f'[J]. {journal}'
        if year:
            ref += f', {year}'
        if volume:
            ref += f', {volume}'
        if issue:
            ref += f'({issue})'
        if pages:
            ref += f': {pages}'
        ref += '.'
        if doi:
            ref += f' DOI: {doi}.'
        return ref.strip()

    if style == 'APA':
        a = _fmt_authors_apa(authors)
        ref = a if a else ''
        ref += f' ({year}).' if year else ('.' if a else '')
        ref += f' {title}.'
        if journal:
            ref += f' {journal}'
        if volume:
            ref += f', {volume}'
        if issue:
            ref += f'({issue})'
        if pages:
            ref += f', {pages}'
        ref += '.'
        if doi:
            ref += f' https://doi.org/{doi}'
        return ref.strip()

    if style == 'MLA':
        a = _fmt_authors_mla(authors)
        ref = (f'{a}. ' if a else '') + f'"{title}."'
        if journal:
            ref += f' {journal}'
        if volume:
            ref += f', vol. {volume}'
        if issue:
            ref += f', no. {issue}'
        if year:
            ref += f', {year}'
        if pages:
            ref += f', pp. {pages}'
        ref += '.'
        if doi:
            ref += f' {doi}.'
        return ref.strip()

    if style == 'Chicago':
        a = _fmt_authors_gbt(authors)
        ref = (f'{a}. ' if a else '') + f'"{title}."'
        if journal:
            ref += f' {journal}'
        if volume:
            ref += f' {volume}'
        if issue:
            ref += f', no. {issue}'
        if year:
            ref += f' ({year})'
        if pages:
            ref += f': {pages}'
        ref += '.'
        if doi:
            ref += f' https://doi.org/{doi}.'
        return ref.strip()

    # fallback
    parts = [_fmt_authors_gbt(authors), title, journal, year]
    return '. '.join(p for p in parts if p) + '.'


# ─── Result display helper ───────────────────────────────────

def make_result_label(paper: Dict) -> str:
    """One-line display string for a paper in the search results list."""
    src = paper.get('source', '')
    badge = _SOURCE_BADGES.get(src, '[?]')
    title = (paper.get('title') or '')[:72]
    authors = paper.get('authors') or []
    year = paper.get('year', '')
    first_author = authors[0].split(',')[0] if authors else ''
    if len(authors) > 1:
        first_author += ' et al.'
    suffix = ', '.join(filter(None, [first_author, year]))
    return f'{badge} {title}' + (f'  —  {suffix}' if suffix else '')


# ─── Unified parallel search ─────────────────────────────────

_SOURCE_FUNCTIONS = {
    SOURCE_SEMANTIC_SCHOLAR: search_semantic_scholar,
    SOURCE_PUBMED: search_pubmed,
    SOURCE_CROSSREF: search_crossref,
    SOURCE_ARXIV: search_arxiv,
}


def search_all(
    query: str,
    sources: List[str],
    on_source_done: Callable[[str, List[Dict], Optional[str]], None],
    limit: int = MAX_RESULTS_PER_SOURCE,
) -> None:
    """Launch parallel searches; calls on_source_done(source, results, error) from threads."""
    def _run(source: str) -> None:
        fn = _SOURCE_FUNCTIONS.get(source)
        if not fn:
            on_source_done(source, [], f'未知数据源: {source}')
            return
        try:
            on_source_done(source, fn(query, limit=limit), None)
        except Exception as exc:
            on_source_done(source, [], str(exc))

    for source in sources:
        threading.Thread(target=_run, args=(source,), daemon=True).start()
