from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional
from linkedin_api import Linkedin
import os
from fastapi.responses import StreamingResponse, JSONResponse
import json
from fastapi.middleware.cors import CORSMiddleware
import requests
from mailscout import Scout

app = FastAPI()

# Add CORS middleware for localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# You should set these as environment variables or use a .env file in production
LINKEDIN_USERNAME = os.getenv('LINKEDIN_USERNAME', 'your_email@example.com')
LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD', 'your_password')

# Authenticate once at startup
api = Linkedin(LINKEDIN_USERNAME, LINKEDIN_PASSWORD, debug=True)
scout = Scout()

class PersonOut(BaseModel):
    name: str
    first_name: str
    last_name: str
    linkedInUrl: str
    company: str
    title: str
    id: str

@app.get("/search", response_model=None)
def search_people(query: str = Query(..., description="Search query for LinkedIn people"), limit: int = Query(10, description="Number of results to return")):
    def event_stream():
        results = api.search_people(keywords=query, limit=limit)
        for person in results:
            urn_id = person.get('urn_id')
            if not urn_id:
                continue
            profile = api.get_profile(urn_id=urn_id)
            first_name = profile.get('firstName', '')
            last_name = profile.get('lastName', '')
            name = profile.get('full_name') or f"{first_name} {last_name}"
            public_id = profile.get('public_id', '')
            profile_url = f"https://www.linkedin.com/in/{public_id}" if public_id else ''
            experiences = profile.get('experience', [{}])
            current_org = ''
            title = ''
            if experiences:
                current_org = experiences[0].get('companyName', '')
                title = experiences[0].get('title', '')
            person_out = PersonOut(
                name=name.strip(),
                first_name=first_name,
                last_name=last_name,
                linkedInUrl=profile_url,
                company=current_org,
                title=title,
                id=urn_id
            )
            yield f"data: {person_out.json()}\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")

class EmailOut(BaseModel):
    first_name: str
    last_name: str
    emails: List[str]
    score: Optional[int]
    domain: Optional[str]
    company: Optional[str]
    status: Optional[str]
    is_deliverable: Optional[bool]
    source: Optional[str]

@app.get("/find-email", response_model=EmailOut)
def find_email(
    first_name: str = Query(..., description="First name of the person"),
    last_name: str = Query(..., description="Last name of the person"),
    source: str = Query("mailscout", description="Source to use: 'mailscout' or 'hunter'"),
    domain: Optional[str] = Query(None, description="Company domain, e.g. razorpay.com (required for mailscout, optional for hunter)"),
    company: Optional[str] = Query(None, description="Company name, e.g. Razorpay (optional, only for hunter)")
):
    first_name = first_name.strip()
    last_name = last_name.strip()
    if source == "mailscout":
        if not domain:
            return JSONResponse(status_code=400, content={"error": "'domain' is required for mailscout source"})
        name = f"{first_name} {last_name}"
        emails = scout.find_valid_emails(domain, name)
        return EmailOut(
            first_name=first_name,
            last_name=last_name,
            emails=emails,
            score=None,
            domain=domain,
            company=None,
            status=None,
            is_deliverable=True,
            source="mailscout"
        )
    else:  # hunter
        api_key = os.getenv('HUNTER_API_KEY')
        # Prefer domain if present, else use company
        if domain:
            url = f"https://api.hunter.io/v2/email-finder?domain={domain}&first_name={first_name}&last_name={last_name}&api_key={api_key}"
        elif company:
            url = f"https://api.hunter.io/v2/email-finder?company={company}&first_name={first_name}&last_name={last_name}&api_key={api_key}"
        else:
            return JSONResponse(status_code=400, content={"error": "Either 'domain' or 'company' is required for hunter source"})
        response = requests.get(url)
        if response.status_code != 200:
            return JSONResponse(status_code=500, content={"error": "Failed to fetch email"})
        data = response.json().get('data', {})
        verification = data.get('verification', {})
        email = data.get('email')
        emails = [email] if email else []
        return EmailOut(
            first_name=data.get('first_name', first_name),
            last_name=data.get('last_name', last_name),
            emails=emails,
            score=data.get('score'),
            domain=data.get('domain', domain),
            company=data.get('company', company),
            status=verification.get('status'),
            is_deliverable=scout.check_smtp(email) if email else False,
            source="hunter"
        )

@app.get("/verify-email")
def verify_email(email: str = Query(..., description="Email address to verify deliverability")):
    is_deliverable = scout.check_smtp(email)
    return {"email": email, "is_deliverable": is_deliverable}