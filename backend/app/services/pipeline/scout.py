import requests
import json
import math
import asyncio
import numpy as np
from typing import List, Dict, Optional, Any
from shapely.geometry import Polygon, Point
from shapely.prepared import prep
from shapely.ops import unary_union

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

    # Curated list of actual Tucson zip codes (excludes suburbs like Marana, Oro Valley, Sahuarita, Green Valley)
    TUCSON_ZIPS = {
        "85701", "85704", "85705", "85706", "85707", "85708", "85710", "85711",
        "85712", "85713", "85714", "85715", "85716", "85718", "85719", "85724",
        "85726", "85730", "85743", "85745", "85746", "85747", "85748", "85749",
        "85750", "85756", "85741"  # 85741 is Catalina Foothills, borderline
    }

    # Curated City to Zip Map (Hardcoded for accuracy)
    # This prevents "Green Valley" searches from returning Tucson properties due to bad GIS data
    CITY_ZIP_MAP = {
        "GREEN VALLEY": ["85614", "85622"],
        "SAHUARITA": ["85629"],
        "VAIL": ["85641", "85747"],
        "MARANA": ["85653", "85658", "85743"],
        "ORO VALLEY": ["85737", "85755", "85704"],
        "CATALINA": ["85739"],
        "ORACLE": ["85623"],
        "SAN MANUEL": ["85631"],
        "AJO": ["85321"],
        "SELLS": ["85634"],
        "SOUTH TUCSON": ["85713", "85714"],
        "TUCSON": [
            "85701", "85704", "85705", "85706", "85707", "85708", "85710", "85711",
            "85712", "85713", "85714", "85715", "85716", "85718", "85719", "85724",
            "85726", "85730", "85743", "85745", "85746", "85747", "85748", "85749",
            "85750", "85756", "85741"
        ]
    }

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
        self._violations_cache_ttl = 1800  # 30 minutes TTL (increased from 10)

        # City zips cache - stores zip codes per city (rarely changes)
        # Key: city name (lowercase), Value: list of zip codes
        self._city_zips_cache: Dict[str, List[str]] = {}
        
        # Zip metadata cache - stores envelope/polygon for each zip code
        # Key: zip code, Value: metadata dict with envelope and polygon
        self._zip_metadata_cache: Dict[str, Dict] = {}

        
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
        
        # Zip record counts cache file path (persistent across restarts)
        import os
        self._cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "cache")
        self._zip_counts_file = os.path.join(self._cache_dir, "zip_counts.json")
        self._zip_counts_cache: Dict[str, Dict[str, int]] = self._load_zip_counts()

    def _load_zip_counts(self) -> Dict[str, Dict[str, int]]:
        """Load zip record counts from persistent JSON file."""
        import os
        try:
            if os.path.exists(self._zip_counts_file):
                with open(self._zip_counts_file, 'r') as f:
                    data = json.load(f)
                    print(f"[Scout] Loaded zip counts cache from file")
                    return data
        except Exception as e:
            print(f"[Scout] Error loading zip counts cache: {e}")
        return {"code_violations": {}, "parcels": {}}
    
    def _save_zip_counts(self):
        """Save zip record counts to persistent JSON file."""
        import os
        try:
            os.makedirs(self._cache_dir, exist_ok=True)
            with open(self._zip_counts_file, 'w') as f:
                json.dump(self._zip_counts_cache, f, indent=2)
            print(f"[Scout] Saved zip counts cache to file")
        except Exception as e:
            print(f"[Scout] Error saving zip counts cache: {e}")
    
    async def _get_zip_record_counts(self, city: str, data_type: str = "code_violations") -> Dict[str, int]:
        """
        Get record counts per zip for weighted sampling.
        Uses persistent file cache - only fetches from GIS if not cached.
        
        Args:
            city: City name (e.g., "tucson")
            data_type: "code_violations" or "parcels"
        
        Returns:
            Dict mapping zip code to record count
        """
        cache_key = data_type
        
        # Check if we have cached counts with actual data (more than just metadata)
        cached = self._zip_counts_cache.get(cache_key, {})
        real_counts = {k: v for k, v in cached.items() if not k.startswith("_")}
        if real_counts:
            print(f"[Scout] Using cached {data_type} counts: {len(real_counts)} zips")
            return real_counts
        
        # Need to fetch counts from GIS
        print(f"[Scout] Fetching {data_type} record counts for {city}...")
        city_zips = await self._fetch_zips_by_city(city)
        if not city_zips:
            return {}
        
        counts = {}
        
        if data_type == "code_violations":
            # Query code violations layer for counts per zip
            for zip_code in city_zips:
                try:
                    # Get just the count, not full records
                    zip_metadata = await self._get_zip_metadata(zip_code)
                    if zip_metadata and "envelope" in zip_metadata:
                        params = {
                            "where": "STATUS_1 NOT IN ('COMPLIAN', 'CLOSED', 'VOID')",
                            "geometry": json.dumps(zip_metadata["envelope"]),
                            "geometryType": "esriGeometryEnvelope",
                            "spatialRel": "esriSpatialRelIntersects",
                            "inSR": "2868",
                            "returnCountOnly": "true",
                            "f": "json"
                        }
                        resp = requests.post(self.tucson_violations_url, data=params, timeout=10)
                        if resp.status_code == 200:
                            data = resp.json()
                            counts[zip_code] = data.get("count", 0)
                except Exception as e:
                    counts[zip_code] = 0
            
        elif data_type == "parcels":
            # Query parcel layer for counts per zip
            for zip_code in city_zips:
                try:
                    params = {
                        "where": f"ZIP LIKE '{zip_code}%'",
                        "returnCountOnly": "true",
                        "f": "json"
                    }
                    resp = requests.get(self.pima_parcels_url, params=params, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        counts[zip_code] = data.get("count", 0)
                except Exception as e:
                    counts[zip_code] = 0
        
        # Save to cache
        from datetime import datetime
        self._zip_counts_cache[cache_key] = {**counts, "_updated": datetime.now().isoformat()}
        self._save_zip_counts()
        
        print(f"[Scout] Cached {data_type} counts: {len(counts)} zips, total={sum(counts.values())}")
        return counts

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
        #         # Cache expired, remove it
        #         del self._violations_cache[cache_key]
        
        print("Fetching code violations from Tucson GIS...")
        
        # Build WHERE clause
        where_parts = ["STATUS_1 NOT IN ('COMPLIAN', 'CLOSED', 'VOID')"]

        params = {
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": "4326",  # WGS84 for Leaflet map compatibility
            "f": "json",
            "resultRecordCount": limit * 10 if (zip_code or filters.get('bounds')) else limit,  # Fetch more if filtering (spatial)
        }
        
        # OPTIMIZATION: Short-circuit for non-Tucson cities
        # Code Violations are ONLY available in Tucson (Layer 94)
        if filters.get("city"):
            city = filters["city"].upper().strip()
            if city != "TUCSON":
                print(f"Skipping Code Violation search for unsupported city: {city}")
                return []
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

        elif filters.get("city"):
            # ===== CITY-WIDE SEARCH (SIMPLIFIED) =====
            # Query all city zips in parallel, shuffle results for distribution
            import random
            import time as time_module
            
            city = filters.get("city")
            t_start = time_module.time()
            print(f"[PERF] City-wide search: '{city}' code violations")
            
            # Get the zips for this city
            city_zips = await self._fetch_zips_by_city(city)
            if not city_zips:
                print(f"Warning: No zips found for city '{city}'")
                return []
            
            print(f"[PERF] Querying {len(city_zips)} zips in parallel...")
            
            # Query each zip in parallel (limit per zip to avoid huge responses)
            per_zip_limit = max(20, limit // len(city_zips) + 5)  # At least 20 per zip
            
            async def fetch_single_zip(zip_code: str) -> List[Dict]:
                try:
                    zip_filters = {**filters, "zip_code": zip_code, "city": None}
                    return await self._fetch_code_violations(zip_filters, per_zip_limit)
                except Exception as e:
                    print(f"    Error fetching zip {zip_code}: {e}")
                    return []
            
            # Limit to 5 concurrent (Tucson GIS sensitive to overload)
            sem = asyncio.Semaphore(5)
            async def fetch_with_limit(zip_code: str):
                async with sem:
                    return await fetch_single_zip(zip_code)
            
            tasks = [fetch_with_limit(z) for z in city_zips]
            results_list = await asyncio.gather(*tasks)
            
            # Combine all results
            all_results = []
            for zip_results in results_list:
                if zip_results:
                    all_results.extend(zip_results)
            
            # SHUFFLE for random geographic distribution
            random.shuffle(all_results)
            
            t_elapsed = time_module.time() - t_start
            print(f"[PERF] City search complete: {len(all_results)} results in {t_elapsed:.1f}s total")
            
            # Return up to limit results
            return all_results[:limit]
        
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
            import aiohttp
            import time as time_module
            
            t_fetch_start = time_module.time()
            
            # Define async batch fetcher
            async def fetch_batch_async(session: aiohttp.ClientSession, batch_params: Dict, batch_num: int) -> List[Dict]:
                try:
                    async with session.post(self.tucson_violations_url, data=batch_params, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            features = data.get("features", [])
                            return features
                except Exception as e:
                    print(f"[PERF] Batch {batch_num} error: {e}")
                return []
            
            # Create all batch params upfront
            batch_params_list = []
            for batch_num in range(max_batches):
                batch_params = params.copy()
                batch_params["resultRecordCount"] = batch_size
                batch_params["resultOffset"] = batch_num * batch_size
                batch_params_list.append((batch_params, batch_num))
            
            # Execute ALL batches in parallel using aiohttp
            print(f"[PERF] Fetching {max_batches} batches in parallel...")
            async with aiohttp.ClientSession() as session:
                tasks = [fetch_batch_async(session, bp, bn) for bp, bn in batch_params_list]
                results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            for batch_num, result in enumerate(results):
                if isinstance(result, list) and result:
                    all_features.extend(result)
                    print(f"  Batch {batch_num + 1}: {len(result)} violations")
            
            print(f"[PERF] Parallel fetch complete: {len(all_features)} raw in {time_module.time() - t_fetch_start:.1f}s")
            
            print(f"Found {len(all_features)} raw code violations.")
            
            # Map to lead objects
            leads = [self._map_tucson_violation(f) for f in all_features]
            
            # Client-side filtering by zip code OR bounds OR city (strict)
            if (zip_code or bounds or filters.get("city")) and zip_polygon:
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
            
            # Shuffle results to prevent geographic clustering (GIS returns in OBJECTID order)
            import random
            random.shuffle(result)
            
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
        Uses ASYNC aiohttp with PARALLEL batch processing for maximum speed.
        """
        if not leads:
            return
        
        import time as time_module
        import aiohttp
        
        start_time = time_module.time()
        print(f"[PERF] Enriching {len(leads)} violations with parcel data (ASYNC PARALLEL)...")
        
        base_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
        
        # Process in batches of 50
        batch_size = 50
        enriched_count = 0
        
        # Prepare all batches upfront
        batches = []
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
            if points:
                batches.append((points, valid_leads))
        
        print(f"[PERF] Processing {len(batches)} batches in parallel...")
        
        async def fetch_batch(session: aiohttp.ClientSession, points: List, valid_leads: List) -> int:
            """Fetch and process a single batch, returns count of enriched leads."""
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
            
            batch_enriched = 0
            try:
                async with session.post(base_url, data=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        features = data.get("features", [])
                        
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
                        
                        # Match leads to parcels
                        for lead in valid_leads:
                            pt = Point(lead["longitude"], lead["latitude"])
                            pt_buffer = pt.buffer(0.0001)
                            
                            for poly, attr in parcels:
                                if poly.intersects(pt_buffer):
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
                                    
                                    parcel_use = str(attr.get("PARCEL_USE", "")) if attr.get("PARCEL_USE") else ""
                                    lead["parcel_use_code"] = parcel_use
                                    lead["property_type"] = self._map_parcel_use_to_type(parcel_use)
                                    
                                    # Check absentee
                                    prop_street = (lead.get("address_street") or "").upper().strip()
                                    if prop_street and mailing_address:
                                        if prop_street not in mailing_address.upper():
                                            if "Absentee Owner" not in lead.get("distress_signals", []):
                                                lead["distress_signals"].append("Absentee Owner")
                                    
                                    lead["_parcel_enriched"] = True
                                    batch_enriched += 1
                                    break
            except Exception as e:
                print(f"[PERF] Batch error: {e}")
            
            return batch_enriched
        
        # Execute ALL batches in parallel using aiohttp session
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_batch(session, points, valid_leads) for points, valid_leads in batches]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, int):
                    enriched_count += result
        
        elapsed = time_module.time() - start_time
        print(f"[PERF] Enriched {enriched_count}/{len(leads)} violations with parcel data ({elapsed:.2f}s)")

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
        
        # Phase 2: Query API for uncached leads using PARALLEL BATCHES
        import aiohttp
        base_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
        
        # Split into batches of 50 (optimal for GIS multipoint queries)
        batch_size = 50
        batches = [needs_api[i:i + batch_size] for i in range(0, len(needs_api), batch_size)]
        
        async def fetch_batch(session, batch_leads):
            if not batch_leads:
                return []
                
            points = [[lead["longitude"], lead["latitude"]] for lead in batch_leads]
            
            multipoint = {
                "points": points,
                "spatialReference": {"wkid": 4326}
            }
            
            params = {
                "geometry": json.dumps(multipoint),
                "geometryType": "esriGeometryMultipoint",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "PARCEL_USE",
                "returnGeometry": "true",
                "outSR": "4326",
                "f": "json"
            }
            
            try:
                async with session.post(base_url, data=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        features = data.get("features", [])
                        
                        # Process features
                        from shapely import STRtree
                        parcels = []
                        parcel_use_map = {}
                        
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
                        
                        batch_passes = []
                        if parcels:
                            tree = STRtree(parcels)
                            for lead in batch_leads:
                                pt = Point(lead["longitude"], lead["latitude"])
                                result = tree.query(pt)
                                for idx in result:
                                    if parcels[idx].contains(pt):
                                        parcel_use = parcel_use_map[id(parcels[idx])]
                                        use_code = str(parcel_use) if parcel_use else ""
                                        
                                        # Cache and store
                                        key = cache_key(lead)
                                        if key:
                                            self._property_type_cache[key] = use_code
                                            lead["use_desc"] = use_code
                                        
                                        if matches_type(use_code):
                                            batch_passes.append(lead)
                                        break
                        return batch_passes
            except Exception as e:
                print(f"Batch property type filter error: {e}")
            return []

        # Execute batches in parallel
        api_passes = []
        if batches:
            print(f"[PERF] Processing {len(batches)} property type batches in parallel...")
            async with aiohttp.ClientSession() as session:
                tasks = [fetch_batch(session, batch) for batch in batches]
                results = await asyncio.gather(*tasks)
                for res in results:
                    api_passes.extend(res)
        
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
        gis_fields = ["flood_zone", "school_district", "zoning", "nearby_development"]
        
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
                "PROJ_NAME,AA_STATUS",
                {"nearby_development": "PROJ_NAME", "development_status": "AA_STATUS"},
                False  # Use multipoint intersection (spatial query works with correct fields)
            ),
            (
                "Parcels",
                "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query",
                "PARCEL,MAIL1,FCV,CURZONE_OL,PARCEL_USE",
                {"parcel_id": "PARCEL", "owner_name": "MAIL1", "assessed_value": "FCV", "zoning": "CURZONE_OL", "parcel_use_code": "PARCEL_USE"},
                False  # Use multipoint intersection to get real APN from coordinates
            ),
            (
                "Neighborhood Associations",
                "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/Community2/MapServer/9/query",
                "NAME",
                {"neighborhoods": "NAME"},
                False
            ),
            (
                "Subdivisions",
                "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/15/query",
                "SUB_NAME",
                {"subdivision": "SUB_NAME"},
                False
            )
        ]
        
        loop = asyncio.get_event_loop()
        batch_size = 50
        
        for name, url, fields, attr_map, fetch_all in layers:
            print(f"  Querying GIS layer: {name}...")
            
            # For fetchAll layers, query once for all polygons, then match all leads
            if fetch_all:
                polys = []
                offset = 0
                record_count = 2000
                
                while True:
                    params = {
                        "where": "1=1",  # Get ALL features
                        "outFields": fields,
                        "returnGeometry": "true",
                        "outSR": "4326",
                        "f": "json",
                        "resultRecordCount": record_count,
                        "resultOffset": offset
                    }
                    try:
                        resp = await loop.run_in_executor(
                            None,
                            lambda: requests.get(url, params=params, timeout=30)
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            features = data.get("features", [])
                            
                            if not features:
                                break
                                
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
                            
                            # Check if we need to fetch more
                            if len(features) < record_count:
                                break
                            
                            offset += len(features)
                            print(f"    {name}: Fetched {len(features)} features (offset {offset})...")
                            
                        else:
                            print(f"    {name}: API returned {resp.status_code}")
                            break
                    except Exception as e:
                        print(f"  Error querying {name}: {e}")
                        break
                
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
                continue  # Skip to next layer
            
            # Normal multipoint intersection for other layers
            # Use parallel batch processing
            tasks = []
            
            async def process_batch(batch_idx, batch_leads):
                # OPTIMIZATION: Skip "Parcels" layer if leads already have parcel data
                if name == "Parcels":
                    # Filter batch to only those missing parcel_id or owner_name
                    batch_leads = [l for l in batch_leads if not l.get("parcel_id") or not l.get("owner_name")]
                    if not batch_leads:
                        return
                
                points = []
                valid_leads = []
                for lead in batch_leads:
                    lat = lead.get("latitude")
                    lon = lead.get("longitude")
                    if lat and lon:
                        points.append([lon, lat])
                        valid_leads.append(lead)
                
                if not points:
                    return
                    
                multipoint = {
                    "points": points,
                    "spatialReference": {"wkid": 4326}
                }
                
                params = {
                    "geometry": json.dumps(multipoint),
                    "geometryType": "esriGeometryMultipoint",
                    "spatialRel": "esriSpatialRelIntersects",
                    "inSR": "4326",
                    "outFields": fields,
                    "returnGeometry": "true",
                    "outSR": "4326",
                    "f": "json"
                }
                
                try:
                    resp = await loop.run_in_executor(
                        None, 
                        lambda: requests.post(url, data=params, timeout=60)
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        features = data.get("features", [])
                        
                        # DEBUG: Log if features found for Neighborhood Associations
                        # if "Community2/MapServer/9" in url:
                        #     print(f"DEBUG: Neighborhood Associations query returned {len(features)} features")
                        #     if features:
                        #         print(f"DEBUG: First feature attributes: {features[0].get('attributes')}")
                        
                        # Map features to leads
                        polys = []
                        from shapely.geometry import Polygon
                        for f in features:
                            attr = f.get("attributes", {})
                            geom = f.get("geometry")
                            if geom and "rings" in geom:
                                try:
                                    # ESRI JSON uses 'rings' for Polygons
                                    # We construct a Polygon from the first ring (exterior)
                                    # TODO: Handle holes/multipolygons properly if needed
                                    for ring in geom["rings"]:
                                        poly = Polygon(ring)
                                        polys.append((poly, attr))
                                except:
                                    pass
                        
                        enriched_count = 0
                        for lead in valid_leads:
                            pt = Point(lead["longitude"], lead["latitude"])
                            for poly, attr in polys:
                                if poly.contains(pt):
                                    for lead_key, attr_key in attr_map.items():
                                        val = attr.get(attr_key)
                                        if val:
                                            lead[lead_key] = val
                                    
                                    enriched_count += 1
                                    break
                        
                        if polys and enriched_count > 0:
                            print(f"    {name}: {len(polys)} polygons, {enriched_count} leads enriched (batch {batch_idx + 1})")
                except Exception as e:
                    print(f"  Error querying {name} batch {batch_idx}: {e}")

            # Create tasks for all batches
            for i in range(0, len(leads), batch_size):
                batch = leads[i:i + batch_size]
                tasks.append(process_batch(i // batch_size, batch))
            
            if tasks:
                # Run all batches for this layer in parallel
                await asyncio.gather(*tasks)

        
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
        
        # Parking/Garage detection
        parking_garage = data.get("parking_garage")
        lead["parking_garage"] = parking_garage
        lead["garage_spaces"] = parking_garage
        lead["has_garage"] = bool(parking_garage and parking_garage > 0)
        
        # Description and Pool detection
        description = data.get("text") or ""
        lead["description"] = description
        # Parse pool from description (case-insensitive, exclude "no pool")
        desc_lower = description.lower()
        lead["has_pool"] = "pool" in desc_lower and "no pool" not in desc_lower

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

    def _query_cache_for_features(self, filters: Dict, limit: int) -> List[Dict]:
        """
        Queries the in-memory lead cache for properties matching feature filters.
        Returns cached leads that match ZIP/bounds + feature criteria (pool/garage).
        
        This bypasses GIS when searching for rare features like Pool/Garage,
        enabling progressively better results as the cache grows.
        """
        if not self._lead_cache:
            return []
            
        target_zip = filters.get("zip_code")
        target_bounds = filters.get("bounds")  # Dict with xmin, ymin, xmax, ymax
        has_pool = filters.get("has_pool")
        has_garage = filters.get("has_garage")
        has_guest_house = filters.get("has_guest_house")
        min_beds = filters.get("min_beds")
        max_beds = filters.get("max_beds")
        min_baths = filters.get("min_baths")
        max_baths = filters.get("max_baths")
        min_sqft = filters.get("min_sqft")
        max_sqft = filters.get("max_sqft")
        min_year_built = filters.get("min_year_built")
        max_year_built = filters.get("max_year_built")
        
        matches = []
        
        for addr, lead in self._lead_cache.items():
            # Location filter
            if target_zip:
                lead_zip = lead.get("address_zip") or lead.get("zip")
                if not lead_zip or not str(lead_zip).startswith(str(target_zip)[:5]):
                    continue
            elif target_bounds:
                lat = lead.get("latitude")
                lon = lead.get("longitude")
                if not lat or not lon:
                    continue
                xmin = target_bounds.get("xmin") or target_bounds.get("west")
                xmax = target_bounds.get("xmax") or target_bounds.get("east")
                ymin = target_bounds.get("ymin") or target_bounds.get("south")
                ymax = target_bounds.get("ymax") or target_bounds.get("north")
                if not (xmin <= lon <= xmax and ymin <= lat <= ymax):
                    continue
                    
            # Feature filters
            if has_pool is True and not lead.get("has_pool"):
                continue
            if has_garage is True and not lead.get("has_garage"):
                continue
            if has_guest_house is True and not lead.get("has_guest_house"):
                continue
                
            # Detail filters
            if min_beds and (lead.get("beds") or 0) < min_beds:
                continue
            if max_beds and (lead.get("beds") or 0) > max_beds:
                continue
            if min_baths and (lead.get("baths") or 0) < min_baths:
                continue
            if max_baths and (lead.get("baths") or 0) > max_baths:
                continue
            if min_sqft and (lead.get("sqft") or 0) < min_sqft:
                continue
            if max_sqft and (lead.get("sqft") or 0) > max_sqft:
                continue
            if min_year_built and (lead.get("year_built") or 0) < min_year_built:
                continue
            if max_year_built and (lead.get("year_built") or 0) > max_year_built:
                continue
                
            matches.append(lead.copy())
            
            if len(matches) >= limit:
                break
                
        print(f"[Cache Query] Found {len(matches)} matching leads in cache (limit: {limit})")
        return matches

    async def fetch_fsbo(self, location: str) -> List[Dict]:
        """
        Searches for FSBO (For Sale By Owner) listings using Zillow (best for off-market).
        """
        return await self.fetch_hot_leads(location, ["FSBO"])
    
    async def fetch_hot_leads(self, location: str, hot_list: List[str], limit: int = 100, listing_statuses: List[str] = None) -> List[Dict]:
        """
        Fetches MLS listings and filters based on hot list criteria:
        - FSBO: No agent AND no brokerage (office_name)
        - Price Reduced: Has price reduction
        - High Days on Market: 60+ days listed
        - New Listing: 7 or fewer days on market
        
        Also filters by listing_statuses if provided (For Sale, Contingent, Pending, etc.)
        
        Returns normalized lead dictionaries.
        """
        if not hot_list:
            return []
        
        listing_statuses = listing_statuses or []
        print(f"Fetching Hot Leads in {location} for filters: {hot_list}, statuses: {listing_statuses}")
        
        try:
            from homeharvest import scrape_property
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: scrape_property(
                    location=location,
                    listing_type="for_sale"
                )
            )
            
            if df.empty:
                print("  No for_sale listings found")
                return []
            
            print(f"  Found {len(df)} for_sale listings, applying hot list filters...")
            
            # Convert to list of dicts for processing
            all_listings = df.to_dict("records")
            hot_leads = []
            
            # DEBUG: Log available columns and sample data
            print(f"  DEBUG: Available columns in HomeHarvest data: {list(df.columns)}")
            if len(all_listings) > 0:
                sample = all_listings[0]
                print(f"  DEBUG: Sample listing keys: {list(sample.keys())}")
                print(f"  DEBUG: Sample listing agent_name: '{sample.get('agent_name')}'")
                print(f"  DEBUG: Sample listing office_name: '{sample.get('office_name')}'")
                print(f"  DEBUG: Sample listing property_url: '{sample.get('property_url')}'")
                print(f"  DEBUG: Sample listing list_price: '{sample.get('list_price')}'")
                print(f"  DEBUG: Sample listing status: '{sample.get('status')}'")
                print(f"  DEBUG: Sample listing days_on_mls: '{sample.get('days_on_mls')}'")
            
            fsbo_candidates = 0  # Track how many pass FSBO check
            
            for listing in all_listings:
                signals = []
                
                # Check FSBO: No agent AND no brokerage (or agent is "Owner")
                if "FSBO" in hot_list:
                    agent_name = str(listing.get("agent_name") or "").strip().lower()
                    office_name = str(listing.get("office_name") or "").strip().lower()
                    
                    # FSBO = no agent AND no brokerage/office
                    agent_empty = not agent_name or agent_name in ["", "nan", "none", "owner", "for sale by owner", "fsbo"]
                    office_empty = not office_name or office_name in ["", "nan", "none", "owner", "for sale by owner", "fsbo"]
                    
                    if agent_empty and office_empty:
                        signals.append("FSBO")
                        fsbo_candidates += 1
                        # DEBUG: Log first 5 FSBO candidates
                        if fsbo_candidates <= 5:
                            print(f"  DEBUG FSBO CANDIDATE #{fsbo_candidates}:")
                            print(f"    Address: {listing.get('full_street_line') or listing.get('street')} {listing.get('city')}, {listing.get('state')} {listing.get('zip_code')}")
                            print(f"    agent_name: '{listing.get('agent_name')}' (empty: {agent_empty})")
                            print(f"    office_name: '{listing.get('office_name')}' (empty: {office_empty})")
                            print(f"    list_price: {listing.get('list_price')}")
                            print(f"    property_url: {listing.get('property_url')}")
                            print(f"    status: {listing.get('status')}")
                            print(f"    days_on_mls: {listing.get('days_on_mls')}")
                
                # Check Price Reduced
                if "Price Reduced" in hot_list:
                    # Look for price_reduced flag or keywords in description
                    is_reduced = False
                    
                    # 1. Check explicit flag
                    price_reduced = listing.get("price_reduced")
                    if price_reduced and str(price_reduced).lower() not in ["false", "nan", "none", ""]:
                        is_reduced = True
                    
                    # 2. Check description keywords if flag not found
                    if not is_reduced:
                        desc = str(listing.get("text") or "").lower()
                        if "price reduced" in desc or "price drop" in desc or "reduced price" in desc or "reduced!" in desc:
                            is_reduced = True
                            
                    if is_reduced:
                        signals.append("Price Reduced")
                
                # Check High Days on Market (60+)
                if "High Days on Market" in hot_list:
                    days_on_mls = listing.get("days_on_mls")
                    if days_on_mls is not None:
                        try:
                            if int(days_on_mls) >= 60:
                                signals.append("High Days on Market")
                        except (ValueError, TypeError):
                            pass
                
                # Check New Listing (7 or fewer days)
                if "New Listing" in hot_list:
                    days_on_mls = listing.get("days_on_mls")
                    if days_on_mls is not None:
                        try:
                            if int(days_on_mls) <= 7:
                                signals.append("New Listing")
                        except (ValueError, TypeError):
                            pass
                
                # AND logic: Include only if ALL selected hot filters match
                if len(signals) == len(hot_list):
                    # Status filtering - if listing_statuses specified, check if listing status matches
                    if listing_statuses:
                        listing_status = str(listing.get("status") or "").upper()
                        # Map HomeHarvest status to our UI status names
                        status_matches = False
                        for stat in listing_statuses:
                            stat_upper = stat.upper()
                            if stat_upper == "FOR SALE" and listing_status in ["FOR_SALE", "ACTIVE", "NEW"]:
                                status_matches = True
                            elif stat_upper == "CONTINGENT" and "CONTINGENT" in listing_status:
                                status_matches = True
                            elif stat_upper == "PENDING" and "PENDING" in listing_status:
                                status_matches = True
                            elif stat_upper == "UNDER CONTRACT" and listing_status in ["UNDER_CONTRACT", "CONTINGENT", "PENDING"]:
                                status_matches = True
                            elif stat_upper == "COMING SOON" and "COMING" in listing_status:
                                status_matches = True
                            elif stat_upper == "SOLD" and listing_status in ["SOLD", "CLOSED"]:
                                status_matches = True
                        if not status_matches:
                            continue  # Skip this listing - status doesn't match
                    # Normalize to our lead format
                    lead = self._normalize_homeharvest_listing(listing, signals)
                    
                    # VALIDATION: Filter out leads with missing essential data
                    if not lead.get("address") or lead.get("address") == "None, None, AZ ":
                        print(f"  DEBUG: Skipping FSBO - invalid address: {lead.get('address')}")
                        continue
                    if not lead.get("list_price") and not lead.get("estimated_value"):
                        print(f"  DEBUG: Skipping FSBO - no price: {lead.get('address')}")
                        continue
                        
                    hot_leads.append(lead)
            
            print(f"  DEBUG: {fsbo_candidates} listings matched FSBO criteria (no agent/office)")
            print(f"  {len(hot_leads)} leads matched hot list filters (after validation)")
            # Return ALL matches - limit will be applied after distress filtering
            return hot_leads
            
        except Exception as e:
            print(f"Error fetching hot leads: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _normalize_homeharvest_listing(self, listing: Dict, hot_signals: List[str]) -> Dict:
        """
        Converts a Homeharvest listing record to our standard lead format.
        """
        # Build address - prefer formatted_address, then construct from components
        full_address = listing.get("formatted_address") or ""
        street = listing.get("full_street_line") or listing.get("street") or listing.get("street_address") or ""
        city = listing.get("city") or ""
        state = listing.get("state") or "AZ"
        zip_code = listing.get("zip_code") or ""
        
        if not full_address and street:
            full_address = f"{street}, {city}, {state} {zip_code}".strip(", ")
        
        # Determine data source from property_url (realtor.com, zillow.com, redfin.com)
        property_url = listing.get("property_url") or ""
        mls_source = "MLS"
        if "realtor.com" in property_url.lower():
            mls_source = "Realtor.com"
        elif "zillow.com" in property_url.lower():
            mls_source = "Zillow"
        elif "redfin.com" in property_url.lower():
            mls_source = "Redfin"
        elif "trulia.com" in property_url.lower():
            mls_source = "Trulia"
        else:
            # Fallback to MLS name if available
            mls_name = listing.get("mls")
            if mls_name:
                mls_source = f"MLS ({mls_name})"
        
        return {
            "source": "homeharvest_mls",
            "mls_source": mls_source,  # Provider: Realtor.com, Zillow, Redfin, etc.
            "parcel_id": str(listing.get("property_id") or ""),  # Internal ID, not actual APN
            "mls_id": str(listing.get("mls_id") or ""),  # MLS listing ID
            "owner_name": listing.get("agent_name") or "Unknown",
            "address": full_address,
            "address_street": street,
            "address_city": city,
            "address_state": state,
            "address_zip": str(zip_code),
            "property_type": listing.get("style") or listing.get("property_type") or "Unknown",
            "beds": listing.get("beds"),
            "baths": listing.get("full_baths"),
            "half_baths": listing.get("half_baths"),
            "sqft": listing.get("sqft"),
            "lot_size": listing.get("lot_sqft"),
            "year_built": listing.get("year_built"),
            "stories": listing.get("stories"),
            "assessed_value": listing.get("assessed_value"),
            "estimated_value": listing.get("estimated_value"),
            "list_price": listing.get("list_price"),
            "price_per_sqft": listing.get("price_per_sqft"),
            "days_on_market": listing.get("days_on_mls"),
            "list_date": str(listing.get("list_date")) if listing.get("list_date") else None,
            "hoa_fee": listing.get("hoa_fee"),
            "last_sold_price": listing.get("last_sold_price"),
            "last_sold_date": str(listing.get("last_sold_date")) if listing.get("last_sold_date") else None,
            "agent_name": listing.get("agent_name"),
            "office_name": listing.get("office_name"),
            "latitude": float(listing.get("latitude")) if listing.get("latitude") and str(listing.get("latitude")).lower() != "nan" else None,
            "longitude": float(listing.get("longitude")) if listing.get("longitude") and str(listing.get("longitude")).lower() != "nan" else None,
            "status": listing.get("status") or "Active",
            "listing_description": listing.get("text") or "",  # MLS listing description
            "strategy": "Wholesale",
            "distress_signals": hot_signals,
            "assessor_url": property_url,
            "photos": listing.get("primary_photo") or None,
            "primary_photo": listing.get("primary_photo"),
            "alt_photos": listing.get("alt_photos") or "",  # Comma-separated list of photo URLs
        }
    
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
            
            # Fix for "Pima" or "Pima County" being treated as a neighborhood
            # Redirect to "Pima County" city search (aggregates all jurisdictions)
            hood = (filters.get("neighborhood") or "").lower().strip()
            if hood in ["pima", "pima county"]:
                print(f"[Scout] Redirecting 'Pima' neighborhood search to 'Pima County' wide search")
                filters["neighborhood"] = None
                filters["city"] = "Pima County"
                filters["county"] = "Pima"
            
            # Fix for Street Names being treated as Neighborhoods (e.g. "Oracle Rd")
            # If neighborhood ends in common street suffix, treat as address search
            street_suffixes = [" rd", " st", " ave", " blvd", " ln", " dr", " ct", " pl", " way", " ter", " cir", " hwy", " pkwy"]
            if hood and any(hood.endswith(s) for s in street_suffixes):
                print(f"[Scout] Redirecting neighborhood search '{hood}' to address search")
                filters["address"] = filters.get("neighborhood") # Capture value FIRST
                filters["neighborhood"] = None # Then clear it
            
            # ===== HOT LIST FILTER HANDLING =====
            # If hot_list filters are selected, fetch from MLS and return those leads
            hot_list = filters.get("hot_list") or []
            if hot_list:
                # Separate MLS-based filters from GIS-based filters
                mls_filters = [f for f in hot_list if f != "Path of Progress"]
                has_pop = "Path of Progress" in hot_list
                
                # Determine location for search
                location = filters.get("zip_code") or filters.get("city") or filters.get("neighborhood")
                if not location and filters.get("bounds"):
                    location = "Tucson, AZ"
                elif not location:
                    location = "Tucson, AZ"
                
                hot_results = []
                
                # If ONLY Path of Progress selected, use regular parcel search with PoP enrichment
                if has_pop and not mls_filters:
                    print(f"Hot List search: Path of Progress only - using GIS spatial search")
                    # Fall through to regular search - PoP will be enriched by GIS layers
                    # But add Path of Progress as a distress filter
                    modified_filters = {**filters}
                    # Remove hot_list so we don't infinitely recurse
                    modified_filters["hot_list"] = []
                    # Proceed with regular parcel search below
                elif mls_filters:
                    # Fetch from MLS for FSBO, Price Reduced, High DOM, New Listing
                    print(f"Hot List search: {mls_filters} in {location}")
                    listing_statuses = filters.get("listing_statuses") or []
                    hot_results = await self.fetch_hot_leads(location, mls_filters, limit, listing_statuses)
                
                if hot_results:
                    # Optionally filter by property type if specified
                    property_types = filters.get("property_types") or []
                    if property_types and "all" not in [t.lower() for t in property_types]:
                        # Normalize property type matching for Homeharvest styles
                        # Homeharvest uses: SINGLE_FAMILY, CONDOS, TOWNHOUSES, MULTI_FAMILY, etc.
                        type_mapping = {
                            "single family": ["single", "house", "sfr"],
                            "multi family": ["multi", "duplex", "triplex", "fourplex"],
                            "condo": ["condo"],
                            "townhouse": ["townhouse", "townhome"],
                            "mobile home": ["mobile", "manufactured"],
                            "vacant land": ["land", "lot"],
                        }
                        
                        def matches_property_type(lead_type: str, filters: list) -> bool:
                            lead_type_lower = lead_type.lower().replace("_", " ")
                            for f in filters:
                                f_lower = f.lower()
                                # Direct match
                                if f_lower in lead_type_lower:
                                    return True
                                # Check mapping
                                keywords = type_mapping.get(f_lower, [f_lower])
                                if any(kw in lead_type_lower for kw in keywords):
                                    return True
                            return False
                        
                        filtered = [r for r in hot_results 
                                   if matches_property_type(r.get("property_type", ""), property_types)]
                        
                        # STRICT FILTERING: Only return matches
                        hot_results = filtered
                        
                        if not hot_results:
                            print(f"  Property type filter removed all results.")
                    
                    # Apply min/max filters for beds, baths, sqft
                    min_beds = filters.get("min_beds")
                    max_beds = filters.get("max_beds")
                    min_baths = filters.get("min_baths")
                    max_baths = filters.get("max_baths")
                    min_sqft = filters.get("min_sqft")
                    max_sqft = filters.get("max_sqft")
                    
                    if any([min_beds, max_beds, min_baths, max_baths, min_sqft, max_sqft]):
                        print(f"  Applying property detail filters: beds={min_beds}-{max_beds}, baths={min_baths}-{max_baths}, sqft={min_sqft}-{max_sqft}")
                        
                        def matches_property_details(lead: Dict) -> bool:
                            # Beds filter
                            if min_beds is not None:
                                beds = lead.get("beds") or 0
                                if beds < min_beds:
                                    return False
                            if max_beds is not None:
                                beds = lead.get("beds") or 0
                                if beds > max_beds:
                                    return False
                            # Baths filter
                            if min_baths is not None:
                                baths = lead.get("baths") or 0
                                if baths < min_baths:
                                    return False
                            if max_baths is not None:
                                baths = lead.get("baths") or 0
                                if baths > max_baths:
                                    return False
                            # Sqft filter
                            if min_sqft is not None:
                                sqft = lead.get("sqft") or 0
                                if sqft < min_sqft:
                                    return False
                            if max_sqft is not None:
                                sqft = lead.get("sqft") or 0
                                if sqft > max_sqft:
                                    return False
                            return True
                        
                        hot_results = [r for r in hot_results if matches_property_details(r)]
                        print(f"  After property detail filters: {len(hot_results)} results")
                    
                    # ===== GIS ENRICHMENT FIRST =====
                    # Enrich MLS leads with GIS data BEFORE distress check (needed for absentee owner check)
                    await self._enrich_with_gis_layers(hot_results)
                    
                    # ===== DISTRESS TYPE CROSS-REFERENCING (Direct Per-Lead Lookup) =====
                    # Instead of fetching a separate list and matching addresses,
                    # we check each FSBO lead directly for distress indicators
                    distress_types = filters.get("distress_type") or []
                    if distress_types and hot_results:
                        print(f"  Checking {len(hot_results)} leads for distress types: {distress_types}")
                        
                        check_code_violations = any("code violation" in d.lower() for d in distress_types)
                        check_absentee = any("absentee" in d.lower() for d in distress_types)
                        
                        # If checking code violations, fetch violations for the search area
                        # and create a coordinate-based lookup
                        violation_coords = set()
                        if check_code_violations:
                            try:
                                cv_results = await self._fetch_code_violations(filters, limit=1000)
                                # Create coordinate lookup (rounded for matching)
                                for cv in cv_results:
                                    lat = cv.get("latitude") or cv.get("lat")
                                    lng = cv.get("longitude") or cv.get("lng") or cv.get("lon")
                                    if lat and lng:
                                        # Round to 4 decimal places (~11 meter accuracy)
                                        coord_key = (round(float(lat), 4), round(float(lng), 4))
                                        violation_coords.add(coord_key)
                                print(f"    Loaded {len(cv_results)} code violations, {len(violation_coords)} unique coordinates")
                            except Exception as e:
                                print(f"    Error fetching code violations: {e}")
                        
                        def lead_has_distress(lead: Dict) -> bool:
                            """Check if lead matches any selected distress type."""
                            # Absentee Owner Check: mailing address != property address
                            if check_absentee:
                                mailing = lead.get("mailing_address", "").upper().strip()
                                property_addr = lead.get("address", "").upper().strip()
                                # Extract just street portion (before city/state)
                                mailing_street = mailing.split(",")[0].strip() if mailing else ""
                                property_street = property_addr.split(",")[0].strip() if property_addr else ""
                                
                                if mailing_street and property_street and mailing_street != property_street:
                                    lead["distress_signals"] = lead.get("distress_signals", []) + ["Absentee Owner"]
                                    return True
                            
                            # Code Violation Check: coordinates match violation locations
                            if check_code_violations and violation_coords:
                                lat = lead.get("latitude") or lead.get("lat")
                                lng = lead.get("longitude") or lead.get("lng") or lead.get("lon")
                                if lat and lng:
                                    coord_key = (round(float(lat), 4), round(float(lng), 4))
                                    if coord_key in violation_coords:
                                        lead["distress_signals"] = lead.get("distress_signals", []) + ["Code Violation"]
                                        return True
                            
                            return False
                        
                        before_count = len(hot_results)
                        matching = [r for r in hot_results if lead_has_distress(r)]
                        
                        # Debug output
                        if len(matching) == 0 and before_count > 0:
                            sample = hot_results[0]
                            print(f"    DEBUG: No matches. Sample lead:")
                            print(f"      Address: {sample.get('address', '')}")
                            print(f"      Mailing: {sample.get('mailing_address', 'N/A')}")
                            print(f"      Coords: ({sample.get('latitude')}, {sample.get('longitude')})")
                        
                        hot_results = matching
                        print(f"    After distress check: {len(hot_results)} of {before_count} leads have matching distress")
                    else:
                        # No distress filter - still do GIS enrichment (already done above)
                        pass
                    
                    return hot_results[:limit]
                else:
                    print("No hot list results found - returning empty (not falling back to regular search)")
                    # When user specifically filters for FSBO/Price Reduced/etc, don't return unrelated results
                    return []
            
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
                    # Respect skip_homeharvest flag
                    skip_hh = filters.get("skip_homeharvest", False)
                    if skip_hh:
                        print("Fast mode: skipping HomeHarvest enrichment (skip_homeharvest=True)")
                        gis_task = asyncio.create_task(self._enrich_with_gis_layers(candidates))
                        try:
                            await asyncio.wait_for(gis_task, timeout=20.0)
                        except asyncio.TimeoutError:
                            print("GIS Enrichment timed out, returning partial results")
                            gis_task.cancel()
                    else:
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
                    # PERF: Limit enrichment to 3x limit (not all candidates)
                    max_to_enrich = min(len(candidates), limit * 3)
                    candidates_to_check = candidates[:max_to_enrich]
                    print(f"[PERF] Limiting early parcel enrichment to {max_to_enrich} of {len(candidates)} candidates")
                    
                    # OPTIMIZATION: Apply cache FIRST to avoid redundant parcel API calls
                    early_cache_hits = self._apply_cached_enrichment(candidates_to_check)
                    if early_cache_hits > 0:
                        print(f"AND-Logic: Applied cache to {early_cache_hits}/{len(candidates_to_check)} candidates")
                    
                    # Only enrich candidates that don't have mailing_address from cache
                    needs_parcel = [c for c in candidates_to_check if not c.get("mailing_address")]
                    if needs_parcel:
                        print(f"AND-Logic: Early parcel enrichment for {len(needs_parcel)} candidates...")
                        await self._enrich_violations_with_parcel_data(needs_parcel)
                        
                        # Save enriched candidates to cache for faster subsequent searches
                        saved = self._save_to_lead_cache(candidates_to_check)
                        print(f"AND-Logic: Saved {saved} candidates to cache")
                    else:
                        print(f"AND-Logic: Skipping early parcel enrichment ({early_cache_hits} have mailing_address from cache)")
                    
                    # Replace candidates with the enriched subset for absentee filtering
                    candidates = candidates_to_check
                
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

            # ===== SMART ENRICHMENT STRATEGY =====
            # If we are filtering for rare features (Pool/Garage) that require enrichment,
            # we cannot truncate candidates to 'limit' BEFORE enrichment.
            # Instead, we must process candidates in batches until we find enough matches.
            
            has_pool = filters.get("has_pool")
            has_garage = filters.get("has_garage")
            has_guest_house = filters.get("has_guest_house")
            
            # Guest House is now handled at GIS level, so it doesn't trigger smart enrichment
            smart_enrichment_needed = bool(has_pool or has_garage)
            
            final_results = []
            
            # ===== CACHE-FIRST STRATEGY FOR POOL/GARAGE =====
            # Query cache BEFORE fetching new data from GIS
            if smart_enrichment_needed:
                cache_hits = self._query_cache_for_features(filters, limit)
                if cache_hits:
                    final_results.extend(cache_hits)
                    print(f"[Cache-First] Got {len(cache_hits)} results from cache")
                    
                    if len(final_results) >= limit:
                        # Cache satisfied the full request - skip GIS entirely!
                        print(f"[Cache-First] Cache satisfied full request ({len(final_results)} >= {limit}). Skipping GIS fetch.")
                        final_results = final_results[:limit]
                        smart_enrichment_needed = False  # Skip the GIS loop below
                    else:
                        # Cache gave partial results - dedupe candidates to avoid re-processing
                        cached_addrs = {(c.get("address") or "").upper() for c in cache_hits}
                        original_count = len(candidates)
                        candidates = [c for c in candidates if (c.get("address") or "").upper() not in cached_addrs]
                        print(f"[Cache-First] Deduped candidates: {original_count} -> {len(candidates)} (removed {original_count - len(candidates)} already cached)")
                        # Update limit for remaining fetch
                        limit = limit - len(cache_hits)
                        print(f"[Cache-First] Need {limit} more results from GIS")
            
            if smart_enrichment_needed:
                print(f"[Scout] Smart Enrichment Active: Fetching candidates until {limit} matches found...")
                
                # We have a large pool of 'candidates' (up to 5x-10x limit from earlier fetch)
                # Process them in batches
                batch_size = 25
                processed_count = 0
                
                while len(final_results) < limit and processed_count < len(candidates):
                    # Take next batch
                    batch = candidates[processed_count : processed_count + batch_size]
                    processed_count += len(batch)
                    
                    if not batch:
                        break
                        
                    print(f"[Scout] Processing batch {processed_count//batch_size} ({len(batch)} leads)... Found {len(final_results)}/{limit} so far.")
                    
                    # Enrich this batch
                    # Step 1: Apply cache
                    self._apply_cached_enrichment(batch)
                    
                    # Step 2: Run HomeHarvest + GIS (Parallel)
                    skip_hh = filters.get("skip_homeharvest", False)
                    gis_task = asyncio.create_task(self._enrich_with_gis_layers(batch))
                    
                    if skip_hh:
                        self._apply_homeharvest_from_cache(batch)
                        try:
                            await asyncio.wait_for(gis_task, timeout=30.0)
                        except asyncio.TimeoutError:
                            gis_task.cancel()
                    else:
                        hh_task = asyncio.create_task(self._enrich_with_homeharvest(batch))
                        try:
                            await asyncio.wait_for(
                                asyncio.gather(hh_task, gis_task, return_exceptions=True),
                                timeout=90.0
                            )
                        except asyncio.TimeoutError:
                            hh_task.cancel()
                            gis_task.cancel()
                            
                    # Step 3: Apply Filters IMMEDIATELY to this batch
                    # Define filter function (same as below, but applied per batch)
                    min_beds = filters.get("min_beds")
                    max_beds = filters.get("max_beds")
                    min_baths = filters.get("min_baths")
                    max_baths = filters.get("max_baths")
                    min_sqft = filters.get("min_sqft")
                    max_sqft = filters.get("max_sqft")
                    min_year_built = filters.get("min_year_built")
                    max_year_built = filters.get("max_year_built")
                    
                    def matches_details(lead: Dict) -> bool:
                        # Pool/Garage (The reason we are here)
                        if has_pool is True and not lead.get("has_pool"): return False
                        if has_garage is True and not lead.get("has_garage"): return False
                        
                        # Other details
                        if min_beds and (lead.get("beds") or 0) < min_beds: return False
                        if max_beds and (lead.get("beds") or 0) > max_beds: return False
                        if min_baths and (lead.get("baths") or 0) < min_baths: return False
                        if max_baths and (lead.get("baths") or 0) > max_baths: return False
                        if min_sqft and (lead.get("sqft") or 0) < min_sqft: return False
                        if max_sqft and (lead.get("sqft") or 0) > max_sqft: return False
                        if min_year_built and (lead.get("year_built") or 0) < min_year_built: return False
                        if max_year_built and (lead.get("year_built") or 0) > max_year_built: return False
                        
                        return True
                        
                    # Filter batch
                    valid_leads = [l for l in batch if matches_details(l)]
                    final_results.extend(valid_leads)
                    
                    print(f"[Scout] Batch result: {len(valid_leads)} valid matches. Total: {len(final_results)}")
                    
            else:
                # Standard Logic (Truncate -> Enrich -> Filter)
                # This is faster for common searches where we don't expect high drop-off
                print(f"AND-Logic: Final result count: {len(candidates[:limit])}")
                final_results = candidates[:limit]
                
                # Enrich
                skip_enrichment = filters.get("skip_enrichment", False)
                if not skip_enrichment:
                    self._apply_cached_enrichment(final_results)
                    
                    # Code Violations / Zip enrichment (legacy support)
                    if primary == "Code Violations":
                        unenriched = [l for l in final_results if not l.get("_parcel_enriched") and not l.get("_cache_enriched")]
                        if unenriched: await self._enrich_violations_with_parcel_data(unenriched)
                    
                    leads_needing_zip = [l for l in final_results if not l.get("address_zip")]
                    if leads_needing_zip: await self._enrich_violations_with_zip_codes(leads_needing_zip)

                    # HomeHarvest + GIS
                    skip_hh = filters.get("skip_homeharvest", False)
                    gis_task = asyncio.create_task(self._enrich_with_gis_layers(final_results))
                    
                    if skip_hh:
                        self._apply_homeharvest_from_cache(final_results)
                        try:
                            await asyncio.wait_for(gis_task, timeout=30.0)
                        except asyncio.TimeoutError:
                            gis_task.cancel()
                    else:
                        hh_task = asyncio.create_task(self._enrich_with_homeharvest(final_results))
                        try:
                            await asyncio.wait_for(asyncio.gather(hh_task, gis_task, return_exceptions=True), timeout=90.0)
                        except asyncio.TimeoutError:
                            hh_task.cancel()
                            gis_task.cancel()

            # Tax delinquency check (rarely used)
            if len(final_results) <= 10 and not filters.get("skip_tax_check", True):
                await self._check_tax_delinquency(final_results)

            # Save to cache
            self._save_to_lead_cache(final_results)

            # Final Truncate (in case smart loop overshot slightly)
            final_results = final_results[:limit]
            
            # Apply filters one last time for Standard Logic path (Smart path already did it)
            if not smart_enrichment_needed:
                # Re-apply filters for standard path just in case
                # (Logic copied from original code for safety)
                min_beds = filters.get("min_beds")
                max_beds = filters.get("max_beds")
                min_baths = filters.get("min_baths")
                max_baths = filters.get("max_baths")
                min_sqft = filters.get("min_sqft")
                max_sqft = filters.get("max_sqft")
                min_year_built = filters.get("min_year_built")
                max_year_built = filters.get("max_year_built")
                has_pool = filters.get("has_pool")
                has_garage = filters.get("has_garage")
                has_guest_house = filters.get("has_guest_house")
                
                if any([min_beds, max_beds, min_baths, max_baths, min_sqft, max_sqft, 
                        min_year_built, max_year_built, has_pool, has_garage, has_guest_house]):
                    
                    def matches_property_details_final(lead: Dict) -> bool:
                        if min_beds and (lead.get("beds") or 0) < min_beds: return False
                        if max_beds and (lead.get("beds") or 0) > max_beds: return False
                        if min_baths and (lead.get("baths") or 0) < min_baths: return False
                        if max_baths and (lead.get("baths") or 0) > max_baths: return False
                        if min_sqft and (lead.get("sqft") or 0) < min_sqft: return False
                        if max_sqft and (lead.get("sqft") or 0) > max_sqft: return False
                        if min_year_built and (lead.get("year_built") or 0) < min_year_built: return False
                        if max_year_built and (lead.get("year_built") or 0) > max_year_built: return False
                        if has_pool is True and not lead.get("has_pool"): return False
                        if has_garage is True and not lead.get("has_garage"): return False
                        # Guest House handled at GIS level, but double check here
                        if has_guest_house is True and not lead.get("has_guest_house"): return False
                        return True
                        
                    final_results = [l for l in final_results if matches_property_details_final(l)]

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
        Fetches zip code geometry metadata (uses cache):
        1. Native Envelope (2868) for API Query.
        2. WGS84 Polygon (4326) for Client-Side Filtering.
        """
        # Check cache first
        if zip_code in self._zip_metadata_cache:
            cached = self._zip_metadata_cache[zip_code]
            self._log(f"Using cached metadata for zip {zip_code}")
            return cached
        
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
                # Cache the result
                self._zip_metadata_cache[zip_code] = metadata
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



    JURISDICTIONS = [
        "MARANA", "ORO VALLEY", "SAHUARITA", "SOUTH TUCSON", "TUCSON", "UNINCORPORATED PIMA COUNTY"
    ]

    async def _fetch_zips_by_city(self, city: str) -> List[str]:
        """Fetches Zip Codes from Layer 3 (Addresses) for a given ZIPCITY. Uses cache."""
        cache_key = city.upper()
        
        # Check cache first
        if cache_key in self._city_zips_cache:
            cached = self._city_zips_cache[cache_key]
            print(f"[Scout] Using cached zips for city '{city}': {len(cached)} zips")
            return cached
            
        # 1. Check Hardcoded CITY_ZIP_MAP first (Highest Priority)
        if cache_key in self.CITY_ZIP_MAP:
            zips = self.CITY_ZIP_MAP[cache_key]
            print(f"[Scout] Using curated zip map for '{city}': {zips}")
            self._city_zips_cache[cache_key] = zips
            return zips

        # Special handling for "Pima County" - aggregate all jurisdictions
        if city.upper() in ["PIMA", "PIMA COUNTY"]:
            print(f"[Scout] Aggregating zips for entire Pima County...")
            all_zips = set()
            
            # Fetch all jurisdictions in parallel
            tasks = [self._fetch_zips_by_city(j) for j in self.JURISDICTIONS]
            results = await asyncio.gather(*tasks)
            
            for res in results:
                all_zips.update(res)
            
            unique_zips = sorted(list(all_zips))
            print(f"[Scout] Found {len(unique_zips)} unique zips in Pima County")
            
            # Cache and return
            self._city_zips_cache[cache_key] = unique_zips
            return unique_zips
        
        url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/Addresses/MapServer/3/query"
        
        url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/Addresses/MapServer/3/query"
        params = {
            "where": f"ZIPCITY = '{city.upper()}'",
            "outFields": "ZIPCODE",
            "returnGeometry": "false",
            "returnDistinctValues": "true",
            "f": "json"
        }
        
        try:
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(None, lambda: requests.get(url, params=params, timeout=10))
            
            if resp.status_code == 200:
                data = resp.json()
                features = data.get("features", [])
                zips = [str(f["attributes"]["ZIPCODE"]) for f in features if f.get("attributes") and f["attributes"].get("ZIPCODE")]
                unique_zips = sorted(list(set(zips)))
                
                # Filter for Tucson if applicable
                if city.upper() == "TUCSON":
                    print(f"[Scout] Filtering Tucson zips against allowlist (removing suburbs)...")
                    original_count = len(unique_zips)
                    unique_zips = [z for z in unique_zips if z in self.TUCSON_ZIPS]
                    print(f"[Scout] Filtered Tucson zips: {original_count} -> {len(unique_zips)}")
                
                # Cache the result
                self._city_zips_cache[cache_key] = unique_zips
                print(f"[Scout] Cached {len(unique_zips)} zips for city '{city}'")
                    
                return unique_zips
            return []
        except Exception as e:
            print(f"[Scout] Error fetching zips for city {city}: {e}")
            return []

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
            city = filters['city'].upper()
            # Only apply JURIS_OL for known official jurisdictions
            # Exclude Oracle, San Manuel, Catalina, Ajo, Sells as they are likely Unincorporated
            official_jurisdictions = ["TUCSON", "SOUTH TUCSON", "MARANA", "ORO VALLEY", "SAHUARITA"]
            
            if city in self.JURISDICTIONS and city in official_jurisdictions:
                where_parts.append(f"JURIS_OL = '{city}'")
            else:
                # Not a jurisdiction (e.g. Vail, Green Valley, Oracle) - Use Spatial/Zip Filter
                print(f"DEBUG: Handling city filter in parcels: {city}")
                
                city_zips = await self._fetch_zips_by_city(city)
                if city_zips:
                    print(f"DEBUG: Mapped city '{city}' to zips: {city_zips}")
                    
                    # STRICT ZIP FILTERING: Enforce zip codes to prevent envelope overlap pollution
                    # This fixes issues where Oracle (85623) envelope overlaps with Tucson (85739)
                    formatted_zips = ",".join([f"'{z}'" for z in city_zips])
                    where_parts.append(f"ZIP IN ({formatted_zips})")
                    
                    # Fetch envelopes for ALL zips and create a union envelope
                    min_x, min_y = float('inf'), float('inf')
                    max_x, max_y = float('-inf'), float('-inf')
                    polygons = []
                    
                    for z in city_zips:
                        zm = await self._get_zip_metadata(z)
                        if zm and "envelope" in zm:
                            env = zm["envelope"]
                            min_x = min(min_x, env["xmin"])
                            min_y = min(min_y, env["ymin"])
                            max_x = max(max_x, env["xmax"])
                            max_y = max(max_y, env["ymax"])
                            if "polygon" in zm:
                                polygons.append(zm["polygon"])
                    
                    if min_x != float('inf'):
                        # Create union envelope
                        zip_metadata = {
                            "envelope": {
                                "xmin": min_x,
                                "ymin": min_y,
                                "xmax": max_x,
                                "ymax": max_y,
                                "spatialReference": {"wkid": 2868} # Layer 6 returns 2868 usually
                            },
                            "polygon": None
                        }
                        
                        # Create client-side filter
                        if polygons:
                            try:
                                zip_metadata["polygon"] = prep(unary_union(polygons))
                            except Exception as e:
                                print(f"Error creating union polygon for city parcels: {e}")
                        
                        self._log(f"Using City Bounds for {city}: {zip_metadata['envelope']}")
                    else:
                         print(f"Warning: Could not resolve envelopes for city zips: {city_zips}")
                         # Fallback to JURIS_OL just in case, BUT only if it's a jurisdiction
                         if city in self.JURISDICTIONS and city in official_jurisdictions:
                             where_parts.append(f"JURIS_OL = '{city}'")
                         else:
                             print(f"Skipping JURIS_OL fallback for non-jurisdiction: {city}")

                else:
                    # Fallback: Try JURIS_OL anyway
                    print(f"Warning: City '{city}' is not a jurisdiction and no zips found. Using JURIS_OL fallback.")
                    if city in self.JURISDICTIONS and city in official_jurisdictions:
                        where_parts.append(f"JURIS_OL = '{city}'")
                    else:
                        print(f"Skipping JURIS_OL fallback for non-jurisdiction: {city}")
            
        if filters.get('address'):
            # Normalize address for GIS matching (Ave->AV, Street->ST, etc.)
            addr = self._normalize_address(filters['address'])
            where_parts.append(f"ADDRESS_OL LIKE '%{addr}%'")

        # 2. Property Type Filters (OR logic - any selected type matches)
        # Only apply filter if specific types selected (not empty, not "all")
        property_types = filters.get('property_types') or []
        property_subtypes = filters.get('property_subtypes') or []  # Explicit parcel codes
        
        if property_subtypes:
            # Use explicit sub-type codes directly (e.g. "81" for Vacant Land - Residential)
            prefixes = property_subtypes
        elif property_types and "all" not in [t.lower() for t in property_types]:
            prefixes = self._get_codes_for_types(property_types)
        else:
            prefixes = []
            
        if prefixes:
            # Use LIKE 'prefix%' for each prefix, combined with OR
            # e.g. (PARCEL_USE LIKE '01%' OR PARCEL_USE LIKE '03%')
            # Add Guest House filter (018x) if requested
            # CRITICAL FIX: If Guest House is requested, we should PRIORITIZE it over generic Single Family (01)
            # Otherwise, the limit (100) gets filled with standard SFRs (0100) and we filter them all out later
            if filters.get("has_guest_house"):
                print("DEBUG: Optimizing Guest House search - Replacing generic '01'/'87' with '018'")
                # Remove generic SFR prefixes if present
                if "01" in prefixes: prefixes.remove("01")
                if "87" in prefixes: prefixes.remove("87")
                # Add specific Guest House prefix
                if "018" not in prefixes: prefixes.append("018")
                
                # Re-generate conditions with updated prefixes
                prefix_conditions = [f"PARCEL_USE LIKE '{p}%'" for p in prefixes]
            else:
                prefix_conditions = [f"PARCEL_USE LIKE '{p}%'" for p in prefixes]
                
            where_parts.append(f"({' OR '.join(prefix_conditions)})")
                
            where_parts.append(f"({' OR '.join(prefix_conditions)})")
        elif filters.get("has_guest_house"):
            # Guest House ONLY (no other types selected)
            print("DEBUG: Filtering for Guest House ONLY (018%)")
            where_parts.append("PARCEL_USE LIKE '018%'")

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
                    # Use limit parameter to cap fetch (with 2x buffer for polygon filtering)
                    max_id_fetch = min(limit * 2, 15000)  # Fetch 2x limit but cap at 15000
                    
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
                        
                        # Limit total detail fetches to avoid timeout if area is huge
                        # For weighted allocation, respect the requested limit
                        # Use the passed limit directly (caller handles inflation)
                        max_detail_fetch = limit
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
                
                # POST-ENRICHMENT FILTER: Ensure leads actually match the requested zip/city
                # This handles cases where Layer 12 has outdated/incorrect zip data (e.g. Oracle 85623 vs 85739)
                if filters.get('zip_code'):
                    req_zip = filters['zip_code']
                    # Filter out leads that don't match the requested zip prefix
                    # Use startswith to handle 5-digit vs 9-digit zips
                    original_count = len(leads)
                    leads = [l for l in leads if l.get('address_zip', '').startswith(req_zip)]
                    if len(leads) < original_count:
                        self._log(f"Filtered {original_count - len(leads)} leads with mismatched zips (Requested: {req_zip})")
                
                with open("debug_scout_trace.log", "a") as f:
                    f.write("Enrichment complete.\n")
                
                # Shuffle results to prevent geographic clustering (GIS returns in OBJECTID order)
                import random
                random.shuffle(leads)
                
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
        
        # Property Type Mapping (Use comprehensive mapping function)
        use_code = attr.get("PARCEL_USE", "")
        prop_type = self._map_parcel_use_to_type(use_code)
        
        # Guest House Detection: PARCEL_USE 018x = SFR with Additional Unit (Guest House)
        has_guest_house = str(use_code).startswith("018") if use_code else False
        
        # Extract Assessed Value and Zoning directly
        assessed_value = attr.get("FCV")
        zoning = attr.get("CURZONE_OL")

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
            # Property features (pool/garage from HomeHarvest, guest house from PARCEL_USE)
            "has_pool": None,  # Detected from HomeHarvest description
            "has_garage": None,  # Detected from HomeHarvest parking_garage
            "garage_spaces": None,
            "has_guest_house": has_guest_house,  # Detected from PARCEL_USE 018x
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
        Uses multi-zip parallel strategy for city searches to get geographic distribution.
        """
        import random
        import asyncio
        
        # Helper function to check if a lead is absentee owner
        def is_absentee(lead: Dict) -> bool:
            prop_addr = lead.get("address", "").upper().strip()
            mail_addr = lead.get("mailing_address", "").upper().strip()
            
            if not prop_addr or not mail_addr:
                return False
            
            # 1. Check Zip Code Difference (Strongest Signal)
            prop_zip = lead.get("address_zip", "").split("-")[0]
            
            # Extract zip from mailing address (look for 5 digits)
            import re
            # Look for zip at the end or near end of string
            mail_zip_match = re.search(r'\b(\d{5})\b', mail_addr)
            if mail_zip_match:
                mail_zip = mail_zip_match.group(1)
                # If zips are valid and different, it's absentee
                if prop_zip and mail_zip and prop_zip != mail_zip:
                    if "Absentee Owner" not in lead.get("distress_signals", []):
                        lead["distress_signals"] = lead.get("distress_signals", []) + ["Absentee Owner"]
                    return True

            # 2. Fallback to Street Match (if Zips match or Mail Zip missing)
            # This handles cases where owner lives on same street but different number (rare)
            # or if mailing address is just "PO BOX 123" (no street match)
            prop_street = prop_addr.split(",")[0].strip()
            
            # NORMALIZE ADDRESSES (Handle AV vs AVE, BL vs BLVD, etc.)
            def normalize_suffix(addr_str):
                replacements = {
                    r'\bAV\b': 'AVE',
                    r'\bAVE\b': 'AVE',
                    r'\bBL\b': 'BLVD',
                    r'\bBLVD\b': 'BLVD',
                    r'\bWY\b': 'WAY',
                    r'\bWAY\b': 'WAY',
                    r'\bPL\b': 'PLACE',
                    r'\bPLACE\b': 'PLACE',
                    r'\bTR\b': 'TRAIL',
                    r'\bTRAIL\b': 'TRAIL',
                    r'\bPK\b': 'PKWY',
                    r'\bPKWY\b': 'PKWY',
                    r'\bRD\b': 'ROAD',
                    r'\bROAD\b': 'ROAD',
                    r'\bST\b': 'STREET',
                    r'\bSTREET\b': 'STREET',
                    r'\bDR\b': 'DRIVE',
                    r'\bDRIVE\b': 'DRIVE',
                    r'\bLN\b': 'LANE',
                    r'\bLANE\b': 'LANE',
                    r'\bCT\b': 'COURT',
                    r'\bCOURT\b': 'COURT',
                    r'\bCI\b': 'CIRCLE',
                    r'\bCIR\b': 'CIRCLE',
                    r'\bCIRCLE\b': 'CIRCLE',
                    r'\bTE\b': 'TERRACE',
                    r'\bTER\b': 'TERRACE',
                    r'\bTERRACE\b': 'TERRACE',
                    r'\bLP\b': 'LOOP',
                    r'\bLOOP\b': 'LOOP',
                    r'\bHWY\b': 'HIGHWAY',
                    r'\bHIGHWAY\b': 'HIGHWAY'
                }
                for pattern, repl in replacements.items():
                    addr_str = re.sub(pattern, repl, addr_str)
                return addr_str

            norm_prop = normalize_suffix(prop_street)
            norm_mail = normalize_suffix(mail_addr)
            
            # Heuristic: If property street is NOT in mailing address, it's likely absentee
            # Use Regex Word Boundaries to avoid partial matches (e.g. "123 MAIN" matching "1123 MAIN")
            try:
                # Escape special chars in address just in case
                pattern = r'\b' + re.escape(norm_prop) + r'\b'
                if not re.search(pattern, norm_mail):
                    # Fallback: Try matching WITHOUT suffix (if mailing address omits it)
                    # e.g. Prop: "4842 N MARYVALE AVE", Mail: "4842 N MARYVALE"
                    # Remove the last word if it's a known suffix?
                    # Or just try to match the "Number + Street Name" part?
                    # Simple heuristic: Remove the last token from prop address and check again
                    prop_parts = norm_prop.split()
                    if len(prop_parts) > 2: # Ensure we have Number + Name + Suffix
                        prop_no_suffix = " ".join(prop_parts[:-1])
                        pattern_no_suffix = r'\b' + re.escape(prop_no_suffix) + r'\b'
                        if re.search(pattern_no_suffix, norm_mail):
                             return False # It MATCHED without suffix, so Owner Occupied
                    
                    if "Absentee Owner" not in lead.get("distress_signals", []):
                        lead["distress_signals"] = lead.get("distress_signals", []) + ["Absentee Owner"]
                    return True
            except:
                # Fallback to simple substring if regex fails
                if norm_prop not in norm_mail:
                    if "Absentee Owner" not in lead.get("distress_signals", []):
                        lead["distress_signals"] = lead.get("distress_signals", []) + ["Absentee Owner"]
                    return True
                
            return False
        
        # ===== WEIGHTED PROPORTIONAL ZIP SAMPLING for city searches =====
        if filters.get("city") and not filters.get("zip_code"):
            # ===== CITY-WIDE SEARCH (SIMPLIFIED) =====
            # Query all city zips in parallel, shuffle results for distribution
            import random
            import time as time_module
            
            city = filters.get("city")
            t_start = time_module.time()
            print(f"[PERF] City-wide search: '{city}' absentee owners")
            
            # Get the zips for this city
            city_zips = await self._fetch_zips_by_city(city)
            if not city_zips:
                print(f"Warning: No zips found for city '{city}'")
                return []
            
            print(f"[PERF] Querying {len(city_zips)} zips in parallel...")
            
            # Query each zip in parallel (need ~10x limit since only ~30-50% are absentee)
            per_zip_limit = max(30, (limit * 10) // len(city_zips) + 5)
            
            async def fetch_absentee_single_zip(zip_code: str) -> List[Dict]:
                try:
                    # Fix for South Tucson: Keep city filter if it's a jurisdiction
                    # This allows _fetch_pima_parcels to add "AND JURIS_OL = 'SOUTH TUCSON'"
                    search_city = filters.get("city")
                    keep_city = False
                    if search_city and search_city.upper() in self.JURISDICTIONS:
                        keep_city = True
                        
                    zip_filters = {**filters, "zip_code": zip_code}
                    if not keep_city:
                        zip_filters["city"] = None
                        
                    candidates = await self._fetch_pima_parcels(zip_filters, limit=per_zip_limit, offset=0)
                    if not candidates:
                        return []
                    return [c for c in candidates if is_absentee(c)]
                except Exception as e:
                    print(f"    Error fetching absentee for zip {zip_code}: {e}")
                    return []
            
            # No concurrent limit for Pima County API (handles load well)
            tasks = [fetch_absentee_single_zip(z) for z in city_zips]
            results_list = await asyncio.gather(*tasks)
            
            # Combine results
            all_results = []
            for zip_results in results_list:
                if zip_results:
                    all_results.extend(zip_results)
            
            # SHUFFLE for random geographic distribution
            random.shuffle(all_results)
            
            t_elapsed = time_module.time() - t_start
            print(f"[PERF] City search complete: {len(all_results)} absentee results in {t_elapsed:.1f}s total")
            
            return all_results[:limit]
        
        # ===== SINGLE-ZIP OR BOUNDS SEARCH (original logic) =====
        candidate_limit = limit * 20
        candidates = await self._fetch_pima_parcels(filters, limit=candidate_limit, offset=0)
        
        self._log(f"Absentee Search: Found {len(candidates)} candidates.")
        
        # Filter to absentee owners
        all_absentee_leads = [c for c in candidates if is_absentee(c)]
        
        # Random sample for geographic distribution
        if len(all_absentee_leads) > limit:
            print(f"  Absentee: {len(all_absentee_leads)} matches, randomly sampling {limit}")
            return random.sample(all_absentee_leads, limit)
        else:
            return all_absentee_leads

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
        Resolves a neighborhood/subdivision name to a bounding box.
        Strategy:
        1. Try Neighborhood Associations (Layer 9) - Broad search (e.g. "Sam Hughes")
        2. Fallback to Subdivisions (Layer 15) - Specific search (e.g. "Alta Vista Addition")
        """
        if not neighborhood:
            return None
            
        print(f"Resolving neighborhood bounds for: {neighborhood}")
        
        # Helper to query a layer for bounds
        async def query_layer_bounds(url: str, field: str, value: str) -> Optional[tuple]:
            where_clause = f"{field} LIKE '%{value.upper()}%'"
            params = {
                "where": where_clause,
                "outFields": field,
                "returnGeometry": "true",
                "returnExtentOnly": "false",
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
                        print(f"DEBUG: Using API Extent from {url}: {extent}")
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
            except Exception as e:
                print(f"Error querying layer {url}: {e}")
            return None

        # 1. Try Neighborhood Associations (Layer 9)
        assoc_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/Community2/MapServer/9/query"
        bounds = await query_layer_bounds(assoc_url, "NAME", neighborhood)
        
        if bounds:
            print(f"Found Neighborhood Association: {neighborhood}")
            return bounds
            
        # 2. Fallback to Subdivisions (Layer 15)
        print(f"Neighborhood Association not found, trying Subdivisions...")
        subdiv_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/15/query"
        bounds = await query_layer_bounds(subdiv_url, "SUB_NAME", neighborhood)
        
        if bounds:
            print(f"Found Subdivision: {neighborhood}")
            return bounds
            
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
