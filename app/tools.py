from __future__ import annotations

from .database import save_lead


class CounsellorTools:
    """Business-action boundary for future integrations such as CRM, calendar and telephony."""

    @staticmethod
    def capture_lead(payload) -> dict:
        return {"success": True, "lead_id": save_lead(payload)}

    @staticmethod
    def human_handoff(reason: str = "customer_requested") -> dict:
        # Keep this deterministic now; a telephony/CRM adapter can replace it later.
        return {"success": True, "status": "handoff_requested", "reason": reason}

    @staticmethod
    def schedule_callback(preferred_time: str, phone: str) -> dict:
        # Placeholder contract for the future calendar/telephony adapter.
        return {"success": True, "status": "callback_requested", "preferred_time": preferred_time, "phone": phone}
