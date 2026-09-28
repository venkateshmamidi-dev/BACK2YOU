import os
from typing import Optional
from backend.config import settings

supabase_client = None

def get_supabase_client():
    global supabase_client
    if supabase_client is not None:
        return supabase_client

    if settings.SUPABASE_URL and (settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY):
        try:
            from supabase import create_client, Client
            key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
            supabase_client = create_client(settings.SUPABASE_URL, key)
            return supabase_client
        except Exception as e:
            print(f"[Supabase] Could not connect to remote Supabase: {e}. Using local storage fallback.")
            return None
    return None

def is_supabase_configured() -> bool:
    return bool(settings.SUPABASE_URL and (settings.SUPABASE_ANON_KEY or settings.SUPABASE_SERVICE_ROLE_KEY))
