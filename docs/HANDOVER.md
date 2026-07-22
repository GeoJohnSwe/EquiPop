##In general for both machines 1&2:
The x/y choice/settings:
*please keep the guessing of field (i.,e. x, y, north, south, point_x, etc.) but the main thing is to let the user specify the fields holding the X/Y. 
*For georeferenced material – i.e. shapefiles and alike it is even easier since the shapefile contains the x/y locations (although the fields are invisible) 
 **For instance - Using geopanda – the x/y sits in the geometry column
 **In other words – do not ask for the user to rename fields if they are available.  
