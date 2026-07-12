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


def fetch(url: str, workdir: str, unzip: bool = False,
          filename: str | None = None, timeout: int = 120):
    """
    Download url into workdir (cached). Returns the local file path,
    or the list of extracted paths if unzip=True.
    """
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
