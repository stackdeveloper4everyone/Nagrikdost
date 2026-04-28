"""Mock Government API endpoints for hackathon demonstration.

Simulates real government backend services that the citizen assistant
would integrate with in production.
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter

from app.models import GrievanceTicket, GrievanceStatus

router = APIRouter(prefix="/mock", tags=["Mock Government APIs"])

# ─── IN-MEMORY MOCK DATA STORES ─────────────────────────────────────

_aadhaar_db = {
    "123456789012": {"name": "Rajesh Kumar", "age": 35, "state": "Uttar Pradesh", "gender": "male"},
    "234567890123": {"name": "Priya Sharma", "age": 28, "state": "Maharashtra", "gender": "female"},
    "345678901234": {"name": "Suresh Reddy", "age": 45, "state": "Telangana", "gender": "male"},
    "456789012345": {"name": "Lakshmi Devi", "age": 55, "state": "Tamil Nadu", "gender": "female"},
    "567890123456": {"name": "Amit Patel", "age": 22, "state": "Gujarat", "gender": "male"},
}

_ration_card_db = {
    "RC-UP-001": {"holder": "Rajesh Kumar", "type": "BPL", "members": 4, "state": "Uttar Pradesh"},
    "RC-MH-002": {"holder": "Priya Sharma", "type": "APL", "members": 3, "state": "Maharashtra"},
    "RC-TS-003": {"holder": "Suresh Reddy", "type": "AAY", "members": 5, "state": "Telangana"},
}

_land_records_db = {
    "LR-UP-001": {"owner": "Rajesh Kumar", "area_acres": 2.5, "state": "Uttar Pradesh", "district": "Lucknow", "crop": "Wheat"},
    "LR-TS-001": {"owner": "Suresh Reddy", "area_acres": 5.0, "state": "Telangana", "district": "Hyderabad", "crop": "Rice"},
}

_grievance_store: dict = {}


# ─── ENDPOINTS ───────────────────────────────────────────────────────

@router.get("/aadhaar/verify/{aadhaar_number}")
async def verify_aadhaar(aadhaar_number: str):
    """Simulate Aadhaar verification (UIDAI-like endpoint)."""
    record = _aadhaar_db.get(aadhaar_number)
    if record:
        return {
            "verified": True,
            "name": record["name"],
            "age": record["age"],
            "state": record["state"],
            "gender": record["gender"],
            "last_verified": datetime.now().isoformat(),
        }
    return {"verified": False, "message": "Aadhaar number not found"}


@router.get("/ration-card/{card_number}")
async def check_ration_card(card_number: str):
    """Simulate ration card lookup."""
    record = _ration_card_db.get(card_number)
    if record:
        return {"found": True, **record}
    return {"found": False, "message": "Ration card not found"}


@router.get("/land-records/{record_id}")
async def get_land_record(record_id: str):
    """Simulate land record lookup for farmer schemes."""
    record = _land_records_db.get(record_id)
    if record:
        return {"found": True, **record}
    return {"found": False, "message": "Land record not found"}


@router.get("/schemes")
async def list_schemes(
    state: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 20,
):
    """List available government schemes with optional filters."""
    import json
    import os

    data_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "schemes.json")
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            schemes = json.load(f)
    except FileNotFoundError:
        return {"schemes": [], "total": 0}

    results = schemes

    if state:
        results = [
            s for s in results
            if s.get("is_central", True) or (s.get("states") and state in s["states"])
        ]

    if category:
        results = [s for s in results if s.get("category", "").lower() == category.lower()]

    return {"schemes": results[:limit], "total": len(results)}


@router.post("/eligibility-check")
async def check_eligibility(data: dict):
    """Rule-based eligibility check against a specific scheme."""
    scheme_id = data.get("scheme_id")
    user_age = data.get("age")
    user_income = data.get("income")
    user_gender = data.get("gender", "all")
    user_state = data.get("state")
    user_category = data.get("category")

    import json
    import os

    data_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "schemes.json")
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            schemes = json.load(f)
    except FileNotFoundError:
        return {"eligible": False, "reason": "Scheme data not available"}

    scheme = next((s for s in schemes if s["id"] == scheme_id), None)
    if not scheme:
        return {"eligible": False, "reason": f"Scheme '{scheme_id}' not found"}

    eligibility = scheme.get("eligibility", {})
    reasons = []
    eligible = True

    if user_age is not None:
        if eligibility.get("min_age") and user_age < eligibility["min_age"]:
            eligible = False
            reasons.append(f"Minimum age is {eligibility['min_age']}, you are {user_age}")
        if eligibility.get("max_age") and user_age > eligibility["max_age"]:
            eligible = False
            reasons.append(f"Maximum age is {eligibility['max_age']}, you are {user_age}")

    if user_income is not None and eligibility.get("max_income"):
        if user_income > eligibility["max_income"]:
            eligible = False
            reasons.append(f"Maximum income limit is ₹{eligibility['max_income']:,}, yours is ₹{user_income:,}")

    if user_gender and eligibility.get("gender") and eligibility["gender"] != "all":
        if user_gender != eligibility["gender"]:
            eligible = False
            reasons.append(f"This scheme is for {eligibility['gender']} applicants only")

    if user_state and eligibility.get("states"):
        if user_state not in eligibility["states"]:
            eligible = False
            reasons.append(f"This scheme is available only in: {', '.join(eligibility['states'])}")

    return {
        "scheme_id": scheme_id,
        "scheme_name": scheme["name_en"],
        "eligible": eligible,
        "reasons": reasons if not eligible else ["You meet all eligibility criteria!"],
        "benefits": scheme.get("benefits", ""),
        "required_documents": scheme.get("required_documents", []),
    }


@router.post("/grievance")
async def file_grievance(data: dict):
    """File a new grievance and get a tracking ticket."""
    ticket_id = f"GRV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    ticket = {
        "ticket_id": ticket_id,
        "subject": data.get("subject", ""),
        "description": data.get("description", ""),
        "category": data.get("category", "General"),
        "state": data.get("state", ""),
        "district": data.get("district", ""),
        "status": "submitted",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "expected_resolution": (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d"),
        "assigned_to": f"Officer-{random.randint(100,999)}",
    }

    _grievance_store[ticket_id] = ticket
    return ticket


@router.get("/grievance/{ticket_id}")
async def check_grievance_status(ticket_id: str):
    """Check the status of a filed grievance."""
    ticket = _grievance_store.get(ticket_id)
    if ticket:
        # Simulate progress
        return ticket
    return {"found": False, "message": f"Grievance ticket '{ticket_id}' not found"}


@router.get("/grievance")
async def list_grievances():
    """List all filed grievances."""
    return {"grievances": list(_grievance_store.values()), "total": len(_grievance_store)}


@router.post("/income-certificate/verify")
async def verify_income_certificate(data: dict):
    """Simulate income certificate verification."""
    cert_number = data.get("certificate_number", "")
    return {
        "verified": True,
        "certificate_number": cert_number,
        "holder_name": "Verified Citizen",
        "annual_income": random.choice([150000, 200000, 300000, 500000]),
        "issuing_authority": "District Collector",
        "valid_until": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
    }


@router.get("/health")
async def mock_health():
    """Health check for mock API server."""
    return {
        "status": "healthy",
        "service": "Mock Government API Server",
        "endpoints": [
            "/mock/aadhaar/verify/{number}",
            "/mock/ration-card/{number}",
            "/mock/land-records/{id}",
            "/mock/schemes",
            "/mock/eligibility-check",
            "/mock/grievance",
            "/mock/grievance/{ticket_id}",
            "/mock/income-certificate/verify",
        ],
    }
