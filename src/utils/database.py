# src/database.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

# Creamos la instancia aquí
supabase: Client = create_client(URL, KEY)