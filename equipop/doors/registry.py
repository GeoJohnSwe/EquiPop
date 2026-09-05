"""
registry.py - PROVIDER DEFINITIONS AS DATA, NOT CODE.

JOHN'S IDEA (BACKLOG 258): "relying on http is tough of course if they
change the content structure all will need to be reinstalled ... what
if the site specific instructions could be separated from the tool -
so that if the user is running an old tool and it doesn't work - just
retrieving site specific instructions from GIT would be enough."

Not a dumb thought. THIS PROJECT ALREADY HAS THE EVIDENCE. BACKLOG
211: the WorldPop naming registry was written from four sample files
and failed on all 120 of John's real ones. It was DATA BAKED INTO
CODE, so fixing it cost a release, a build, a PyPI upload and three
host installs. As a registry entry it would have been a one-line edit.

THE SEAM. The MECHANISM is stable - fetch, checksum, manifest, refuse
to overwrite. The SITE KNOWLEDGE is volatile - URL patterns, which
products exist, how they are named. Volatile things belong in data.

THREE RULES, AND THE FIRST IS NOT NEGOTIABLE
--------------------------------------------
1. DATA ONLY, NEVER CODE. A definition is templates and declarations.
   No Python, no eval, no import. EquiPop is installed inside QGIS and
   ArcGIS Pro; a tool that executed instructions fetched over the
   network would be a remote code execution hole in a research
   instrument. load_one() below REFUSES anything that looks like code.
2. THE BUNDLED COPY IS THE FALLBACK. Definitions ship with the
   package. A remote registry is an UPDATE, never a dependency: with
   no network, the tool works with what it shipped with.
3. THE MANIFEST RECORDS WHICH VERSION WAS USED. Otherwise a fetch
   becomes unreproducible in a NEW way - "which rules were in force?"
   - and reproducibility is the entire reason machine 5 exists.

WHAT A DEFINITION CANNOT DO. Some providers need real logic: WorldPop
has a REST catalogue that must be queried, paged and filtered. Those
stay as Python adapters. A definition describes providers whose files
can be NAMED from the user's choices - which is most archives, GHSL
included.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

__all__ = ["load_registry", "load_one", "TemplateProvider",
           "RegistryError", "BUNDLED"]

# INSIDE the package, so it travels in the wheel. Beside it, the
# definitions would be in the repository and absent from every
# install - the same fault as run_fetch.py importing a module no
# wheel contained (BACKLOG 241).
BUNDLED = Path(__file__).resolve().parent.parent / "providers"

# A template placeholder: {field} or {field:upper} / {field:lower}.
_SLOT = re.compile(r"\{([a-z0-9_]+)(?::(upper|lower|us))?\}")

# Anything resembling code in a definition is refused outright.
_FORBIDDEN = ("__", "import ", "eval(", "exec(", "lambda", "os.",
              "subprocess", "\x00")


class RegistryError(Exception):
    """A provider definition was refused, with the reason."""


def _check_safe(obj, where="definition"):
    """A definition is DATA. Refuse anything that smells of code.

    Not paranoia: these files are meant to be updatable from a remote
    repository, and EquiPop runs inside QGIS and ArcGIS Pro.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            _check_safe(k, where)
            _check_safe(v, where)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _check_safe(v, where)
    elif isinstance(obj, str):
        low = obj.lower()
        for bad in _FORBIDDEN:
            if bad in low:
                raise RegistryError(
                    f"{where} contains {bad!r}, which is not allowed. "
                    "A provider definition is DATA - templates and "
                    "declarations. It may never contain code.")
    elif not isinstance(obj, (int, float, bool, type(None))):
        raise RegistryError(
            f"{where} holds a {type(obj).__name__}, which JSON cannot "
            "produce. Only text, numbers, lists and objects.")


def _fill(template, values):
    """Substitute {field} slots. NO format(), so nothing is evaluated."""
    def sub(m):
        name, how = m.group(1), m.group(2)
        if name not in values:
            raise RegistryError(
                f"The URL template needs {name!r}, which is not one of "
                "the fields this provider declares.")
        v = str(values[name])
        if how == "upper":
            return v.upper()
        if how == "lower":
            return v.lower()
        if how == "us":
            return v.replace("-", "_").replace(".", "_")
        return v
    return _SLOT.sub(sub, template)


