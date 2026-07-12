"""
projection.py - a framework for choosing a metric projection for
WGS84 (lat/long) data when none is specified.

Why this matters: lat/long degrees are NOT equal-sized - at 60 N a
degree of longitude is half as wide as at the equator - so gridding
in degrees produces cells of different physical size. All analysis
must happen in a metric projection; this module decides WHICH.

Decision framework (suggest_projection):
  1. Compute the lon/lat extent and centroid of the data.
  2. One UTM zone (or small overshoot within tolerance)
        -> that UTM zone (EPSG:326xx north / 327xx south).
  3. Two adjacent zones
        -> primary = zone holding most data, secondary = the other;
           recommend the A/B overlap-zone workflow (assign_zones).
  4. Wider than ~2 zones or polar (|lat| > 80)
        -> recommend an equal-distance-compromise CRS instead:
           Europe: ETRS89-LAEA (EPSG:3035); world: leave UTM behind
           and warn that no single projection preserves all distances -
           tiled runs (A/B) are the honest solution.
Every recommendation returns a structured result with a human-readable
rationale, and nothing is applied silently - the caller decides.
"""

from dataclasses import dataclass, field
import numpy as np
import pandas as pd


@dataclass
class ProjectionAdvice:
    epsg: int                    # recommended primary EPSG
    name: str
    rationale: str
    secondary_epsg: int | None = None   # for two-zone data
    tiled_run_recommended: bool = False
    warnings: list = field(default_factory=list)

    def __str__(self):
        s = f"Recommended: EPSG:{self.epsg} ({self.name})\n  {self.rationale}"
        if self.secondary_epsg:
            s += (f"\n  Secondary: EPSG:{self.secondary_epsg} - use "
                  f"assign_zones() for the A/B overlap workflow.")
        for w in self.warnings:
            s += f"\n  WARNING: {w}"
        return s


def _utm_zone(lon: float) -> int:
    return int((lon + 180) // 6) + 1


def _utm_epsg(zone: int, north: bool) -> int:
    return (32600 if north else 32700) + zone


def suggest_projection(df: pd.DataFrame,
                       lat_col: str = "lat", lon_col: str = "lon",
                       zone_tolerance: float = 0.05) -> ProjectionAdvice:
    """
    Analyse WGS84 coordinates and recommend a metric projection.

    zone_tolerance : share of points allowed to spill into a
        neighbouring zone while still recommending a single zone
        (default 5% - a thin border fringe should not force the
        two-zone machinery).
    """
    lat = pd.to_numeric(df[lat_col], errors="coerce")
    lon = pd.to_numeric(df[lon_col], errors="coerce")
    ok = lat.notna() & lon.notna()
    lat, lon = lat[ok], lon[ok]
    north = lat.mean() >= 0

    zones = lon.apply(_utm_zone)
    counts = zones.value_counts().sort_index()
    main_zone = counts.idxmax()
    share_main = counts.max() / counts.sum()
    span_zones = counts.index.max() - counts.index.min() + 1

    warns = []
    if lat.abs().max() > 80:
        warns.append("Data reaches beyond +/-80 latitude where UTM is "
                     "not defined - polar stereographic needed for that part.")
    if not north and lat.max() > 0:
        warns.append("Data spans both hemispheres - southern EPSG chosen "
                     "by majority; verify.")

    # --- single zone (or tolerable fringe) ---
    if span_zones == 1 or share_main >= 1 - zone_tolerance:
        z = main_zone
        return ProjectionAdvice(
            epsg=_utm_epsg(z, north),
            name=f"WGS84 / UTM zone {z}{'N' if north else 'S'}",
            rationale=(f"{share_main*100:.1f}% of points fall in UTM zone "
                       f"{z}; single-zone projection is safe "
                       f"(distortion < 0.1% within the zone)."),
            warnings=warns)

    # --- two adjacent zones: primary + secondary, A/B workflow ---
    if span_zones == 2:
        z2 = [z for z in counts.index if z != main_zone][0]
        return ProjectionAdvice(
            epsg=_utm_epsg(main_zone, north),
            name=f"WGS84 / UTM zone {main_zone}{'N' if north else 'S'}",
            secondary_epsg=_utm_epsg(z2, north),
            tiled_run_recommended=True,
            rationale=(f"Data spans UTM zones {main_zone} "
                       f"({share_main*100:.0f}%) and {z2} "
                       f"({(1-share_main)*100:.0f}%). Recommend two tiled "
                       f"runs, each in its own zone, with an overlap "
                       f"buffer (spec's A/B variables)."),
            warnings=warns)

    # --- wide/continental data ---
    in_europe = (lon.between(-11, 32).mean() > 0.9
                 and lat.between(34, 72).mean() > 0.9)
    if in_europe:
        return ProjectionAdvice(
            epsg=3035, name="ETRS89-extended / LAEA Europe",
            tiled_run_recommended=True,
            rationale=(f"Data spans {span_zones} UTM zones across Europe. "
                       f"EPSG:3035 is the standard pan-European equal-area "
                       f"compromise; NOTE it preserves area, not distance - "
                       f"distances stretch up to ~1-2% at the margins. For "
                       f"distance-critical results, tiled UTM runs (A/B) "
                       f"are more accurate."),
            warnings=warns)
    warns.append("No single projection preserves distances over this "
                 "extent; results near the margins will be biased.")
    return ProjectionAdvice(
        epsg=_utm_epsg(main_zone, north),
        name=f"WGS84 / UTM zone {main_zone}{'N' if north else 'S'} "
             f"(majority zone)",
        tiled_run_recommended=True,
        rationale=(f"Data spans {span_zones} UTM zones. Strongly recommend "
                   f"tiled per-zone runs with A/B overlap buffers."),
        warnings=warns)


def assign_zones(df: pd.DataFrame, buffer_m: float = 20000,
                 lat_col: str = "lat", lon_col: str = "lon") -> pd.DataFrame:
    """
    The spec's A/B overlap workflow for two-zone (or multi-zone) data:
    adds 'zone_A' (the UTM zone each point mainly belongs to) and one
    boolean 'in_zone_<z>_buffer' column per zone, true for points
    within buffer_m of that zone's boundary meridian - i.e. points to
    INCLUDE as neighbours when running the adjacent zone's tile.
    Buffer width in metres is converted to degrees at each point's
    latitude (1 deg lon = 111320 * cos(lat) m).
    """
    df = df.copy()
    lat = pd.to_numeric(df[lat_col], errors="coerce")
    lon = pd.to_numeric(df[lon_col], errors="coerce")
    df["zone_A"] = lon.apply(_utm_zone)
    deg_buffer = buffer_m / (111320 * np.cos(np.radians(lat)))
    for z in sorted(df["zone_A"].dropna().unique()):
        west, east = (z - 1) * 6 - 180, z * 6 - 180
        inside = df["zone_A"] == z
        near = (~inside & ((lon.between(west - 0, west + 0)
                            | ((lon >= west - deg_buffer) & (lon < west))
                            | ((lon > east) & (lon <= east + deg_buffer)))))
        df[f"in_zone_{int(z)}_buffer"] = inside | near
    n_buf = sum(df[c].sum() for c in df.columns
                if c.startswith("in_zone_")) - len(df)
    print(f"[projection] A/B zones assigned; {int(n_buf)} point-inclusions "
          f"added via {buffer_m/1000:.0f} km buffers.")
    return df
