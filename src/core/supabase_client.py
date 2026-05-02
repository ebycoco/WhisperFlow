import logging
from supabase import create_client, Client
from typing import Optional, Dict, Any

logger = logging.getLogger("WhisperFlow.Supabase")

class SupabaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.url = "https://nffvhotbnxapniqhakld.supabase.co"
        self.key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5mZnZob3RibnhhcG5pcWhha2xkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc3MzE2MjksImV4cCI6MjA5MzMwNzYyOX0.FIVkuo_cqwLTdRVegwadWHiFo05yte3N7m8cDvtPj2k"
        self.client: Client = create_client(self.url, self.key)
        self.user = None
        self._initialized = True
        logger.info("Supabase client initialized")

    def login(self, email: str, password: str) -> bool:
        try:
            res = self.client.auth.sign_in_with_password({"email": email, "password": password})
            self.user = res.user
            logger.info(f"User logged in: {email}")
            return True
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    def signup(self, email: str, password: str) -> bool:
        try:
            res = self.client.auth.sign_up({"email": email, "password": password})
            self.user = res.user
            logger.info(f"User signed up: {email}")
            return True
        except Exception as e:
            logger.error(f"Signup failed: {e}")
            return False

    def logout(self):
        try:
            self.client.auth.sign_out()
            self.user = None
            logger.info("User logged out")
        except Exception as e:
            logger.error(f"Logout failed: {e}")

    def is_logged_in(self) -> bool:
        try:
            res = self.client.auth.get_user()
            if res.user:
                self.user = res.user
                return True
        except:
            pass
        return False

    def save_transcription(self, text: str, language: str, duration: float, engine: str):
        if not self.user:
            logger.warning("No user logged in, cannot save transcription")
            return

        try:
            data = {
                "user_id": self.user.id,
                "text": text,
                "language": language,
                "duration_seconds": duration,
                "engine": engine
            }
            self.client.table("transcriptions").insert(data).execute()
            logger.info("Transcription saved to cloud")
        except Exception as e:
            logger.error(f"Failed to save transcription: {e}")