class TemplateProvider:
    """A provider whose files can be NAMED from the user's choices.

    Everything it knows comes from a JSON definition. It has the same
    shape as the WorldPop adapter - FIELDS and plan() - so the spine
    cannot tell them apart, which is the point.
    """

    def __init__(self, spec):
        self.spec = spec
        self.name = spec["provider"]
        self.label = spec.get("label", self.name)
        self.FIELDS = spec["fields"]
        self.registry_version = spec.get("registry_version", "unknown")

    # --------------------------------------------------------------
    def _options(self, field, choices):
        """What a field may hold, given what is already chosen.

        A field may list its options outright, or take them from a
        product entry - GHSL's epochs and grids differ per product.
        """
        if "options" in field:
            return list(field["options"])
        src = field.get("from_product")
        if src:
            prod = choices.get(self.spec.get("product_field", "product"))
            entry = (self.spec.get("products") or {}).get(str(prod), {})
            return list(entry.get(src, []))
        return []

    def plan(self, choices, get_json=None, say=print):
        from .fetching import FetchError, numbered, resolve

        values, described = {}, {}
        products = self.spec.get("products") or {}

        for field in self.FIELDS:
            name = field["name"]
            given = choices.get(name)
            opts = self._options(field, choices)

            if given in (None, "", []):
                if "default" in field:
                    given = field["default"]
                elif len(opts) == 1:
                    given = opts[0]
                elif field.get("required"):
                    raise FetchError(
                        field.get("missing")
                        or (f"{self.name} needs {name} - "
                            f"{field['label']}. Choices:\n"
                            + "\n".join(numbered({o: "" for o in opts}))
                            if opts else
                            f"{self.name} needs {name} - "
                            f"{field['label']}."))
                else:
                    given = ""

            if opts:
                given = resolve(given, {o: field.get("describe", {})
                                        .get(o, "") for o in opts},
                                f"{name} for {self.name}")
            values[name] = given
            described[name] = given

        url = _fill(self.spec["url"], values)
        prod = products.get(str(values.get(
            self.spec.get("product_field", "product"))), {})
        entry = {
            "url": url,
            "name": os.path.basename(url),
            "licence": self.spec.get("licence"),
            "citation": prod.get("citation") or self.spec.get("citation"),
            "doi": prod.get("doi") or self.spec.get("doi"),
            "may_redistribute": self.spec.get("may_redistribute"),
            "share_alike": self.spec.get("share_alike"),
            "registry_version": self.registry_version,
        }
        entry.update({k: v for k, v in described.items()})
        described["registry_version"] = self.registry_version
        return [entry], described


def load_one(path):
    """Read one definition, refusing anything that is not data."""
    path = Path(path)
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise RegistryError(f"{path.name} is not valid JSON: {e}")
    _check_safe(spec, path.name)

    for key in ("provider", "fields", "url"):
        if key not in spec:
            raise RegistryError(
                f"{path.name} has no {key!r}. A definition needs "
                "provider, fields and url.")
    if not isinstance(spec["fields"], list) or not spec["fields"]:
        raise RegistryError(f"{path.name}: fields must be a non-empty "
                            "list.")
    names = set()
    for f in spec["fields"]:
        if "name" not in f or "label" not in f:
            raise RegistryError(
                f"{path.name}: every field needs a name and a label.")
        names.add(f["name"])
    for slot in _SLOT.findall(spec["url"]):
        if slot[0] not in names:
            raise RegistryError(
                f"{path.name}: the url uses {{{slot[0]}}} but no field "
                f"declares it. Declared: {', '.join(sorted(names))}.")
    return TemplateProvider(spec)


def load_registry(folder=None, say=None):
    """Every definition in a folder. Bad ones are skipped, not fatal.

    One malformed definition must not stop the tool from starting -
    the same reason the QGIS plugin loads when equipop is absent.
    """
    folder = Path(folder or BUNDLED)
    out = {}
    if not folder.is_dir():
        return out
    for path in sorted(folder.glob("*.json")):
        try:
            p = load_one(path)
            out[p.name] = p
        except RegistryError as e:
            if say:
                say(f"[registry] skipped {path.name}: {e}")
    return out
