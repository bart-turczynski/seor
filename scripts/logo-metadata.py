#!/usr/bin/env python3
# logo-metadata v3 (SEOR-eyfiidrv; keywords from DESCRIPTION, SEOR-qoqmestu)
"""Write the fleet's logo metadata into man/figures/logo.svg and logo.png.

WHY THIS EXISTS. The owner's artwork (SEOR-wxjuxbtu) came with a one-shot
finalize-logos.R that only restored a Dublin Core block. The owner then asked
for every link (GitLab, the origin; GitHub, the mirror most users reach; CRAN,
where every package will be), a screen-reader description, and every field
the two formats can carry (2026-10-05). This script owns that metadata: it
rebuilds it from the table below and the package's DESCRIPTION, in place,
and leaves the artwork alone. The
SVG drawing and the PNG pixel data (IDAT) come out byte-identical; rerunning it
on its own output changes nothing.

Two limits found while checking the specs, which shape the output:

- Dublin Core lets every element repeat ("Each Dublin Core element is optional
  and repeatable", DCMI usage guide), so the SVG's RDF lists three dc:source
  links. XMP defines dc:source as a single Text value (ISO 16684-1, Table 4),
  so every XMP packet carries GitLab there and the full list in dc:relation
  and xmp:Identifier.
- IPTC's Digital Source Type is left out by the owner's decision: the art is
  a typeset name on a background, made in Claude Design for its metadata
  export, not media whose origin could mislead anyone.

KEYWORDS come from the package's DESCRIPTION, never from this script
(SEOR-qoqmestu): its X-schema.org-keywords field, the one r-universe indexes,
is the single source. A second list here drifted from it, which is how "SEO"
reached ssrfr's logo. The DESCRIPTION read is <figures>/../../DESCRIPTION,
the repository root for man/figures, unless --description names another;
there is no walking up, so a figures directory outside a repository (the
owner's export) needs --description. Its Package: must match <pkg>.
The tags are written verbatim, after the fixed prefix "R", "rstats",
"R package": image keywords are not r-universe topics, so the prefix names
the language. Verbatim means no hyphen-to-space rewrite, which would mangle
tags such as UTS-46, inet-pton and eTLD+1; only a line break inside a tag
(a DCF continuation) becomes one space. Duplicates are dropped
case-insensitively, keeping the first occurrence and the order. The script
exits, writing nothing, when the field is missing or empty, and when a
package that is neither seor nor a seor member carries the tag "seo" (any
case): SEO marks seor and its members only (owner, 2026-10-05). A member
without it is fine.

Usage:
  python3 scripts/logo-metadata.py <pkg> <man/figures dir>          # rewrite
  python3 scripts/logo-metadata.py --check <pkg> <man/figures dir>  # exit 1 on drift
  python3 scripts/logo-metadata.py --description PATH <pkg> <dir>   # DESCRIPTION elsewhere
  python3 scripts/logo-metadata.py --self-test                      # offline, no files touched

It handles logo.svg, logo.png and, when present, logo-print.svg and
logo-480.png (the rest of the owner's export, kept outside the repositories).
logo.svg is the XMP original; the other files are recorded as derived from it. It also
strips any Content Credentials (C2PA) block the export tool left behind.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import re
import struct
import sys
import tempfile
import uuid
import zlib
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

OWNER = "Bart Turczynski"
EMAIL = "bartek@turczynski.pl"
NAMESPACE = "bart-turczynski"
CREATED = "2026-10-04"  # the artwork's date
METADATA_DATE = "2026-10-05"  # bump when what this script writes changes
YEAR = CREATED[:4]
TOOL = "Claude Design"
SOFTWARE = f"{TOOL}; metadata by seor scripts/logo-metadata.py"
FONT = "Name set in IBM Plex Mono (SIL Open Font License 1.1), converted to outlines."
LICENSE_URL = "https://opensource.org/license/mit"
RIGHTS = f"© {YEAR} {OWNER}. MIT License."
RIGHTS_ASCII = f"Copyright {YEAR} {OWNER}. MIT License."
USAGE_TERMS = f"Licensed under the MIT License: {LICENSE_URL}"
DISCLAIMER = "Provided under the MIT License, without warranty of any kind."
LABEL = "seor fleet"
LANG = "en-US"
MASTER = "logo.svg"  # the vector original; the other files are renditions of it
# Every ID is a uuid5 under this fleet namespace (RFC 9562), not NAMESPACE_URL.
FLEET_NS = uuid.uuid5(uuid.NAMESPACE_URL, "https://gitlab.com/bart-turczynski/seor#logo-ids")
PLACEHOLDER = "uuid:00000000-0000-0000-0000-000000000000"

# pkg: (what the library is, Zenodo concept DOI or None). Keywords come from
# each package's DESCRIPTION (see the docstring).
PACKAGES = {
    "seor": ("SEO library for R", "10.5281/zenodo.23136687"),
    "rurl": ("URL library for R", "10.5281/zenodo.20972584"),
    "punycoder": ("Punycode library for R", "10.5281/zenodo.20973629"),
    "pslr": ("Public Suffix List library for R", "10.5281/zenodo.20973660"),
    "raddr": ("IP address library for R", None),
    "pagerankr": ("PageRank library for R", "10.5281/zenodo.23046334"),
    "robotstxtr": ("robots.txt library for R", "10.5281/zenodo.23018995"),
    "sitemapr": ("XML sitemap library for R", None),
    "ssrfr": ("SSRF protection library for R", None),
}
HUB = "seor"
REPO_FILES = ("logo.svg", "logo.png")
# seor's members: DESCRIPTION Imports plus robotstxtr in Suggests (ARCHITECTURE.md).
# ssrfr is a fleet package but not a seor member.
MEMBERS = ("rurl", "punycoder", "pslr", "raddr", "pagerankr", "sitemapr", "robotstxtr")
KEYWORD_FIELD = "X-schema.org-keywords"
KEYWORD_PREFIX = ("R", "rstats", "R package")  # names the language; see the docstring


# --- keywords from DESCRIPTION -------------------------------------------------

def parse_dcf(text: str, where: str) -> dict[str, str]:
    """One DCF record, as R's read.dcf() reads a DESCRIPTION: "Field: value",
    continued on lines that start with whitespace. Continuation lines join with
    a newline; comment lines (#) are skipped, as R 4.6 does."""
    fields: dict[str, str] = {}
    last = None
    lines = text.splitlines()
    for n, line in enumerate(lines, 1):
        if line.startswith("#"):
            continue
        if not line.strip():
            if any(rest.strip() and not rest.startswith("#") for rest in lines[n:]):
                sys.exit(f"logo-metadata: {where}:{n}: a blank line inside the record; expected one DCF record")
            break
        if line[0] in " \t":
            if last is None:
                sys.exit(f"logo-metadata: {where}:{n}: a continuation line before any field")
            fields[last] += "\n" + line.strip()
            continue
        m = re.match(r"([^\s:]+):(.*)$", line)
        if not m:
            sys.exit(f"logo-metadata: {where}:{n}: not a DCF line: {line!r}")
        last = m.group(1)
        if last in fields:
            sys.exit(f"logo-metadata: {where}:{n}: field {last} appears twice")
        fields[last] = m.group(2).strip()
    return fields


def check_seo(pkg: str, tags: list[str], where: str) -> None:
    """The tag "seo" marks seor and its members only (owner, 2026-10-05: ssrfr
    is not an SEO tool). One way only: a member need not carry it."""
    found = [t for t in tags if t.casefold() == "seo"]
    if pkg != HUB and pkg not in MEMBERS and found:
        sys.exit(f"logo-metadata: {where} tags {pkg} {found[0]!r}, but {pkg} is neither {HUB} nor a {HUB} member; "
                 f"remove it from {KEYWORD_FIELD}")


def logo_keywords(pkg: str, text: str, where: str) -> list[str]:
    """KEYWORD_PREFIX plus the DESCRIPTION's tags, verbatim, de-duplicated
    case-insensitively (first occurrence kept, order kept)."""
    fields = parse_dcf(text, where)
    if fields.get("Package") != pkg:
        sys.exit(f"logo-metadata: {where} is the DESCRIPTION of {fields.get('Package')!r}, not {pkg!r}")
    # A line break inside a tag is layout, not content: it becomes one space.
    # Other whitespace inside a tag stays as written, as read.dcf() keeps it.
    tags = [t.replace("\n", " ").strip() for t in fields.get(KEYWORD_FIELD, "").split(",")]
    tags = [t for t in tags if t]
    if not tags:
        sys.exit(f"logo-metadata: {where} has no {KEYWORD_FIELD} (or it is empty); "
                 "the logo keywords come from it, so add the field first")
    check_seo(pkg, tags, where)
    keywords: list[str] = []
    seen: set[str] = set()
    for k in (*KEYWORD_PREFIX, *tags):
        if k.casefold() not in seen:
            seen.add(k.casefold())
            keywords.append(k)
    for k in keywords:
        try:
            k.encode("latin-1")  # the PNG tEXt Keywords chunk is Latin-1
        except UnicodeEncodeError:
            sys.exit(f"logo-metadata: {where}: the tag {k!r} is not Latin-1, which PNG tEXt requires")
    return keywords


class Facts:
    def __init__(self, pkg: str, description: Path) -> None:
        if pkg not in PACKAGES:
            sys.exit(f"logo-metadata: unknown package {pkg!r}; known: {', '.join(PACKAGES)}")
        if not description.is_file():
            sys.exit(f"logo-metadata: no DESCRIPTION at {description}; name one with --description")
        self.pkg = pkg
        self.what, doi = PACKAGES[pkg]
        try:
            text = description.read_text(encoding="utf-8-sig")  # tolerate a BOM
        except UnicodeDecodeError:
            sys.exit(f"logo-metadata: {description} is not UTF-8; the fleet's DESCRIPTIONs are")
        self.keywords = logo_keywords(pkg, text, str(description))
        self.a11y = f"Logo of the {pkg} library for R, white text on a black background"
        self.ext_descr = (
            f"A black hexagon with a thin white border. The package name, {pkg}, "
            "is set across the center in white capital letters, with the R that marks "
            "it as an R package in a lighter weight than the rest."
        )
        self.gitlab = f"https://gitlab.com/{NAMESPACE}/{pkg}"
        self.github = f"https://github.com/{NAMESPACE}/{pkg}"
        self.cran = f"https://CRAN.R-project.org/package={pkg}"
        self.runiverse = f"https://{NAMESPACE}.r-universe.dev/{pkg}"
        self.site = f"https://{NAMESPACE}.gitlab.io/{pkg}/"
        self.doi = f"https://doi.org/{doi}" if doi else None
        self.sources = [self.gitlab, self.github, self.cran]
        self.links = [self.gitlab, self.github, self.cran, self.runiverse, self.site]
        if self.doi:
            self.links.append(self.doi)
        self.hub = f"https://gitlab.com/{NAMESPACE}/{HUB}"
        self.members = [f"https://gitlab.com/{NAMESPACE}/{p}" for p in MEMBERS]
        # XMP (ISO 16684-1, xmpMM:OriginalDocumentID): saving to another format
        # gives the new file its own DocumentID, and OriginalDocumentID keeps the
        # original's. logo.svg is the original; once it has been written, the
        # renditions name it and its exact instance (xmpMM:DerivedFrom).
        self.master: tuple[str, str] | None = None
        # InstanceID per file: a hash of the file rendered with PLACEHOLDER in
        # its place, so any change to the artwork or the metadata changes it.
        self.iid: dict[str, str] = {}

    def file_url(self, name: str) -> str:
        return f"{self.gitlab}/-/raw/main/man/figures/{name}"

    def self_links(self, name: str) -> list[str]:
        """The file's own URL, for the two files the repositories carry; the
        print and 480 px artwork stay outside them, so they get none."""
        return [self.file_url(name)] if name in REPO_FILES else []

    def document_id(self, name: str) -> str:
        """Stable per package and file name, independent of where it is hosted."""
        return "uuid:" + str(uuid.uuid5(FLEET_NS, f"document:{self.pkg}/{name}"))

    def original_id(self, name: str) -> str:
        return self.document_id(MASTER) if self.master else self.document_id(name)

    def instance_id(self, name: str) -> str:
        return self.iid.get(name, PLACEHOLDER)


def esc(text: str) -> str:
    """XML-escape, with every non-ASCII character as a numeric reference."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    return "".join(c if ord(c) < 128 else f"&#{ord(c)};" for c in text)


def alt(text: str) -> str:
    return f'<rdf:Alt><rdf:li xml:lang="x-default">{esc(text)}</rdf:li></rdf:Alt>'


def bag(items: list[str], kind: str = "Bag") -> str:
    return f"<rdf:{kind}>" + "".join(f"<rdf:li>{esc(i)}</rdf:li>" for i in items) + f"</rdf:{kind}>"


def xmp_packet(f: Facts, name: str, mime: str, wrapper: bool) -> str:
    """One XMP packet: Dublin Core, XMP basic, rights, media management,
    photoshop, IPTC Core, PLUS and Creative Commons."""
    props = [
        f"<dc:title>{alt(f.pkg)}</dc:title>",
        f"<dc:description>{alt(f.a11y)}</dc:description>",
        f"<dc:creator>{bag([OWNER], 'Seq')}</dc:creator>",
        f"<dc:publisher>{bag([OWNER])}</dc:publisher>",
        f"<dc:contributor>{bag([FONT])}</dc:contributor>",
        f"<dc:rights>{alt(RIGHTS)}</dc:rights>",
        f"<dc:subject>{bag(f.keywords)}</dc:subject>",
        f"<dc:source>{esc(f.gitlab)}</dc:source>",
        f"<dc:relation>{bag(f.links)}</dc:relation>",
        f"<dc:identifier>{esc(f.pkg)}</dc:identifier>",
        f"<dc:format>{mime}</dc:format>",
        f"<dc:language>{bag([LANG])}</dc:language>",
        f"<dc:type>{bag(['Image', 'StillImage'])}</dc:type>",
        f"<dc:date>{bag([CREATED], 'Seq')}</dc:date>",
        f"<xmp:CreateDate>{CREATED}</xmp:CreateDate>",
        f"<xmp:ModifyDate>{METADATA_DATE}</xmp:ModifyDate>",
        f"<xmp:MetadataDate>{METADATA_DATE}</xmp:MetadataDate>",
        f"<xmp:CreatorTool>{esc(TOOL)}</xmp:CreatorTool>",
        f"<xmp:Label>{esc(LABEL)}</xmp:Label>",
        f"<xmp:Nickname>{esc(f.pkg)} logo</xmp:Nickname>",
        f"<xmp:Identifier>{bag(f.self_links(name) + f.links)}</xmp:Identifier>",
        "<xmpRights:Marked>True</xmpRights:Marked>",
        f"<xmpRights:WebStatement>{LICENSE_URL}</xmpRights:WebStatement>",
        f"<xmpRights:UsageTerms>{alt(USAGE_TERMS)}</xmpRights:UsageTerms>",
        f"<xmpRights:Owner>{bag([OWNER])}</xmpRights:Owner>",
        f"<xmpMM:DocumentID>{f.document_id(name)}</xmpMM:DocumentID>",
        f"<xmpMM:OriginalDocumentID>{f.original_id(name)}</xmpMM:OriginalDocumentID>",
        f"<xmpMM:InstanceID>{f.instance_id(name)}</xmpMM:InstanceID>",
        *([] if not f.master or name == MASTER else [
            '<xmpMM:DerivedFrom rdf:parseType="Resource">'
            f"<stRef:documentID>{f.master[0]}</stRef:documentID>"
            f"<stRef:instanceID>{f.master[1]}</stRef:instanceID>"
            "</xmpMM:DerivedFrom>"]),
        f"<photoshop:Headline>{esc(f.pkg)}: {esc(f.what)}</photoshop:Headline>",
        f"<photoshop:Credit>{esc(OWNER)}</photoshop:Credit>",
        f"<photoshop:Source>{esc(OWNER)}</photoshop:Source>",
        f"<photoshop:AuthorsPosition>Maintainer</photoshop:AuthorsPosition>",
        f"<photoshop:CaptionWriter>{esc(OWNER)}</photoshop:CaptionWriter>",
        f"<photoshop:DateCreated>{CREATED}</photoshop:DateCreated>",
        f"<Iptc4xmpCore:AltTextAccessibility>{alt(f.a11y)}</Iptc4xmpCore:AltTextAccessibility>",
        f"<Iptc4xmpCore:ExtDescrAccessibility>{alt(f.ext_descr)}</Iptc4xmpCore:ExtDescrAccessibility>",
        "<Iptc4xmpCore:IntellectualGenre>logo</Iptc4xmpCore:IntellectualGenre>",
        '<Iptc4xmpCore:CreatorContactInfo rdf:parseType="Resource">'
        f"<Iptc4xmpCore:CiEmailWork>{EMAIL}</Iptc4xmpCore:CiEmailWork>"
        f"<Iptc4xmpCore:CiUrlWork>{esc(f.gitlab)}</Iptc4xmpCore:CiUrlWork>"
        "</Iptc4xmpCore:CreatorContactInfo>",
        '<plus:Licensor><rdf:Seq><rdf:li rdf:parseType="Resource">'
        f"<plus:LicensorName>{esc(OWNER)}</plus:LicensorName>"
        f"<plus:LicensorURL>{esc(f.gitlab)}</plus:LicensorURL>"
        f"<plus:LicensorEmail>{EMAIL}</plus:LicensorEmail>"
        "</rdf:li></rdf:Seq></plus:Licensor>",
        '<plus:CopyrightOwner><rdf:Seq><rdf:li rdf:parseType="Resource">'
        f"<plus:CopyrightOwnerName>{esc(OWNER)}</plus:CopyrightOwnerName>"
        "</rdf:li></rdf:Seq></plus:CopyrightOwner>",
        '<plus:ImageCreator><rdf:Seq><rdf:li rdf:parseType="Resource">'
        f"<plus:ImageCreatorName>{esc(OWNER)}</plus:ImageCreatorName>"
        "</rdf:li></rdf:Seq></plus:ImageCreator>",
        "<plus:ModelReleaseStatus>http://ns.useplus.org/ldf/vocab/MR-NAP</plus:ModelReleaseStatus>",
        "<plus:PropertyReleaseStatus>http://ns.useplus.org/ldf/vocab/PR-NAP</plus:PropertyReleaseStatus>",
        f'<cc:license rdf:resource="{LICENSE_URL}"/>',
        f"<cc:attributionName>{esc(OWNER)}</cc:attributionName>",
        f'<cc:attributionURL rdf:resource="{esc(f.gitlab)}"/>',
    ]
    body = (
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n'
        '<rdf:Description rdf:about=""'
        ' xmlns:dc="http://purl.org/dc/elements/1.1/"'
        ' xmlns:xmp="http://ns.adobe.com/xap/1.0/"'
        ' xmlns:xmpRights="http://ns.adobe.com/xap/1.0/rights/"'
        ' xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/"'
        ' xmlns:stRef="http://ns.adobe.com/xap/1.0/sType/ResourceRef#"'
        ' xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/"'
        ' xmlns:Iptc4xmpCore="http://iptc.org/std/Iptc4xmpCore/1.0/xmlns/"'
        ' xmlns:plus="http://ns.useplus.org/ldf/xmp/1.0/"'
        ' xmlns:cc="http://creativecommons.org/ns#">\n'
        + "\n".join(props)
        + "\n</rdf:Description></rdf:RDF></x:xmpmeta>"
    )
    if wrapper:
        body = '<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>\n' + body + '\n<?xpacket end="r"?>'
    return body


# --- SVG ---------------------------------------------------------------------

def svg_rdf(f: Facts, name: str) -> str:
    """The Dublin Core / DC terms / Creative Commons block (the form Inkscape and
    the SVG spec's own example use), where every element may repeat."""
    agent = lambda who: f"<cc:Agent><dc:title>{esc(who)}</dc:title></cc:Agent>"  # noqa: E731
    lines = [
        f"<dc:title>{esc(f.pkg)}</dc:title>",
        f"<dc:description>{esc(f.what)}</dc:description>",
        f"<dc:description>{esc(f.a11y)}</dc:description>",
        f"<dc:creator>{agent(OWNER)}</dc:creator>",
        f"<dc:publisher>{agent(OWNER)}</dc:publisher>",
        f"<dc:rights>{agent(RIGHTS)}</dc:rights>",
        f"<dc:date>{CREATED}</dc:date>",
        '<dc:type rdf:resource="http://purl.org/dc/dcmitype/StillImage"/>',
        "<dc:format>image/svg+xml</dc:format>",
        f"<dc:language>{LANG}</dc:language>",
        f"<dc:identifier>{esc(f.pkg)}</dc:identifier>",
        *[f"<dc:identifier>{esc(u)}</dc:identifier>" for u in f.self_links(name)],
        *[f"<dc:source>{esc(u)}</dc:source>" for u in f.sources],
        *[f"<dc:relation>{esc(u)}</dc:relation>" for u in f.links],
        f"<dc:subject>{bag(f.keywords)}</dc:subject>",
        f"<dc:contributor>{esc(FONT)}</dc:contributor>",
        f"<dcterms:alternative>{esc(f.pkg)} logo</dcterms:alternative>",
        f"<dcterms:created>{CREATED}</dcterms:created>",
        f"<dcterms:modified>{METADATA_DATE}</dcterms:modified>",
        f"<dcterms:dateCopyrighted>{YEAR}</dcterms:dateCopyrighted>",
        f"<dcterms:rightsHolder>{esc(OWNER)}</dcterms:rightsHolder>",
        f'<dcterms:license rdf:resource="{LICENSE_URL}"/>',
        "<dcterms:accessRights>Public</dcterms:accessRights>",
        "<dcterms:audience>R users</dcterms:audience>",
    ]
    if f.pkg == HUB:
        lines += [f'<dcterms:hasPart rdf:resource="{esc(u)}"/>' for u in f.members]
    elif f.pkg in MEMBERS:
        lines.append(f'<dcterms:isPartOf rdf:resource="{esc(f.hub)}"/>')
    lines += [
        f'<cc:license rdf:resource="{LICENSE_URL}"/>',
        f"<cc:attributionName>{esc(OWNER)}</cc:attributionName>",
        f'<cc:attributionURL rdf:resource="{esc(f.gitlab)}"/>',
    ]
    return (
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"'
        ' xmlns:dc="http://purl.org/dc/elements/1.1/"'
        ' xmlns:dcterms="http://purl.org/dc/terms/"'
        ' xmlns:cc="http://creativecommons.org/ns#">\n'
        '<cc:Work rdf:about="">\n' + "\n".join(lines) + "\n</cc:Work>\n</rdf:RDF>"
    )


ROOT = re.compile(r"<svg\b[^>]*>", re.S)
ATTR = re.compile(r"""([\w:.-]+)\s*=\s*("[^"]*"|'[^']*')""")


def rewrite_svg(f: Facts, path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    # Drop what this script owns: every <metadata> (ours or a C2PA one), the
    # root <title> and <desc>, and the c2pa namespace declaration.
    text = re.sub(r"\s*<metadata\b.*?</metadata>", "", text, flags=re.S)
    for tag in ("title", "desc"):
        found = re.findall(rf"<{tag}\b", text)
        if len(found) > 1:
            sys.exit(f"logo-metadata: {path} has {len(found)} <{tag}> elements; expected at most one")
        text = re.sub(rf"\s*<{tag}\b[^>]*>.*?</{tag}>", "", text, flags=re.S)
    text = re.sub(r'\s+xmlns:c2pa="[^"]*"', "", text)

    m = ROOT.search(text)
    if not m:
        sys.exit(f"logo-metadata: {path} has no <svg> root")
    attrs = dict(ATTR.findall(m.group(0)))
    # version="1.1" goes: role, aria-* and lang are not SVG 1.1 attributes.
    for key in ("version", "role", "aria-labelledby", "aria-describedby", "xml:lang", "lang"):
        attrs.pop(key, None)
    ours = {
        "role": "img",
        "aria-labelledby": f"{f.pkg}-title",
        "aria-describedby": f"{f.pkg}-desc",
        "xml:lang": LANG,
        "lang": LANG,
    }
    attrs.update({k: f'"{v}"' for k, v in ours.items()})
    root = "<svg " + " ".join(f"{k}={v}" for k, v in attrs.items()) + ">"
    head = (
        f'\n<title id="{f.pkg}-title">{esc(f.pkg)}</title>'
        f'\n<desc id="{f.pkg}-desc">{esc(f.a11y)}</desc>'
        f'\n<metadata id="{f.pkg}-metadata">{svg_rdf(f, path.name)}\n'
        f"{xmp_packet(f, path.name, 'image/svg+xml', wrapper=False)}\n</metadata>"
    )
    text = text[: m.start()] + root + head + text[m.end():]
    if not text.startswith("<?xml"):
        text = '<?xml version="1.0" encoding="UTF-8"?>' + text
    return text


# --- PNG ---------------------------------------------------------------------

PNG_SIG = b"\x89PNG\r\n\x1a\n"
# Chunks this script owns and rewrites. caBX is the C2PA manifest.
OWNED = {b"tEXt", b"zTXt", b"iTXt", b"eXIf", b"tIME", b"caBX"}
# Color information already in the file is kept; sRGB is added only when there is none.
COLOR_CHUNKS = {b"sRGB", b"iCCP", b"gAMA", b"cHRM"}


def rfc1123(day: str) -> str:
    """The PNG spec's recommended Creation Time form (RFC 1123), at midnight UTC."""
    return format_datetime(datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc), usegmt=True)


def chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))


