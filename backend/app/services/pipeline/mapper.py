import googlemaps
from app.core.config import settings

class MapperService:
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.client = googlemaps.Client(key=self.api_key) if self.api_key else None

    async def enrich_property(self, address: str):
        """
        Fetches zoning and lot data from Google Maps/GIS.
        """
        if not self.client:
            print("Google Maps API Key missing. Returning mock data.")
            return {"address": address, "zoning": "Unknown", "lot_size": 0}

        try:
            print(f"Enriching data for: {address}")
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
