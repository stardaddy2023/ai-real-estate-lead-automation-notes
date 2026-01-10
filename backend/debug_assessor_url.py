import asyncio
from app.services.pipeline.scout import ScoutService

async def test_assessor_url():
    scout = ScoutService()
    # Mock a feature with the target parcel ID
    feature = {
        "attributes": {
            "PARCEL": "117023950",
            "OWNER_NAME": "KRKT FAMILY TR",
            "ADDRESS_OL": "927 N PERRY AV",
            "JURIS_OL": "TUCSON",
            "ZIP": "85705",
            "EFF_YR_BLT": 1920,
            "IMPR_SQFT": 1758,
            "GISAREA": 5280,
            "CURZONE_OL": "R-2",
            "FCV": 505900
        },
        "geometry": {"x": -110.97, "y": 32.23}
    }
    
    lead = scout._map_pima_parcel(feature)
    print(f"Parcel ID: {lead['parcel_id']}")
    print(f"Assessor URL: {lead['assessor_url']}")
    print(f"Longitude: {lead['longitude']}")
    print(f"Flood Zone Key Present: {'flood_zone' in lead}")

if __name__ == "__main__":
    asyncio.run(test_assessor_url())
