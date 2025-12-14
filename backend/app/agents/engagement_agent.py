class EngagementAgent:
    def __init__(self):
        pass

    async def skip_trace(self, lead_data: dict):
        """
        Simulates a skip trace to find phone/email.
        """
        import random
        import asyncio
        
        # Simulate API latency
        await asyncio.sleep(1.5)
        
        # Mock data generation
        mock_phones = ["(520) 555-0123", "(520) 555-4567", "(520) 555-8901"]
        mock_emails = ["owner@example.com", "investor@gmail.com", "info@properties.com"]
        mock_names = ["John Doe", "Jane Smith", "ABC Properties LLC"]
        mock_addresses = ["123 Main St, Tucson, AZ 85701", "PO Box 456, Phoenix, AZ 85001", "456 Oak Ave, Scottsdale, AZ 85251"]
        
        return {
            "phone": random.choice(mock_phones),
            "email": random.choice(mock_emails),
            "owner_name": random.choice(mock_names),
            "mailing_address": random.choice(mock_addresses),
            "social_ids": {
                "linkedin": "https://linkedin.com/in/example",
                "facebook": "https://facebook.com/example",
                "twitter": "https://twitter.com/example"
            },
            "status": "found"
        }

    async def engage_lead(self, lead_data: dict):
        """
        Decides engagement strategy (SMS/Voice) and initiates contact.
        """
        phone = lead_data.get("phone")
        if not phone:
            return {"status": "failed", "reason": "No phone number"}

        channel = self._select_channel(lead_data)
        print(f"Engaging {phone} via {channel}...")
        
        # TODO: Call Twilio/Vapi API
        return {"status": "queued", "channel": channel, "timestamp": "2023-10-27T10:00:00Z"}

    def _select_channel(self, data: dict) -> str:
        # Simple logic: High equity -> Voice, Low equity -> SMS
        if data.get("equity_percent", 0) > 0.4:
            return "voice"
        return "sms"
