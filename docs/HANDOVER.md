# Handover: GIS update

## Objective

Redevelop the GIS input workflow for Machines 1 and 2 so that users can load ordinary tables and georeferenced vector data without renaming fields or manually converting valid GIS geometry into X/Y columns.

## Recommended design

Create one shared **GIS input and field-selection component** and use it in both machines. Keep Machine 1 and Machine 2 as separate task-oriented workflows; do not turn Machine 1 into a container for every function.

The shared component should handle:

- file or layer selection;
- format and geometry detection;
- coordinate-source selection;
- automatic X/Y-field suggestions;
- manual X/Y-field overrides;
- value-field selection, such as friction or population;
- CRS validation and transformation; and
- conversion of point, line, and polygon features to the analysis grid.

This gives both machines the same reliable loading behaviour without making users pass through Machine 1 when they only need Machine 2.

## Requirements common to Machines 1 and 2

### Input formats

- Accept tabular inputs supported by the deployed stack, such as CSV and Excel tables.
- Accept georeferenced vector formats supported by the deployed GIS stack, such as shapefiles, GeoPackage layers, GeoJSON, and ArcGIS feature classes where available.
- Populate field selectors only after the selected input has been inspected.
- Display a clear validation message when a format, layer, field type, geometry type, or CRS cannot be used.

### Coordinate selection

Provide a **Coordinate source** control with these options:

1. **Auto (default)**
2. **Feature geometry**
3. **Attribute fields**

The expected behaviour is:

- If the input has valid feature geometry, **Auto** should use that geometry by default. The user must not be asked to create, expose, or rename X/Y fields.
- If the input is a non-spatial table, try to identify likely coordinate pairs, including `x/y`, `lon/lat`, `longitude/latitude`, `east/north`, `easting/northing`, `point_x/point_y`, and equivalent case variants.
- Show separate **X field** and **Y field** selectors whenever attribute fields are being used. Preselect the guessed fields, but always let the user override them.
- If guessing fails, leave the selectors unresolved and ask the user to choose fields. Do not instruct the user to rename columns.
- Validate that selected coordinate fields are numeric and contain usable values.
- Make the expected axis order explicit: X is longitude/easting; Y is latitude/northing.
- Use or request the input CRS before comparing, snapping, or overlaying coordinates. Reproject inputs to the analysis CRS when necessary.

For point features, coordinates can be read from the geometry (`geometry.x` and `geometry.y` in GeoPandas). Lines and polygons must be handled spatially; they must not be treated as though they contain one representative X/Y pair.

## Machine 1: friction and distance inputs

Redesign the **Distance ingredient / barrier table** workflow.

### Required user flow

1. Select an input table or GIS layer.
2. Select the coordinate source, with geometry preferred automatically for spatial data.
3. If attribute coordinates are used, confirm or select the X and Y fields.
4. Select the numeric field containing the friction value.
5. Choose any geometry-to-grid or overlap options that are relevant.
6. Validate the configuration before execution.

The friction-field selector must list suitable numeric fields from the chosen input. Field-name matching should be case-insensitive, so names such as `FRiction` are valid.

### Geometry handling

Machine 1 should support points, lines, and polygons rather than restricting input to points.

- **Points:** snap or assign each point to the appropriate analysis-grid cell using the existing tolerance/rule.
- **Lines:** identify every grid cell crossed by the line, or rasterize the line to the working grid, and assign the feature's friction value to those cells.
- **Polygons:** identify every covered/intersected grid cell, or rasterize the polygon to the working grid, and assign the feature's friction value to those cells.
- **Multipart features:** process all component geometries.
- **Empty or invalid geometries:** reject them with a useful message or repair them only when that behaviour is explicit and safe.

Do not silently reduce lines or polygons to centroids: doing so loses their spatial extent and produces incorrect barriers. “Snap to grid” should be applied after the feature has been mapped to the cells it affects; snapping alone cannot turn a line or polygon into all relevant grid points.

When multiple features affect the same grid cell, provide an explicit aggregation rule. Recommended options are **maximum**, **minimum**, **mean**, and **sum**, with **maximum** as the default for barrier-style friction so that a strong barrier is not diluted by a weaker overlapping feature.

### Machine 1 acceptance criteria

- A CSV with non-standard coordinate-column names can be used after selecting the X and Y fields.
- A point shapefile works without visible X/Y attributes.
- A line shapefile with a numeric friction field affects all grid cells crossed by its features.
- A polygon friction layer affects all cells covered or intersected according to the documented rule.
- The user selects the friction field after selecting the input.
- Invalid or non-numeric friction fields produce a clear validation error before processing begins.

## Machine 2: population and statistics

Redesign the input workflow using the same shared component as Machine 1.

### Required user flow

1. Select an input table or GIS layer.
2. Select the coordinate source, with geometry preferred automatically for spatial data.
3. If attribute coordinates are used, confirm or select the X and Y fields.
4. Select the numeric **full population** field: the population against which `k` is measured.
5. Select the summary measures to calculate.
6. Validate the configuration before execution.

