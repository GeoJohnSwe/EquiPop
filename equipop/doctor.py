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


def _as_numbers(version: str):
    """'1.49.1' -> (1, 49, 1), for COMPARING rather than matching.

    BACKLOG 330. The doctor used `!=`, which cannot tell the two
    mismatches apart - and they are not the same fault at all. Returns
    None for anything it cannot read as numbers, so an unexpected
    version string makes the doctor go quiet rather than guess.
    """
    parts = str(version or "").strip().split(".")
    try:
        return tuple(int(p) for p in parts[:3]) if parts[0] else None
    except (ValueError, IndexError):
        return None


def _lines_floor(min_engine: str, version: str) -> list[str]:
    """What to say when the ado has told us the engine it NEEDS.

    BACKLOG 332. This replaces comparing the engine against the ado's
    RELEASE NUMBER, which is not a dependency: `equipop setup` asks
    pip for the floor, the floor is a fact about which engine
    functions the commands call, and those two numbers move for
    different reasons. Judging against the floor means the ordinary
    case - an engine newer than the commands, which is what setup
    produces - has nothing to report at all, rather than a paragraph
    explaining itself.
    """
    need, have = _as_numbers(min_engine), _as_numbers(version)
    if need is None or have is None:
        return []
    if have >= need:
        return [f"  needs engine : {min_engine} or newer - satisfied"]
    return [
        f"  needs engine : {min_engine} or newer",
        "",
        "  THE ENGINE IS TOO OLD FOR THESE COMMANDS. They call on "
        "engine functions",
        f"  that {version} does not have, which arrives as "
        "`ImportError: cannot import",
        "  name ...` and looks like a fault in EquiPop. Update the "
        "engine, then",
        "  restart Stata:",
        "     equipop setup",
        "  or, from a terminal, into THIS Python:",
        f"     {sys.executable} -m pip install --upgrade equipop",
    ]


def _lines_version_gap(ado_version: str, version: str) -> list[str]:
    """What to say when the commands and the engine differ, and the
    ado has NOT told us which engine it needs.

    Reached only for a pre-1.49.3 ado, which sends no floor. Kept
    because those .ado files are installed on real machines and will
    call a newer engine for as long as they sit there; BACKLOG 332's
    floor is the right answer and this is the best guess without one.

    BACKLOG 330, KIT BAUM ON THE SSC RELEASE: "I am a bit confused as
    to why the doctor routine identifies a version mismatch." He had
    followed the manuscript exactly, including the full restart, and
    landed on commands 1.48.2 with engine 1.49.1.

    HE WAS RIGHT TO BE CONFUSED, AND THE DOCTOR WAS WRONG. That state
    is not a mismatch to repair: it is what `equipop setup` PRODUCES.
    Setup asks pip for `equipop>=<ado version>`, deliberately, because
    new commands need a new engine - so pip installs the newest there
    is, which is ahead of SSC whenever PyPI has moved since the last
    SSC release. And PyPI and SSC are on separate tracks by design
    (1.48.2). So the package shipped an installer that creates a state
    and a diagnostic that calls that state a fault. TWO VOICES IN ONE
    PACKAGE CONTRADICTING EACH OTHER, which is BACKLOG 328's lesson
    arriving from the other direction.

    THE DIRECTION IS THE WHOLE DIAGNOSIS:

      engine NEWER than commands   expected, harmless, nothing to do.
                                   The commands only ever call engine
                                   functions that existed when they
                                   were written.
      engine OLDER than commands   the real fault, and the only one
                                   that produces `ImportError: cannot
                                   import name ...` - commands written
                                   against an engine that is not there
                                   yet.

    The loud message belongs to the second and now goes only there.
    """
    new, old = _as_numbers(version), _as_numbers(ado_version)
    if new is None or old is None or new == old:
        return []
    if new > old:
        return [
            f"  (the engine is newer than the commands, which is what "
            f"`equipop setup` asks for -",
            f"   it installs equipop>={ado_version} - and is nothing "
            f"to fix. Commands only call",
            "   engine functions that existed when they were written.)",
        ]
    return [
        "",
        "  THE ENGINE IS OLDER THAN THE COMMANDS, and that combination "
        "does break:",
        f"  these commands ({ado_version}) may call on an engine "
        f"function that {version}",
        "  does not have yet, which arrives as `ImportError: cannot "
        "import name ...`",
        "  and looks like a fault in EquiPop. Update the engine, then "
        "restart Stata:",
        "     equipop setup",
        "  or, from a terminal, into THIS Python:",
        f"     {sys.executable} -m pip install --upgrade equipop",
    ]


def _lines_equipop(ado_version: str = "",
                   min_engine: str = "") -> list[str]:
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
        if version != "unknown":
            # BACKLOG 332: the FLOOR decides, when the ado sent one.
            # The two release numbers above are shown and not judged.
            out += (_lines_floor(min_engine, version) if min_engine
                    else _lines_version_gap(ado_version, version))
    out.append(f"  installed in : {folder}")
    return out


def report(ado_version: str = "",
           min_engine: str = "") -> list[str]:
    """The whole report as a list of lines, safest first.

    ado_version is what the .ado files believe they are. They and the
    Python package are installed by different means - net install or
    ssc install, and pip - so the two numbers drift, and for most of
    this project's life the doctor treated any difference as a fault.

    min_engine is what the .ado files say they NEED, and it is the
    thing worth judging (BACKLOG 332). A pre-1.49.3 ado sends none,
    and then the direction of the difference is the best available
    signal - see _lines_version_gap.
    """
    out = _lines_environment() + _lines_equipop(ado_version, min_engine)

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
