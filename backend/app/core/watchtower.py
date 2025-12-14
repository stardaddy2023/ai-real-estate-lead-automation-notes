class WatchtowerService:
    def __init__(self):
        pass

    def log_event(self, event_type: str, details: dict):
        """
        Logs system events and tracks API usage.
        """
        print(f"[WATCHTOWER] {event_type}: {details}")