def text_chunk(key: str, value: str) -> bytes:
    return chunk(b"tEXt", key.encode("latin-1") + b"\0" + value.encode("latin-1"))


def itxt_chunk(key: str, value: str, lang: str = "", translated: str = "") -> bytes:
    data = (key.encode("latin-1") + b"\0\0\0" + lang.encode("ascii") + b"\0"
            + translated.encode("utf-8") + b"\0" + value.encode("utf-8"))
    return chunk(b"iTXt", data)


def exif_block(f: Facts, name: str, width: int, height: int) -> bytes:
    """A little-endian TIFF structure: IFD0 (with the Windows XP fields that
    Explorer's Details tab shows) and an Exif sub-IFD."""
    def ascii_(s: str) -> tuple[int, bytes]:
        return 2, s.encode("ascii") + b"\0"

    def xp(s: str) -> tuple[int, bytes]:
        return 1, s.encode("utf-16-le") + b"\0\0"

    stamp = lambda d: d.replace("-", ":") + " 00:00:00"  # noqa: E731
    ifd0 = {
        0x010E: ascii_(f.a11y),
        0x0131: ascii_(SOFTWARE),
        0x0132: ascii_(stamp(METADATA_DATE)),
        0x013B: ascii_(OWNER),
        0x8298: ascii_(RIGHTS_ASCII),
        0x8769: (4, b"\0\0\0\0"),  # Exif IFD offset, patched below
        0x9C9B: xp(f.pkg),
        0x9C9C: xp(f"{f.a11y}. {FONT} {' '.join(f.links)}"),
        0x9C9D: xp(OWNER),
        0x9C9E: xp("; ".join(f.keywords)),
        0x9C9F: xp(f.what),
    }
    exif = {
        0x9000: (7, b"0232"),
        0x9003: ascii_(stamp(CREATED)),
        0x9286: (7, b"ASCII\0\0\0" + f"{f.what}. {f.gitlab}".encode("ascii")),
        0xA001: (3, struct.pack("<H", 1)),  # sRGB
        0xA002: (4, struct.pack("<I", width)),
        0xA003: (4, struct.pack("<I", height)),
        0xA420: ascii_(f.instance_id(name).removeprefix("uuid:").replace("-", "")),
    }
    size = {1: 1, 2: 1, 3: 2, 4: 4, 7: 1}

    def ifd_len(entries: dict) -> int:
        return 2 + 12 * len(entries) + 4

    ifd0_at = 8
    exif_at = ifd0_at + ifd_len(ifd0)
    data_at = exif_at + ifd_len(exif)
    ifd0[0x8769] = (4, struct.pack("<I", exif_at))
    blobs = bytearray()

    def emit(entries: dict) -> bytes:
        out = bytearray(struct.pack("<H", len(entries)))
        for tag in sorted(entries):
            kind, value = entries[tag]
            count = len(value) // size[kind]
            if len(value) <= 4:
                field = value.ljust(4, b"\0")
            else:
                field = struct.pack("<I", data_at + len(blobs))
                blobs.extend(value + (b"\0" if len(value) % 2 else b""))
            out += struct.pack("<HHI", tag, kind, count) + field
        return bytes(out + b"\0\0\0\0")

    head = b"II*\0" + struct.pack("<I", ifd0_at)
    return head + emit(ifd0) + emit(exif) + bytes(blobs)


