import json
from src.garage61api.client import Garage61Client


g61 = Garage61Client(token="YOUR_TOKEN_HERE")
print("Client instance created")

cars = g61.cars()
if not cars:
    print("No access to car IDs")
tracks = g61.tracks()
if not tracks:
    print("No access to track IDs")


cars_to_file = []
tracks_to_file = []
for i in cars:
    cars_to_file.append({
        "ir_id": int(i["platform_id"]),
        "g61_id": i["id"]
    })

for i in tracks:
    tracks_to_file.append({
        "ir_id": int(i["platform_id"]),
        "g61_id": i["id"]
    })


ids_file = {
    "cars": cars_to_file,
    "tracks": tracks_to_file
}
with open("../src/garage61api/ids.json", "w") as f:
    json.dump(ids_file, f, indent=2)

print("Update completed!")