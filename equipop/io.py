"""
io.py - reading and writing the usual suspects.

read_table(path)   -> DataFrame, format detected from the extension,
                      separator sniffed for text files, BOM stripped.
save_output(df, path) -> format from the extension.

Formats:
  READ : .csv .tsv .txt .dat (sniffed sep: tab ; , |), .xlsx .xls,
         .json (records or geojson points), .parquet,
         .shp .gpkg .geojson-as-geo (needs geopandas; point layers ->
         x/y columns, line/polygon layers -> representative points
         with a printed note, per spec: ask/inform on representation),
         .dbf (needs geopandas/pyogrio)
  WRITE: .csv .tsv .txt (tab), .xlsx, .json, .parquet,
         .gpkg .shp (needs geopandas + x/y column names)

Optional dependencies fail with a helpful message, never a stack trace.
"""

import csv
import io as _io
import json
from pathlib import Path
import pandas as pd


_TEXT = {".csv", ".tsv", ".txt", ".dat"}


def _sniff_sep(path: Path) -> str:
    sample = path.open("r", encoding="utf-8-sig", errors="replace").read(4096)
    try:
        return csv.Sniffer().sniff(sample, delimiters="\t;,|").delimiter
    except csv.Error:
        return ","


def read_table(path: str, sheet: str | int = 0, **kw) -> pd.DataFrame:
    """Read any supported file into a DataFrame. Extra keyword
    arguments are passed to the underlying pandas reader."""
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".dbf":
        try:
            from dbfread import DBF
        except ImportError:
            raise ImportError("[io] .dbf files need dbfread: "
                              "pip install dbfread")
        df = pd.DataFrame(iter(DBF(str(p), load=True)))
        print(f"[io] {p.name}: dbf, {len(df)} rows, "
              f"{len(df.columns)} columns")
        return df

    if ext in _TEXT:
        sep = kw.pop("sep", None) or _sniff_sep(p)
        df = pd.read_csv(p, sep=sep, encoding="utf-8-sig", **kw)
        print(f"[io] {p.name}: separator '{sep}', "
              f"{len(df)} rows, {len(df.columns)} columns")
        return df

    if ext in (".xlsx", ".xls"):
        return pd.read_excel(p, sheet_name=sheet, **kw)

    if ext == ".sav":
        try:
            import pyreadstat
        except ImportError:
            raise ImportError("SPSS .sav needs pyreadstat: "
                              "pip install pyreadstat")
        df, meta = pyreadstat.read_sav(str(p), **kw)
        print(f"[io] {p.name}: SPSS, {len(df)} rows, "
              f"{len(df.columns)} columns")
        return df

    if ext == ".parquet":
        return pd.read_parquet(p, **kw)

    if ext == ".json":
        obj = json.loads(p.read_text(encoding="utf-8-sig"))
        if isinstance(obj, dict) and obj.get("type") == "FeatureCollection":
            rows = []
            for f in obj["features"]:
                r = dict(f.get("properties") or {})
                g = f.get("geometry") or {}
                if g.get("type") == "Point":
                    r["lon"], r["lat"] = g["coordinates"][:2]
                rows.append(r)
            print(f"[io] GeoJSON: {len(rows)} features "
                  f"(points -> lon/lat columns)")
            return pd.DataFrame(rows)
        return pd.json_normalize(obj)

    if ext == ".zip":
        # zipped GIS archive (e.g. Geofabrik *-free_gpkg.zip): extract
        # next to the zip and read the contained gpkg/shp.
        #
        # BACKLOG 157. This used to extract into <stem>/ and then GLOB
        # THAT DIRECTORY, so whatever was already there could win -
        # an older extraction of a replaced archive, or anything the
        # user had put beside it. Replacing an archive while keeping
        # its name is an ordinary workflow, and the run then succeeded
        # on the wrong data with nothing to say so.
        # Now the choice is made from the ARCHIVE'S OWN LISTING, and
        # an ambiguous archive is refused rather than guessed at.
        import zipfile
        outdir = p.parent / p.stem
        outdir.mkdir(exist_ok=True)
        with zipfile.ZipFile(p) as z:
            names = [n for n in z.namelist() if not n.endswith("/")]
            z.extractall(outdir)
        wanted = ([n for n in sorted(names) if n.lower().endswith(".gpkg")]
                  or [n for n in sorted(names) if n.lower().endswith(".shp")])
        if not wanted:
            raise ValueError(
                f"No gpkg/shp found inside {p.name} - it contains "
                f"{len(names)} file(s), none of them a GIS layer.")
        if len(wanted) > 1:
            listed = ", ".join(Path(w).name for w in wanted[:6])
            raise ValueError(
                f"{p.name} contains {len(wanted)} GIS layers "
                f"({listed}{', ...' if len(wanted) > 6 else ''}). "
                "EquiPop will not guess which one you meant - unzip it "
                "and name the layer you want.")
        inner = outdir / wanted[0]
        print(f"[io] {p.name} -> {inner.name} (named by the archive, "
              "not found by searching the folder)")
        return read_table(str(inner), **kw)

    if ext in (".shp", ".gpkg", ".dbf", ".geojson", ".pbf"):
        try:
            import geopandas as gpd
        except ImportError:
            raise ImportError(f"Reading {ext} needs geopandas: "
                              f"pip install geopandas")
        if ext == ".pbf" and "layer" not in kw:
            kw["layer"] = "points"     # OSM pbf default: point features
            print("[io] .pbf: defaulting to layer='points' "
                  "(see list_layers() for others)")
        g = gpd.read_file(p, **kw)
        crs = g.crs.to_epsg() if g.crs else None
        geom_types = set(g.geometry.geom_type.unique()) if "geometry" in g else set()
        if geom_types <= {"Point"}:
            g["x"], g["y"] = g.geometry.x, g.geometry.y
        elif geom_types:
            print(f"[io] NOTE: {p.name} holds {sorted(geom_types)} - using "
                  f"representative points (centroid-like) as x/y, per spec. "
                  f"Provide your own point representation if inappropriate.")
            rp = g.geometry.representative_point()
            g["x"], g["y"] = rp.x, rp.y
        df = pd.DataFrame(g.drop(columns="geometry", errors="ignore"))
        df.attrs["crs_epsg"] = crs
        print(f"[io] {p.name}: {len(df)} features, CRS EPSG:{crs}")
        return df

    raise ValueError(f"Unsupported extension: {ext}")