def rewrite_png(f: Facts, path: Path) -> bytes:
    raw = path.read_bytes()
    if not raw.startswith(PNG_SIG):
        sys.exit(f"logo-metadata: {path} is not a PNG")
    chunks, p = [], len(PNG_SIG)
    while p < len(raw):
        (n,) = struct.unpack(">I", raw[p:p + 4])
        chunks.append((raw[p + 4:p + 8], raw[p + 8:p + 8 + n]))
        p += 12 + n
    kinds = [k for k, _ in chunks]
    if kinds[0] != b"IHDR" or kinds[-1] != b"IEND":
        sys.exit(f"logo-metadata: {path} does not start with IHDR and end with IEND")
    width, height = struct.unpack(">II", chunks[0][1][:8])
    kept = [(k, d) for k, d in chunks if k not in OWNED]
    first_idat = next(i for i, (k, _) in enumerate(kept) if k == b"IDAT")

    texts = [
        text_chunk("Title", f.pkg),
        text_chunk("Author", OWNER),
        text_chunk("Description", f.a11y),
        text_chunk("Copyright", RIGHTS),
        text_chunk("Creation Time", rfc1123(CREATED)),
        text_chunk("Software", SOFTWARE),
        text_chunk("Source", TOOL),
        text_chunk("Disclaimer", DISCLAIMER),
        text_chunk("Comment", f"{FONT} Links: {' '.join(f.links)}"),
        text_chunk("Keywords", ", ".join(f.keywords)),
        *[text_chunk("URL", u) for u in f.links],
        itxt_chunk("Description", f.a11y, LANG, "Description"),
        itxt_chunk("XML:com.adobe.xmp", xmp_packet(f, path.name, "image/png", wrapper=True)),
    ]
    out = [PNG_SIG, chunk(*kept[0])]
    if not any(k in COLOR_CHUNKS for k in kinds):
        out.append(chunk(b"sRGB", b"\0"))  # perceptual intent
    out += [chunk(k, d) for k, d in kept[1:first_idat]]
    out.append(chunk(b"eXIf", exif_block(f, path.name, width, height)))
    out += texts
    out += [chunk(k, d) for k, d in kept[first_idat:-1]]
    y, mo, d = (int(x) for x in METADATA_DATE.split("-"))
    out.append(chunk(b"tIME", struct.pack(">HBBBBB", y, mo, d, 0, 0, 0)))
    out.append(chunk(*kept[-1]))
    return b"".join(out)


