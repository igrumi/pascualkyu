from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(URL, KEY)

PROJECT_REF = os.getenv("PROJECT_REF")

pokemons = supabase.table("pokemon_unite").select("*").execute().data

for p in pokemons:

    filename = f"{p['name'].lower().replace(' ', '-')}.png"
    
    public_url = f"https://{PROJECT_REF}.supabase.co/storage/v1/object/public/unitepkmns/{filename}"
    
    supabase.table("pokemon_unite").update({"image_url": public_url}).eq("id", p['id']).execute()
    print(f"✅ Asignada imagen para {p['name']}: {public_url}")