def save_output(df: pd.DataFrame, path: str,
                x_col: str = "EastWest", y_col: str = "NorthSouth",
                epsg: int | None = None, **kw) -> str:
    """Save a result table; format from the extension. For .gpkg/.shp,
    x_col/y_col/epsg define the point geometry."""
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".csv":
        df.to_csv(p, index=False, **kw)
    elif ext in (".tsv", ".txt"):
        df.to_csv(p, sep="\t", index=False, **kw)
    elif ext == ".xlsx":
        df.to_excel(p, index=False, **kw)
    elif ext == ".parquet":
        df.to_parquet(p, index=False, **kw)
    elif ext == ".json":
        df.to_json(p, orient="records", **kw)
    elif ext in (".gpkg", ".shp"):
        try:
            import geopandas as gpd
        except ImportError:
            raise ImportError(f"Writing {ext} needs geopandas: "
                              f"pip install geopandas")
        g = gpd.GeoDataFrame(
            df, geometry=gpd.points_from_xy(df[x_col], df[y_col]),
            crs=f"EPSG:{epsg}" if epsg else None)
        g.to_file(p, **kw)
    else:
        raise ValueError(f"Unsupported output extension: {ext}")
    print(f"[io] saved {p.name} ({len(df)} rows)")
    return str(p)


def list_layers(path: str):
    """List layers of a multi-layer GIS source (gpkg, pbf, ...)."""
    import pyogrio
    return pyogrio.list_layers(path)


# ---------------------------------------------------------- v1.15.0
_XY_CANDIDATES = [("x", "y"), ("east", "north"),
                  ("easting", "northing"),
                  ("eastwest", "northsouth"), ("point_x", "point_y"),
                  ("xcoord", "ycoord"), ("xkoord", "ykoord"),
                  ("east_rt90", "north_rt90"),
                  ("longitude", "latitude"), ("lon", "lat")]
# pairs whose match means DEGREES - refused with advice, never used
_DEGREE_PAIRS = {("longitude", "latitude"), ("lon", "lat")}


def guess_xy_fields(names, context: str = "table"):
    """Names-only coordinate guess for interactive dialogs (v1.16):
    returns (x_name, y_name, is_degrees) or (None, None, False) when
    no recognised pair exists. NEVER raises - the dialog stays in
    charge and simply asks the user to pick fields. Same alias table
    and precedence as resolve_xy_columns."""
    low = {str(c).lower().strip(): c for c in names}
    for cx, cy in _XY_CANDIDATES:
        fx = low.get(cx) or next((low[k] for k in low
                                  if k.startswith(cx)), None)
        fy = low.get(cy) or next((low[k] for k in low
                                  if k.startswith(cy)), None)
        if fx and fy and fx != fy:
            return fx, fy, (cx, cy) in _DEGREE_PAIRS
    return None, None, False


def resolve_xy_columns(df, context: str = "table"):
    """Find the coordinate pair whatever it is called (case-
    insensitive; prefix matches like East_RT90 accepted) and return
    a copy with columns renamed to x, y. Loud, honest failure."""
    low = {c.lower().strip(): c for c in df.columns}
    for cx, cy in _XY_CANDIDATES:
        fx = low.get(cx) or next((low[k] for k in low
                                  if k.startswith(cx)), None)
        fy = low.get(cy) or next((low[k] for k in low
                                  if k.startswith(cy)), None)
        if fx and fy and fx != fy:
            if (fx, fy) != ("x", "y"):
                print(f"[io] {context}: using '{fx}'/'{fy}' as x/y")
            if (cx, cy) in _DEGREE_PAIRS:
                raise ValueError(
                    f"[io] {context}: found lon/lat DEGREES - EquiPop "
                    "needs metric coordinates; project first "
                    "(chapter 3 / projection module).")
            return df.rename(columns={fx: "x", fy: "y"})
    raise ValueError(
        f"[io] {context}: could not identify coordinate columns among "
        f"{list(df.columns)} - rename them to x/y or one of the "
        "recognised pairs (East/North, POINT_X/POINT_Y, ...).")