def render(f: Facts, path: Path) -> bytes:
    return rewrite_svg(f, path).encode("utf-8") if path.suffix == ".svg" else rewrite_png(f, path)


def finalize(f: Facts, path: Path) -> bytes:
    """Render with PLACEHOLDER as the InstanceID, hash those bytes (artwork and
    metadata), then render again with the ID that hash gives."""
    f.iid[path.name] = PLACEHOLDER
    draft = render(f, path)
    f.iid[path.name] = "uuid:" + str(uuid.uuid5(FLEET_NS, "instance:" + hashlib.sha256(draft).hexdigest()))
    if path.name == MASTER:
        f.master = (f.document_id(MASTER), f.iid[path.name])
    return render(f, path)


# The files this script handles, in the order it finalizes them: logo.svg
# first, so the renditions can name it.
LOGO_NAMES = ("logo.svg", "logo.png", "logo-print.svg", "logo-480.png")


def finalized(f: Facts, targets: list[Path]):
    """Each target (in LOGO_NAMES order) with what this script writes for it
    and whether that differs from the file: the --check verdict."""
    for t in targets:
        new = finalize(f, t)
        yield t, new, new != t.read_bytes()


def check_logos(pkg: str, description: str, logos: dict[str, bytes]) -> dict[str, bytes | None]:
    """--check on files held in memory (the fleet checker reads them from
    GitLab or a checkout): for each name in `logos`, what this script would
    write, or None when the file is current. They are written to a temporary
    man/figures under a DESCRIPTION holding `description`, and judged by the
    same loop as --check, so the verdict is its verdict. Exits as --check
    does on a DESCRIPTION or a file it refuses."""
    unknown = sorted(set(logos) - set(LOGO_NAMES))
    if unknown:
        raise ValueError(f"not a logo file name: {', '.join(unknown)}")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        figures = root / "man" / "figures"
        figures.mkdir(parents=True)
        (root / "DESCRIPTION").write_bytes(description.encode("utf-8"))
        targets = []
        for name in LOGO_NAMES:
            if name in logos:
                (figures / name).write_bytes(logos[name])
                targets.append(figures / name)
        f = Facts(pkg, default_description(figures))
        return {t.name: new if drift else None for t, new, drift in finalized(f, targets)}


