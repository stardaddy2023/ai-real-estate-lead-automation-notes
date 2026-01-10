import requests
import json
import math
import asyncio
import numpy as np
from typing import List, Dict, Optional, Any
from shapely.geometry import Polygon, Point
from shapely.prepared import prep

class ScoutService:
    # Priority order for AND-logic filtering (most restrictive first)
    FILTER_PRIORITY = [
        "Code Violations",
        "Absentee Owner",
        "Tax Liens", 
        "Pre-Foreclosure",
        "Divorce",
        "Judgements",
        "Probate",
        "Evictions",
        "Liens (HOA, Mechanics)"
    ]

    def __init__(self):
        print("SCOUT SERVICE V4 - WITH COMPREHENSIVE LEAD CACHE")
        # Pima County GIS - Parcels - Regional (Verified Public URL)
        self.pima_parcels_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
        
        # Pinal County GIS - Assessor Info
        self.pinal_parcels_url = "https://rogue.casagrandeaz.gov/arcgis/rest/services/Pinal_County/Pinal_County_Assessor_Info/MapServer/0/query"
        
        # Tucson Open Data - Code Violations (Verified Layer 94)
        self.tucson_violations_url = "https://gis.tucsonaz.gov/arcgis/rest/services/PDSD/pdsdMain_General5/MapServer/94/query"
        
        # HomeHarvest cache - keyed by normalized address (for HomeHarvest API)
        self._homeharvest_cache: Dict[str, Optional[Dict]] = {}
        
        # Comprehensive lead cache - stores ALL enrichment data keyed by address
        # This includes: parcel data, GIS layers, HomeHarvest data, assessor data, etc.
        self._lead_cache: Dict[str, Dict] = {}
        
        # Property type cache - stores PARCEL_USE code by normalized address
        # Allows skipping property type API calls on repeat searches
        self._property_type_cache: Dict[str, str] = {}
        
        # Violations source cache - stores raw violations by location key with TTL
        # Tuple: (violations_list, timestamp)
        # Key format: "zip_{zip_code}" or "bounds_{hash}"
        self._violations_cache: Dict[str, tuple] = {}
        self._violations_cache_ttl = 600  # 10 minutes TTL

        
        # Fields that indicate a lead has been enriched
        self._enrichment_fields = [
            # Address fields
            "address", "address_zip", "address_street",
            # Parcel/Assessor data
            "owner", "owner_name", "mailing_address", "legal_desc", "land_value", 
            "building_value", "total_value", "zoning", "use_desc",
            "parcel_id", "parcel_use_code", "property_type", "assessed_value", "lot_size",
            # GIS layer data  
            "flood_zone", "school_district", "supervisorial_district", "council_ward",
            # HomeHarvest data
            "beds", "baths", "sqft", "lot_sqft", "stories", "year_built",
            "primary_photo", "neighborhoods", "estimated_value", "hoa_fee"
        ]

    async def _fetch_code_violations(self, filters: Dict, limit: int) -> List[Dict]:
        import time as time_module  # For TTL timestamp
        
        zip_code = filters.get("zip_code")
        bounds = filters.get('bounds')
        
        # Build cache key based on location filter
        cache_key = None
        if bounds:
            # Create hash of bounds for cache key
            bounds_str = f"{bounds.get('west', bounds.get('xmin'))}_{bounds.get('south', bounds.get('ymin'))}_{bounds.get('east', bounds.get('xmax'))}_{bounds.get('north', bounds.get('ymax'))}"
            cache_key = f"bounds_{hash(bounds_str)}"
        elif zip_code:
            cache_key = f"zip_{zip_code}"
        elif filters.get("neighborhood"):
            cache_key = f"hood_{filters.get('neighborhood').replace(' ', '_')}"
        
        # Check cache first
        # DEBUG: DISABLE CACHE TO FIX MAP SEARCH
        # if cache_key and cache_key in self._violations_cache:
        #     cached_data, cached_time = self._violations_cache[cache_key]
        #     age = time_module.time() - cached_time
        #     if age < self._violations_cache_ttl:
        #         print(f"Code violations from cache ({len(cached_data)} violations, {age:.0f}s old)")
        #         return cached_data
        #     else:
        #         # Cache expired, remove it
        #         del self._violations_cache[cache_key]
        
        print("Fetching code violations from Tucson GIS...")
        
        # Build WHERE clause
        where_parts = ["STATUS_1 NOT IN ('COMPLIAN', 'CLOSED', 'VOID')"]

        
        params = {
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": "4326",  # WGS84 for Leaflet map compatibility
            "resultRecordCount": limit * 10 if (zip_code or filters.get('bounds')) else limit,  # Fetch more if filtering (spatial)
            "f": "json",
            "orderByFields": "DT_ENT DESC"
        }
        
        # If zip code provided, use spatial query with envelope
        zip_polygon = None
        bounds = filters.get('bounds')
        
        if bounds:
            print(f"DEBUG: _fetch_code_violations received bounds: {bounds}")
            # Handle Bounds Filter (Map Selection) - Priority over Zip
            # Construct envelope from bounds
            # Expected format: {xmin, ymin, xmax, ymax} or {south, west, north, east}
            if 'west' in bounds:
                 # Convert Google Maps bounds to Envelope
                 envelope = {
                     "xmin": bounds['west'],
                     "ymin": bounds['south'],
                     "xmax": bounds['east'],
                     "ymax": bounds['north'],
                     "spatialReference": {"wkid": 4326}
                 }
            elif 'xmin' in bounds:
                 envelope = {
                     "xmin": bounds['xmin'],
                     "ymin": bounds['ymin'],
                     "xmax": bounds['xmax'],
                     "ymax": bounds['ymax'],
                     "spatialReference": {"wkid": 4326}
                 }
            
            print(f"DEBUG: Constructed envelope: {envelope}")

            # Create Shapely Polygon for client-side filtering
            from shapely.geometry import box
            zip_polygon = prep(box(envelope['xmin'], envelope['ymin'], envelope['xmax'], envelope['ymax']))
            print("DEBUG: Created zip_polygon for filtering")
            
            # Add envelope to spatial query for server-side pre-filtering
            params["geometry"] = json.dumps(envelope)
            params["geometryType"] = "esriGeometryEnvelope"
            params["spatialRel"] = "esriSpatialRelIntersects"
            params["inSR"] = "4326"
            
        elif zip_code:
            zip_metadata = await self._get_zip_metadata(zip_code)
            if zip_metadata and "polygon" in zip_metadata:
                zip_polygon = prep(zip_metadata["polygon"])
                # Add envelope to spatial query for server-side pre-filtering
                if "envelope" in zip_metadata:
                    params["geometry"] = json.dumps(zip_metadata["envelope"])
                    params["geometryType"] = "esriGeometryEnvelope"
                    params["spatialRel"] = "esriSpatialRelIntersects"
                    params["spatialRel"] = "esriSpatialRelIntersects"
                    params["inSR"] = "2868"
        
        elif filters.get("neighborhood"):
            # Resolve neighborhood to bounds
            hood_bounds = await self._resolve_neighborhood_to_bounds(filters.get("neighborhood"))
            if hood_bounds:
                # Create envelope from bounds
                envelope = {
                    "xmin": hood_bounds[0],
                    "ymin": hood_bounds[1],
                    "xmax": hood_bounds[2],
                    "ymax": hood_bounds[3],
                    "spatialReference": {"wkid": 4326}
                }
                
                # Create Shapely Polygon for client-side filtering
                from shapely.geometry import box
                zip_polygon = prep(box(hood_bounds[0], hood_bounds[1], hood_bounds[2], hood_bounds[3]))
                
                # Add envelope to spatial query
                params["geometry"] = json.dumps(envelope)
                params["geometryType"] = "esriGeometryEnvelope"
                params["spatialRel"] = "esriSpatialRelIntersects"
                params["inSR"] = "4326"
                print(f"Filtering by neighborhood: {filters.get('neighborhood')} (Bounds: {hood_bounds})")
            else:
                print(f"Warning: Could not resolve neighborhood '{filters.get('neighborhood')}'. Returning empty results.")
                return []
        
        params["where"] = " AND ".join(where_parts)
        
        # PAGINATION: API caps at 1000 results, so we need multiple fetches
        all_features = []
        batch_size = 1000  # Max per request
        
        # Calculate how many batches based on limit (with minimum of 1, max of 6)
        # Add extra batch for filtering losses
        target_records = limit * 2  # Fetch 2x limit to account for filtering
        max_batches = max(1, min(6, (target_records // batch_size) + 1))
        offset = 0
        
        try:
            for batch_num in range(max_batches):
                batch_params = params.copy()
                batch_params["resultRecordCount"] = batch_size
                batch_params["resultOffset"] = offset
                
                response = requests.get(self.tucson_violations_url, params=batch_params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    features = data.get("features", [])
                    
                    if not features:
                        # No more results
                        break
                    
                    all_features.extend(features)
                    print(f"  Batch {batch_num + 1}: Fetched {len(features)} violations (total: {len(all_features)})")
                    
                    # Check if this was the last batch
                    if len(features) < batch_size:
                        # Server returned less than requested, no more data
                        break
                    
                    offset += batch_size
                else:
                    print(f"Error fetching violations batch {batch_num}: {response.status_code}")
                    break
            
            print(f"Found {len(all_features)} raw code violations.")
            
            # Map to lead objects
            leads = [self._map_tucson_violation(f) for f in all_features]
            
            # Client-side filtering by zip code OR bounds (strict)
            if (zip_code or bounds) and zip_polygon:
                filtered_leads = []
                for lead in leads:
                    if lead.get("latitude") and lead.get("longitude"):
                        pt = Point(lead["longitude"], lead["latitude"])
                        if zip_polygon.contains(pt):
                            # Override extracted zip with search zip if searching by zip
                            if zip_code:
                                lead["address_zip"] = zip_code
                            # Update full address to include city and zip
                            if zip_code:
                                lead["address"] = f"{lead['address_street']}, Tucson, AZ {zip_code}"
                            filtered_leads.append(lead)
                print(f"After spatial filter: {len(filtered_leads)} code violations.")
                leads = filtered_leads
            
            # Filter by specific address BEFORE enrichment (performance optimization)
            address_filter = filters.get("address")
            if address_filter:
                address_norm = address_filter.upper().strip()
                leads = [l for l in leads if address_norm in l.get("address_street", "").upper()]
                print(f"After address filter: {len(leads)} code violations.")

            # ===== CONSOLIDATE MULTIPLE VIOLATIONS PER ADDRESS (BEFORE LIMIT) =====
            # Group violations by address and create consolidated leads
            consolidated = {}
            for lead in leads:
                addr_key = (lead.get("address_street") or "").upper().strip()
                if not addr_key:
                    continue
                    
                if addr_key not in consolidated:
                    # First violation at this address - create base lead
                    lead["violations"] = [{
                        "description": lead.get("violation_description", "Unknown"),
                        "activity_num": lead.get("id")
                    }]
                    lead["violation_count"] = 1
                    # Create unique ID from address (no duplicates possible)
                    lead["id"] = addr_key.replace(" ", "_").replace(",", "")
                    consolidated[addr_key] = lead
                else:
                    # Additional violation at same address - merge
                    existing = consolidated[addr_key]
                    existing["violations"].append({
                        "description": lead.get("violation_description", "Unknown"),
                        "activity_num": lead.get("id")
                    })
                    existing["violation_count"] = len(existing["violations"])
                    # Keep any enrichment data from either source (though not enriched yet)
                    if not existing.get("owner_name") and lead.get("owner_name"):
                        existing["owner_name"] = lead.get("owner_name")
            
            print(f"Consolidated {len(leads)} violations into {len(consolidated)} unique properties.")
            
            # Save to cache for future searches
            result = list(consolidated.values())
            if cache_key:
                self._violations_cache[cache_key] = (result, time_module.time())
            
            # Return ALL UNENRICHED leads - final limit applied in fetch_leads after property type filtering
            return result
        except Exception as e:
            print(f"Error fetching violations: {e}")
            return []
    
    async def _enrich_violations_with_parcel_data(self, leads: List[Dict]):
        """
        Enriches code violation leads with owner info from the parcel layer.
        Uses BATCH spatial queries (Multipoint) for performance.
        """
        if not leads:
            return
        
        import time
        start_time = time.time()
        print(f"Enriching {len(leads)} violations with parcel data (BATCH)...")
        
        base_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
        
        # Process in batches of 50
        batch_size = 50
        enriched_count = 0
        
        loop = asyncio.get_event_loop()
        
        for i in range(0, len(leads), batch_size):
            batch = leads[i:i + batch_size]
            
            # 1. Build Multipoint Geometry
            points = []
            valid_leads = []
            for lead in batch:
                lat = lead.get("latitude")
                lon = lead.get("longitude")
                if lat and lon:
                    points.append([lon, lat])
                    valid_leads.append(lead)
            
            if not points:
                continue
                
            multipoint = {
                "points": points,
                "spatialReference": {"wkid": 4326}
            }
            
            params = {
                "geometry": json.dumps(multipoint),
                "geometryType": "esriGeometryMultipoint",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "PARCEL,MAIL1,MAIL2,MAIL3,MAIL4,MAIL5,ZIP,FCV,CURZONE_OL,GISAREA,PARCEL_USE",
                "returnGeometry": "true",
                "outSR": "4326",
                "f": "json"
            }
            
            try:
                resp = await loop.run_in_executor(
                    None, 
                    lambda: requests.post(base_url, data=params, timeout=10)
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    features = data.get("features", [])
                    
                    # 2. Map Parcels to Leads (Point in Polygon)
                    # Pre-process parcels into Shapely polygons
                    parcels = []
                    for f in features:
                        attr = f.get("attributes", {})
                        geom = f.get("geometry")
                        if geom and "rings" in geom:
                            try:
                                poly = Polygon(geom["rings"][0])
                                parcels.append((poly, attr))
                            except:
                                pass

                    # Check each lead against parcels
                    for lead in valid_leads:
                        pt = Point(lead["longitude"], lead["latitude"])
                        # Create a small buffer around the point (approx 11 meters) to catch leads near the boundary
                        pt_buffer = pt.buffer(0.0001) 
                        
                        for poly, attr in parcels:
                            if poly.intersects(pt_buffer):
                                # Match! Enrich.
                                print(f"  MATCHED PARCEL: {attr.get('PARCEL')} for lead {lead.get('address_street')}")
                                print(f"  PARCEL ATTRIBUTES: {json.dumps(attr, default=str)}")
                                
                                # Build mailing address
                                mail_parts = []
                                for k in range(1, 6):
                                    mail_val = attr.get(f"MAIL{k}")
                                    if mail_val and mail_val.strip():
                                        mail_parts.append(mail_val.strip())
                                m_zip = attr.get("ZIP")
                                if m_zip and str(m_zip) != "000000000":
                                    mail_parts.append(str(m_zip))
                                mailing_address = ", ".join(mail_parts)
                                
                                lead["owner_name"] = attr.get("MAIL1", "").title() if attr.get("MAIL1") else None
                                lead["mailing_address"] = mailing_address
                                if attr.get("PARCEL"):
                                    lead["parcel_id"] = attr.get("PARCEL")
                                lead["zoning"] = attr.get("CURZONE_OL")
                                lead["lot_size"] = attr.get("GISAREA")
                                lead["assessed_value"] = attr.get("FCV")
                                
                                # NOTE: Do NOT use m_zip (attr["ZIP"]) for address_zip here!
                                # That's the OWNER's mailing zip, not the property's physical zip.
                                # Property zip is set by _enrich_violations_with_zip_codes using GIS Layer 6.
                                
                                # Map PARCEL_USE to human-readable property type
                                parcel_use = str(attr.get("PARCEL_USE", "")) if attr.get("PARCEL_USE") else ""
                                lead["parcel_use_code"] = parcel_use  # Raw code for display
                                lead["property_type"] = self._map_parcel_use_to_type(parcel_use)
                                
                                # Check absentee
                                prop_street = (lead.get("address_street") or "").upper().strip()
                                if prop_street and mailing_address:
                                    if prop_street not in mailing_address.upper():
                                        if "Absentee Owner" not in lead.get("distress_signals", []):
                                            lead["distress_signals"].append("Absentee Owner")
                                
                                # Mark as enriched to skip duplicate enrichment
                                lead["_parcel_enriched"] = True
                                enriched_count += 1
                                break # Found the parcel for this lead
            except Exception as e:
                print(f"Batch enrichment error: {e}")
                
        elapsed = time.time() - start_time
        print(f"Enriched {enriched_count}/{len(leads)} violations with parcel data ({elapsed:.2f}s)")

    async def _enrich_violations_with_zip_codes(self, leads: List[Dict]):
        """
        Enriches code violation leads with proper zip codes using spatial queries.
        Uses bounding box of all leads to fetch ALL zip polygons in the area,
        then matches each lead point to the containing polygon.
        """
        print(f"[Scout] Starting zip code enrichment for {len(leads)} code violations...", flush=True)
        if not leads:
            return
            
        zip_layer_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/Addresses/MapServer/6/query"
        loop = asyncio.get_event_loop()
        
        # Calculate bounding box of all leads
        valid_leads = []
        min_lon, max_lon = float('inf'), float('-inf')
        min_lat, max_lat = float('inf'), float('-inf')
        
        for lead in leads:
            # Handle both coordinate formats
            lat = lead.get("latitude")
            lon = lead.get("longitude")
            
            # Fallback to geometry object if present
            if (lat is None or lon is None) and lead.get("geometry"):
                geom = lead.get("geometry")
                if isinstance(geom, dict):
                    lon = geom.get("x")
                    lat = geom.get("y")
            
            if lat and lon:
                # Ensure we have float values
                try:
                    lat = float(lat)
                    lon = float(lon)
                    # Store normalized coords on lead for easier access later
                    lead["_enrich_lat"] = lat
                    lead["_enrich_lon"] = lon
                    
                    valid_leads.append(lead)
                    min_lon = min(min_lon, lon)
                    max_lon = max(max_lon, lon)
                    min_lat = min(min_lat, lat)
                    max_lat = max(max_lat, lat)
                except (ValueError, TypeError):
                    pass
        
        if not valid_leads:
            print(f"[Scout] No valid leads with coordinates for zip enrichment")
            return
            
        # Build envelope with small buffer
        buffer = 0.01  # ~1km buffer
        envelope = {
            "xmin": min_lon - buffer,
            "ymin": min_lat - buffer,
            "xmax": max_lon + buffer,
            "ymax": max_lat + buffer,
            "spatialReference": {"wkid": 4326}
        }
        
        print(f"[Scout] Querying zip polygons for envelope: {min_lat:.4f},{min_lon:.4f} to {max_lat:.4f},{max_lon:.4f}")
        
        params = {
            "geometry": json.dumps(envelope),
            "geometryType": "esriGeometryEnvelope",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "ZIPCODE",
            "returnGeometry": "true",
            "outSR": "4326",  # Force WGS84 output
            "f": "json"
        }
        
        enriched_count = 0
        
        try:
            resp = await loop.run_in_executor(
                None,
                lambda: requests.post(zip_layer_url, data=params, timeout=15)
            )
            print(f"[Scout] Zip layer response status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                features = data.get("features", [])
                print(f"[Scout] Zip layer returned {len(features)} zip polygons for {len(valid_leads)} leads")
                
                if "error" in data:
                    print(f"[Scout] Zip layer error: {data['error']}")
                    return
                
                # Build list of (polygon, zipcode) tuples
                zip_polygons = []
                for f in features:
                    zipcode = f.get("attributes", {}).get("ZIPCODE")
                    geom = f.get("geometry")
                    if zipcode and geom and "rings" in geom:
                        try:
                            poly = Polygon(geom["rings"][0])
                            zip_polygons.append((poly, str(zipcode)[:5]))
                        except Exception as poly_err:
                            print(f"[Scout] Polygon creation error: {poly_err}")
                
                print(f"[Scout] Built {len(zip_polygons)} valid zip polygons: {[z[1] for z in zip_polygons]}")
                
                # Build spatial index for faster matching
                prepared_polys = [(zipcode, prep(poly), poly) for poly, zipcode in zip_polygons]
                
                enriched_count = 0
                debug_first_match = True
                
                for lead in valid_leads:
                    # Use the normalized coords we stored earlier
                    lat = lead.get("_enrich_lat")
                    lon = lead.get("_enrich_lon")
                    
                    if lat is None or lon is None:
                        continue
                        
                    pt = Point(lon, lat)
                    
                    # Debug first lead coordinates
                    if debug_first_match:
                        print(f"[Scout] Debug 1st lead: {lead.get('address', 'Unknown')} at {pt.x}, {pt.y}", flush=True)
                        # Log first polygon ring sample
                        if zip_polygons:
                            first_poly, first_zip = zip_polygons[0]
                            print(f"[Scout] Debug 1st poly ({first_zip}) bounds: {first_poly.bounds}", flush=True)
                    
                    match_found = False
                    for zipcode, prepared, poly in prepared_polys:
                        if prepared.contains(pt):
                            lead["address_zip"] = zipcode
                            # Reconstruct address with new zip
                            if lead.get("address_street") and lead.get("address_city") and lead.get("address_state"):
                                lead["address"] = f"{lead['address_street']}, {lead['address_city']}, {lead['address_state']} {zipcode}"
                            elif lead.get("address_street"):
                                # Fallback if city/state missing (common in violations)
                                lead["address"] = f"{lead['address_street']}, Tucson, AZ {zipcode}"
                            
                            enriched_count += 1
                            match_found = True
                            if debug_first_match:
                                print(f"[Scout] MATCHED! Lead at {pt.x},{pt.y} inside {zipcode}", flush=True)
                                debug_first_match = False
                            break
                    
                    if debug_first_match and not match_found:
                         print(f"[Scout] NO MATCH for 1st lead at {pt.x},{pt.y}. Checked {len(zip_polygons)} polys.", flush=True)
                         debug_first_match = False
                    
                    # Cleanup temporary fields
                    lead.pop("_enrich_lat", None)
                    lead.pop("_enrich_lon", None)
            else:
                print(f"[Scout] Zip layer HTTP error: {resp.status_code} - {resp.text[:200]}")
        except Exception as e:
            print(f"[Scout] Zip code enrichment error: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"Enriched {enriched_count}/{len(leads)} code violations with zip codes.")

    async def _filter_violations_by_property_type(self, leads: List[Dict], property_types: List[str]) -> List[Dict]:
        """
        Filters code violation leads by property type using BATCH spatial query.
        Uses property type cache to skip API calls for known leads.
        Returns leads that match the selected property types.
        """
        if not leads or not property_types:
            return leads
        
        # Skip filter if "all" is selected or list is empty
        if "all" in [t.lower() for t in property_types]:
            return leads
        
        # Get the PARCEL_USE prefixes for the selected types
        prefixes = self._get_codes_for_types(property_types)
        if not prefixes:
            return leads
        
        import time
        start_time = time.time()
        
        # Helper to normalize address for cache key
        def cache_key(lead):
            addr = lead.get("address_street") or lead.get("address", "")
            return " ".join(str(addr).upper().split()) if addr else None
        
        # Helper to check if PARCEL_USE code matches our property types
        def matches_type(use_code):
            return any(str(use_code).startswith(prefix) for prefix in prefixes)
        
        # Phase 1: Check cache for already-known property types
        cached_passes = []  # Leads that passed from cache
        needs_api = []  # Leads that need API lookup
        
        for lead in leads:
            lat = lead.get("latitude")
            lon = lead.get("longitude")
            if not (lat and lon):
                continue  # Skip leads without coords
            
            key = cache_key(lead)
            if key and key in self._property_type_cache:
                # We know this lead's property type from cache
                use_code = self._property_type_cache[key]
                if matches_type(use_code):
                    cached_passes.append(lead)
            else:
                needs_api.append(lead)
        
        cached_count = len(cached_passes)
        
        # If all leads are cached, skip API call entirely
        if not needs_api:
            elapsed = time.time() - start_time
            print(f"Property type filter: {cached_count}/{len(leads)} passed (all from cache, {elapsed:.2f}s)")
            return cached_passes
        
        print(f"Filtering {len(leads)} violations by property type: {property_types}...")
        print(f"  Cache: {cached_count} already known, {len(needs_api)} need API lookup")
        
        # Phase 2: Query API for uncached leads only
        base_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
        
        points = []
        for lead in needs_api:
            points.append([lead["longitude"], lead["latitude"]])
        
        multipoint = {
            "points": points,
            "spatialReference": {"wkid": 4326}
        }
        
        params = {
            "geometry": json.dumps(multipoint),
            "geometryType": "esriGeometryMultipoint",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "PARCEL_USE",  # Minimal fields for performance
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "json"
        }
        
        loop = asyncio.get_event_loop()
        api_passes = []
        
        try:
            resp = await loop.run_in_executor(
                None,
                lambda: requests.post(base_url, data=params, timeout=30)
            )
            
            if resp.status_code == 200:
                data = resp.json()
                features = data.get("features", [])
                
                # Build list of parcel polygons with their PARCEL_USE codes
                from shapely import STRtree
                parcels = []
                parcel_use_map = {}  # polygon id -> use code
                for f in features:
                    attr = f.get("attributes", {})
                    geom = f.get("geometry")
                    if geom and "rings" in geom:
                        try:
                            poly = Polygon(geom["rings"][0])
                            parcels.append(poly)
                            parcel_use_map[id(poly)] = attr.get("PARCEL_USE", "")
                        except:
                            pass
                
                # Create spatial index for fast lookup
                if parcels:
                    tree = STRtree(parcels)
                    
                    # Use spatial index to find matching parcel for each lead
                    for lead in needs_api:
                        pt = Point(lead["longitude"], lead["latitude"])
                        result = tree.query(pt)
                        for idx in result:
                            if parcels[idx].contains(pt):
                                parcel_use = parcel_use_map[id(parcels[idx])]
                                use_code = str(parcel_use) if parcel_use else ""
                                
                                # Save to cache for future searches
                                key = cache_key(lead)
                                if key:
                                    self._property_type_cache[key] = use_code
                                    lead["use_desc"] = use_code  # Also store on lead
                                
                                # Check if it matches our filter
                                if matches_type(use_code):
                                    api_passes.append(lead)
                                break  # Found matching parcel for this lead
            else:
                print(f"Property type filter API failed: {resp.status_code}")
        except Exception as e:
            print(f"Property type filter error: {e}")
        
        # Combine cached and API results
        all_passes = cached_passes + api_passes
        elapsed = time.time() - start_time
        print(f"Property type filter: {len(all_passes)}/{len(leads)} passed ({cached_count} cached, {len(api_passes)} new, {elapsed:.2f}s)")
        return all_passes


    async def _enrich_with_gis_layers(self, leads: List[Dict]):
        """
        Enriches leads with Zoning, Floodplain, and School District data using batch spatial queries.
        """
        if not leads:
            return

        # Check if leads already have GIS data from cache - skip entirely if so
        # A lead needs GIS enrichment if it's NOT cache-enriched OR doesn't have any GIS data yet
        gis_fields = ["flood_zone", "school_district", "zoning"]
        
        def needs_gis(lead):
            """Returns True if lead needs GIS enrichment."""
            # Only skip if lead has ALL GIS fields from cache (not just some)
            if lead.get("_cache_enriched") and all(lead.get(f) for f in gis_fields):
                return False  # Already has ALL GIS data from cache
            return True
        
        needs_enrichment = [l for l in leads if needs_gis(l)]
        
        if not needs_enrichment:
            print(f"GIS Layers: All {len(leads)} leads already have GIS data from cache (skipping)")
            return
        
        if len(needs_enrichment) < len(leads):
            print(f"GIS Layers: {len(leads) - len(needs_enrichment)}/{len(leads)} already enriched from cache")
        
        print(f"Enriching {len(needs_enrichment)} leads with Advanced GIS Layers...")
        
        # Define layers to query
        # Format: (Name, Service URL, Fields, Attribute Map, FetchAll)
        # FetchAll=True means fetch all polygons with 1=1 (for small layers like school districts)
        layers = [
            (
                "Zoning",
                "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/OverlayZoningBase/MapServer/1/query",
                "ZONE_CLASS,MUNICIPALITY",
                {"zoning": "ZONE_CLASS", "municipality": "MUNICIPALITY"},
                False  # Use multipoint intersection
            ),
            (
                "Floodplain",
                "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/FloodControl2/MapServer/8/query",
                "ZONE",
                {"flood_zone": "ZONE"},
                False  # Use multipoint intersection
            ),
            (
                "School District",
                "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/Community2/MapServer/14/query",
                "SDISTNAME",
                {"school_district": "SDISTNAME"},
                True  # Fetch ALL (only 18 districts, multipoint fragments polygons)
            ),
            (
                "Path of Progress",
                "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/OverlayDevelopment/MapServer/13/query",
                "PLAT_NAME,STATUS",
                {"nearby_development": "PLAT_NAME", "development_status": "STATUS"},
                False  # Use multipoint intersection
            ),
            (
                "Neighborhoods",
                "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/15/query",
                "SUB_NAME",
                {"neighborhoods": "SUB_NAME"},
                False  # Use multipoint intersection
            )
        ]
        
        loop = asyncio.get_event_loop()
        batch_size = 50
        
        for name, url, fields, attr_map, fetch_all in layers:
            print(f"  Querying GIS layer: {name}...")
            
            # For fetchAll layers, query once for all polygons, then match all leads
            if fetch_all:
                params = {
                    "where": "1=1",  # Get ALL features
                    "outFields": fields,
                    "returnGeometry": "true",
                    "outSR": "4326",
                    "f": "json"
                }
                try:
                    resp = await loop.run_in_executor(
                        None,
                        lambda: requests.get(url, params=params, timeout=20)
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        features = data.get("features", [])
                        polys = []
                        for f in features:
                            attr = f.get("attributes", {})
                            geom = f.get("geometry")
                            if geom and "rings" in geom:
                                try:
                                    rings = geom["rings"]
                                    poly = None
                                    
                                    # Try each ring until we get a valid polygon
                                    for ring in rings:
                                        try:
                                            test_poly = Polygon(ring)
                                            # Use buffer(0) to fix self-intersecting polygons
                                            if not test_poly.is_valid:
                                                test_poly = test_poly.buffer(0)
                                            if test_poly.is_valid and test_poly.area > 0.0001:  # Min area threshold
                                                if poly is None or test_poly.area > poly.area:
                                                    poly = test_poly
                                        except:
                                            continue
                                    
                                    if poly is not None:
                                        polys.append((poly, attr))
                                except Exception as e:
                                    pass
                        
                        if polys:
                            enriched_count = 0
                            for lead in leads:
                                lat = lead.get("latitude")
                                lon = lead.get("longitude")
                                if lat and lon:
                                    pt = Point(lon, lat)
                                    for poly, attr in polys:
                                        if poly.contains(pt):
                                            for lead_key, attr_key in attr_map.items():
                                                val = attr.get(attr_key)
                                                if val:
                                                    lead[lead_key] = val
                                                    enriched_count += 1
                                            break
                            print(f"    {name}: {len(polys)} polygons, {enriched_count} leads enriched (fetchAll)")
                            # Debug: if 0 enriched, print sample point and all polygon names
                            if enriched_count == 0 and leads:
                                sample_lead = leads[0]
                                print(f"      Sample point: ({sample_lead.get('longitude', 0):.6f}, {sample_lead.get('latitude', 0):.6f})")
                                # Show which polygons we have and if point is contained
                                for idx, (poly, attr) in enumerate(polys):
                                    dist_name = attr.get("SDISTNAME", "Unknown")
                                    bounds = poly.bounds
                                    pt = Point(sample_lead.get('longitude', 0), sample_lead.get('latitude', 0))
                                    contains = poly.contains(pt)
                                    print(f"        {idx}: {dist_name[:30]} contains={contains}")
                        else:
                            print(f"    {name}: 0 polygons returned (fetchAll)")
                except Exception as e:
                    print(f"  Error querying {name}: {e}")
                continue  # Skip to next layer
            
            # Normal multipoint intersection for other layers
            for i in range(0, len(leads), batch_size):
                batch = leads[i:i + batch_size]
                
                points = []
                valid_leads = []
                for lead in batch:
                    lat = lead.get("latitude")
                    lon = lead.get("longitude")
                    if lat and lon:
                        points.append([lon, lat])
                        valid_leads.append(lead)
                
                if not points:
                    continue
                    
                multipoint = {
                    "points": points,
                    "spatialReference": {"wkid": 4326}
                }
                
                params = {
                    "geometry": json.dumps(multipoint),
                    "geometryType": "esriGeometryMultipoint",
                    "spatialRel": "esriSpatialRelIntersects",
                    "inSR": "4326",  # Input spatial reference (our points are WGS84)
                    "outFields": fields,
                    "returnGeometry": "true",
                    "outSR": "4326",  # Output spatial reference (want WGS84 back)
                    "f": "json"
                }
                
                try:
                    resp = await loop.run_in_executor(
                        None, 
                        lambda: requests.post(url, data=params, timeout=20)  # Increased from 10s
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        features = data.get("features", [])
                        
                        # Map features to leads
                        # Pre-process polygons
                        polys = []
                        for f in features:
                            attr = f.get("attributes", {})
                            geom = f.get("geometry")
                            if geom and "rings" in geom:
                                try:
                                    poly = Polygon(geom["rings"][0])
                                    polys.append((poly, attr))
                                except:
                                    pass
                        
                        # Debug: show how many polygons were returned
                        if not polys:
                            print(f"    {name}: 0 polygons returned (batch {i//batch_size + 1})")
                        
                        enriched_count = 0
                        for lead in valid_leads:
                            pt = Point(lead["longitude"], lead["latitude"])
                            for poly, attr in polys:
                                if poly.contains(pt):
                                    # Match! Update lead with mapped attributes
                                    for lead_key, attr_key in attr_map.items():
                                        val = attr.get(attr_key)
                                        if val:
                                            lead[lead_key] = val
                                            enriched_count += 1
                                    break
                        
                        if polys and enriched_count > 0:
                            print(f"    {name}: {len(polys)} polygons, {enriched_count} leads enriched (batch {i//batch_size + 1})")
                        elif polys and enriched_count == 0:
                            # Polygons returned but no points matched - debug coordinate mismatch
                            sample_poly = polys[0][0]
                            sample_pt = valid_leads[0] if valid_leads else None
                            bounds = sample_poly.bounds  # (minx, miny, maxx, maxy)
                            print(f"    {name}: {len(polys)} polygons BUT 0 points matched (batch {i//batch_size + 1})")
                            print(f"      Polygon bounds: ({bounds[0]:.2f}, {bounds[1]:.2f}) - ({bounds[2]:.2f}, {bounds[3]:.2f})")
                            if sample_pt:
                                print(f"      Sample point: ({sample_pt['longitude']:.6f}, {sample_pt['latitude']:.6f})")
                    else:
                        print(f"    {name}: API returned {resp.status_code}")
                except Exception as e:
                    print(f"  Error querying {name}: {e}")
        
        print(f"GIS Layers enrichment complete for {len(leads)} leads.")

    async def _enrich_with_homeharvest(self, leads: List[Dict]):
        """
        Enriches leads with property details (beds, baths, sqft, year_built, sold_price)
        using the HomeHarvest library.
        """
        if not leads:
            return

        print(f"Enriching {len(leads)} leads with HomeHarvest data...")
        
        try:
            from homeharvest import scrape_property
            import pandas as pd
            
            # Collect addresses with indices for reliable matching
            address_leads = []  # List of (index, address, lead) tuples
            
            for i, lead in enumerate(leads):
                # Construct search address
                addr = lead.get("address")
                if not addr:
                    street = lead.get("address_street")
                    zip_code = lead.get("address_zip")
                    if street:
                        addr = f"{street}, Tucson, AZ"
                        if zip_code:
                            addr += f" {zip_code}"
                
                # Ensure City/State is present for GIS addresses (which are usually just street)
                if addr and "AZ" not in addr.upper() and "ARIZONA" not in addr.upper():
                    addr = f"{addr}, Tucson, AZ"
                
                # Normalize AV -> Ave for better matching
                if addr:
                    addr = addr.replace(" AV,", " Ave,").replace(" ST,", " St,").replace(" RD,", " Rd,").replace(" DR,", " Dr,")

                if addr:
                    address_leads.append((i, addr, lead))

            if not address_leads:
                return

            loop = asyncio.get_event_loop()
            
            # Helper to normalize address for cache key
            def normalize_addr(addr):
                return addr.upper().split(",")[0].strip()
            
            # Check cache first and separate cached/uncached
            uncached_leads = []
            cache_hits = 0
            
            for idx, addr, lead_obj in address_leads:
                cache_key = normalize_addr(addr)
                if cache_key in self._homeharvest_cache:
                    cached_data = self._homeharvest_cache[cache_key]
                    if cached_data:
                        # Apply cached data to lead
                        self._apply_homeharvest_data(lead_obj, cached_data)
                        cache_hits += 1
                else:
                    uncached_leads.append((idx, addr, lead_obj, cache_key))
            
            if cache_hits > 0:
                print(f"  HomeHarvest: {cache_hits} from cache, {len(uncached_leads)} to fetch")
            
            if not uncached_leads:
                print(f"HomeHarvest: {cache_hits} enriched from cache (0 API calls needed)")
                return
            
            async def fetch_hh(address, cache_key):
                try:
                    print(f"  Fetching HomeHarvest for: '{address}'")
                    # Run in executor to avoid blocking
                    df = await asyncio.wait_for(
                        loop.run_in_executor(
                            None,
                            lambda: scrape_property(
                                location=address,
                                listing_type="sold",
                                past_days=365
                            )
                        ),
                        timeout=30.0  # Increased to 30s
                    )
                    if not df.empty:
                        # Sanitize DataFrame: Replace NaN/Inf with None
                        df = df.replace({np.nan: None, np.inf: None, -np.inf: None})
                        data = df.iloc[0].to_dict()
                        # Store in cache
                        self._homeharvest_cache[cache_key] = data
                        return data
                except asyncio.TimeoutError:
                    pass
                except Exception as e:
                    print(f"  HomeHarvest Error for '{address}': {e}")
                
                # Cache the "not found" result too to avoid re-fetching
                self._homeharvest_cache[cache_key] = None
                return None

            sem = asyncio.Semaphore(10) # Higher concurrency to get more results in time window
            
            async def safe_fetch(idx, addr, lead_obj, cache_key):
                async with sem:
                    data = await fetch_hh(addr, cache_key)
                    return (idx, data, lead_obj)

            tasks = [asyncio.create_task(safe_fetch(idx, addr, lead, cache_key)) for idx, addr, lead, cache_key in uncached_leads]
            
            # Global timeout for all enrichment: 60 seconds
            # Use asyncio.wait to get partial results
            done, pending = await asyncio.wait(tasks, timeout=60.0)
            
            for task in pending:
                task.cancel()
            
            enriched_count = 0
            empty_count = 0
            timeout_count = len(pending)
            
            for task in done:
                try:
                    idx, data, lead = await task
                    if data:
                        # Apply data using shared helper
                        self._apply_homeharvest_data(lead, data)
                        enriched_count += 1
                    else:
                        empty_count += 1
                except Exception:
                    pass
            
            total_enriched = enriched_count + cache_hits
            print(f"HomeHarvest: {total_enriched} enriched ({cache_hits} cached, {enriched_count} new), {empty_count} empty, {timeout_count} timed out (of {len(leads)} leads)")

        except ImportError:
            print("HomeHarvest not installed. Skipping enrichment.")
        except Exception as e:
            print(f"HomeHarvest Error: {e}")

    def _apply_homeharvest_data(self, lead: Dict, data: Dict):
        """Apply HomeHarvest data to a lead object."""
        # Basic property details
        lead["beds"] = data.get("beds")
        lead["baths"] = data.get("full_baths")
        lead["half_baths"] = data.get("half_baths")
        lead["sqft"] = data.get("sqft")
        lead["year_built"] = data.get("year_built")
        lead["lot_sqft"] = data.get("lot_sqft")
        lead["stories"] = data.get("stories")
        
        # Value and sale info
        lead["estimated_value"] = data.get("estimated_value") or data.get("estimate") or data.get("price")
        lead["last_sold_date"] = data.get("last_sold_date")
        lead["last_sold_price"] = data.get("sold_price")
        lead["price_per_sqft"] = data.get("price_per_sqft")
        lead["hoa_fee"] = data.get("hoa_fee")
        
        # Location and photos
        lead["neighborhoods"] = data.get("neighborhoods")
        lead["property_url"] = data.get("property_url")
        lead["primary_photo"] = data.get("primary_photo")
        lead["alt_photos"] = data.get("alt_photos")
        
        # Parking and description
        lead["parking_garage"] = data.get("parking_garage")
        lead["description"] = data.get("text")

    async def fetch_comps(self, address: str, radius: float = 1.0, past_days: int = 180) -> List[Dict]:
        """
        Fetches comparable sales (comps) using Redfin (best for sold data).
        """
        print(f"Fetching comps for {address} via Redfin...")
        try:
            from homeharvest import scrape_property
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: scrape_property(
                    location=address,
                    radius=radius,
                    listing_type="sold",
                    past_days=past_days
                )
            )
            
            if df.empty:
                return []
                
            return df.to_dict("records")
            
        except Exception as e:
            print(f"Error fetching comps: {e}")
            return []

    async def fetch_fsbo(self, location: str) -> List[Dict]:
        """
        Searches for FSBO (For Sale By Owner) listings using Zillow (best for off-market).
        """
        print(f"Searching FSBO in {location} via Zillow...")
        try:
            from homeharvest import scrape_property
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: scrape_property(
                    location=location,
                    listing_type="for_sale"  # We want active FSBOs
                )
            )
            
            if df.empty:
                return []
                
            # Filter for likely FSBOs if possible, or just return all found
            # HomeHarvest might not explicitly flag FSBO in all versions, 
            # but Zillow source is the best bet.
            return df.to_dict("records")
            
        except Exception as e:
            print(f"Error fetching FSBO: {e}")
            return []
    
    def _apply_homeharvest_from_cache(self, leads: List[Dict]) -> int:
        """Apply cached HomeHarvest data to leads without making any API calls.
        Returns the number of leads enriched from cache."""
        if not leads:
            return 0
        
        applied_count = 0
        
        def normalize_addr(addr):
            return addr.upper().split(",")[0].strip() if addr else ""
        
        for lead in leads:
            # Skip leads already enriched (e.g., from previous full enrichment this session)
            if lead.get("beds") or lead.get("sqft") or lead.get("primary_photo"):
                continue
                
            address = lead.get("address") or lead.get("full_address") or ""
            if not address:
                continue
            
            cache_key = normalize_addr(address)
            if cache_key in self._homeharvest_cache:
                cached_data = self._homeharvest_cache[cache_key]
                if cached_data:
                    self._apply_homeharvest_data(lead, cached_data)
                    applied_count += 1
        
        return applied_count
    
    def _apply_cached_enrichment(self, leads: List[Dict]) -> int:
        """Apply ALL cached enrichment data (parcel, GIS, HomeHarvest) to leads.
        Returns number of leads enriched from cache.
        Uses normalized street address as cache key (consistent before/after enrichment)."""
        if not leads:
            return 0
        
        applied_count = 0
        leads_with_addr = 0
        
        for lead in leads:
            # Use normalized street address as cache key (consistent before/after parcel enrichment)
            addr = lead.get("address_street") or lead.get("address", "")
            if not addr:
                continue
            
            leads_with_addr += 1
            # Normalize: uppercase, remove extra spaces
            cache_key = " ".join(str(addr).upper().split())
            if cache_key in self._lead_cache:
                cached = self._lead_cache[cache_key]
                # Apply all cached enrichment fields
                for field in self._enrichment_fields:
                    if field in cached and cached[field] is not None:
                        lead[field] = cached[field]
                # Mark as cache-enriched for debug
                lead["_cache_enriched"] = True
                applied_count += 1
        
        # Debug: show cache stats
        if len(leads) > 0:
            sample = leads[0]
            sample_addr = sample.get("address_street") or sample.get("address", "")
            print(f"  Cache debug: {leads_with_addr}/{len(leads)} have addresses, cache has {len(self._lead_cache)} entries, matched {applied_count}")
            if sample_addr and applied_count == 0 and len(self._lead_cache) > 0:
                sample_key = " ".join(str(sample_addr).upper().split())
                print(f"  Sample addr: '{sample_key}', in cache: {sample_key in self._lead_cache}")
        
        return applied_count
    
    def _save_to_lead_cache(self, leads: List[Dict]) -> int:
        """Save enriched leads to cache for future searches.
        Uses normalized street address as cache key (consistent before/after enrichment).
        Returns number of leads saved to cache."""
        if not leads:
            return 0
        
        saved_count = 0
        
        for lead in leads:
            # Use normalized street address as cache key
            addr = lead.get("address_street") or lead.get("address", "")
            if not addr:
                continue
            
            # Normalize: uppercase, remove extra spaces
            cache_key = " ".join(str(addr).upper().split())
            
            # Check if lead has any enrichment data worth caching
            has_enrichment = any(lead.get(field) for field in self._enrichment_fields)
            if not has_enrichment:
                continue
            
            # Update or create cache entry with all enrichment fields
            if cache_key not in self._lead_cache:
                self._lead_cache[cache_key] = {}
            
            for field in self._enrichment_fields:
                if field in lead and lead[field] is not None:
                    self._lead_cache[cache_key][field] = lead[field]
            
            saved_count += 1
        
        return saved_count

    async def _check_tax_delinquency(self, leads: List[Dict]):
        """
        Checks tax delinquency status for leads using Playwright to scrape paypimagov.com.
        Adds 'tax_status' and 'tax_link' fields.
        """
        if not leads:
            return

        print(f"Checking tax status for {len(leads)} leads...")
        
        # Filter leads with parcel IDs
        valid_leads = [l for l in leads if l.get("parcel_id")]
        if not valid_leads:
            return

        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                
                # Process in small batches to avoid overwhelming the browser/site
                batch_size = 5
                for i in range(0, len(valid_leads), batch_size):
                    batch = valid_leads[i:i + batch_size]
                    
                    for lead in batch:
                        parcel_id = lead["parcel_id"]
                        url = f"https://paypimagov.com/#/WildfireSearch/{parcel_id}"
                        lead["tax_link"] = url
                        
                        try:
                            page = await context.new_page()
                            await page.goto("https://paypimagov.com/", timeout=15000)
                            
                            # Handle modal if present
                            try:
                                close_btn = page.locator("button[aria-label='Close']")
                                if await close_btn.is_visible(timeout=2000):
                                    await close_btn.click()
                            except:
                                pass
                                
                            # Search
                            await page.fill("#searchBox", parcel_id)
                            await page.press("#searchBox", "Enter")
                            
                            # Wait for results
                            try:
                                await page.wait_for_selector(".searchResults tbody tr, .alert-warning", timeout=5000)
                                
                                content = await page.content()
                                if "No Records Found" in content:
                                    lead["tax_status"] = "Current"
                                else:
                                    # Check rows for "Total Due"
                                    rows = await page.locator(".searchResults tbody tr").all()
                                    is_delinquent = False
                                    for row in rows:
                                        text = await row.inner_text()
                                        if "Total Due" in text or "Delinquent" in text:
                                            is_delinquent = True
                                            break
                                    
                                    lead["tax_status"] = "Delinquent" if is_delinquent else "Current"
                                    if is_delinquent:
                                        if "Unpaid Taxes" not in lead.get("distress_signals", []):
                                            lead["distress_signals"].append("Unpaid Taxes")
                                            
                            except Exception:
                                lead["tax_status"] = "Unknown"
                                
                            await page.close()
                            
                        except Exception as e:
                            print(f"Tax check error for {parcel_id}: {e}")
                            lead["tax_status"] = "Error"
                            
                await browser.close()
                
        except ImportError:
            print("Playwright not installed. Skipping tax check.")
        except Exception as e:
            print(f"Tax check pipeline error: {e}")

    def _is_absentee(self, lead: Dict) -> bool:
        """Quick in-memory check if property is absentee-owned."""
        prop_street = (lead.get("address_street") or "").upper().strip()
        mail_addr = (lead.get("mailing_address") or "").upper().strip()
        
        if not prop_street or not mail_addr:
            return False
        
        return prop_street not in mail_addr

    def _normalize_address(self, address: str) -> str:
        """Normalize address for matching (Ave->AV, Street->ST, etc.)"""
        if not address:
            return ""
        addr = address.upper().strip()
        # Common abbreviations
        replacements = [
            (" AVENUE", " AV"), (" AVE", " AV"), (" STREET", " ST"), (" STR", " ST"),
            (" DRIVE", " DR"), (" BOULEVARD", " BLVD"), (" ROAD", " RD"),
            (" LANE", " LN"), (" COURT", " CT"), (" CIRCLE", " CIR"),
            (" PLACE", " PL"), (" NORTH", " N"), (" SOUTH", " S"),
            (" EAST", " E"), (" WEST", " W"), ("  ", " ")
        ]
        for old, new in replacements:
            addr = addr.replace(old, new)
        # Remove unit/apt info
        for sep in [" #", " APT", " UNIT", " STE"]:
            if sep in addr:
                addr = addr.split(sep)[0].strip()
        return addr.strip()

    async def _fetch_by_address(self, address: str, filters: Dict) -> List[Dict]:
        """
        Pure address lookup - fetches a single parcel by address search.
        Bypasses distress filters for direct property lookup.
        """
        print(f"Pure Address Lookup: Searching for '{address}'...")
        
        # Normalize the search address
        search_term = self._normalize_address(address)
        # Extract just street number and name (without city/state/zip)
        if "," in search_term:
            search_term = search_term.split(",")[0].strip()
        
        print(f"  Normalized search term: '{search_term}'")
        
        base_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
        
        # Try multiple search strategies
        search_strategies = [
            f"ADDRESS_OL LIKE '%{search_term}%'",  # Full match
            f"SITUS_FULL LIKE '%{search_term}%'",  # Alternative field
        ]
        
        # Also try just the street number and first word of street name
        parts = search_term.split()
        if len(parts) >= 2 and parts[0].isdigit():
            street_num = parts[0]
            street_name = parts[-1] if len(parts) > 2 else parts[1]
            search_strategies.append(f"ADDRESS_OL LIKE '{street_num}%{street_name}%'")
        
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        
        out_fields = "OBJECTID,PARCEL_ID,ADDRESS_OL,SITUS_FULL,OWNER_OL,MAIL_ADDR,MAIL_CITY,MAIL_STATE,MAIL_ZIP,PARCEL_USE,JURIS_OL,FULL_VALUE,TOTAL_ACRES"
        
        for where in search_strategies:
            try:
                params = {
                    "where": where,
                    "outFields": out_fields,
                    "returnGeometry": "true",
                    "outSR": "4326",
                    "f": "json",
                    "resultRecordCount": 10
                }
                
                loop = asyncio.get_event_loop()
                resp = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: requests.post(base_url, data=params, headers=headers, timeout=15)),
                    timeout=20.0
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    features = data.get("features", [])
                    
                    if features:
                        print(f"  Found {len(features)} matches with strategy: {where[:50]}...")
                        
                        results = []
                        for feat in features:
                            attr = feat.get("attributes", {})
                            geom = feat.get("geometry", {})
                            
                            # Build mailing address
                            mail_parts = [
                                attr.get("MAIL_ADDR", ""),
                                attr.get("MAIL_CITY", ""),
                                attr.get("MAIL_STATE", ""),
                                str(attr.get("MAIL_ZIP", ""))[:5]
                            ]
                            mailing_address = ", ".join([p for p in mail_parts if p and p.strip()])
                            
                            # Get coordinates
                            lat = geom.get("y") if geom else None
                            lon = geom.get("x") if geom else None
                            
                            # Get address
                            address_full = attr.get("ADDRESS_OL") or attr.get("SITUS_FULL") or ""
                            
                            lead = {
                                "id": f"parcel_{attr.get('OBJECTID', '')}",
                                "parcel_id": attr.get("PARCEL_ID", ""),
                                "address": address_full,
                                "address_street": address_full.split(",")[0] if "," in address_full else address_full,
                                "owner_name": attr.get("OWNER_OL", ""),
                                "mailing_address": mailing_address,
                                "assessed_value": attr.get("FULL_VALUE"),
                                "lot_size": (attr.get("TOTAL_ACRES") or 0) * 43560,  # Convert acres to sqft
                                "property_type": self._get_property_type_name(attr.get("PARCEL_USE", "")),
                                "latitude": lat,
                                "longitude": lon,
                                "distress_signals": [],
                                "source": "Address Lookup"
                            }
                            
                            # Check if absentee owner
                            if self._is_absentee(lead):
                                lead["distress_signals"].append("Absentee Owner")
                            
                            results.append(lead)
                        
                        # Apply property type filter if specified
                        property_types = filters.get("property_types")
                        if property_types and results:
                            normalized_types = [t.lower() for t in property_types]
                            results = [r for r in results if r.get("property_type", "").lower() in normalized_types or "all" in normalized_types or "single family" in normalized_types]
                        
                        return results
                        
            except Exception as e:
                print(f"  Address search strategy failed: {e}")
                continue
        
        print(f"  No results found for address '{address}'")
        return []

    async def _fetch_primary(self, filter_type: str, filters: Dict, limit: int) -> List[Dict]:
        """Fetches leads from the primary (most restrictive) filter source."""
        county = filters.get("county") or "Pima"  # Handle None explicitly
        
        if filter_type == "Code Violations":
            if county.lower() == "pima":
                return await self._fetch_code_violations(filters, limit)
            return []
            
        elif filter_type == "Absentee Owner":
            return await self._fetch_absentee_owners(filters, limit)
            
        elif filter_type in ["Liens (HOA, Mechanics)", "Pre-Foreclosure", "Divorce", "Judgements", "Tax Liens", "Probate", "Evictions"]:
            return await self._fetch_recorder_data(filter_type, limit)
            
        return []

    async def _verify_filter(self, candidates: List[Dict], filter_type: str, filters: Dict) -> List[Dict]:
        """Verifies candidates against a secondary filter (AND logic)."""
        
        if filter_type == "Absentee Owner":
            # In-memory check: mailing address != property address
            verified = []
            for c in candidates:
                if self._is_absentee(c):
                    if "Absentee Owner" not in c.get("distress_signals", []):
                        c["distress_signals"].append("Absentee Owner")
                    verified.append(c)
            print(f"AND filter '{filter_type}': {len(verified)}/{len(candidates)} passed")
            return verified
        
        elif filter_type == "Code Violations":
            # Check if addresses have violations (lookup)
            # For now, use address-based lookup against violations
            violations = await self._fetch_code_violations(filters, limit=500)
            violation_streets = set()
            for v in violations:
                street = v.get("address_street", "").upper().strip()
                if street:
                    violation_streets.add(street)
            
            verified = []
            for c in candidates:
                street = c.get("address_street", "").upper().strip()
                if street in violation_streets:
                    if "Code Violation" not in c.get("distress_signals", []):
                        c["distress_signals"].append("Code Violation")
                    # Merge violation data
                    for v in violations:
                        if v.get("address_street", "").upper().strip() == street:
                            c["violation_description"] = v.get("violation_description")
                            break
                    verified.append(c)
            print(f"AND filter '{filter_type}': {len(verified)}/{len(candidates)} passed")
            return verified
        
        # For other filter types (recorder data), would need similar lookup
        # For now, pass through
        return candidates

    async def fetch_leads(self, filters: Dict) -> List[Dict]:
        try:

            limit = filters.get("limit", 100)
            county = filters.get("county")
            if not county:
                county = "Pima"
            
            print(f"Scout fetching leads with filters: {filters}")
            
            # ===== PURE ADDRESS LOOKUP =====
            # If address is provided without zip/bounds, use direct parcel lookup
            address_query = filters.get("address")
            zip_code = filters.get("zip_code")
            bounds = filters.get("bounds")
            distress_types = filters.get("distress_type") or []
            
            # If we have an address but no zip/bounds and no/empty distress types, do direct parcel lookup
            if address_query and not zip_code and not bounds:
                print(f"Using direct parcel lookup for address: '{address_query}'")
                
                # For address-only search, only bypass property type filter if NO types are selected
                # If user selected specific types, respect their selection
                address_filters = {**filters}
                selected_types = filters.get("property_types") or []
                if not selected_types or "all" in [t.lower() for t in selected_types]:
                    # No types selected or "all" - bypass filter to find any property
                    address_filters.pop("property_types", None)
                # Otherwise keep property_types in address_filters
                
                # Use existing parcel fetch which has address filtering built-in
                candidates = await self._fetch_pima_parcels(address_filters, limit=20, offset=0)
                
                if candidates:
                    print(f"  Found {len(candidates)} parcels matching address")
                    
                    # Check for absentee owner status on each
                    for lead in candidates:
                        if self._is_absentee(lead):
                            if "distress_signals" not in lead:
                                lead["distress_signals"] = []
                            if "Absentee Owner" not in lead["distress_signals"]:
                                lead["distress_signals"].append("Absentee Owner")
                    
                    # Run enrichment on found properties
                    hh_task = asyncio.create_task(self._enrich_with_homeharvest(candidates))
                    gis_task = asyncio.create_task(self._enrich_with_gis_layers(candidates))
                    
                    try:
                        await asyncio.wait_for(
                            asyncio.gather(hh_task, gis_task, return_exceptions=True),
                            timeout=20.0
                        )
                    except asyncio.TimeoutError:
                        print("Enrichment timed out, returning partial results")
                        hh_task.cancel()
                        gis_task.cancel()
                    
                    return candidates[:limit]
                else:
                    print(f"No parcels found for address '{address_query}'")
            
            
            
            # Get distress types
            distress_types = filters.get("distress_type")
            if isinstance(distress_types, str):
                distress_types = [distress_types]
            
            candidates = []
            selected = []  # Initialize to avoid UnboundLocalError for generic searches
            primary = None  # Initialize to avoid UnboundLocalError for generic searches
            
            # If "all" or empty, use generic parcel search
            if not distress_types or "all" in distress_types:
                target_raw = int(limit * 1.5)
                if county and county.lower() == "pinal":
                    candidates = await self._fetch_pinal_parcels(filters, 200, 0)
                else:
                    candidates = await self._fetch_pima_parcels(filters, limit=target_raw, offset=0)
                
                # Verify we have candidates
                if not candidates:
                    print("Generic search returned no candidates.")
                    return []

            else:
                # ========== AND-LOGIC ARCHITECTURE ==========
                # Sort selected filters by priority (most restrictive first)
                selected = [f for f in self.FILTER_PRIORITY if f in distress_types]
                
                if not selected:
                    # Fallback to generic search if no recognized filters
                    candidates = await self._fetch_pima_parcels(filters, limit=limit, offset=0)
                else:
                    print(f"AND-Logic: Selected filters: {selected}")
            
            if selected:
                # Step 1: Fetch from PRIMARY (most restrictive) source
                primary = selected[0]
                
                # HYBRID FETCH STRATEGY: Dynamic multiplier + Progressive fetch
                property_types = filters.get("property_types") or []
                base_multiplier = self._estimate_fetch_multiplier(property_types)
                fetch_limit = limit * base_multiplier
                max_fetch_limit = 2000  # Safety cap
                
                print(f"AND-Logic: Fetching from primary source '{primary}' with initial limit {fetch_limit} (multiplier: {base_multiplier}x)")
                
                candidates = await self._fetch_primary(primary, filters, min(fetch_limit, max_fetch_limit))
                print(f"AND-Logic: Got {len(candidates)} candidates from primary source")
                
                # Step 1.5: Apply Property Type Filter (for Code Violations)
                if property_types and primary == "Code Violations":
                    # Code Violations come unenriched, filter by property type first
                    filtered_candidates = await self._filter_violations_by_property_type(candidates, property_types)
                    print(f"AND-Logic: After property type filter: {len(filtered_candidates)} candidates")
                    
                    # PROGRESSIVE FETCH: If not enough results, fetch more and try again
                    fetch_attempts = 0
                    while len(filtered_candidates) < limit and fetch_attempts < 3:
                        current_count = len(candidates)
                        additional_needed = (limit - len(filtered_candidates)) * base_multiplier
                        new_fetch_limit = min(current_count + int(additional_needed), max_fetch_limit)
                        
                        if new_fetch_limit <= current_count:
                            print(f"AND-Logic: Reached max fetch limit, cannot fetch more")
                            break
                        
                        fetch_attempts += 1
                        print(f"AND-Logic: Progressive fetch #{fetch_attempts}: need {limit - len(filtered_candidates)} more, fetching up to {new_fetch_limit}")
                        
                        # Fetch more candidates
                        candidates = await self._fetch_primary(primary, filters, new_fetch_limit)
                        filtered_candidates = await self._filter_violations_by_property_type(candidates, property_types)
                        print(f"AND-Logic: After progressive fetch: {len(filtered_candidates)} candidates")
                    
                    candidates = filtered_candidates
                
                # Step 1.75: Early parcel enrichment if Absentee Owner is a secondary filter
                # (Absentee check needs mailing_address which comes from parcel data)
                if "Absentee Owner" in selected[1:] and primary == "Code Violations":
                    # OPTIMIZATION: Apply cache FIRST to avoid redundant parcel API calls
                    early_cache_hits = self._apply_cached_enrichment(candidates)
                    if early_cache_hits > 0:
                        print(f"AND-Logic: Applied cache to {early_cache_hits}/{len(candidates)} candidates (before Absentee check)")
                    
                    # Only enrich candidates that don't have mailing_address from cache
                    needs_parcel = [c for c in candidates if not c.get("mailing_address")]
                    if needs_parcel:
                        print(f"AND-Logic: Early parcel enrichment for {len(needs_parcel)}/{len(candidates)} candidates...")
                        await self._enrich_violations_with_parcel_data(needs_parcel)
                        
                        # CRITICAL: Save enriched candidates to cache for faster subsequent searches
                        saved = self._save_to_lead_cache(candidates)
                        print(f"AND-Logic: Saved {saved} candidates to cache (for faster future searches)")
                    else:
                        print(f"AND-Logic: Skipping early parcel enrichment ({early_cache_hits} have mailing_address from cache)")
                
                # Step 2: Verify against SECONDARY filters (AND logic)
                for secondary in selected[1:]:
                    print(f"AND-Logic: Verifying against secondary filter '{secondary}'")
                    candidates = await self._verify_filter(candidates, secondary, filters)
                    
                    # Early exit if no candidates left
                    if not candidates:
                        print(f"AND-Logic: No candidates passed '{secondary}' filter")
                        break
            
            # SAFETY NET: Enforce Map Bounds (Client-Side)
            # This catches any results that slipped through due to strategy fallbacks or missing spatial filters
            # (Fixes Absentee Owner and other strategies ignoring bounds)
            if bounds and candidates:
                print(f"Applying safety net spatial filter to {len(candidates)} candidates...")
                from shapely.geometry import box
                
                # Construct envelope
                xmin = bounds.get('west', bounds.get('xmin'))
                ymin = bounds.get('south', bounds.get('ymin'))
                xmax = bounds.get('east', bounds.get('xmax'))
                ymax = bounds.get('north', bounds.get('ymax'))
                
                if xmin and ymin and xmax and ymax:
                    search_box = prep(box(xmin, ymin, xmax, ymax))
                    filtered = []
                    for c in candidates:
                        lat = c.get("latitude")
                        lon = c.get("longitude")
                        if lat and lon:
                            if search_box.contains(Point(lon, lat)):
                                filtered.append(c)
                    
                    if len(filtered) < len(candidates):
                        print(f"Safety net removed {len(candidates) - len(filtered)} out-of-bounds leads.")
                    candidates = filtered

            print(f"AND-Logic: Final result count: {len(candidates[:limit])}")
            
            final_results = candidates[:limit]
            
            # ===== ENRICHMENT PHASE (ONLY for final candidates) =====
            # Skip slow enrichment if requested (for faster initial results)
            skip_enrichment = filters.get("skip_enrichment", False)
            
            if not skip_enrichment:
                # Step 0: Apply cached enrichment data FIRST (parcel, GIS, HomeHarvest)
                # This prevents redundant API calls for already-enriched leads
                cache_hits = self._apply_cached_enrichment(final_results)
                if cache_hits > 0:
                    print(f"Applied cached enrichment to {cache_hits} leads (skipping redundant API calls)")
                
                # Step 3a: Enrich Code Violations with parcel data (owner info)
                # Skip leads already enriched during early parcel check OR from cache
                print(f"[Scout] DEBUG: primary = {primary}, checking for Code Violations enrichment", flush=True)
                if primary == "Code Violations":
                    unenriched = [l for l in final_results if not l.get("_parcel_enriched") and not l.get("_cache_enriched")]
                    if unenriched:
                        await self._enrich_violations_with_parcel_data(unenriched)
                        print(f"Parcel enrichment: {len(unenriched)} leads enriched, {len(final_results) - len(unenriched)} skipped (cached/already done)", flush=True)
                    else:
                        print(f"Skipping parcel enrichment ({len(final_results)} already enriched from cache)", flush=True)
                    
                # Step 3b: Enrich Zip Codes (for ALL leads that miss it, e.g. Violations or Parcels)
                # This is fast (spatial query) so we do it for all leads missing zip
                leads_needing_zip = [l for l in final_results if not l.get("address_zip")]
                if leads_needing_zip:
                    try:
                        await self._enrich_violations_with_zip_codes(leads_needing_zip)
                    except Exception as zip_err:
                        print(f"[Scout] ERROR in zip code enrichment: {zip_err}", flush=True)

                
                # Step 3b: Run HomeHarvest and GIS enrichment IN PARALLEL for speed
                # HomeHarvest can be skipped for faster response (adds ~45s when enabled)
                skip_hh = filters.get("skip_homeharvest", False)
                
                gis_task = asyncio.create_task(self._enrich_with_gis_layers(final_results))
                
                if skip_hh:
                    # Fast mode - apply cached HomeHarvest data (no new API calls) + GIS enrichment
                    print("Fast mode: applying cached HomeHarvest data (no new API calls)")
                    cache_applied = self._apply_homeharvest_from_cache(final_results)
                    if cache_applied > 0:
                        print(f"  Applied cached HomeHarvest data to {cache_applied} leads")
                    try:
                        await asyncio.wait_for(gis_task, timeout=30.0)
                    except asyncio.TimeoutError:
                        print("GIS enrichment timed out")
                        gis_task.cancel()
                else:
                    # Full enrichment with HomeHarvest (~45s)
                    hh_task = asyncio.create_task(self._enrich_with_homeharvest(final_results))
                    
                    # Wait for both with a global timeout
                    try:
                        await asyncio.wait_for(
                            asyncio.gather(hh_task, gis_task, return_exceptions=True),
                            timeout=90.0  # Increased from 45s for slower property types
                        )
                    except asyncio.TimeoutError:
                        print("Enrichment timed out, returning partial results")
                        hh_task.cancel()
                        gis_task.cancel()

                # Tax delinquency check is the slowest (uses Playwright) - skip by default
                # Only run if explicitly requested or if lead count is small
                if len(final_results) <= 10 and not filters.get("skip_tax_check", True):
                    await self._check_tax_delinquency(final_results)
                

                # Step FINAL: Save all enriched leads to cache for future searches
                saved = self._save_to_lead_cache(final_results)
                if saved > 0:
                    print(f"Saved {saved} enriched leads to cache (total cached: {len(self._lead_cache)})")

            # Sanitize results to replace NaN with None (JSON compliance)
            # Recursive function to handle nested dicts/lists
            def sanitize(obj):
                if isinstance(obj, float) and math.isnan(obj):
                    return None
                if isinstance(obj, dict):
                    return {k: sanitize(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [sanitize(x) for x in obj]
                return obj

            import math
            final_results = sanitize(final_results)

            return final_results
            
        except Exception as e:
            import traceback
            print(f"ERROR IN FETCH_LEADS: {str(e)}\n{traceback.format_exc()}")
            return []

    def _log(self, msg: str):
        """Legacy logging wrapper."""
        print(f"[Scout] {msg}")



    async def _get_zip_metadata(self, zip_code: str) -> Optional[Dict]:
        """
        Fetches zip code geometry metadata:
        1. Native Envelope (2868) for API Query.
        2. WGS84 Polygon (4326) for Client-Side Filtering.
        """
        url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/Addresses/MapServer/6/query"
        metadata = {}
        
        try:
            # 1. Fetch Native for Envelope
            params_native = {
                "where": f"ZIPCODE = '{zip_code}'",
                "outFields": "ZIPCODE",
                "returnGeometry": "true",
                "f": "json"
            }
            
            # Request 1: Native
            resp_native = requests.get(url, params=params_native, timeout=10)
            if resp_native.status_code == 200:
                data = resp_native.json()
                if data.get("features"):
                    geom = data["features"][0]["geometry"]
                    if "rings" in geom:
                        # Calculate Envelope
                        rings = geom["rings"]
                        min_x, min_y = float('inf'), float('inf')
                        max_x, max_y = float('-inf'), float('-inf')
                        for ring in rings:
                            for p in ring:
                                min_x = min(min_x, p[0])
                                max_x = max(max_x, p[0])
                                min_y = min(min_y, p[1])
                                max_y = max(max_y, p[1])
                        
                        metadata["envelope"] = {
                            "xmin": min_x, "ymin": min_y,
                            "xmax": max_x, "ymax": max_y,
                            "spatialReference": {"wkid": 2868}
                        }
                        self._log(f"Got envelope: {metadata['envelope']}")

            # 2. Fetch WGS84 for Polygon
            params_wgs = {
                "where": f"ZIPCODE = '{zip_code}'",
                "outFields": "ZIPCODE",
                "returnGeometry": "true",
                "outSR": "4326",
                "f": "json"
            }

            # Request 2: WGS84
            resp_wgs = requests.get(url, params=params_wgs, timeout=10)
            if resp_wgs.status_code == 200:
                data = resp_wgs.json()
                if data.get("features"):
                    # Create Shapely Polygon
                    geom = data["features"][0]["geometry"]
                    if "rings" in geom:
                        polys = [Polygon(r) for r in geom["rings"]]
                        from shapely.geometry import MultiPolygon
                        metadata["polygon"] = MultiPolygon(polys)
                        self._log("Got polygon")

            if "envelope" in metadata and "polygon" in metadata:
                return metadata
                
        except Exception as e:
            print(f"Error fetching zip metadata: {e}")
            self._log(f"Error fetching zip metadata: {e}")
            
        return None

    async def _enrich_with_zip_codes(self, leads: List[Dict]):
        """
        Enriches leads with the correct Zip Code using a Spatial Query against Layer 6.
        This fixes the issue where Layer 12 returns the Owner's Zip instead of Property Zip.
        """
        with open("debug_scout_trace.log", "a") as f:
            f.write(f"_enrich_with_zip_codes called with {len(leads)} leads.\n")

        if not leads:
            return

        # 1. Collect Points
        points = []
        valid_leads = []
        for lead in leads:
            lat = lead.get("latitude")
            lon = lead.get("longitude")
            if lat and lon:
                points.append((lon, lat))
                valid_leads.append(lead)
        
        if not points:
            return

        # 2. Calculate Bounding Box
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        
        # Expand slightly
        envelope = {
            "xmin": min_x - 0.001,
            "ymin": min_y - 0.001,
            "xmax": max_x + 0.001,
            "ymax": max_y + 0.001,
            "spatialReference": {"wkid": 4326}
        }

        # 3. Query Layer 6 for Intersecting Zip Polygons
        url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/Addresses/MapServer/6/query"
        params = {
            "geometry": json.dumps(envelope),
            "geometryType": "esriGeometryEnvelope",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "ZIPCODE",
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "json"
        }
        
        try:
            with open("debug_scout_trace.log", "a") as f:
                f.write("Querying Layer 6 for Zip Polygons...\n")
                
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(None, lambda: requests.post(url, data=params, timeout=10))
            
            with open("debug_scout_trace.log", "a") as f:
                f.write(f"Layer 6 response: {resp.status_code}\n")
                
            if resp.status_code == 200:
                data = resp.json()
                features = data.get("features", [])
                
                # 4. Map Leads to Zips (Client-Side Point-in-Polygon)
                zip_polys = []
                for f in features:
                    zip_code = f["attributes"]["ZIPCODE"]
                    geom = f["geometry"]
                    if "rings" in geom:
                        poly = Polygon(geom["rings"][0])
                        prepared_poly = prep(poly)
                        zip_polys.append((zip_code, prepared_poly))
                
                count_updated = 0
                for lead in valid_leads:
                    pt = Point(lead["longitude"], lead["latitude"])
                    for zip_code, poly in zip_polys:
                        if poly.contains(pt):
                            # Found the correct zip!
                            old_zip = lead.get("address_zip")
                            if old_zip != zip_code:
                                lead["address_zip"] = zip_code
                                # Update full address string too
                                parts = lead["address"].split(",")
                                if len(parts) >= 2:
                                    # Reconstruct: Street, City, AZ Zip
                                    # Assuming format: "STREET, CITY, AZ ZIP"
                                    # Or just replace the last part
                                    lead["address"] = f"{parts[0]}, {parts[1]}, AZ {zip_code}"
                                count_updated += 1
                            break
                
                self._log(f"Enriched {count_updated} leads with correct Zip Codes.")
                
        except Exception as e:
            self._log(f"Error enriching zip codes: {e}")


    async def _fetch_pima_parcels(self, filters: Dict, limit: int, offset: int = 0) -> List[Dict]:
        print(f"DEBUG: Entered _fetch_pima_parcels with filters keys: {list(filters.keys())}")
        self._log(f"Fetching parcels with filters: {filters}")
        """
        Fetches parcels from Pima County GIS (Layer 12).
        Uses a Two-Step Strategy + Client-Side Filtering.
        """
        base_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
        address_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/Addresses/MapServer/3/query"
        
        where_parts = ["1=1"]
        
        # 1. Location Filters
        zip_metadata = None
        envelope = None # Initialize to None for scope visibility
        zip_code = filters.get('zip_code')
        
        if zip_code:
            # Use Spatial Query for Zip Code
            zip_metadata = await self._get_zip_metadata(filters['zip_code'])
            
            # Always add ZIP filter as backup/refinement
            where_parts.append(f"ZIP LIKE '{filters['zip_code']}%'")
        
        bounds = filters.get('bounds')
        print(f"DEBUG: Processing bounds: {bounds} (Type: {type(bounds)})")
        
        if bounds:
            # Construct envelope from bounds
            # Expected format: {xmin, ymin, xmax, ymax} or {south, west, north, east}
            if 'west' in bounds:
                 # Convert Google Maps bounds to Envelope
                 zip_metadata = {
                     "envelope": {
                         "xmin": bounds['west'],
                         "ymin": bounds['south'],
                         "xmax": bounds['east'],
                         "ymax": bounds['north'],
                         "spatialReference": {"wkid": 4326}
                     },
                     "polygon": None # No complex polygon for box selection
                 }
                 self._log(f"Using Map Selection Bounds: {zip_metadata['envelope']}")
            elif 'xmin' in bounds:
                 zip_metadata = {
                     "envelope": {
                         "xmin": bounds['xmin'],
                         "ymin": bounds['ymin'],
                         "xmax": bounds['xmax'],
                         "ymax": bounds['ymax'],
                         "spatialReference": {"wkid": 4326}
                     },
                     "polygon": None
                 }
                 self._log(f"Using Direct Envelope Bounds: {zip_metadata['envelope']}")
            else:
                 self._log(f"DEBUG: Bounds present but missing keys. Keys: {bounds.keys()}")
        
        elif filters.get('neighborhood'):
             # Resolve neighborhood to bounds
             hood_bounds = await self._resolve_neighborhood_to_bounds(filters.get('neighborhood'))
             if hood_bounds:
                 zip_metadata = {
                     "envelope": {
                         "xmin": hood_bounds[0],
                         "ymin": hood_bounds[1],
                         "xmax": hood_bounds[2],
                         "ymax": hood_bounds[3],
                         "spatialReference": {"wkid": 4326}
                     },
                     "polygon": None
                 }
                 self._log(f"Using Neighborhood Bounds: {zip_metadata['envelope']}")
             else:
                 print(f"Warning: Could not resolve neighborhood '{filters.get('neighborhood')}'. Returning empty results.")
                 return []
                
        if filters.get('city'):
            where_parts.append(f"JURIS_OL = '{filters['city'].upper()}'")
            
        if filters.get('address'):
            # Normalize address for GIS matching (Ave->AV, Street->ST, etc.)
            addr = self._normalize_address(filters['address'])
            where_parts.append(f"ADDRESS_OL LIKE '%{addr}%'")

        # 2. Property Type Filters (OR logic - any selected type matches)
        # Only apply filter if specific types selected (not empty, not "all")
        property_types = filters.get('property_types') or []
        if property_types and "all" not in [t.lower() for t in property_types]:
            prefixes = self._get_codes_for_types(property_types)
            if prefixes:
                # Use LIKE 'prefix%' for each prefix, combined with OR
                # e.g. (PARCEL_USE LIKE '01%' OR PARCEL_USE LIKE '03%')
                prefix_conditions = [f"PARCEL_USE LIKE '{p}%'" for p in prefixes]
                where_parts.append(f"({' OR '.join(prefix_conditions)})")

        # 4. Ensure Address Exists
        where_parts.append("ADDRESS_OL <> ''")

        where_clause = " AND ".join(where_parts)
        
        # DEBUG: Log the exact WHERE clause being used
        print(f"  GIS Query WHERE clause: {where_clause}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            import time
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            
            start_total = time.time()
            object_ids = []
            loop = asyncio.get_event_loop()
            
            # STRATEGY A: Spatial Query (Two-Step + Filter)
            # Attempt this first, but fallback to B if it fails/times out
            strategy_a_success = False
            
            if zip_metadata:
                envelope = zip_metadata["envelope"]
            elif envelope:
                # Fallback: Use the envelope passed directly to the function (e.g. from scout_area)
                self._log(f"Using Direct Envelope: {envelope}")
                # Ensure it has spatialReference if missing (default to 4326 for safety if coming from frontend)
                if "spatialReference" not in envelope:
                    envelope["spatialReference"] = {"wkid": 4326}
            
            if envelope:
                try:
                    
                    # Step 1: Fetch IDs using Envelope (Native SR)
                    self._log(f"Fetching IDs for Zip Envelope...")
                    t0 = time.time()
                    params_step1 = {
                        "where": where_clause,
                        "geometry": json.dumps(envelope),
                        "geometryType": "esriGeometryEnvelope",
                        "spatialRel": "esriSpatialRelIntersects",
                        "inSR": str(envelope.get("spatialReference", {}).get("wkid", "2868")), # Dynamic SR
                        "outFields": "OBJECTID",
                        "returnGeometry": "false",
                        "f": "json",
                        "resultRecordCount": 4000, # INCREASED POOL to 4000
                        "resultOffset": offset
                    }
                    
                    # Pagination Loop to fetch ALL IDs using OBJECTID > last_max (more robust than resultOffset)
                    all_object_ids = set() # Use set to avoid duplicates
                    last_max_id = -1
                    max_id_fetch = 15000 # Safety cap
                    
                    while len(all_object_ids) < max_id_fetch:
                        # Append OBJECTID filter if we have a previous page
                        current_where = where_clause
                        if last_max_id > 0:
                            current_where = f"({where_clause}) AND OBJECTID > {last_max_id}"
                            
                        params_ids = {
                            "where": current_where,
                            "geometry": json.dumps(envelope),
                            "geometryType": "esriGeometryEnvelope",
                            "spatialRel": "esriSpatialRelIntersects",
                            "inSR": str(envelope.get("spatialReference", {}).get("wkid", "2868")),
                            "outFields": "OBJECTID",
                            "returnGeometry": "false",
                            "f": "json",
                            "resultRecordCount": 2000,
                            "orderByFields": "OBJECTID ASC" # Critical for pagination
                        }
                        
                        # self._log(f"Fetching IDs with last_max_id {last_max_id}...")
                        resp = await loop.run_in_executor(None, lambda: requests.post(base_url, data=params_ids, headers=headers, timeout=15))
                        
                        if resp.status_code != 200:
                            self._log(f"ID Fetch failed with status {resp.status_code}")
                            break
                            
                        data = resp.json()
                        ids = []
                        if "features" in data:
                            ids = [f["attributes"]["OBJECTID"] for f in data["features"]]
                        elif "objectIds" in data:
                            ids = data["objectIds"]
                        
                        self._log(f"Fetched {len(ids)} IDs. Last Max: {last_max_id}")
                        
                        if not ids:
                            break
                        
                        # Update last_max_id
                        new_max = max(ids)
                        if new_max <= last_max_id:
                            # Should not happen with > filter, but safety check
                            break
                        last_max_id = new_max
                        
                        all_object_ids.update(ids)
                        
                        if len(ids) < 1000: # Heuristic: if less than 1000 returned, likely end of list
                             break
                    
                    object_ids = list(all_object_ids)
                    self._log(f"Total Unique IDs found in area: {len(object_ids)}")
                    
                    if object_ids:
                        self._log(f"ID Range: {min(object_ids)} - {max(object_ids)}")
                    
                    if object_ids:
                        # Step 2: Connection Pooling & Smart Concurrency
                        leads = []
                        batch_size = 50

                        # Define fetch_batch_safe helper
                        async def fetch_batch_safe(batch_ids):
                            """Fetch parcel details for a batch of IDs."""
                            try:
                                id_list = ",".join(str(oid) for oid in batch_ids)
                                params = {
                                    "where": f"OBJECTID IN ({id_list})",
                                    "outFields": "*",
                                    "returnGeometry": "true",
                                    "outSR": "4326",
                                    "f": "json"
                                }
                                resp = await loop.run_in_executor(
                                    None,
                                    lambda: requests.post(base_url, data=params, headers=headers, timeout=15)
                                )
                                if resp.status_code == 200:
                                    data = resp.json()
                                    features = data.get("features", [])
                                    return [self._map_pima_parcel(f) for f in features]
                            except Exception as e:
                                self._log(f"Batch fetch error: {e}")
                            return []

                        # Randomize IDs to ensure we don't just process the first N spatially clustered IDs
                        import random
                        random.shuffle(object_ids)
                        
                        # Limit total detail fetches to avoid timeout if area is huge (e.g. max 500)
                        # We only need 'limit' leads eventually, but we fetch more to account for filtering.
                        # If user wants 100, fetching 500 random candidates is usually enough.
                        max_detail_fetch = max(limit * 5, 500)
                        object_ids = object_ids[:max_detail_fetch]

                        tasks = []
                        for i in range(0, len(object_ids), batch_size):
                            batch = object_ids[i:i+batch_size]
                            tasks.append(fetch_batch_safe(batch))
                        
                        results = await asyncio.gather(*tasks)
                        for r in results:
                            leads.extend([l for l in r if l])
                            
                        # self._log(f"Fetched {len(leads)} raw parcels from {len(object_ids)} IDs.")
                        
                        # STRICT CLIENT-SIDE FILTERING
                        # 1. Polygon Filter (Best): Use actual Zip geometry
                        if zip_metadata and zip_metadata.get("polygon"):
                            self._log(f"*** USING POLYGON FILTER *** for {zip_code}. Raw count: {len(leads)}")
                            poly = zip_metadata["polygon"]
                            prepared_poly = prep(poly)
                            
                            filtered_leads = []
                            for lead in leads:
                                pt = Point(lead["longitude"], lead["latitude"])
                                if prepared_poly.contains(pt):
                                    filtered_leads.append(lead)
                            
                            leads = filtered_leads
                            self._log(f"After polygon filter count: {len(leads)}")

                        # 2. Text Filter (Fallback): Only if polygon failed or not available
                        elif zip_code:
                             self._log(f"Applying strict ZIP text filter for {zip_code}. Raw count: {len(leads)}")
                             # Note: This is risky if raw data has Owner Zip. 
                             # Ideally we should enrich first if we rely on text.
                             # But Polygon filter is preferred.
                             leads = [l for l in leads if l.get('address_zip') == zip_code]
                             self._log(f"After text filter count: {len(leads)}")

                        if not leads:
                            self._log("Strategy A yielded 0 leads after strict ZIP filtering. Falling back to Strategy B.")
                            strategy_a_success = False
                            # Do not return [], fall through
                        else:
                            strategy_a_success = True
                            # Randomize leads to avoid clustering when limit is hit
                            import random
                            random.shuffle(leads)
                            
                            # Enrich with correct Zip Codes before returning
                            final_leads = leads[:limit]
                            await self._enrich_with_zip_codes(final_leads)
                            return final_leads
                        
                except Exception as e:
                    self._log(f"Strategy A failed/timed out: {e}. Falling back to Strategy B.")
                    # Fall through to Strategy B

            # STRATEGY B: Standard Attribute Query (Fallback)
            # Only run if Strategy A failed AND we are not in strict spatial mode (i.e. no bounds)
            # If we had an envelope (Map Search), we should NOT fall back to global search.
            if not strategy_a_success and not envelope:
                with open("debug_scout_trace.log", "a") as f:
                    f.write("Starting Strategy B...\n")
                
                # Fetch slightly more than limit to account for cleaning/deduping
                fetch_limit = int(limit * 1.5)
                
                params = {
                    "where": where_clause,
                    "outFields": "*",
                    "returnGeometry": "true",
                    "outSR": "4326",
                    "f": "json",
                    "resultRecordCount": fetch_limit,
                    "resultOffset": offset,
                    "orderByFields": "OBJECTID ASC"
                }
                self._log(f"Fetching Pima Parcels (Attribute Query - Strategy B) with limit={fetch_limit}...")
                self._log(f"Strategy B Where Clause: {where_clause}")
                response = requests.get(base_url, params=params, headers=headers, timeout=30)
                if response.status_code != 200:
                    return []
                data = response.json()

                if "error" in data:
                    self._log(f"API Error: {data['error']}")
                    return []
                    
                features = data.get("features", [])
                with open("debug_scout_trace.log", "a") as f:
                    f.write(f"Strategy B found {len(features)} features.\n")
                
                leads = []
                
                for f in features:
                    try:
                        lead = self._map_pima_parcel(f)
                        if lead:
                            # Strict Client-Side Filter
                            if zip_code and lead.get('address_zip') != zip_code:
                                continue
                            leads.append(lead)
                    except Exception as e:
                        self._log(f"Error mapping parcel: {e}")
                
                # STRATEGY C: Address Layer Fallback (Two-Step Lookup)
                # If Strategy A/B yielded 0 leads AND we are filtering by address
                if not leads and filters.get('address'):
                    with open("debug_scout_trace.log", "a") as f:
                        f.write("Strategy A/B yielded 0 leads. Attempting Strategy C (Address Layer Fallback)...\n")
                    
                    try:
                        addr_q = self._normalize_address(filters['address'])
                        # Query Address Layer (Layer 3)
                        # Try fuzzy match on ADDRESS field
                        params_c = {
                            "where": f"ADDRESS LIKE '%{addr_q}%'",
                            "outFields": "PARCEL",
                            "f": "json",
                            "returnGeometry": "false"
                        }
                        
                        self._log(f"Strategy C: Querying Address Layer for '{addr_q}'...")
                        resp_c = requests.get(address_url, params=params_c, headers=headers, timeout=10)
                        
                        parcel_ids = []
                        if resp_c.status_code == 200:
                            data_c = resp_c.json()
                            features_c = data_c.get("features", [])
                            # Extract PARCEL IDs (clean them)
                            for fc in features_c:
                                pid = fc["attributes"].get("PARCEL")
                                if pid:
                                    # Pima Parcel IDs in Layer 3 usually match Layer 12 format (e.g. 11007009C)
                                    # Sometimes Layer 12 expects dashes? 
                                    # My debug script showed Layer 12 accepted '11007009C' (no dashes) but returned 0 results initially due to wrong URL.
                                    # The correct Layer 12 (GISOpenData) uses '11007009C' (no dashes) in PARCEL field?
                                    # Let's assume exact match first.
                                    parcel_ids.append(pid)
                            
                            # Dedupe
                            parcel_ids = list(set(parcel_ids))
                            
                            if parcel_ids:
                                self._log(f"Strategy C found {len(parcel_ids)} Parcel IDs: {parcel_ids}")
                                with open("debug_scout_trace.log", "a") as f:
                                    f.write(f"Strategy C found Parcel IDs: {parcel_ids}\n")
                                
                                # Query Parcel Layer (Layer 12) by PARCEL ID
                                # Construct IN clause
                                # Note: PARCEL field is String, needs quotes
                                pid_list = ",".join([f"'{pid}'" for pid in parcel_ids])
                                where_c = f"PARCEL IN ({pid_list})"
                                
                                # CRITICAL: Re-apply Property Type Filters for Strategy C
                                # Otherwise we return properties that don't match the selected type
                                property_types = filters.get('property_types') or []
                                if property_types and "all" not in [t.lower() for t in property_types]:
                                    prefixes = self._get_codes_for_types(property_types)
                                    if prefixes:
                                        prefix_conditions = [f"PARCEL_USE LIKE '{p}%'" for p in prefixes]
                                        where_c += f" AND ({' OR '.join(prefix_conditions)})"
                                
                                params_c2 = {
                                    "where": where_c,
                                    "outFields": "*",
                                    "returnGeometry": "true",
                                    "outSR": "4326",
                                    "f": "json"
                                }
                                
                                resp_c2 = requests.get(base_url, params=params_c2, headers=headers, timeout=10)
                                if resp_c2.status_code == 200:
                                    data_c2 = resp_c2.json()
                                    features_c2 = data_c2.get("features", [])
                                    for f in features_c2:
                                        # Pass the searched address as fallback, since Layer 12 often has null address for multi-unit
                                        lead = self._map_pima_parcel(f, fallback_address=addr_q)
                                        if lead:
                                            leads.append(lead)
                                            
                                    with open("debug_scout_trace.log", "a") as f:
                                        f.write(f"Strategy C retrieved {len(leads)} parcels.\n")
                        
                    except Exception as e:
                        self._log(f"Strategy C failed: {e}")
                        with open("debug_scout_trace.log", "a") as f:
                            f.write(f"Strategy C failed: {e}\n")

                # Enrich with correct Zip Codes (Spatial Query)
                # This fixes the issue where Layer 12 returns Owner Zip instead of Property Zip
                with open("debug_scout_trace.log", "a") as f:
                    f.write(f"Calling _enrich_with_zip_codes for {len(leads)} leads...\n")
                
                await self._enrich_with_zip_codes(leads)
                
                with open("debug_scout_trace.log", "a") as f:
                    f.write("Enrichment complete.\n")
                
                return leads[:limit]

        except Exception as e:
            print(f"Error fetching parcels: {e}")
            return []

    def _get_centroid_x(self, geometry: Dict) -> Optional[float]:
        if "x" in geometry:
            return geometry["x"]
        if "rings" in geometry and geometry["rings"]:
            try:
                from shapely.geometry import Polygon
                poly = Polygon(geometry["rings"][0])
                return poly.centroid.x
            except:
                # Fallback to first point
                try:
                    return geometry["rings"][0][0][0]
                except:
                    return None
        return None

    def _get_centroid_y(self, geometry: Dict) -> Optional[float]:
        if "y" in geometry:
            return geometry["y"]
        if "rings" in geometry and geometry["rings"]:
            try:
                from shapely.geometry import Polygon
                poly = Polygon(geometry["rings"][0])
                return poly.centroid.y
            except:
                # Fallback to first point
                try:
                    return geometry["rings"][0][0][1]
                except:
                    pass
            return None
            
    def _map_pima_parcel(self, feature: Dict, override_zip: str = None, fallback_address: str = None) -> Optional[Dict]:
        attr = feature.get("attributes", {})
        geometry = feature.get("geometry", {})
        
        # Handle None value for ADDRESS_OL safely
        raw_addr = attr.get("ADDRESS_OL")
        address = (raw_addr or "").strip()
        
        if not address and fallback_address:
            address = fallback_address
            
        if not address:
            return None
            
        city = attr.get("JURIS_OL", "TUCSON").title()
        zip_code = str(attr.get("ZIP", "")).split("-")[0]
        if override_zip:
            zip_code = override_zip
            
        full_address = f"{address}, {city}, AZ {zip_code}"
        
        # Mailing Address Construction (Directly from Layer 12)
        mail_parts = []
        for i in range(1, 6):
            m = attr.get(f"MAIL{i}")
            if m and m.strip() and m.strip() != ".":
                mail_parts.append(m.strip())
        
        # Add Zip if available (ZIP or ZIP9)
        m_zip = attr.get("ZIP9") or attr.get("ZIP")
        if m_zip and m_zip != "000000000":
             mail_parts.append(str(m_zip))
             
        mailing_address = ", ".join(mail_parts)
        
        # Owner Name Normalization
        # Fallback to MAIL1 if OWNER_NAME is missing (common in Pima GIS)
        owner = attr.get("OWNER_NAME")
        if not owner or not owner.strip():
             owner = attr.get("MAIL1", "Unknown")
        owner = owner.title()
        
        # Property Type Mapping (Basic)
        use_code = attr.get("PARCEL_USE", "")
        prop_type = "Unknown"
        if use_code:
            if use_code.startswith("01"): prop_type = "Single Family"
            elif use_code.startswith("03"): prop_type = "Multi-Family"
            elif use_code.startswith("02"): prop_type = "Commercial"
            elif use_code.startswith("00"): prop_type = "Land"

        # Dynamic Absentee Logic
        distress_signals = []
        # Simple normalization for comparison
        addr_norm = address.upper().replace(" ", "").replace(",", "")
        mail_norm = mailing_address.upper().replace(" ", "").replace(",", "")
        
        # Check if property address is contained in mailing address (to handle formatting diffs)
        # If the street address part isn't in the mailing address, it's likely absentee
        # This is a heuristic.
        is_absentee = False
        if address.upper() not in mailing_address.upper():
             # Double check strict equality of normalized strings if simple substring fails
             # (e.g. 123 MAIN ST vs 123 MAIN STREET) - for now, simple substring is a good start
             # But mailing address usually includes name, so we check if the address part is present.
             # Actually, mailing address in Pima often starts with Name. 
             # Let's check if the *street* part of the property address is in the mailing address.
             if address.split(",")[0].strip().upper() not in mailing_address.upper():
                 is_absentee = True

        if is_absentee:
            distress_signals.append("Absentee Owner")
            
        # Use Pima County GIS Detail Page as the primary link
        # The direct Assessor URL (asr.pima.gov) does not support reliable deep linking.
        # The GIS page (gis.pima.gov) accepts the raw parcel ID (no dashes) and provides a stable landing page.
        parcel_id = attr.get("PARCEL") or str(attr.get("OBJECTID"))
        
        # Ensure we use the raw format for GIS URL (e.g. 117023950)
        raw_parcel_id = parcel_id.replace("-", "") if parcel_id else None

        return {
            "source": "pima_county_gis",
            "parcel_id": parcel_id, # Use PARCEL for joining
            "owner_name": owner,
            "address": full_address,
            "address_street": address,
            "address_city": city,
            "address_state": "AZ",
            "address_zip": zip_code,
            "mailing_address": mailing_address,
            "property_type": prop_type,
            "year_built": attr.get("EFF_YR_BLT"), # Often missing in Layer 12
            "sqft": attr.get("IMPR_SQFT"), # Often missing in Layer 12
            "lot_size": attr.get("GISAREA") or attr.get("LAND_SQFT"), # Map GISAREA
            "zoning": attr.get("CURZONE_OL") or attr.get("ZONING"), # Map CURZONE_OL
            "assessed_value": attr.get("FCV"), # Map FCV
            "last_sale_date": attr.get("LAST_SALE_DATE"),
            "last_sale_price": attr.get("LAST_SALE_PRICE"),
            "latitude": geometry.get("y") or self._get_centroid_y(geometry),
            "longitude": geometry.get("x") or self._get_centroid_x(geometry),
            "status": "New",
            "strategy": "Wholesale",
            "distress_score": len(distress_signals),
            "distress_signals": distress_signals,
            "assessor_url": f"http://gis.pima.gov/maps/detail.cfm?p={raw_parcel_id}" if raw_parcel_id else None,
            # Placeholders for enrichment
            "flood_zone": None, 
            "school_district": None,
            "nearby_development": None,
            "beds": None,
            "baths": None,
            "pool": None,
            "garage": None,
            "arv": None,
            "phone": None,
            "email": None
        }

    async def _fetch_pinal_parcels(self, filters: Dict, limit: int, offset: int) -> List[Dict]:
        # Placeholder for Pinal County
        print("Pinal County fetch not yet implemented.")
        return []

    def _map_parcel_use_to_type(self, parcel_use: str) -> str:
        """
        Maps a PARCEL_USE code to a detailed human-readable property type.
        Format: XX-YZ where XX=Category, Y=Subtype, Z=Characteristic
        Based on Pima County Property Use Code Manual.
        """
        if not parcel_use:
            return "Unknown"
        
        code = str(parcel_use).strip()
        
        # 4-digit codes with full descriptions
        full_code_map = {
            # Vacant Land (00-XX)
            "0010": "Vacant Land - Undetermined",
            "0011": "Vacant Land - Residential, Urban Subdivided",
            "0012": "Vacant Land - Residential, Urban Non-Subdivided",
            "0013": "Vacant Land - Residential, Rural Subdivided",
            "0014": "Vacant Land - Residential, Rural Non-Subdivided",
            "0020": "Vacant Land - Commercial",
            "0021": "Vacant Land - Commercial, Urban Subdivided",
            "0022": "Vacant Land - Commercial, Urban Non-Subdivided",
            "0026": "Vacant Land - Commercial, Multiple Use",
            "0030": "Vacant Land - Industrial",
            "0031": "Vacant Land - Industrial, Urban Subdivided",
            "0032": "Vacant Land - Industrial, Urban Non-Subdivided",
            "0040": "Vacant Land - Condo",
            "0041": "Vacant Land - Condo, Urban Subdivided",
            "0070": "Vacant Land - Incomplete Subdivision",
            "0071": "Vacant Land - Incomplete Subdivision, Urban Subdivided",
            "0080": "Vacant Land - Manufactured Home",
            
            # Single Family (01-XX) - Site ≤5 Acres
            "0100": "Single Family Residential - Site ≤5 Acres",
            "0101": "Single Family Residential - Site ≤5 Acres, Urban Subdivided",
            "0102": "Single Family Residential - Site ≤5 Acres, Urban Non-Subdivided",
            "0103": "Single Family Residential - Site ≤5 Acres, Rural Subdivided",
            "0104": "Single Family Residential - Site ≤5 Acres, Rural Non-Subdivided",
            "0110": "Single Family Residential - Grade 1",
            "0120": "Single Family Residential - Grade 2",
            "0130": "Single Family Residential - Grade 3",
            "0140": "Single Family Residential - Grade 4",
            "0150": "Single Family Residential - Grade 5",
            "0180": "Single Family Residential - With Additional Unit",
            "0190": "Single Family Residential - Miscellaneous Improvements",
            
            # Multi-Family (03-XX)
            "0310": "Multi-Family - Mixed Complex",
            "0320": "Multi-Family - Duplex",
            "0321": "Multi-Family - Duplex (2-4 Buildings)",
            "0330": "Multi-Family - Triplex",
            "0340": "Multi-Family - Fourplex",
            "0350": "Multi-Family - Apartments (5-24 Units)",
            "0360": "Multi-Family - Apartments (25-99 Units)",
            "0370": "Multi-Family - Apartments (100+ Units)",
            "0380": "Multi-Family - Boarding/Rooming House",
            "0390": "Multi-Family - Apartment Cooperative",
            
            # Condo/Townhouse (07-XX)
            "0710": "Condo/Townhouse",
            "0720": "Condo/Townhouse - Grade 2",
            "0730": "Condo/Townhouse - Grade 3",
            "0740": "Condo/Townhouse - Grade 4",
            "0750": "Condo/Townhouse - Grade 5",
            "0780": "Condo/Townhouse - Common Area w/ Improvements",
            "0790": "Condo/Townhouse - Common Area w/o Improvements",
            
            # Manufactured Homes (08-XX)
            "0810": "Manufactured Home Subdivision",
            "0820": "Manufactured Home - Subdivided Lot",
            "0830": "Manufactured Home - Non-Subdivided",
            "0840": "Manufactured Home Park",
            "0850": "RV/Travel Trailer Park",
            "0860": "Manufactured Home Cooperative",
            "0890": "Manufactured Home/RV Park - Mixed",
            
            # Rural Residential (87-XX) - Site >5 Acres
            "8710": "Single Family Residential - Site >5 Acres",
            "8711": "Single Family Residential - Site >5 Acres, Urban Subdivided",
            "8720": "Single Family Residential - Site >5 Acres, Multiple Residences",
            "8730": "Rural Residential - Unsecured Manufactured Home",
            "8740": "Rural Residential - Secured Manufactured Home",
            "8750": "Rural Residential - Affixed Manufactured Home",
        }
        
        # Check for exact 4-digit match first
        if code in full_code_map:
            return full_code_map[code]
        
        # 2-digit prefix mapping with general descriptions
        prefix_map = [
            # Vacant Land
            ("00", "Vacant Land"),
            # Single Family
            ("01", "Single Family Residential - Site ≤5 Acres"),
            ("87", "Single Family Residential - Site >5 Acres"),
            # PUD
            ("02", "PUD Common Area"),
            # Multi-Family
            ("03", "Multi-Family"),
            # Commercial
            ("04", "Commercial - Hotel"),
            ("05", "Commercial - Motel"),
            ("06", "Commercial - Resort"),
            ("07", "Condo/Townhouse"),
            ("081", "Manufactured Home"),
            ("082", "Manufactured Home"),
            ("083", "Manufactured Home"),
            ("084", "Manufactured Home Park"),
            ("085", "RV/Travel Trailer Park"),
            ("08", "Manufactured Home"),
            ("09", "Salvage/Teardown"),
            ("10", "Commercial - Miscellaneous"),
            ("11", "Commercial - Retail"),
            ("12", "Mixed Use - Store/Residential"),
            ("13", "Commercial - Department Store"),
            ("14", "Commercial - Shopping Center"),
            ("15", "Commercial - Office"),
            ("16", "Commercial - Bank"),
            ("17", "Commercial - Gas/Auto Services"),
            ("18", "Commercial - Vehicle Sales"),
            ("19", "Care Facility"),
            ("20", "Commercial - Restaurant/Bar"),
            ("21", "Commercial - Medical"),
            ("22", "Commercial - Track/Airfield"),
            ("23", "Commercial - Cemetery"),
            ("24", "Commercial - Golf Course"),
            ("25", "Commercial - Entertainment"),
            ("26", "Parking Facility"),
            ("27", "Commercial - Club/Lodge"),
            ("28", "Partially Complete Structure"),
            ("29", "Private School"),
            ("30", "Industrial"),
            ("37", "Industrial - Warehouse"),
            ("40", "Agricultural - Plant Nursery"),
            ("41", "Agricultural - Field Crops"),
            ("42", "Agricultural - Vineyard"),
            ("43", "Agricultural - Orchard"),
            ("44", "Agricultural - Citrus"),
            ("45", "Agricultural - High Density"),
            ("46", "Agricultural - Jojoba"),
            ("47", "Ranch"),
            ("48", "Pasture Land"),
            ("49", "Agricultural - Waste/Fallow"),
            ("88", "Limited Use"),
            ("89", "Converted Use"),
            ("90", "Tax Exempt - Private"),
            ("91", "Tax Exempt - Private"),
            ("92", "Religious Property"),
        ]
        
        for prefix, prop_type in prefix_map:
            if code.startswith(prefix):
                return prop_type
        
        # Fallback
        if code.startswith("0") or code.startswith("8"):
            return "Residential"
        elif code.startswith("1") or code.startswith("2"):
            return "Commercial"
        elif code.startswith("3"):
            return "Industrial"
        elif code.startswith("4"):
            return "Agricultural"
        
        return "Unknown"

    def _estimate_fetch_multiplier(self, property_types: List[str]) -> int:
        """
        Estimates the fetch multiplier based on property type rarity.
        Rare property types need higher multipliers to ensure enough results.
        Based on typical distribution in code violations data.
        """
        if not property_types or "all" in [t.lower() for t in property_types]:
            return 3  # Default: 3x for all types
        
        # Property type rarity estimates (based on verification data)
        # Lower % = higher multiplier needed
        rarity_multipliers = {
            # Common types (40-60% of violations) - low multiplier
            "Single Family": 2,
            "Multi-Family": 4,
            "Multi Family": 4,
            
            # Moderate types (10-20% of violations) - medium multiplier
            "Commercial": 5,
            "Condo": 6,
            "Townhouse": 6,
            "Condo/Townhouse": 6,
            "Mobile Home": 8,
            
            # Rare types (<5% of violations) - high multiplier
            "Vacant Land": 25,
            "Land": 25,
            "Mobile Home Park": 20,
            "Industrial / Storage": 15,
            "Parking": 30,
            "Partially Complete": 50,  # Very rare
            "Salvage / Teardown": 50,
            "Mixed Use": 20,
        }
        
        # Use the highest multiplier among selected types
        multiplier = 3  # Default minimum
        for prop_type in property_types:
            if prop_type in rarity_multipliers:
                multiplier = max(multiplier, rarity_multipliers[prop_type])
            else:
                # Unknown type - use moderate multiplier
                multiplier = max(multiplier, 10)
        
        return multiplier

    def _get_codes_for_types(self, types: List[str]) -> List[str]:
        """
        Maps friendly property types to Pima County Use Code PREFIXES (2 digits).
        The query logic will use LIKE 'prefix%' to match all subtypes.
        Reference: Pima County Property Use Code Manual
        """
        type_map = {
            # Residential
            "Single Family": ["01", "87"], # 01=SFR, 87=Rural SFR (>5 acres)
            "Mobile Home": ["081", "082", "083"], # Individual Mobile Homes
            "Mobile Home Park": ["084", "085"], # MH Parks (Commercial)
            "Condo": ["07"], # 07=Condos/Townhouses
            "Townhouse": ["07"],
            # Multi-Family
            "Multi-Family": ["03"], # 03=Multi-Res (Duplex, Triplex, Apts)
            "Multi Family": ["03"],
            # Commercial & Specialty
            "Commercial": ["04", "05", "06", "10", "11", "13", "14", "15", 
                          "16", "17", "18", "19", "20", "21", "22", "23", "24", 
                          "25", "27", "29", "30"], # Removed 12, 26, 28, 37 to be specific if needed
            "Mixed Use": ["12"], # Store + Apt
            "Parking": ["26"], # Garage/Carport/Lot
            "Partially Complete": ["28"], # Distress Indicator
            "Industrial / Storage": ["37"], # Warehouses, Mini-Storage
            "Salvage / Teardown": ["09"], # Improvements with little/no value
            # Land / Agricultural
            "Vacant Land": ["00", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49"],
            "Land": ["00", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49"]
        }
        
        prefixes = []
        for t in types:
            # Exact match first to avoid "Mobile Home" matching "Mobile Home Park" incorrectly
            if t in type_map:
                prefixes.extend(type_map[t])
            else:
                # Fuzzy match fallback (careful with overlaps)
                for key, val in type_map.items():
                    if t.lower() in key.lower() or key.lower() in t.lower():
                        prefixes.extend(val)
        return list(set(prefixes))

    async def _enrich_with_tucson_data(self, leads: List[Dict]):
        """
        Enriches leads with data from Pima County Layer 4 (Tax Parcels).
        Fetches Mailing Address, Sqft, Use Desc.
        """
        # Collect Parcel IDs
        parcel_ids = [l["parcel_id"] for l in leads if l.get("parcel_id")]
        if not parcel_ids:
            return

        # Query Layer 4 using PARCEL
        where_clause = f"PARCEL IN ({','.join([repr(pid) for pid in parcel_ids])})"
        
        url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/4/query"
        params = {
            "where": where_clause,
            "outFields": "PARCEL,USE_,SQ_FT,CODE,SALE_DATE,SALE_PRICE,MAIL1,MAIL2,MAIL3,MAIL4,MAIL5,ZIP9,STREETCITY,STREETDIR,STREETNAME,STREETNO",
            "returnGeometry": "false",
            "f": "json"
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                features = data.get("features", [])
                
                # Debug: Log enrichment success
                with open("debug_cleaner.log", "a") as f:
                    f.write(f"Enrichment: Found {len(features)} matches for {len(parcel_ids)} leads\n")
                    if features:
                        f.write(f"Sample Enrichment: {features[0]['attributes']}\n")
                
                # Create lookup map: PARCEL -> attributes
                tucson_map = {f["attributes"]["PARCEL"]: f["attributes"] for f in features if f.get("attributes", {}).get("PARCEL")}
                
                for lead in leads:
                    pid = lead.get("parcel_id")
                    if pid and pid in tucson_map:
                        tucson_data = tucson_map[pid]
                        
                        # Construct Mailing Address
                        mail_parts = []
                        for i in range(1, 6):
                            m = tucson_data.get(f"MAIL{i}")
                            if m and m.strip() and m.strip() != ".":
                                mail_parts.append(m.strip())
                        
                        zip9 = tucson_data.get("ZIP9")
                        if zip9 and zip9 != "000000000":
                             mail_parts.append(zip9)
                             
                        lead["mailing_address"] = ", ".join(mail_parts)
                        
                        # Update other fields
                        use_desc = tucson_data.get("USE_") # Layer 4 uses USE_
                        if use_desc:
                             # Map numeric codes to text if possible, or just append
                             pass

                        if tucson_data.get("SQ_FT"):
                            lead["sqft"] = int(tucson_data.get("SQ_FT"))
                            
                        # Map Sale Data
                        if tucson_data.get("SALE_DATE"):
                            sale_ts = tucson_data.get("SALE_DATE")
                            if isinstance(sale_ts, int):
                                from datetime import datetime
                                lead["last_sale_date"] = datetime.fromtimestamp(sale_ts / 1000).strftime('%Y-%m-%d')
                            else:
                                lead["last_sale_date"] = str(sale_ts)
                                
                        if tucson_data.get("SALE_PRICE"):
                            lead["last_sale_price"] = tucson_data.get("SALE_PRICE")
                        
        except Exception as e:
            print(f"Error enriching with Tucson data: {e}")
            with open("debug_cleaner.log", "a") as f:
                f.write(f"Error enriching: {e}\n")

    async def _fetch_absentee_owners(self, filters: Dict, limit: int) -> List[Dict]:
        """
        Fetches parcels where Owner Address != Property Address.
        Leverages _fetch_pima_parcels to get base data, then filters in memory.
        """
        with open("debug_cleaner.log", "a") as f:
            f.write(f"TRACE: _fetch_absentee_owners called. Limit={limit}\n")
            
        # Fetch more candidates than needed since we'll filter many out
        # Typically 30-50% of properties are absentee, so 20x should be enough
        candidate_limit = limit * 20 
        
        with open("debug_cleaner.log", "a") as f:
            f.write(f"TRACE: Fetching candidates with limit={candidate_limit}...\n")
            
        candidates = await self._fetch_pima_parcels(filters, limit=candidate_limit, offset=0)
        
        with open("debug_cleaner.log", "a") as f:
            f.write(f"TRACE: Candidates fetched: {len(candidates)}\n")
        
        absentee_leads = []
        self._log(f"Absentee Search: Found {len(candidates)} candidates.")
        absentee_leads = []
        for lead in candidates:
            try:
                prop_addr = lead.get("address", "").upper().strip()
                mail_addr = lead.get("mailing_address", "").upper().strip()
                
                # DEBUG LOGGING
                if "2932" in prop_addr:
                    with open("debug_cleaner.log", "a") as f:
                        f.write(f"TRACE: Checking Candidate: {prop_addr}\n")
                        f.write(f"TRACE: Mailing Address: {mail_addr}\n")
                
                if not prop_addr or not mail_addr:
                    continue
                    
                # Basic normalization for comparison
                # Remove city/state/zip for street comparison if possible, or just compare full strings
                # Heuristic: If the first 10 chars of property address (Street Num + Name) 
                # are NOT in mailing address, it's likely absentee.
                
                # Extract Street Number and Name from Property Address (e.g. "123 MAIN ST")
                # Pima address format: "123 E MAIN ST, TUCSON, AZ 85701"
                prop_street = prop_addr.split(",")[0]
                
                if "2932" in prop_addr:
                    with open("debug_cleaner.log", "a") as f:
                        f.write(f"TRACE: Prop Street: '{prop_street}'\n")
                        f.write(f"TRACE: Is In Mailing? {prop_street in mail_addr}\n")
                
                if prop_street not in mail_addr:
                    # Double check: sometimes mailing address is just "PO BOX 123" -> Absentee
                    # Sometimes it's "123 E MAIN ST" -> Owner Occupied
                    
                    if "Absentee Owner" not in lead["distress_signals"]:
                        lead["distress_signals"].append("Absentee Owner")
                    absentee_leads.append(lead)
                    
                    if len(absentee_leads) >= limit:
                        break
                        
            except Exception as e:
                continue

        return absentee_leads

    def _map_tucson_violation(self, feature: Dict) -> Dict:
        attr = feature.get("attributes", {})
        geometry = feature.get("geometry", {})
        
        address_full = attr.get("ADDRESSFULL", "") or ""
        
        # Extract zip code from address if present (e.g. "123 MAIN ST, TUCSON AZ 85719")
        import re
        zip_match = re.search(r'\b(\d{5})(?:-\d{4})?\b', address_full)
        address_zip = zip_match.group(1) if zip_match else None
        
        # Clean address for display
        address_street = address_full.split(",")[0].strip() if "," in address_full else address_full
        
        # Activity Number is unique per violation - use as ID
        activity_num = attr.get("ACT_NUM", "")
        
        # Ensure address has City/State for HomeHarvest accuracy
        if "TUCSON" not in address_full.upper():
            address_full = f"{address_street}, Tucson, AZ"
            if address_zip:
                address_full += f" {address_zip}"

        return {
            "id": activity_num,  # Unique ID for React keys
            "source": "tucson_code_enforcement",
            "parcel_id": None,  # Will be set from real parcel data during enrichment
            "owner_name": None, # Not available from Code Enforcement data
            "address": address_full,
            "address_street": address_street,
            "address_city": "Tucson",
            "address_state": "AZ",
            "address_zip": address_zip,
            "mailing_address": None, # Not available
            "property_type": "Unknown",
            "year_built": None,
            "sqft": None,
            "lot_size": None,
            "zoning": None,
            "assessed_value": None,
            "last_sale_date": None,
            "last_sale_price": None,
            "latitude": geometry.get("y") or self._get_centroid_y(geometry),
            "longitude": geometry.get("x") or self._get_centroid_x(geometry),
            "status": "New",
            "strategy": "Wholesale",
            "distress_score": 1,
            "distress_signals": ["Code Violation"],
            "violation_description": f"{attr.get('DESCRIPTION', 'Unknown')} ({attr.get('STATUS_1')})",
            "beds": None,
            "baths": None,
            "pool": None,
            "garage": None,
            "arv": None,
            "phone": None,
            "email": None
        }

    async def autocomplete_address(self, query: str, limit: int = 5) -> List[str]:
        """
        Fetches address suggestions from Pima County GIS.
        """
        if not query or len(query) < 3:
            return []

        where_clause = f"ADDRESS_OL LIKE '%{query.upper()}%'"
        
        params = {
            "where": where_clause,
            "outFields": "ADDRESS_OL",
            "returnGeometry": "false",
            "returnDistinctValues": "true",
            "f": "json",
            "resultRecordCount": limit,
            "orderByFields": "ADDRESS_OL ASC"
        }
        
        try:
            response = requests.get(self.pima_parcels_url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                features = data.get("features", [])
                # Extract unique addresses
                addresses = [f["attributes"]["ADDRESS_OL"] for f in features if f.get("attributes", {}).get("ADDRESS_OL")]
                return list(set(addresses)) # Ensure uniqueness
            return []
        except Exception as e:
            print(f"Error fetching autocomplete suggestions: {e}")
            return []

    async def _resolve_neighborhood_to_bounds(self, neighborhood: str) -> Optional[tuple]:
        """
        Resolves a neighborhood/subdivision name to a bounding box (xmin, ymin, xmax, ymax).
        Queries the Parcel layer for matching SUBDIV_NAME and calculates extent.
        """
        if not neighborhood:
            return None
            
        print(f"Resolving neighborhood bounds for: {neighborhood}")
        
        # Query for parcels in this subdivision - USE LAYER 15 (Subdivisions)
        # Field is SUB_NAME
        url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/15/query"
        where_clause = f"SUB_NAME LIKE '%{neighborhood.upper()}%'"
        
        params = {
            "where": where_clause,
            "outFields": "SUB_NAME",
            "returnGeometry": "true",
            "returnExtentOnly": "false", # Get features if extent is NaN
            "outSR": "4326",
            "f": "json"
        }
        
        try:
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(
                None,
                lambda: requests.get(url, params=params, timeout=10)
            )
            
            if resp.status_code == 200:
                data = resp.json()
                extent = data.get("extent")
                
                # Check if extent is valid (not NaN)
                is_valid_extent = False
                if extent:
                    try:
                        if not math.isnan(float(extent["xmin"])):
                            is_valid_extent = True
                    except:
                        pass
                
                if is_valid_extent:
                    print(f"DEBUG: Using API Extent: {extent}")
                    buffer = 0.001
                    return (
                        float(extent["xmin"]) - buffer,
                        float(extent["ymin"]) - buffer,
                        float(extent["xmax"]) + buffer,
                        float(extent["ymax"]) + buffer
                    )
                
                # Fallback: Calculate from features
                features = data.get("features", [])
                if features:
                    print(f"DEBUG: Calculating bounds from {len(features)} features")
                    min_x, min_y = float('inf'), float('inf')
                    max_x, max_y = float('-inf'), float('-inf')
                    
                    found_geom = False
                    for f in features:
                        geom = f.get("geometry")
                        if geom and "rings" in geom:
                            for ring in geom["rings"]:
                                for pt in ring:
                                    x, y = pt[0], pt[1]
                                    min_x = min(min_x, x)
                                    min_y = min(min_y, y)
                                    max_x = max(max_x, x)
                                    max_y = max(max_y, y)
                                    found_geom = True
                    
                    if found_geom:
                        buffer = 0.001
                        return (min_x - buffer, min_y - buffer, max_x + buffer, max_y + buffer)
                        
            return None
        except Exception as e:
            print(f"Error resolving neighborhood: {e}")
            return None

    async def autocomplete_address(self, query: str, limit: int = 5) -> List[str]:
        """
        Fetches address AND neighborhood suggestions from Pima County GIS.
        """
        if not query or len(query) < 3:
            return []

        # 1. Search Addresses
        addr_where = f"ADDRESS_OL LIKE '%{query.upper()}%'"
        addr_params = {
            "where": addr_where,
            "outFields": "ADDRESS_OL",
            "returnGeometry": "false",
            "returnDistinctValues": "true",
            "f": "json",
            "resultRecordCount": limit,
            "orderByFields": "ADDRESS_OL ASC"
        }
        
        # 2. Search Subdivisions (Neighborhoods) - USE LAYER 15
        sub_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/15/query"
        sub_where = f"SUB_NAME LIKE '%{query.upper()}%'"
        sub_params = {
            "where": sub_where,
            "outFields": "SUB_NAME",
            "returnGeometry": "false",
            "returnDistinctValues": "true",
            "f": "json",
            "resultRecordCount": limit,
            "orderByFields": "SUB_NAME ASC"
        }
        
        suggestions = []
        
        try:
            loop = asyncio.get_event_loop()
            
            # Run both queries in parallel
            f1 = loop.run_in_executor(None, lambda: requests.get(self.pima_parcels_url, params=addr_params, timeout=5))
            f2 = loop.run_in_executor(None, lambda: requests.get(sub_url, params=sub_params, timeout=5))
            
            r1, r2 = await asyncio.gather(f1, f2, return_exceptions=True)
            
            # Process Addresses
            if isinstance(r1, requests.Response) and r1.status_code == 200:
                data = r1.json()
                features = data.get("features", [])
                suggestions.extend([f["attributes"]["ADDRESS_OL"] for f in features if f.get("attributes", {}).get("ADDRESS_OL")])
                
            # Process Subdivisions
            if isinstance(r2, requests.Response) and r2.status_code == 200:
                data = r2.json()
                features = data.get("features", [])
                suggestions.extend([f["attributes"]["SUB_NAME"] for f in features if f.get("attributes", {}).get("SUB_NAME")])
            
            # Deduplicate and sort
            return sorted(list(set(suggestions)))[:limit]
            
        except Exception as e:
            print(f"Error fetching autocomplete suggestions: {e}")
            return []
    async def _fetch_recorder_data(self, distress_type: str, limit: int) -> List[Dict]:
        """
        Fetches data from Pima County Recorder via MCP Server.
        """
        print(f"Fetching Recorder data for: {distress_type}")
        
        # Map distress type to MCP doc_type
        type_map = {
            "Liens (HOA, Mechanics)": "LIEN",
            "Pre-Foreclosure": "FORECLOSURE",
            "Divorce": "DIVORCE",
            "Judgements": "JUDGMENT",
            "Tax Liens": "TAX LIEN"
        }
        
        doc_type = type_map.get(distress_type)
        if not doc_type:
            return []

        # Path to MCP server script
        # Assuming relative path from backend/app/services/pipeline/scout.py to backend/mcp_servers/recorder/server.py
        print("MCP Recorder integration temporarily disabled due to import errors.")
        return []
        
        # server_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../mcp_servers/recorder/server.py"))
        # backend/app/services/pipeline/../../../mcp_servers/recorder/server.py
        server_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../mcp_servers/recorder/server.py"))
        
        if not os.path.exists(server_script):
            print(f"MCP Server script not found at: {server_script}")
            return []

        server_params = StdioServerParameters(
            command=sys.executable,
            args=[server_script],
            env=os.environ.copy()
        )

        leads = []
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Call tool
                    print(f"Calling tool search_documents with doc_type={doc_type}")
                    results = await session.call_tool("search_documents", arguments={"query": "", "doc_type": doc_type})
                    print(f"Raw MCP Results: {results}")
                    
                    # Map results to Lead format
                    if results and hasattr(results, 'content') and isinstance(results.content, list):
                        for content in results.content:
                            print(f"Content Type: {content.type}")
                            if content.type == "text":
                                print(f"Content Text: {content.text}")
                                try:
                                    data = json.loads(content.text)
                                    # data should be the List[Dict] I returned
                                    if isinstance(data, list):
                                        for item in data:
                                            leads.append({
                                                "source": "pima_recorder_mcp",
                                                "owner_name": item.get("grantor", "Unknown"),
                                                "address": "Unknown Address (Recorder Match)", # Recorder often lacks address, need cross-ref
                                                "distress_signals": [f"{distress_type}: {item.get('doc_type')}"],
                                                "status": "New",
                                                "strategy": "Creative Finance",
                                                "parcel_id": f"REC-{item.get('doc_id')}",
                                                "distress_score": 80
                                            })
                                except json.JSONDecodeError:
                                    print("Failed to decode JSON from content text")

        except Exception as e:
            print(f"Error calling MCP server: {e}")
            
        return leads[:limit]
