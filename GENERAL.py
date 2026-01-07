import json

geojson_path = r"C:\Users\97250\PycharmProjects\VISUALIZATION_PROJECT\zcta.geojson"

with open(geojson_path, "r", encoding="utf-8") as f:
    gj = json.load(f)

props = gj["features"][0]["properties"]
print("Keys in properties:")
print(list(props.keys()))

print("\nExample values:")
for k in list(props.keys())[:10]:
    print(k, "=", props[k])