# --- self-test ---------------------------------------------------------------

def read_svg_subjects(svg: str) -> list[list[str]]:
    """Every dc:subject bag in an SVG (the RDF block's and the XMP packet's)."""
    bags = re.findall(r"<dc:subject><rdf:Bag>(.*?)</rdf:Bag></dc:subject>", svg, re.S)
    return [[html.unescape(li) for li in re.findall(r"<rdf:li>(.*?)</rdf:li>", b, re.S)] for b in bags]


def png_chunks(raw: bytes) -> list[tuple[bytes, bytes]]:
    out, p = [], len(PNG_SIG)
    while p < len(raw):
        (n,) = struct.unpack(">I", raw[p:p + 4])
        out.append((raw[p + 4:p + 8], raw[p + 8:p + 8 + n]))
        p += 12 + n
    return out


def read_png_keywords(raw: bytes) -> tuple[str, str]:
    """The PNG's tEXt Keywords and its EXIF IFD0 XPKeywords."""
    chunks = png_chunks(raw)
    text = next(d.split(b"\0", 1)[1].decode("latin-1") for k, d in chunks
                if k == b"tEXt" and d.startswith(b"Keywords\0"))
    tiff = next(d for k, d in chunks if k == b"eXIf")
    (ifd0,) = struct.unpack("<I", tiff[4:8])
    (count,) = struct.unpack("<H", tiff[ifd0:ifd0 + 2])
    for i in range(count):
        tag, _kind, n, field = struct.unpack("<HHII", tiff[ifd0 + 2 + 12 * i:ifd0 + 14 + 12 * i])
        if tag == 0x9C9E:
            return text, tiff[field:field + n].decode("utf-16-le").rstrip("\0")
    raise SystemExit("self-test: no XPKeywords in the eXIf chunk")


