import os
from dotenv import load_dotenv
from supabase import create_client, Client, ClientOptions
from typing import Optional, List, Dict, Any

load_dotenv()

class SupabaseService:
    _instance = None
    client: Optional[Client] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
            
        self.client = create_client(
            url, 
            key,
            options=ClientOptions(
                postgrest_client_timeout=10,
                storage_client_timeout=10
            )
        )

    def insert(self, table: str, data: Dict[str, Any]) -> Any:
        try:
            response = self.client.table(table).insert(data).execute()
            # In supabase-py v2, response has 'data' attribute
            return response.data
        except Exception as e:
            print(f"Error inserting into {table}: {e}")
            raise e

    def select(self, table: str, columns: str = "*", filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        try:
            query = self.client.table(table).select(columns)
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"Error selecting from {table}: {e}")
            raise e
            
    def update(self, table: str, property_id: str, data: Dict[str, Any]) -> Any:
        try:
            response = self.client.table(table).update(data).eq("id", property_id).execute()
            return response.data
        except Exception as e:
            print(f"Error updating {table}: {e}")
            raise e

    def delete(self, table: str, property_id: str) -> bool:
        try:
            self.client.table(table).delete().eq("id", property_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting from {table}: {e}")
            return False

supabase_service = SupabaseService()
