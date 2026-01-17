import googlemaps
from app.api.endpoints.settings import get_setting_sync

class MapperService:
    def __init__(self):
        self.client = None
        self._init_client()

    def _init_client(self):
        try:
            api_key = get_setting_sync("GOOGLE_MAPS_API_KEY")
            if api_key:
                self.client = googlemaps.Client(key=api_key)
            else:
                self.client = None
        except Exception as e:
            print(f"Error initializing Google Maps client: {e}")
            self.client = None

    async def enrich_property(self, address: str):
        """
        Fetches zoning and lot data from Google Maps/GIS.
        """
        # Refresh client to pick up any key changes
        self._init_client()
        
        if not self.client:
            print("Google Maps API Key missing. Returning mock data.")
            return {"address": address, "zoning": "Unknown", "lot_size": 0}

        try:
            print(f"Enriching data for: {address}")
            # googlemaps client is synchronous, so we might want to run this in an executor
            # but for now, keeping it simple as per original code
            geocode_result = self.client.geocode(address)
            
            if not geocode_result:
                return {"address": address, "error": "Address not found"}

            location = geocode_result[0]['geometry']['location']
            
            # In a real scenario, we'd also query a zoning API here using the lat/lng
            return {
                "address": geocode_result[0]['formatted_address'], 
                "zoning": "R-1 (Residential)", # Placeholder as Maps doesn't give zoning directly
                "lot_size": 7500, # Placeholder
                "location": location
            }
        except Exception as e:
            print(f"Error enriching property: {e}")
            return {"address": address, "error": str(e)}