TEST_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10" height="10"/></svg>\n'


def test_png() -> bytes:
    """A 1x1 grayscale PNG: IHDR, one IDAT, IEND."""
    return (PNG_SIG + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"\0\0")) + chunk(b"IEND", b""))


def exits_with(fn, needle: str) -> bool:
    """True when fn() calls sys.exit with a message containing needle."""
    try:
        fn()
    except SystemExit as e:
        return needle in str(e.code)
    return False


SEOR_TAGS = ("seo, search-engine-optimization, metapackage,\n"
             "    url-parsing, idna, public-suffix-list, ip-address, xml-sitemap, pagerank,\n"
             "    robots-txt")


def description(pkg: str, keywords: str | None) -> str:
    field = "" if keywords is None else f"{KEYWORD_FIELD}: {keywords}\n"
    return f"Package: {pkg}\nTitle: A test\n{field}License: MIT + file LICENSE\n"


def self_test() -> int:
    def expect(tag: str, condition: bool) -> None:
        if not condition:
            raise SystemExit(f"self-test FAILED ({tag})")

    def kw(pkg: str, keywords: str | None) -> list[str]:
        return logo_keywords(pkg, description(pkg, keywords), "DESCRIPTION")

    # DCF: continuation lines join, a broken tag becomes one space, others stay verbatim.
    expect("continuation lines", kw("pslr", "eTLD+1, registrable\n    domain,\n\tUTS-46 ,inet-pton")
           == [*KEYWORD_PREFIX, "eTLD+1", "registrable domain", "UTS-46", "inet-pton"])
    expect("field after a continuation", parse_dcf("A: x,\n  y\nB: z\n", "t") == {"A": "x,\ny", "B": "z"})
    expect("one record only", exits_with(lambda: parse_dcf("A: x\n\nB: y\n", "t"), "blank line"))
    expect("a comment after the record", parse_dcf("A: x\n\n# note\n", "t") == {"A": "x"})
    expect("inner whitespace kept", kw("punycoder", "RFC  3492, a\tb") == [*KEYWORD_PREFIX, "RFC  3492", "a\tb"])
    expect("prefix and case-insensitive de-duplication",
           kw("rurl", "r, Rstats, url, URL, R PACKAGE, idna") == [*KEYWORD_PREFIX, "url", "idna"])
    # Package: must match.
    expect("Package mismatch refused", exits_with(lambda: logo_keywords("rurl", description("pslr", "url"), "D"),
                                                  "DESCRIPTION of 'pslr', not 'rurl'"))
    # A missing or empty field is refused.
    expect("missing field refused", exits_with(lambda: kw("rurl", None), f"no {KEYWORD_FIELD}"))
    expect("empty field refused", exits_with(lambda: kw("rurl", " , "), f"no {KEYWORD_FIELD}"))
    # The SEO rule: one way, case-insensitive.
    expect("seo on seor", "seo" in kw("seor", "seo, metapackage"))
    expect("member without seo", kw("rurl", "url") == [*KEYWORD_PREFIX, "url"])
    expect("member with seo", "seo" in kw("pagerankr", "pagerank, seo"))
    for tag in ("seo", "SEO", "Seo"):
        expect(f"{tag} on a non-member refused",
               exits_with(lambda: kw("ssrfr", f"ssrf, {tag}"), f"{tag!r}, but ssrfr is neither seor nor a seor member"))
    expect("a tag merely containing seo", "technical-seo" in kw("ssrfr", "ssrf, technical-seo"))

    # Keyword output, read back from rendered files.
    want = [*KEYWORD_PREFIX, "seo", "search-engine-optimization", "metapackage", "url-parsing", "idna",
            "public-suffix-list", "ip-address", "xml-sitemap", "pagerank", "robots-txt"]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        figures = root / "man" / "figures"
        figures.mkdir(parents=True)
        (root / "DESCRIPTION").write_text(description("seor", SEOR_TAGS), encoding="utf-8")
        (figures / "logo.svg").write_text(TEST_SVG, encoding="utf-8")
        (figures / "logo.png").write_bytes(test_png())
        expect("default DESCRIPTION", default_description(figures) == (root / "DESCRIPTION").resolve())
        expect("no DESCRIPTION refused", exits_with(lambda: Facts("seor", root / "nowhere"), "no DESCRIPTION"))
        f = Facts("seor", default_description(figures))
        svg = finalize(f, figures / "logo.svg")
        png = finalize(f, figures / "logo.png")
        expect("SVG dc:subject (RDF and XMP)", read_svg_subjects(svg.decode("utf-8")) == [want, want])
        text, xp = read_png_keywords(png)
        expect("PNG Keywords", text == ", ".join(want))
        expect("EXIF XPKeywords", xp == "; ".join(want))
    print("logo-metadata self-test: OK")
    return 0


