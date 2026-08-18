"""A read-only report on the Python a door is using, and on the
libraries EquiPop needs to be there. BACKLOG 128.

Nothing here is imported at module level except the standard library.
That is the point: this file has to run on the machine where the
normal imports are what is broken.

WHY IT EXISTS
-------------
Two failures cost real days in 1.35 and 1.37, and neither of them was
EquiPop's fault. Both happened before any EquiPop code was reached, so
neither could produce an EquiPop error message:

  1. A library built for the wrong processor. Umut's Mac ran Stata as
     an Apple-Silicon program while pandas in his user folder was an
     Intel build. The loader refuses to mix them and the import stops
     dead. numpy imported fine, which made it look like a pandas bug.
  2. Two copies of the same maths library in one process. Stata plus
     Anaconda on Windows: `import numpy` closes Stata outright, with
     no error and no return code.

The second one is why the ORDER of this report matters and why every
line is flushed as it is written. If the window disappears halfway
through, whatever reached the screen is still evidence - and the
interpreter path, which is the thing that has to change, is printed
before anything risky is attempted.
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import platform
import struct
import sys

# Machine 1 cannot run without these three.
REQUIRED = ("numpy", "pandas", "scipy")

# Everything else, with the feature that needs it, so an absence reads
# as a consequence rather than a fault.
OPTIONAL = (
    ("pyproj", "projection - transforming lat/long to metres"),
    ("matplotlib", "map_output - drawing maps"),
    ("geopandas", "shapefiles, GeoPackages and other GIS formats"),
    ("rasterio", "rasters: terrain, WorldPop, barrier surfaces"),
    ("openpyxl", "reading .xlsx"),
    ("pyarrow", "parquet, used by tiled continental runs"),
)

_ARCH_HINT = (
    "This is a PROCESSOR MISMATCH, not a missing package. The library "
    "is built for a different chip than the Python running it. Reinstall "
    "it from this same Python so pip picks the matching build:\n"
    "       python -m pip install --force-reinstall --no-cache-dir "
    "--only-binary=:all: {lib}"
)


def _describe_failure(exc: BaseException) -> tuple[str, str]:
    """Turn an import failure into (one-line reason, advice).

    Kept separate from the probing so it can be tested without
    breaking a real library.
    """
    text = str(exc)
    first = text.strip().splitlines()[0] if text.strip() else exc.__class__.__name__

    lowered = text.lower()
    if "incompatible architecture" in lowered or "mach-o" in lowered:
        return first, "ARCH"
    if "dll load failed" in lowered:
        return first, "DLL"
    return first, ""


def _probe(name: str) -> tuple[str, str, str]:
    """Import one library. Returns (state, detail, advice-tag).

    Catches BaseException on purpose. An import that fails is ordinary;
    an import that raises something exotic is exactly the case worth
    reporting rather than crashing the diagnostic that was called to
    explain it.
    """
    if importlib.util.find_spec(name) is None:
        return "absent", "not installed in this Python", ""
    try:
        mod = importlib.import_module(name)
    except BaseException as exc:            # noqa: BLE001 - deliberate
        reason, tag = _describe_failure(exc)
        return "BROKEN", reason, tag
    return "ok", str(getattr(mod, "__version__", "version unknown")), ""


def _lines_environment() -> list[str]:
    """The cheap facts. Nothing here can crash the process."""
    bits = struct.calcsize("P") * 8
    out = [
        "EquiPop doctor - a read-only report, nothing is changed",
        "",
        "PYTHON",
        f"  executable   : {sys.executable}",
        f"  version      : {sys.version.split()[0]}",
        f"  processor    : {platform.machine()} ({bits}-bit)",
        f"  system       : {platform.system()} {platform.release()}",
        f"  prefix       : {sys.prefix}",
    ]
    try:
        import site
        user = site.getusersitepackages()
    except Exception:                        # noqa: BLE001
        user = "(could not be determined)"
    out.append(f"  user packages: {user}")
    return out


def _lines_equipop(ado_version: str = "") -> list[str]:
    """Where EquiPop itself is, without importing anything heavy."""
    out = ["", "EQUIPOP"]
    spec = importlib.util.find_spec("equipop")
    if spec is None or not spec.origin:
        out.append("  NOT FOUND in this Python - pip install equipop")
        return out
    folder = os.path.dirname(spec.origin)
    version = "unknown"
    try:
        with open(spec.origin, "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("__version__"):
                    version = line.split("=", 1)[1].strip().strip('"\'')
                    break
    except OSError:
        pass
    out.append(f"  engine       : {version}   (the Python package)")
    if ado_version:
        out.append(f"  commands     : {ado_version}   (the .ado files)")
        if ado_version != version and version != "unknown":
            out += [
                "",
                "  VERSION MISMATCH. These two are updated separately "
                "and must match:",
                "     the commands come from the repository, by "
                "net install",
                "     the engine comes from pip, into THIS Python",
                "  A mismatch usually shows up as ImportError: cannot "
                "import name ...,",
                "  which looks like a fault in EquiPop and is not. "
                "Update the older",
                "  half, then restart Stata.",
            ]
    out.append(f"  installed in : {folder}")
    return out


def report(ado_version: str = "") -> list[str]:
    """The whole report as a list of lines, safest first.

    ado_version is what the .ado files believe they are. They and the
    Python package are installed by different means - net install and
    pip - and updating one without the other is the single most
    frequent field failure this project has (see the handover). The
    doctor is the natural place to notice.
    """
    out = _lines_environment() + _lines_equipop(ado_version)

    out += ["", "REQUIRED - machine 1 cannot run without these"]
    verdict_ok = True
    for lib in REQUIRED:
        state, detail, tag = _probe(lib)
        out.append(f"  {lib:<12} : {state:<7} {detail}")
        if tag == "ARCH":
            out.append("       " + _ARCH_HINT.format(lib=lib))
        if state != "ok":
            verdict_ok = False

    out += ["", "OPTIONAL - absent only means the feature is unavailable"]
    for lib, why in OPTIONAL:
        state, detail, tag = _probe(lib)
        out.append(f"  {lib:<12} : {state:<7} {detail}")
        out.append(f"       needed for {why}")
        if tag == "ARCH":
            out.append("       " + _ARCH_HINT.format(lib=lib))

    out += ["", "VERDICT"]
    if verdict_ok:
        out.append("  machine 1 can run in this Python.")
    else:
        out.append("  machine 1 CANNOT run here - see REQUIRED above.")
        out.append("  Install into THIS Python, the one whose path is "
                   "printed at the top:")
        out.append("       python -m pip install --force-reinstall "
                   "--no-cache-dir --only-binary=:all: numpy pandas scipy")
        out.append("  Then restart Stata: its Python starts once per "
                   "session and keeps the old packages loaded.")
    return out


def run(stream=None, ado_version: str = "") -> None:
    """Print the report, flushing every line.

    The flush is not tidiness. If a compiled library takes the whole
    process down mid-report - which is what Stata plus Anaconda does on
    Windows - the lines already written are the only evidence there
    will be, and an unflushed buffer dies with the process.
    """
    stream = stream or sys.stdout
    for line in report(ado_version):
        stream.write(line + "\n")
        try:
            stream.flush()
        except Exception:                    # noqa: BLE001
            pass


if __name__ == "__main__":                   # python -m equipop.doctor
    run()
