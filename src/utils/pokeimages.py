import requests
import json

with open('pokemons.json') as f:
    data = json.load(f)

for p in data:
    img_data = requests.get(p['url']).content
    with open(f"images/{p['name']}.png", 'wb') as handler:
        handler.write(img_data)