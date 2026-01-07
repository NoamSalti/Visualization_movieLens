import geopandas as gpd

shp_path = r"C:\Users\97250\PycharmProjects\VISUALIZATION_PROJECT\cb_2018_us_zcta510_500k\cb_2018_us_zcta510_500k.shp"
out_geojson = r"C:\Users\97250\PycharmProjects\VISUALIZATION_PROJECT\zcta.geojson"

gdf = gpd.read_file(shp_path)

# חשוב: Plotly עובד הכי טוב עם WGS84 (lat/lon)
gdf = gdf.to_crs(epsg=4326)

gdf.to_file(out_geojson, driver="GeoJSON")
print("DONE. Saved:", out_geojson)