Do not infer the full-population field without showing the result to the user. The field selector should contain suitable numeric fields and allow the user to override any suggestion.

### Summary-measure selection

Replace the fixed set of mean, median, and Gini outputs with a group of checkboxes. At minimum, offer:

- Mean
- Median
- Gini coefficient
- Standard error
- Standard deviation
- Minimum
- Maximum
- Count
- Sum
- Variance
- Range
- Selected percentiles, if supported

Keep the currently established measures selected by default to preserve existing behaviour. Only calculate and return measures checked by the user. Disable or explain any measure that is not valid for the selected data rather than failing during execution.

Definitions must be documented where implementation choices matter, particularly:

- sample versus population standard deviation and variance;
- the standard-error formula and treatment of weights;
- handling of null values and zero-population records;
- Gini behaviour for negative values or an all-zero population; and
- percentile interpolation.

### Machine 2 acceptance criteria

- The user can select the full-population field after selecting the input.
- Spatial inputs work from feature geometry without visible X/Y fields.
- Tabular inputs work with automatically suggested or manually selected X/Y fields.
- The interface shows all available measures as checkboxes.
- Only selected measures are calculated and included in the result.
- Unsupported measure/data combinations are identified before processing.

## Decision: should all functions be moved to Machine 1?

**Recommendation: no.** Share the input, coordinate, CRS, geometry-to-grid, field-selection, and validation code, but retain separate Machine 1 and Machine 2 interfaces.

Putting all functions into Machine 1 would make it harder to understand, test, and maintain. A reusable loader achieves the desired consistency while each machine remains focused on its own outcome. If users need a chained workflow, allow a normalized layer or configuration from Machine 1 to be reused by Machine 2, but do not make Machine 2 dependent on Machine 1's interface state.

## Reported failure

A line shapefile containing friction values was rejected because the current implementation attempted to find X/Y attribute columns instead of reading the feature geometry:

```text
Traceback (most recent call last):
  File "C:\Data\EQP\EquiPop.pyt", line 291, in execute
    _run_tool("counts", parameters[0].value, messages,
              weight_field=v[1] or None,
              ...
              out_mode=v[15] or "Append to input",
              out_fc=v[16] or None, unit=float(v[17] or 100))
  File "C:\Data\EQP\EquiPop.pyt", line 159, in _run_tool
    res = dispatch(engine, x, y, **kw)
  File "C:\Users\joost307\AppData\Local\ESRI\conda\envs\arcgispro-equipop\Lib\site-packages\equipop\stata_bridge.py", line 236, in dispatch
    fr = resolve_xy_columns(fr, context="barrier table")
  File "C:\Users\joost307\AppData\Local\ESRI\conda\envs\arcgispro-equipop\Lib\site-packages\equipop\io.py", line 203, in resolve_xy_columns
    raise ValueError(
ValueError: [io] barrier table: could not identify coordinate columns among
['OBJECTID', 'osm_id', 'code', 'fclass', 'name', 'ref', 'oneway', 'maxspeed',
 'layer', 'bridge', 'tunnel', 'Shape_Length', 'FRiction'] - rename them to x/y
or one of the recognised pairs (East/North, POINT_X/POINT_Y, ...).
```

### Root cause

`resolve_xy_columns()` assumes that a barrier input is a point-like table with visible coordinate columns. A spatial line feature instead stores its coordinates and extent in the geometry. Even if a representative coordinate were extracted, one X/Y pair would not describe all grid cells crossed by the line.

### Required correction

Route spatial inputs through geometry-aware processing before any X/Y-column resolver:

1. Detect whether the input has valid geometry.
2. Read and validate its CRS and geometry type.
3. For points, use point geometry directly.
4. For lines and polygons, intersect or rasterize the geometry against the analysis grid.
5. Apply the selected friction field and overlap rule to affected cells.
6. Use X/Y-column resolution only for non-spatial tables or when the user explicitly selects **Attribute fields**.

## Implementation notes

- Separate loading and schema inspection from execution so that dependent field selectors can be populated immediately.
- Keep coordinate detection as a convenience, not as a hard requirement.
- Centralize aliases and case-insensitive field matching rather than duplicating them across machines.
- Preserve source field names in the UI; normalize only internal identifiers where needed.
- Validate all selected fields, CRS information, and geometry rules before starting a long-running operation.
- Add automated tests for tables and for point, line, polygon, multipart, empty, and mixed-geometry inputs.
- Include regression coverage for the reported line-shapefile failure and the mixed-case `FRiction` field.

## Definition of done

- Both machines use the shared GIS input component.
- Users can override automatically suggested X/Y fields.
- Spatial data uses feature geometry without requiring X/Y attributes or renamed fields.
- Machine 1 accepts supported point, line, and polygon friction layers.
- Machine 2 provides a full-population field selector and selectable summary measures.
- Errors are detected during validation and explain how the user can correct the input.
- Documentation and automated regression tests cover the supported formats, geometries, aggregation rules, CRS behaviour, and statistical definitions.