def default_description(figures: Path) -> Path:
    """<figures>/../../DESCRIPTION: the repository root for man/figures."""
    return figures.resolve().parent.parent / "DESCRIPTION"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="report drift; write nothing")
    ap.add_argument("--self-test", action="store_true", help="run the offline self-test and exit")
    ap.add_argument("--description", type=Path,
                    help="the package's DESCRIPTION (default: <figures>/../../DESCRIPTION)")
    ap.add_argument("pkg", nargs="?")
    ap.add_argument("figures", type=Path, nargs="?")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.pkg is None or args.figures is None:
        ap.error("pkg and figures are required")
    targets = [args.figures / n for n in LOGO_NAMES if (args.figures / n).exists()]
    if not any(t.name in ("logo.svg", "logo.png") for t in targets):
        sys.exit(f"logo-metadata: no logo.svg or logo.png in {args.figures}")
    f = Facts(args.pkg, args.description or default_description(args.figures))
    drift = 0
    for t, new, drifted in finalized(f, targets):
        if not drifted:
            print(f"current  {t}")
            continue
        drift += 1
        if args.check:
            print(f"drift    {t}")
        else:
            t.write_bytes(new)
            print(f"written  {t}")
    if args.check and drift:
        print(f"regenerate: python3 scripts/logo-metadata.py {args.pkg} {args.figures}, then commit the logos")
    return 1 if args.check and drift else 0


if __name__ == "__main__":
    sys.exit(main())
