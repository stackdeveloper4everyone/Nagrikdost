"""Grievance management service with CRUD and status tracking."""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.models import GrievanceRequest, GrievanceTicket, GrievanceStatus

logger = logging.getLogger(__name__)

# In-memory grievance store
_grievances: Dict[str, GrievanceTicket] = {}


def file_grievance(request: GrievanceRequest) -> GrievanceTicket:
    """File a new grievance and create a tracking ticket."""
    ticket_id = f"GRV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    now = datetime.now()

    ticket = GrievanceTicket(
        ticket_id=ticket_id,
        subject=request.subject,
        description=request.description,
        category=request.category,
        state=request.state,
        district=request.district,
        status=GrievanceStatus.SUBMITTED,
        created_at=now,
        updated_at=now,
    )

    _grievances[ticket_id] = ticket
    logger.info(f"Grievance filed: {ticket_id} - {request.subject}")
    return ticket


def get_grievance(ticket_id: str) -> Optional[GrievanceTicket]:
    """Get a grievance by ticket ID."""
    return _grievances.get(ticket_id)


def list_grievances(state: Optional[str] = None) -> List[GrievanceTicket]:
    """List all grievances, optionally filtered by state."""
    results = list(_grievances.values())
    if state:
        results = [g for g in results if g.state == state]
    return sorted(results, key=lambda g: g.created_at, reverse=True)


def update_status(ticket_id: str, status: GrievanceStatus, notes: str = None) -> Optional[GrievanceTicket]:
    """Update the status of a grievance."""
    ticket = _grievances.get(ticket_id)
    if ticket:
        ticket.status = status
        ticket.updated_at = datetime.now()
        if notes:
            ticket.resolution_notes = notes
        logger.info(f"Grievance {ticket_id} status updated to {status}")
        return ticket
    return None


def add_document(ticket_id: str, document_text: str) -> bool:
    """Add extracted document text to a grievance."""
    ticket = _grievances.get(ticket_id)
    if ticket:
        ticket.documents.append(document_text)
        ticket.updated_at = datetime.now()
        return True
    return False


def get_stats() -> Dict:
    """Get grievance statistics."""
    total = len(_grievances)
    by_status = {}
    for ticket in _grievances.values():
        status = ticket.status.value
        by_status[status] = by_status.get(status, 0) + 1

    return {
        "total": total,
        "by_status": by_status,
        "avg_resolution_days": 7,  # Mock value
    }
