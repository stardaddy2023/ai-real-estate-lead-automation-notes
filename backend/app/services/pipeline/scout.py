import requests
import json
import math
import asyncio
from typing import List, Dict, Optional, Any
from shapely.geometry import Polygon, Point
from shapely.prepared import prep

class ScoutService:
    def __init__(self):
        print("SCOUT SERVICE V3 - WITH REQUESTS IMPORT (RELOADED)")
        # Pima County GIS - Parcels - Regional (Verified Public URL)
        self.pima_parcels_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
        
        # Pinal County GIS - Assessor Info
        self.pinal_parcels_url = "https://rogue.casagrandeaz.gov/arcgis/rest/services/Pinal_County/Pinal_County_Assessor_Info/MapServer/0/query"
        
        # Tucson Open Data - Code Violations (Verified Layer 94)
        self.tucson_violations_url = "https://gis.tucsonaz.gov/arcgis/rest/services/PDSD/pdsdMain_General5/MapServer/94/query"

    async def _fetch_code_violations(self, filters: Dict, limit: int) -> List[Dict]:
        print("Fetching code violations from Tucson GIS...")
        
        zip_code = filters.get("zip_code")
        
        # Build WHERE clause
        where_parts = ["STATUS_1 NOT IN ('COMPLIAN', 'CLOSED', 'VOID')"]
        
        params = {
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": "4326",  # WGS84 for Leaflet map compatibility
            "resultRecordCount": limit * 3 if zip_code else limit,  # Fetch more if filtering
            "f": "json",
            "orderByFields": "DT_ENT DESC"
        }
        
        # If zip code provided, use spatial query with envelope
        zip_polygon = None
        if zip_code:
            zip_metadata = await self._get_zip_metadata(zip_code)
            if zip_metadata and "polygon" in zip_metadata:
                zip_polygon = prep(zip_metadata["polygon"])
                # Add envelope to spatial query for server-side pre-filtering
                if "envelope" in zip_metadata:
                    params["geometry"] = json.dumps(zip_metadata["envelope"])
                    params["geometryType"] = "esriGeometryEnvelope"
                    params["spatialRel"] = "esriSpatialRelIntersects"
                    params["inSR"] = "2868"
        
        params["where"] = " AND ".join(where_parts)
        
        try:
            response = requests.get(self.tucson_violations_url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                features = data.get("features", [])
                print(f"Found {len(features)} raw code violations.")
                
                # Map to lead objects
                leads = [self._map_tucson_violation(f) for f in features]
                
                # Client-side filtering by zip code (strict)
                if zip_code and zip_polygon:
                    filtered_leads = []
                    for lead in leads:
                        if lead.get("latitude") and lead.get("longitude"):
                            pt = Point(lead["longitude"], lead["latitude"])
                            if zip_polygon.contains(pt):
                                # Override extracted zip with search zip
                                lead["address_zip"] = zip_code
                                # Update full address to include city and zip
                                lead["address"] = f"{lead['address_street']}, Tucson, AZ {zip_code}"
                                filtered_leads.append(lead)
                    print(f"After zip filter: {len(filtered_leads)} code violations.")
                    leads = filtered_leads[:limit]
                else:
                    leads = leads[:limit]
                
                # Filter by specific address BEFORE enrichment (performance optimization)
                address_filter = filters.get("address")
                if address_filter:
                    address_norm = address_filter.upper().strip()
                    leads = [l for l in leads if address_norm in l.get("address_street", "").upper()]
                    print(f"After address filter: {len(leads)} code violations.")
                
                # Only enrich the filtered results (not all 100!)
                # Enrich with parcel data (owner info)
                await self._enrich_violations_with_parcel_data(leads)
                
                # Enrich with zip codes based on coordinates (for leads missing zip)
                await self._enrich_violations_with_zip_codes(leads)
                
                # ===== CONSOLIDATE MULTIPLE VIOLATIONS PER ADDRESS =====
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
                        # Keep any enrichment data from either source
                        if not existing.get("owner_name") and lead.get("owner_name"):
                            existing["owner_name"] = lead.get("owner_name")
                        if not existing.get("mailing_address") and lead.get("mailing_address"):
                            existing["mailing_address"] = lead.get("mailing_address")
                        if not existing.get("parcel_id") and lead.get("parcel_id"):
                            existing["parcel_id"] = lead.get("parcel_id")
                
                print(f"Consolidated {len(leads)} violations into {len(consolidated)} unique properties.")
                return list(consolidated.values())[:limit]
            else:
                print(f"Error fetching violations: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching violations: {e}")
            return []
    
    async def _enrich_violations_with_parcel_data(self, leads: List[Dict]):
        """
        Enriches code violation leads with owner info from the parcel layer.
        Uses concurrent spatial queries to find the parcel at each violation's location.
        """
        if not leads:
            return
            
        print(f"Enriching {len(leads)} code violations with parcel data (concurrent)...")
        
        base_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
        
        loop = asyncio.get_event_loop()
        sem = asyncio.Semaphore(10)  # Limit to 10 concurrent requests
        
        async def enrich_single(lead, idx):
            """Enriches a single lead with parcel data."""
            async with sem:
                lat = lead.get("latitude")
                lon = lead.get("longitude")
                if not lat or not lon:
                    return False
                    
                # Create a point geometry for spatial query
                point_geom = {
                    "x": lon,
                    "y": lat,
                    "spatialReference": {"wkid": 4326}
                }
                
                params = {
                    "geometry": json.dumps(point_geom),
                    "geometryType": "esriGeometryPoint",
                    "spatialRel": "esriSpatialRelIntersects",
                    "outFields": "PARCEL,MAIL1,MAIL2,MAIL3,MAIL4,MAIL5,ZIP,ZIP4,FCV,CURZONE_OL,GISAREA",
                    "returnGeometry": "false",
                    "outSR": "4326",
                    "f": "json"
                }
                
                try:
                    resp = await loop.run_in_executor(
                        None, 
                        lambda: requests.get(base_url, params=params, timeout=5)
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        features = data.get("features", [])
                        if features:
                            attr = features[0].get("attributes", {})
                            
                            # Build mailing address from MAIL fields
                            mail_parts = []
                            for i in range(1, 6):
                                mail_val = attr.get(f"MAIL{i}")
                                if mail_val and mail_val.strip():
                                    mail_parts.append(mail_val.strip())
                            
                            # Add Zip if available
                            m_zip = attr.get("ZIP9") or attr.get("ZIP")
                            if m_zip and m_zip != "000000000":
                                mail_parts.append(str(m_zip))
                            
                            mailing_address = ", ".join(mail_parts)
                            
                            # Get owner name from MAIL1 (usually first line of mailing address)
                            owner_name = attr.get("MAIL1", "").title() if attr.get("MAIL1") else None
                            
                            # Update lead with enriched data
                            lead["owner_name"] = owner_name
                            lead["mailing_address"] = mailing_address
                            # Use parcel ID from parcel layer (clean, no suffix)
                            parcel = attr.get("PARCEL")
                            if parcel:
                                lead["parcel_id"] = parcel
                            lead["zoning"] = attr.get("CURZONE_OL")
                            lead["lot_size"] = attr.get("GISAREA")
                            lead["assessed_value"] = attr.get("FCV")
                            
                            # NOTE: Do NOT use parcel layer's ZIP field here!
                            # That field contains the OWNER'S MAILING ZIP, not the property location.
                            # Code Violations are known to be in Tucson - keep the city/zip from search or lookup.
                            
                            # Check for Absentee Owner status
                            # If property street address is NOT in the mailing address, it's absentee
                            prop_street = lead.get("address_street", "").upper().strip()
                            if prop_street and mailing_address:
                                if prop_street not in mailing_address.upper():
                                    if "Absentee Owner" not in lead.get("distress_signals", []):
                                        lead["distress_signals"].append("Absentee Owner")
                            
                            return True
                except Exception as e:
                    pass  # Silent fail for individual enrichment
                return False
        
        # Run all enrichment tasks concurrently
        tasks = [enrich_single(lead, idx) for idx, lead in enumerate(leads)]
        results = await asyncio.gather(*tasks)
        
        enriched_count = sum(1 for r in results if r)
        print(f"Enriched {enriched_count}/{len(leads)} code violations with parcel data.")

    async def _enrich_violations_with_zip_codes(self, leads: List[Dict]):
        """
        Enriches code violation leads with proper zip codes using coordinate-based lookup
        against the Zip Code layer (Layer 6).
        """
        if not leads:
            return
            
        zip_layer_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/Addresses/MapServer/6/query"
        loop = asyncio.get_event_loop()
        
        async def lookup_zip(lead):
            lat = lead.get("latitude")
            lon = lead.get("longitude")
            
            # Skip if already has zip or no coordinates
            if lead.get("address_zip") or not lat or not lon:
                return
                
            point_geom = {
                "x": lon,
                "y": lat,
                "spatialReference": {"wkid": 4326}
            }
            
            params = {
                "geometry": json.dumps(point_geom),
                "geometryType": "esriGeometryPoint",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "ZIPCODE",
                "returnGeometry": "false",
                "f": "json"
            }
            
            try:
                resp = await loop.run_in_executor(
                    None,
                    lambda: requests.get(zip_layer_url, params=params, timeout=5)
                )
                if resp.status_code == 200:
                    data = resp.json()
                    features = data.get("features", [])
                    if features:
                        zipcode = features[0].get("attributes", {}).get("ZIPCODE")
                        if zipcode:
                            lead["address_zip"] = str(zipcode)[:5]
                            lead["address"] = f"{lead.get('address_street', '')}, Tucson, AZ {lead['address_zip']}"
            except Exception:
                pass
        
        # Run lookups concurrently
        tasks = [lookup_zip(lead) for lead in leads]
        await asyncio.gather(*tasks)
        
        enriched = sum(1 for l in leads if l.get("address_zip"))
        print(f"Enriched {enriched}/{len(leads)} code violations with zip codes.")

    # Filter priority order (most restrictive first)
    FILTER_PRIORITY = [
        "Code Violations",       # Very selective - specific violations
        "Divorce",               # Recorder data - specific events
        "Probate",               # Recorder data - specific events  
        "Evictions",             # Court records - specific events
        "Liens (HOA, Mechanics)",# Recorded documents
        "Pre-Foreclosure",       # NOD filings
        "Tax Liens",             # County records
        "Judgements",            # Court records
        "Absentee Owner",        # ~40% of all parcels - least restrictive
    ]

    def _is_absentee(self, lead: Dict) -> bool:
        """Quick in-memory check if property is absentee-owned."""
        prop_street = (lead.get("address_street") or "").upper().strip()
        mail_addr = (lead.get("mailing_address") or "").upper().strip()
        
        if not prop_street or not mail_addr:
            return False
        
        return prop_street not in mail_addr

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
            
            # Get distress types
            distress_types = filters.get("distress_type")
            if isinstance(distress_types, str):
                distress_types = [distress_types]
            
            # If "all" or empty, use generic parcel search
            if not distress_types or "all" in distress_types:
                target_raw = int(limit * 1.5)
                if county and county.lower() == "pinal":
                    return await self._fetch_pinal_parcels(filters, 200, 0)
                else:
                    return await self._fetch_pima_parcels(filters, limit=target_raw, offset=0)

            # ========== AND-LOGIC ARCHITECTURE ==========
            # Sort selected filters by priority (most restrictive first)
            selected = [f for f in self.FILTER_PRIORITY if f in distress_types]
            
            if not selected:
                # Fallback to generic search if no recognized filters
                return await self._fetch_pima_parcels(filters, limit=limit, offset=0)
            
            print(f"AND-Logic: Selected filters: {selected}")
            
            # Step 1: Fetch from PRIMARY (most restrictive) source
            primary = selected[0]
            # Fetch more than needed since AND filtering will reduce results
            fetch_limit = limit * 3 if len(selected) > 1 else limit
            print(f"AND-Logic: Fetching from primary source '{primary}' with limit {fetch_limit}")
            
            candidates = await self._fetch_primary(primary, filters, fetch_limit)
            print(f"AND-Logic: Got {len(candidates)} candidates from primary source")
            
            # Step 2: Verify against SECONDARY filters (AND logic)
            for secondary in selected[1:]:
                print(f"AND-Logic: Verifying against secondary filter '{secondary}'")
                candidates = await self._verify_filter(candidates, secondary, filters)
                
                # Early exit if no candidates left
                if not candidates:
                    print(f"AND-Logic: No candidates passed '{secondary}' filter")
                    break
            
            print(f"AND-Logic: Final result count: {len(candidates[:limit])}")
            return candidates[:limit]
            
        except Exception as e:
            import traceback
            print(f"ERROR IN FETCH_LEADS: {str(e)}\n{traceback.format_exc()}")
            return []

    def _log(self, msg: str):
        """Stub method for legacy logging calls. Does nothing."""
        pass

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
        self._log(f"Fetching parcels with filters: {filters}")
        """
        Fetches parcels from Pima County GIS (Layer 12).
        Uses a Two-Step Strategy + Client-Side Filtering.
        """
        base_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
        
        where_parts = ["1=1"]
        
        # 1. Location Filters
        zip_metadata = None
        zip_code = filters.get('zip_code')
        
        if zip_code:
            # Use Spatial Query for Zip Code
            zip_metadata = await self._get_zip_metadata(filters['zip_code'])
            
            # Always add ZIP filter as backup/refinement
            where_parts.append(f"ZIP LIKE '{filters['zip_code']}%'")
                
        if filters.get('city'):
            where_parts.append(f"JURIS_OL = '{filters['city'].upper()}'")
            
        if filters.get('address'):
            addr = filters['address'].upper()
            where_parts.append(f"ADDRESS_OL LIKE '%{addr}%'")

        # 2. Property Type Filters
        if filters.get('property_types'):
            codes = self._get_codes_for_types(filters['property_types'])
            if codes:
                code_list = ",".join([f"'{c}'" for c in codes])
                where_parts.append(f"PARCEL_USE IN ({code_list})")

        # 4. Ensure Address Exists
        where_parts.append("ADDRESS_OL <> ''")

        where_clause = " AND ".join(where_parts)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            import time
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            
            start_total = time.time()
            object_ids = []
            
            # STRATEGY A: Spatial Query (Two-Step + Filter)
            # Attempt this first, but fallback to B if it fails/times out
            strategy_a_success = False
            
            if zip_metadata:
                try:
                    envelope = zip_metadata["envelope"]
                    
                    # Step 1: Fetch IDs using Envelope (Native SR)
                    self._log(f"Fetching IDs for Zip Envelope...")
                    t0 = time.time()
                    params_step1 = {
                        "where": where_clause,
                        "geometry": json.dumps(envelope),
                        "geometryType": "esriGeometryEnvelope",
                        "spatialRel": "esriSpatialRelIntersects",
                        "inSR": "2868",
                        "outFields": "OBJECTID",
                        "returnGeometry": "false",
                        "f": "json",
                        "resultRecordCount": 4000, # INCREASED POOL to 4000
                        "resultOffset": offset
                    }
                    
                    # Run Step 1 in thread with strict timeout
                    loop = asyncio.get_event_loop()
                    # Reduced timeout to 10s for Step 1 to fail fast
                    resp1 = await asyncio.wait_for(
                        loop.run_in_executor(None, lambda: requests.post(base_url, data=params_step1, headers=headers, timeout=10)),
                        timeout=12.0
                    )
                    
                    object_ids = []
                    if resp1.status_code == 200:
                        data1 = resp1.json()
                        if "features" in data1:
                            object_ids = [f["attributes"]["OBJECTID"] for f in data1["features"]]
                            self._log(f"Found {len(object_ids)} IDs in envelope. Took {time.time() - t0:.2f}s")
                    
                    if object_ids:
                        # Step 2: Connection Pooling & Smart Concurrency
                        leads = []
                        batch_size = 50
                        
                        # self._log(f"Found {len(object_ids)} IDs. Fetching details...")
                        
                        async def fetch_batch(batch_ids):
                            batch_where = f"OBJECTID IN ({','.join(map(str, batch_ids))})"
                            params_batch = {
                                "where": batch_where,
                                "outFields": "*", 
                                "returnGeometry": "true",
                                "outSR": "4326",
                                "f": "json"
                            }
                            try:
                                resp = await loop.run_in_executor(None, lambda: requests.post(base_url, data=params_batch, headers=headers, timeout=10))
                                if resp.status_code == 200:
                                    b_data = resp.json()
                                    return [self._map_pima_parcel(f) for f in b_data.get("features", [])]
                            except Exception as e:
                                pass # Silent fail on batch
                            return []

                        # Limit concurrency to 5 to prevent server/API overload
                        sem = asyncio.Semaphore(5)

                        async def fetch_batch_safe(batch_ids):
                            async with sem:
                                return await fetch_batch(batch_ids)

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
                        if zip_metadata and "polygon" in zip_metadata:
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
                            # Enrich with correct Zip Codes before returning
                            final_leads = leads[:limit]
                            await self._enrich_with_zip_codes(final_leads)
                            return final_leads
                        
                except Exception as e:
                    self._log(f"Strategy A failed/timed out: {e}. Falling back to Strategy B.")
                    # Fall through to Strategy B

            # STRATEGY B: Standard Attribute Query (Fallback)
            if not strategy_a_success:
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
            
    def _map_pima_parcel(self, feature: Dict, override_zip: str = None) -> Optional[Dict]:
        attr = feature.get("attributes", {})
        geometry = feature.get("geometry", {})
        
        address = attr.get("ADDRESS_OL", "").strip()
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
            
        return {
            "source": "pima_county_gis",
            "parcel_id": attr.get("PARCEL") or str(attr.get("OBJECTID")), # Use PARCEL for joining
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
            # New Fields (Placeholders until data source found)
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

    def _get_codes_for_types(self, types: List[str]) -> List[str]:
        """
        Maps friendly property types to Pima County Use Codes.
        """
        # Reverse mapping of common_codes
        type_map = {
            "Single Family": ["0111", "0113", "0121", "0131", "0133", "0191", "0011", "0013"],
            "Mobile Home": ["0141"],
            "Condo": ["0151"],
            "Townhouse": ["0152"],
            "Multi-Family": ["0311", "0312", "0313", "0314", "0315", "0316", "0031"],
            "Multi Family": ["0311", "0312", "0313", "0314", "0315", "0316", "0031"],
            "Commercial": ["0211", "0212", "0213", "1120", "1170", "2140", "2821", "0021"],
            "Land": ["0011", "0013", "0021", "0031", "0041", "9600"]
        }
        
        codes = []
        for t in types:
            # Simple fuzzy match
            for key, val in type_map.items():
                if t.lower() in key.lower() or key.lower() in t.lower():
                    codes.extend(val)
        return list(set(codes))

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
        
        return {
            "id": activity_num,  # Unique ID for React keys
            "source": "tucson_code_enforcement",
            "parcel_id": activity_num,  # Will be overwritten with real parcel during enrichment
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
