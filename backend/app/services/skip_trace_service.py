"""
Skip Trace Service - Enriches leads with contact information using BatchData API.

This is a modular design:
- Primary: BatchData API (real skip trace data)
- Fallback: Mock data for development/testing

Usage:
    service = SkipTraceService()
    result = await service.lookup("123 Main St, Tucson, AZ 85711", "John Doe")
"""

import os
import aiohttp
from typing import Dict, Optional, List
from pydantic import BaseModel


class SkipTraceResult(BaseModel):
    """Result from a skip trace lookup"""
    status: str  # "found", "not_found", "error"
    phone: Optional[str] = None
    phones: Optional[List[str]] = None  # All phone numbers found
    email: Optional[str] = None
    emails: Optional[List[str]] = None  # All emails found
    owner_name: Optional[str] = None
    mailing_address: Optional[str] = None
    social_ids: Optional[Dict] = None
    message: Optional[str] = None


class SkipTraceService:
    """
    Skip Trace Service with modular provider support.
    
    Currently supports:
    - BatchData API (requires BATCHDATA_API_KEY env var)
    - Mock provider (for development/testing)
    """
    
    def __init__(self):
        self.api_key = os.getenv("BATCHDATA_API_KEY")
        self.base_url = "https://api.batchdata.com/api/v1"
        self.mock_mode = not bool(self.api_key)
        
        if self.mock_mode:
            print("[SkipTrace] Running in MOCK mode (no BATCHDATA_API_KEY found)")
        else:
            print("[SkipTrace] BatchData API configured")
    
    async def lookup(
        self,
        address: str,
        owner_name: Optional[str] = None,
        city: Optional[str] = None,
        state: str = "AZ",
        zip_code: Optional[str] = None
    ) -> SkipTraceResult:
        """
        Perform a skip trace lookup for the given property/owner.
        
        Args:
            address: Property street address
            owner_name: Owner/debtor name (optional, improves accuracy)
            city: City name (optional)
            state: State abbreviation (default: AZ)
            zip_code: Zip code (optional)
            
        Returns:
            SkipTraceResult with contact information
        """
        if self.mock_mode:
            return await self._mock_lookup(address, owner_name)
        else:
            return await self._batchdata_lookup(address, owner_name, city, state, zip_code)
    
    async def _batchdata_lookup(
        self,
        address: str,
        owner_name: Optional[str],
        city: Optional[str],
        state: str,
        zip_code: Optional[str]
    ) -> SkipTraceResult:
        """
        Real skip trace using BatchData API.
        
        BatchData offers:
        - Property Skip Trace (address-based)
        - Person Skip Trace (name + location)
        
        We use property-based first, then name-based if needed.
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Try property-based skip trace first
                payload = {
                    "requests": [{
                        "streetAddress": address,
                        "city": city,
                        "state": state,
                        "zip": zip_code
                    }]
                }
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                async with session.post(
                    f"{self.base_url}/property/skip-trace",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_batchdata_response(data)
                    elif response.status == 401:
                        return SkipTraceResult(
                            status="error",
                            message="Invalid BatchData API key"
                        )
                    else:
                        error_text = await response.text()
                        print(f"[SkipTrace] BatchData error: {response.status} - {error_text}")
                        return SkipTraceResult(
                            status="error",
                            message=f"API error: {response.status}"
                        )
                        
        except aiohttp.ClientError as e:
            print(f"[SkipTrace] Network error: {e}")
            return SkipTraceResult(
                status="error",
                message=f"Network error: {str(e)}"
            )
        except Exception as e:
            print(f"[SkipTrace] Unexpected error: {e}")
            return SkipTraceResult(
                status="error",
                message=f"Unexpected error: {str(e)}"
            )
    
    def _parse_batchdata_response(self, data: Dict) -> SkipTraceResult:
        """Parse BatchData API response into SkipTraceResult."""
        try:
            results = data.get("results", [])
            if not results:
                return SkipTraceResult(status="not_found", message="No data found")
            
            result = results[0]
            persons = result.get("persons", [])
            
            if not persons:
                return SkipTraceResult(status="not_found", message="No persons found")
            
            # Get first (primary) person
            person = persons[0]
            
            # Extract phones
            phones = []
            for phone_data in person.get("phones", []):
                phone = phone_data.get("phoneNumber")
                if phone:
                    phones.append(phone)
            
            # Extract emails
            emails = []
            for email_data in person.get("emails", []):
                email = email_data.get("email")
                if email:
                    emails.append(email)
            
            # Extract mailing address
            addresses = person.get("addresses", [])
            mailing_address = None
            if addresses:
                addr = addresses[0]
                parts = [
                    addr.get("streetAddress", ""),
                    addr.get("city", ""),
                    addr.get("state", ""),
                    addr.get("zip", "")
                ]
                mailing_address = ", ".join(p for p in parts if p)
            
            # Extract name
            name = person.get("name", {})
            full_name = " ".join([
                name.get("first", ""),
                name.get("middle", ""),
                name.get("last", "")
            ]).strip()
            
            return SkipTraceResult(
                status="found",
                phone=phones[0] if phones else None,
                phones=phones,
                email=emails[0] if emails else None,
                emails=emails,
                owner_name=full_name or None,
                mailing_address=mailing_address,
                social_ids={}  # BatchData doesn't provide social IDs in standard response
            )
            
        except Exception as e:
            print(f"[SkipTrace] Parse error: {e}")
            return SkipTraceResult(
                status="error",
                message=f"Failed to parse response: {str(e)}"
            )
    
    async def _mock_lookup(
        self,
        address: str,
        owner_name: Optional[str]
    ) -> SkipTraceResult:
        """
        Mock skip trace for development/testing.
        Returns realistic fake data based on the address.
        """
        import hashlib
        
        # Generate deterministic "random" data based on address hash
        addr_hash = hashlib.md5(address.encode()).hexdigest()
        
        # 70% chance of finding data
        if int(addr_hash[0], 16) < 11:  # ~70%
            # Generate fake phone from hash
            phone_digits = "".join([str(int(c, 16) % 10) for c in addr_hash[:10]])
            phone = f"(520) {phone_digits[:3]}-{phone_digits[3:7]}"
            
            # Generate fake email from owner name
            if owner_name:
                email_user = owner_name.lower().replace(" ", ".").replace(",", "")
                email = f"{email_user}@gmail.com"
            else:
                email = f"owner{addr_hash[:6]}@email.com"
            
            return SkipTraceResult(
                status="found",
                phone=phone,
                phones=[phone],
                email=email,
                emails=[email],
                owner_name=owner_name,
                mailing_address=f"123 Different St, Tucson, AZ 85711",
                social_ids={},
                message="[MOCK DATA] Enable BatchData API for real results"
            )
        else:
            return SkipTraceResult(
                status="not_found",
                message="[MOCK DATA] No contact info found"
            )


# Singleton instance for reuse
_skip_trace_service: Optional[SkipTraceService] = None


def get_skip_trace_service() -> SkipTraceService:
    """Get or create singleton SkipTraceService instance."""
    global _skip_trace_service
    if _skip_trace_service is None:
        _skip_trace_service = SkipTraceService()
    return _skip_trace_service
