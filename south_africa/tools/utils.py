import os
import re
import unicodedata

_DELIMITERS_RE = re.compile(r"[._()\[\]{}\s-]+")
_NON_ALPHANUM_RE = re.compile(r"[^a-z0-9\-]")
_MULTI_HYPHEN_RE = re.compile(r"-+")
_EXT_CLEAN_RE = re.compile(r"[^a-z0-9.-]")


def slugify(filename: str) -> str:
    if not filename or not isinstance(filename, str):
        return ""

    filename = filename.strip()
    if not filename:
        return ""

    filename = filename.replace("\\", "/").split("/")[-1]

    base, ext = os.path.splitext(filename)

    base = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode("ascii")
    slug = base.lower()

    slug = _DELIMITERS_RE.sub("-", slug)
    slug = _NON_ALPHANUM_RE.sub("", slug)
    slug = _MULTI_HYPHEN_RE.sub("-", slug).strip("-")

    ext = _EXT_CLEAN_RE.sub("", ext.lower().strip())

    return f"{slug}{ext}"
