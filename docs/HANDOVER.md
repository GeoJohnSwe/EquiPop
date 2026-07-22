Things to redevelop – GIS update.
##In general for both machines 1&2:
The x/y choice/settings:
•	please keep the guessing of field (i.,e. x, y, north, south, point_x, etc.) but the main thing is to let the user specify the fields holding the X/Y. 
•	For georeferenced material – i.e. shapefiles and alike it is even easier since the shapefile contains the x/y locations (although the fields are invisible) 
o	For instance - Using geopanda – the x/y sits in the geometry column
o	In other words – do not ask for the user to rename fields if they are available.  
##For machine 1:
Friction: Distance ingredient: barrier table (any x/y -style + friction column)
•	Please redo the load file thing (Indata should be any supported GIS format that you have easy access to)
o	In addition, the Load friction variable should be designed so that you choose a table/shapefile and thereafter select a suitable field.   
##For machine 2: 
•	Redesign as machine 1, there should be a selection of an input-file, and thereafter there should be the option to specify fields for full pop (i.e. the field that has the pop to which k is being measured). 
•	mean median gini are offered now, please allow for more measures (se history), and allow the user to determine if functions such as standard error, standard deviation, max, min, and such works or not – a good design is to generate checkboxes so that the user knows which measures are offered and that the user can check those to include. 
##For you to decide Claude:
•	Should we bring all functions to machine 1? – i.e. is it wise to use it as a vehicle for loading, and then we let the user specify and choose between a wide range of options?
##Potential problems
•	I loaded a shapefile (line) with values of friction – but it was not accepted (error report here:
 Traceback (most recent call last):  File "C:\Data\EQP\EquiPop.pyt", line 291, in execute    _run_tool("counts", parameters[0].value, messages,    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^              weight_field=v[1] or None,              ^^^^^^^^^^^^^^^^^^^^^^^^^^    ...<13 lines>...              out_mode=v[15] or "Append to input",              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^              out_fc=v[16] or None, unit=float(v[17] or 100))              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  File "C:\Data\EQP\EquiPop.pyt", line 159, in _run_tool    res = dispatch(engine, x, y, **kw)  File "C:\Users\joost307\AppData\Local\ESRI\conda\envs\arcgispro-equipop\Lib\site-packages\equipop\stata_bridge.py", line 236, in dispatch    fr = resolve_xy_columns(fr, context="barrier table")  File "C:\Users\joost307\AppData\Local\ESRI\conda\envs\arcgispro-equipop\Lib\site-packages\equipop\io.py", line 203, in resolve_xy_columns    raise ValueError(    ...<2 lines>...        "recognised pairs (East/North, POINT_X/POINT_Y, ...).")ValueError: [io] barrier table: could not identify coordinate columns among ['OBJECTID', 'osm_id', 'code', 'fclass', 'name', 'ref', 'oneway', 'maxspeed', 'layer', 'bridge', 'tunnel', 'Shape_Length', 'FRiction'] - rename them to x/y or one of the recognised pairs (East/North, POINT_X/POINT_Y, ...).)
•	I assumed that the snap to grid would take care of the line segment to gridpoint. My solution > I used a function to generate points along lines and used that point feature for friction. It worked. I haven’t tried polygons (to depict zones of friction) but I assume that they have the same problems as the lines
o	I wonder if the main issue is that lines and polygons have no coordinates for each grid point since their geometry is different.
o	I suggest you specify either a:
	Simple solution that caters for the different sorts
	Or – limit the functions to points
