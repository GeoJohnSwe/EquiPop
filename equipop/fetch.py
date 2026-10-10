"""
fetch.py - retrieving data from external sources (URL instead of
local upload), per the original specification's InData section.

    from equipop.fetch import fetch
    path = fetch("https://data.worldpop.org/.../mlt_...zip",
                 workdir="downloads")          # -> local file path
    paths = fetch(url, workdir=..., unzip=True)  # zip -> extracted files

Behaviour (spec: "if external source - ask for local folder"):
  - workdir is REQUIRED: downloads are cached there under the URL's
    file name; a second call with the same URL reuses the cached copy
    instead of re-downloading (delete the file to force re-fetch).
  - zip archives are optionally extracted into workdir/<zipname>/.
  - every fetch prints size and destination, and returns local paths
    ready for read_table() / rasters_to_points().

Note on restricted networks: some environments (including the sandbox
this library was developed in) allow only whitelisted domains. The
function reports HTTP/network errors verbatim so the cause is visible.
"""

from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen, Request
import shutil
import zipfile

#: REVIEW H1. The only schemes a provider has ever needed. http is
#: kept because one WorldPop mirror still serves it; everything else -
#: file://, ftp://, data:, and a bare path urlopen treats as a local
#: file - is refused, so a mistyped or pasted string cannot read the
#: local disk and be reported as a download.
ALLOWED_SCHEMES = ("https", "http")


def _check_scheme(url: str) -> None:
    """Refuse anything that is not an http(s) URL. One reader, so the
    three download paths cannot disagree."""
    scheme = (urlparse(str(url)).scheme or "").lower()
    if scheme not in ALLOWED_SCHEMES:
        raise ValueError(
            f"[fetch] {url!r} is not an http or https URL"
            + (f" - its scheme is {scheme!r}" if scheme else
               " - it has no scheme at all, so urlopen would read it "
               "as a path on this machine")
            + ". EquiPop only downloads over http(s); to use a local "
            "file, pass its path to the reader directly instead of "
            "fetching it.")


def fetch(url: str, workdir: str, unzip: bool = False,
          filename: str | None = None, timeout: int = 120):
    """
    Download url into workdir (cached). Returns the local file path,
    or the list of extracted paths if unzip=True.
    """
    # FIRST, before the cache lookup and before the directory is
    # created (review finding 4, 1.54.2). H1 put this inside the
    # download branch, so a forbidden URL whose BASENAME was already
    # cached returned the cached file and printed `[fetch] cached`:
    # `fetch("file:///etc/payload.bin", wd)` was reported as
    # satisfied. Nothing forbidden is read in that case, so it is not
    # the local-file-copy risk itself - it is worse as a contract,
    # because an invalid request comes back looking successful and the
    # caller believes it holds that URL's content.
    #
    # The ordering is the property, and it is what the first test
    # missed: an AST check that every function containing `urlopen`
    # also contains `_check_scheme` proves PRESENCE, not position.
    _check_scheme(url)

    wd = Path(workdir)
    wd.mkdir(parents=True, exist_ok=True)
    name = filename or Path(urlparse(url).path).name or "download.bin"
    dest = wd / name

    if dest.exists():
        print(f"[fetch] cached: {dest} ({dest.stat().st_size:,} bytes) - "
              f"delete the file to force a re-download.")
    else:
        print(f"[fetch] downloading {url}")
        req = Request(url, headers={"User-Agent": "equipop-pangea"})
        try:
            with urlopen(req, timeout=timeout) as r, open(dest, "wb") as f:
                shutil.copyfileobj(r, f)
        except Exception as e:
            if dest.exists():
                dest.unlink()
            raise ConnectionError(f"Could not fetch {url}: {e}") from e
        print(f"[fetch] saved {dest} ({dest.stat().st_size:,} bytes)")

    if unzip and dest.suffix.lower() == ".zip":
        outdir = wd / dest.stem
        outdir.mkdir(exist_ok=True)
        with zipfile.ZipFile(dest) as z:
            z.extractall(outdir)
        paths = sorted(str(p) for p in outdir.rglob("*") if p.is_file())
        print(f"[fetch] extracted {len(paths)} files -> {outdir}")
        return paths
    return str(dest)
