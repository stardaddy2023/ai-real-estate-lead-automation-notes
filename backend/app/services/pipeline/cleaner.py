import re

class CleanerService:
    def __init__(self):
        pass

    def clean_leads(self, raw_leads: list) -> list:
        """
        Standardizes addresses and removes duplicates within the batch.
        """
        cleaned = []
        seen_addresses = set()

        for lead in raw_leads:
            # 1. Normalize Address
            raw_addr = lead.get("address", "")
            if not raw_addr:
                continue
                
            norm_addr = self._normalize_address(raw_addr)
            lead["address"] = norm_addr
            
            # 2. Deduplicate in batch
            if norm_addr in seen_addresses:
                continue
            seen_addresses.add(norm_addr)
            
            # 3. Basic Validation
            if "TUCSON" not in norm_addr and "AZ" not in norm_addr:
                # Maybe append default city/state if missing?
                # For now, just keep it.
                pass

            cleaned.append(lead)
            
        return cleaned

    def _normalize_address(self, address: str) -> str:
        """
        Converts to uppercase, removes extra spaces, standardizes suffixes.
        """
        if not address:
            return ""
            
        addr = address.upper().strip()
        
        # Remove multiple spaces
        addr = re.sub(r'\s+', ' ', addr)
        
        # Standardize common suffixes (very basic list)
        replacements = {
            " AVENUE": " AVE",
            " STREET": " ST",
            " ROAD": " RD",
            " DRIVE": " DR",
            " LANE": " LN",
            " BOULEVARD": " BLVD",
            " PLACE": " PL",
            " COURT": " CT",
            " NORTH ": " N ",
            " SOUTH ": " S ",
            " EAST ": " E ",
            " WEST ": " W "
        }
        
        for old, new in replacements.items():
            addr = addr.replace(old, new)
            
        return addr
