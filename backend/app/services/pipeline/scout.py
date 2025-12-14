import requests
import json
from typing import List, Dict, Optional

class ScoutService:
    def __init__(self):
        # Pima County GIS - Parcels - Regional (Verified Public URL)
        self.pima_parcels_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
        
        # Pinal County GIS - Assessor Info
        self.pinal_parcels_url = "https://rogue.casagrandeaz.gov/arcgis/rest/services/Pinal_County/Pinal_County_Assessor_Info/MapServer/0/query"
        
        # Tucson Open Data - Code Violations
        # Note: Public API is elusive. Using a placeholder that returns empty if 404.
        self.tucson_violations_url = "https://gisdata.tucsonaz.gov/server/rest/services/Code_Enforcement/Code_Enforcement_Violations_Open_Data/FeatureServer/0/query"

    async def fetch_leads(self, filters: Dict) -> List[Dict]:
        """
        Orchestrates data fetching based on filters.
        Ensures we return enough leads to meet the limit after cleaning/deduplication.
        """
        results = []
        limit = filters.get("limit", 100)
        county = filters.get("county", "Pima") # Default to Pima
        
        print(f"Scout fetching leads with filters: {filters}")
        
        # Dispatch based on Distress Type
        if filters.get("distress_type") == "code_violations":
            # Currently only supported for Tucson (Pima)
            if county.lower() != "pima":
                print("Code violations only supported for Pima/Tucson currently.")
                return []
            return await self._fetch_code_violations(filters, limit)
            
        elif filters.get("distress_type") == "absentee_owner":
            return await self._fetch_absentee_owners(filters, limit)
            
        else:
            # Generic Parcel Search
            # We loop until we have enough raw leads to likely satisfy the limit
            target_raw = int(limit * 1.5) # 50% buffer for duplicates/attrition
            
            all_parcels = []
            
            # Fetch Loop
            offset = 0
            batch_size = 1000
            max_pages = 20
            page = 0
            
            while len(all_parcels) < target_raw and page < max_pages:
                if county and county.lower() == "pinal":
                    batch = await self._fetch_pinal_parcels(filters, batch_size, offset)
                else:
                    batch = await self._fetch_pima_parcels(filters, batch_size, offset)
                    
                if not batch:
                    break
                
                all_parcels.extend(batch)
                offset += len(batch)
                page += 1
                
                if len(batch) < batch_size: # End of data
                    break
            
            return all_parcels[:target_raw]

    async def _fetch_pima_parcels(self, filters: Dict, limit: int, offset: int = 0) -> List[Dict]:
        """
        Fetches parcels from Pima County GIS.
        """
        where_clause = "1=1"
        
        if filters.get("zip_code"):
            where_clause += f" AND ZIP = '{filters['zip_code']}'"
            
        if filters.get("city"):
            # Pima uses JURIS_OL for jurisdiction/city
            where_clause += f" AND JURIS_OL = '{filters['city'].upper()}'"

        if filters.get("address"):
            # Pima uses ADDRESS_OL for street address
            # Split address into terms to allow "927 Perry" to match "927 N PERRY"
            # All terms must be present in the address
            address_terms = filters['address'].upper().split()
            for term in address_terms:
                where_clause += f" AND ADDRESS_OL LIKE '%{term}%'"
            
        if filters.get("property_types"):
            # Map friendly names to Pima Use Codes
            codes = self._get_codes_for_types(filters["property_types"])
            if codes:
                code_list = ",".join([f"'{c}'" for c in codes])
                where_clause += f" AND PARCEL_USE IN ({code_list})"

        # Check if we have any valid filter criteria in the where_clause
        has_filter = "ZIP" in where_clause or "JURIS_OL" in where_clause or "ADDRESS_OL" in where_clause or "PARCEL_USE" in where_clause
        
        params = {
            "where": where_clause if has_filter else "OBJECTID < 10000", # Increased default range
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "json",
            "resultRecordCount": limit,
            "resultOffset": offset,
            "orderByFields": "OBJECTID ASC"
        }
        

        try:
            print(f"Querying Pima Parcels: {self.pima_parcels_url} params={params}")
            response = requests.get(self.pima_parcels_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "error" in data:
                print(f"API Error: {data['error']}")
            
            features = data.get("features", [])
            leads = [self._map_pima_parcel(f) for f in features]
            
            # Enrich with Tucson Data (Layer 4) if possible
            # This layer has SQ_FT and USE_STATUS (Description)
            if leads:
                await self._enrich_with_tucson_data(leads)
                
            return leads
            
        except Exception as e:
            print(f"Error fetching parcels: {e}")
            return []

    def _get_codes_for_types(self, types: List[str]) -> List[str]:
        """
        Maps friendly property types to Pima County Use Codes.
        """
        # Reverse mapping of common_codes
        # We'll define it here for simplicity, or could be a class constant
        type_map = {
            "Single Family": ["0111", "0113", "0121", "0131", "0133", "0191", "0011", "0013"],
            "Mobile Home": ["0141"],
            "Condo": ["0151"],
            "Townhouse": ["0152"],
            "Multi-Family": ["0311", "0312", "0313", "0314", "0315", "0316", "0031"],
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
        Enriches leads with data from City of Tucson Layer 4 (Sqft, Use Desc).
        """
        # Collect Parcel IDs (Tax Codes)
        parcel_ids = [l["parcel_id"] for l in leads if l.get("parcel_id")]
        if not parcel_ids:
            return

        # Query Layer 4
        # Layer 4 uses TAX_CODE for Parcel ID
        # We process in chunks if needed, but for limit=100 it's fine
        where_clause = f"TAX_CODE IN ({','.join([repr(pid) for pid in parcel_ids])})"
        
        url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/4/query"
        params = {
            "where": where_clause,
            "outFields": "TAX_CODE,USE_STATUS,SQ_FT,CODE,SALE_DATE,SALE_PRICE",
            "returnGeometry": "false",
            "f": "json"
        }
        
        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                features = data.get("features", [])
                
                # Create map
                enrich_map = {}
                for f in features:
                    attr = f["attributes"]
                    pid = attr.get("TAX_CODE")
                    if pid:
                        enrich_map[pid] = attr
                
                # Update leads
                for lead in leads:
                    pid = lead.get("parcel_id")
                    if pid and pid in enrich_map:
                        tucson_data = enrich_map[pid]
                        # Update fields
                        use_desc = tucson_data.get("USE_STATUS")
                        prop_class = tucson_data.get("CODE")
                        
                        if use_desc:
                            # User requested "property use desc" -> USE_STATUS
                            lead["property_type"] = use_desc
                            # Append class if available for more detail
                            if prop_class:
                                lead["property_type"] += f" ({prop_class})"
                        elif prop_class:
                            # Fallback to class if desc is missing
                            lead["property_type"] = prop_class
                            
                        if tucson_data.get("SQ_FT"):
                            lead["sqft"] = int(tucson_data.get("SQ_FT"))
                            
                        # Map Sale Data
                        if tucson_data.get("SALE_DATE"):
                            # Convert timestamp to date string if needed, or just pass through
                            # ArcGIS often returns milliseconds
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

    async def _fetch_pinal_parcels(self, filters: Dict, limit: int, offset: int = 0) -> List[Dict]:
        """
        Fetches parcels from Pinal County GIS.
        """
        where_clause = "1=1"
        
        if filters.get("zip_code"):
            # Pinal doesn't have a dedicated Property Zip field, only Mailing Zip (PSTLZIP5)
            # So we search SITEADDRESS for the zip
            where_clause += f" AND SITEADDRESS LIKE '%{filters['zip_code']}%'"
            
        if filters.get("city"):
            # Similarly for City, SITEADDRESS usually contains it, but PSTLCITY is Mailing City.
            # However, often they match. Let's try SITEADDRESS for City too to be safe.
            where_clause += f" AND SITEADDRESS LIKE '%{filters['city'].upper()}%'"

        if filters.get("address"):
            # Pinal uses SITEADDRESS
            address_terms = filters['address'].upper().split()
            for term in address_terms:
                where_clause += f" AND SITEADDRESS LIKE '%{term}%'"
            
        if filters.get("property_types"):
            # Pinal uses USEDSCRP (Description) or USECD (Code)
            # We'll use simple LIKE matches on Description for now
            # e.g. "Single Family", "Vacant"
            or_clauses = []
            for t in filters["property_types"]:
                # Map friendly to Pinal terms if needed, or just fuzzy match
                if "Single Family" in t:
                    or_clauses.append("USEDSCRP LIKE '%Single Family%'")
                elif "Multi-Family" in t:
                    or_clauses.append("USEDSCRP LIKE '%Multi-Family%' OR USEDSCRP LIKE '%Duplex%' OR USEDSCRP LIKE '%Triplex%'")
                elif "Commercial" in t:
                    or_clauses.append("USEDSCRP LIKE '%Commercial%' OR USEDSCRP LIKE '%Office%' OR USEDSCRP LIKE '%Store%'")
                elif "Land" in t:
                    or_clauses.append("USEDSCRP LIKE '%Vacant%' OR USEDSCRP LIKE '%Land%'")
                elif "Mobile" in t:
                    or_clauses.append("USEDSCRP LIKE '%Mobile%'")
                else:
                    or_clauses.append(f"USEDSCRP LIKE '%{t}%'")
            
            if or_clauses:
                where_clause += f" AND ({' OR '.join(or_clauses)})"

        params = {
            "where": where_clause,
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "json",
            "resultRecordCount": limit,
            "resultOffset": offset,
            "orderByFields": "OBJECTID ASC"
        }
        
        try:
            print(f"Querying Pinal Parcels: {self.pinal_parcels_url} params={params}")
            response = requests.get(self.pinal_parcels_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "error" in data:
                print(f"API Error: {data['error']}")
            
            features = data.get("features", [])
            leads = [self._map_pinal_parcel(f) for f in features]
            return leads
            
        except Exception as e:
            print(f"Error fetching Pinal parcels: {e}")
            return []

    async def _fetch_absentee_owners(self, filters: Dict, limit: int) -> List[Dict]:
        """
        Fetches parcels where Owner Address != Property Address.
        Uses pagination to ensure we reach the requested limit.
        """
        absentee_leads = []
        offset = 0
        batch_size = 1000 # Fetch in larger chunks
        max_pages = 100 # Allow scanning up to 100k records
        page = 0
        county = filters.get("county", "Pima")
        
        print(f"Fetching absentee owners ({county}) with limit={limit}...")
        
        # Fetch MORE than limit to account for CleanerService attrition
        target_count = int(limit * 1.5)
        
        while len(absentee_leads) < target_count and page < max_pages:
            # Fetch batch
            if county.lower() == "pinal":
                raw_parcels = await self._fetch_pinal_parcels(filters, batch_size, offset)
            else:
                raw_parcels = await self._fetch_pima_parcels(filters, batch_size, offset)
            
            if not raw_parcels:
                break # No more data
                
            print(f"  Page {page}: Fetched {len(raw_parcels)} raw parcels (Offset: {offset})")
            
            # Filter for absentee
            batch_leads = []
            for p in raw_parcels:
                prop_addr = p.get("address", "").upper()
                mail_addr = p.get("mailing_address", "").upper()
                
                if not prop_addr or not mail_addr:
                    continue
                    
                # Basic check: if first 5 chars don't match
                # Note: This is a rough heuristic. 
                # Pinal addresses might be formatted differently, but comparing start usually works.
                if prop_addr[:5] != mail_addr[:5]:
                    p["distress_signals"] = ["Absentee Owner"]
                    batch_leads.append(p)
            
            print(f"  Page {page}: Found {len(batch_leads)} absentee leads")
            absentee_leads.extend(batch_leads)
            
            # Prepare next page
            offset += len(raw_parcels)
            page += 1
            
            # Optimization: If we got fewer records than requested, we're likely at the end
            if len(raw_parcels) < batch_size:
                break
                
        return absentee_leads[:target_count]

    async def _fetch_code_violations(self, filters: Dict, limit: int) -> List[Dict]:
        """
        Fetches violations from Tucson Open Data.
        """
        where_clause = "STATUS = 'Open'"
        
        if filters.get("zip_code"):
            where_clause += f" AND ZIP = '{filters['zip_code']}'"

        # Tucson data might not have JURIS_OL, so we skip city filter for now or map it if known
        
        params = {
            "where": where_clause,
            "outFields": "*",
            "returnGeometry": "false",
            "f": "json",
            "resultRecordCount": limit,
            "orderByFields": "CASE_DATE DESC"
        }
        
        try:
            print(f"Querying Tucson Violations: {self.tucson_violations_url} params={params}")
            response = requests.get(self.tucson_violations_url, params=params, timeout=10)
            # If 404 or error, just return empty list instead of crashing
            if response.status_code != 200:
                print(f"Tucson API Error: {response.status_code}")
                return []
                
            data = response.json()
            features = data.get("features", [])
            return [self._map_tucson_violation(f["attributes"]) for f in features]
            
        except Exception as e:
            print(f"Error fetching violations: {e}")
            return []

    def _map_pima_parcel(self, feature: Dict) -> Dict:
        attr = feature.get("attributes", {})
        geometry = feature.get("geometry", {})
        
        # Calculate Centroid from Polygon Rings
        lat, lng = None, None
        if "rings" in geometry and geometry["rings"]:
            ring = geometry["rings"][0]
            if ring:
                # Simple average for centroid
                lng = sum(p[0] for p in ring) / len(ring)
                lat = sum(p[1] for p in ring) / len(ring)
        
        # Map Pima GIS attributes (Verified Fields)
        mail_parts = [
            attr.get('MAIL2', ''),
            attr.get('MAIL3', ''),
            attr.get('MAIL_CITY', ''),
            attr.get('MAIL_STATE', ''),
            attr.get('MAIL_ZIP', '')
        ]
        # Filter empty parts and join
        mail_addr_clean = " ".join([p for p in mail_parts if p and p.strip()])
        
        # Basic Property Use Code Mapping (Fallback)
        # Source: Pima County Assessor UCodes & ADOR Manual
        use_code = attr.get("PARCEL_USE")
        use_desc = use_code
        
        common_codes = {
            # Residential
            "0111": "Single Family Residence",
            "0113": "Single Family Residence",
            "0121": "Single Family Residence",
            "0131": "Single Family Residence (Urban)",
            "0133": "Single Family Residence (Rural)",
            "0141": "Mobile Home",
            "0151": "Condominium",
            "0152": "Townhouse",
            "0191": "Single Family Residence (Other)",
            
            # Multi-Family
            "0311": "Duplex",
            "0312": "Triplex",
            "0313": "Fourplex",
            "0314": "Multi-Family (5-9 Units)",
            "0315": "Multi-Family (10-24 Units)",
            "0316": "Multi-Family (25+ Units)",
            
            # Commercial
            "0211": "Commercial (Store)",
            "0212": "Commercial (Office)",
            "0213": "Commercial (Warehouse)",
            "1120": "Office Building",
            "1170": "Shopping Center",
            "2140": "Commercial Service",
            "2821": "Office/Warehouse",
            
            # Vacant Land
            "0011": "Vacant Single Family Residential",
            "0013": "Vacant Rural Residential",
            "0021": "Vacant Commercial",
            "0031": "Vacant Multi-Family",
            "0041": "Vacant Industrial",
            
            # Other / Institutional / Common Area
            "9130": "Church/Religious",
            "9590": "School/Educational",
            "9600": "Common Area / Waste Land",
            "9710": "Government / Public Use",
            "9900": "Exempt Property"
        }
        
        if use_code in common_codes:
            use_desc = common_codes[use_code]
        
        return {
            "source": "pima_assessor",
            "address": f"{attr.get('ADDRESS_OL', '')}, TUCSON, AZ {attr.get('ZIP', '')}".strip(),
            "owner_name": attr.get("MAIL1"), # Assumption: First line is owner
            "mailing_address": mail_addr_clean,
            "sqft": None, # Not in this layer
            "year_built": None, # Not in this layer
            "property_type": use_desc,
            "parcel_id": attr.get("PARCEL"),
            "lot_size": attr.get("GISACRES"),
            "zoning": attr.get("CURZONE_OL"),
            "estimated_value": attr.get("FCV"), # Full Cash Value
            "latitude": lat,
            "longitude": lng,
            "status": "New",
            "strategy": "Wholesale"
        }

    def _map_pinal_parcel(self, feature: Dict) -> Dict:
        attr = feature.get("attributes", {})
        geometry = feature.get("geometry", {})
        
        # Calculate Centroid
        lat, lng = None, None
        if "x" in geometry and "y" in geometry:
            # Point geometry
            lng, lat = geometry["x"], geometry["y"]
        elif "rings" in geometry and geometry["rings"]:
            # Polygon geometry
            ring = geometry["rings"][0]
            if ring:
                lng = sum(p[0] for p in ring) / len(ring)
                lat = sum(p[1] for p in ring) / len(ring)
                
        # Construct Mailing Address
        mail_parts = [
            attr.get('PSTLADDRESS', ''),
            attr.get('PSTLCITY', ''),
            attr.get('PSTLSTATE', ''),
            attr.get('PSTLZIP5', '')
        ]
        mail_addr_clean = " ".join([str(p) for p in mail_parts if p and str(p).strip()])
        
        return {
            "source": "pinal_assessor",
            "address": attr.get('SITEADDRESS', '').strip(),
            "owner_name": attr.get("OWNERNME1"),
            "mailing_address": mail_addr_clean,
            "sqft": attr.get("BLDGAREA") or attr.get("RESFLRAREA"),
            "year_built": attr.get("RESYRBLT"),
            "property_type": attr.get("USEDSCRP"),
            "parcel_id": str(attr.get("PARCEL_ID") or attr.get("PARCEL")), # Pinal uses PARCEL_ID (int) or PARCEL (string)? Schema had PARCEL_ID
            "lot_size": attr.get("GROSSAC"), # Acres
            "zoning": None, # Not obvious in schema, maybe CLASSCD?
            "estimated_value": attr.get("FCV"), # Full Cash Value if available, schema showed LNDVALUE etc.
            "last_sale_date": attr.get("SALEDATE"),
            "last_sale_price": attr.get("SALEPRICE"),
            "latitude": lat,
            "longitude": lng,
            "status": "New",
            "strategy": "Wholesale"
        }

    def _map_tucson_violation(self, attr: Dict) -> Dict:
        return {
            "source": "tucson_code_enforcement",
            "address": attr.get("ADDRESSMATCH"),
            "distress_signals": [f"Code Violation: {attr.get('VIOLATION_TYPE', 'Unknown')}"],
            "status": "New",
            "strategy": "Wholesale"
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
