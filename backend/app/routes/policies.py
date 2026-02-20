import re
import logging
from fastapi import APIRouter, Depends, HTTPException, status

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.policy import Policy
from app.schemas.policy import (
    PolicyCreate,
    PolicyResponse,
    NLPPolicyParse,
    NLPPolicyParseResponse,
)
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.enforcer import enforcer

router = APIRouter(prefix="/api/policies", tags=["Policies"])


@router.get("/debug/enforcer")
def test_enforcer():
    """Debug endpoint to test enforcer capabilities."""
    import ctypes
    import subprocess as sp
    is_admin = ctypes.windll.shell32.IsUserAnAdmin() if hasattr(ctypes, 'windll') else False
    r = sp.run(
        'netsh advfirewall firewall add rule name=GS_PING_TEST dir=out action=block remoteip=1.2.3.4 protocol=any',
        shell=True, capture_output=True, text=True, timeout=10,
    )
    netsh_ok = r.returncode == 0
    if netsh_ok:
        sp.run('netsh advfirewall firewall delete rule name=GS_PING_TEST', shell=True, capture_output=True, timeout=10)
    resolved = enforcer._resolve_domain_ips(["spotify.com"])
    return {
        "is_admin": is_admin,
        "netsh_works": netsh_ok,
        "netsh_stdout": r.stdout.strip(),
        "netsh_stderr": r.stderr.strip(),
        "resolved_ips": resolved,
        "blocked_domains": {k: v for k, v in list(enforcer.blocked_domains.items())[:3]},
        "blocked_ips": {k: v for k, v in list(enforcer.blocked_ips.items())[:3]},
    }


@router.get("/", response_model=List[PolicyResponse])
def list_policies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    policies = db.query(Policy).all()
    return [PolicyResponse.model_validate(p) for p in policies]


@router.get("/endpoint/{endpoint_id}", response_model=List[PolicyResponse])
def get_policies_by_endpoint(
    endpoint_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    policies = db.query(Policy).filter(Policy.endpoint_id == endpoint_id).all()
    return [PolicyResponse.model_validate(p) for p in policies]


@router.post("/", response_model=PolicyResponse)
def create_policy(
    policy_data: PolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    policy = Policy(
        name=policy_data.name,
        description=policy_data.description,
        purpose=policy_data.purpose,
        conditions=policy_data.conditions,
        endpoint_id=policy_data.endpoint_id,
        is_active=policy_data.is_active,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)

    # Sync existing policies from DB first (in case of restart)
    enforcer.sync_from_db(db)

    # Enforce the policy (block domains/IPs via hosts file + Windows Firewall)
    if policy.is_active and policy.conditions and policy.purpose:
        result = enforcer.enforce_policy(policy.id, policy.purpose, policy.conditions)
        logger.info(f"Policy '{policy.name}' enforcement: {result}")

    return PolicyResponse.model_validate(policy)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )

    # Remove enforcement before deleting
    enforcer.unenforce_policy(policy_id)

    db.delete(policy)
    db.commit()


@router.patch("/{policy_id}/toggle", response_model=PolicyResponse)
def toggle_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )
    policy.is_active = not policy.is_active
    db.commit()
    db.refresh(policy)

    # Enforce or unenforce based on new state
    if policy.is_active and policy.conditions and policy.purpose:
        enforcer.enforce_policy(policy.id, policy.purpose, policy.conditions)
    else:
        enforcer.unenforce_policy(policy.id)

    return PolicyResponse.model_validate(policy)


# Known apps and their process names
KNOWN_APPS = {
    "chrome": "chrome", "firefox": "firefox", "edge": "msedge",
    "safari": "safari", "brave": "brave", "opera": "opera",
    "slack": "slack", "discord": "discord", "teams": "teams",
    "zoom": "zoom", "spotify": "spotify", "vscode": "code",
    "node": "node", "python": "python", "docker": "docker",
    "nginx": "nginx", "postgres": "postgres", "redis": "redis",
}

# Known domains
KNOWN_DOMAINS = {
    "youtube": ["youtube.com"],
    "google": ["google.com"],
    "facebook": ["facebook.com", "fbcdn.net"],
    "twitter": ["twitter.com", "x.com"],
    "x.com": ["x.com", "twitter.com"],
    "instagram": ["instagram.com", "cdninstagram.com"],
    "reddit": ["reddit.com"],
    "tiktok": ["tiktok.com"],
    "netflix": ["netflix.com"],
    "amazon": ["amazon.com"],
    "github": ["github.com"],
    "stackoverflow": ["stackoverflow.com"],
    "linkedin": ["linkedin.com"],
    "whatsapp": ["whatsapp.com", "web.whatsapp.com", "whatsapp.net", "static.whatsapp.net"],
    "telegram": ["telegram.org", "t.me", "web.telegram.org", "api.telegram.org", "core.telegram.org"],
    "spotify": ["spotify.com", "open.spotify.com", "apresolve.spotify.com", "spclient.wg.spotify.com"],
    "discord": ["discord.com", "discord.gg", "discordapp.com", "gateway.discord.gg"],
    "zoom": ["zoom.us", "zoom.com"],
    "slack": ["slack.com"],
}

COUNTRY_CODES = {
    "russia": "RU", "russian": "RU", "china": "CN", "chinese": "CN",
    "iran": "IR", "north korea": "KP", "india": "IN", "indian": "IN",
    "us": "US", "usa": "US", "american": "US", "uk": "GB", "british": "GB",
    "germany": "DE", "german": "DE", "france": "FR", "french": "FR",
    "japan": "JP", "japanese": "JP", "brazil": "BR", "australia": "AU",
}


@router.post("/parse", response_model=NLPPolicyParseResponse)
def parse_natural_language_policy(
    nlp_request: NLPPolicyParse,
    current_user: User = Depends(get_current_user),
):
    """Parse natural language into a structured policy."""
    text = (nlp_request.natural_language or nlp_request.input or "").strip()
    text_lower = text.lower()

    # Determine action
    purpose = "block"
    if any(w in text_lower for w in ["allow", "permit", "enable"]):
        purpose = "unblock"
    elif any(w in text_lower for w in ["monitor", "log", "watch", "alert"]):
        purpose = "block"  # still block-type but with alert action

    # Extract apps
    app_names = []
    for keyword, app in KNOWN_APPS.items():
        if keyword in text_lower:
            app_names.append(app)

    # Extract domains
    domains = []
    for keyword, domain_list in KNOWN_DOMAINS.items():
        if keyword in text_lower:
            for d in domain_list:
                if d not in domains:
                    domains.append(d)
    # Also match explicit domain patterns (strip URL prefixes/suffixes)
    domain_matches = re.findall(r'[\w.-]+\.\w{2,}', text)
    for d in domain_matches:
        # Clean: remove protocol prefixes and trailing slashes
        d = re.sub(r'^(https?://|www\.)', '', d).rstrip('/')
        if d and d not in domains and d.count('.') >= 1 and not d[0].isdigit():
            domains.append(d)

    # Extract IPs
    ips = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', text)

    # Extract ports
    ports = []
    port_matches = re.findall(r'port\s*(\d+)', text_lower)
    for p in port_matches:
        ports.append({"port": int(p), "protocol": ["TCP"]})

    # Extract countries
    geo_countries = []
    for keyword, code in COUNTRY_CODES.items():
        if keyword in text_lower and code not in geo_countries:
            geo_countries.append(code)

    # Extract time ranges
    time_range = None
    time_match = re.search(r'after\s+(\d{1,2})\s*(pm|am)?', text_lower)
    if time_match:
        hour = int(time_match.group(1))
        if time_match.group(2) == 'pm' and hour < 12:
            hour += 12
        time_range = {"start": f"{hour:02d}:00", "end": "23:59"}
    time_match2 = re.search(r'before\s+(\d{1,2})\s*(pm|am)?', text_lower)
    if time_match2:
        hour = int(time_match2.group(1))
        if time_match2.group(2) == 'pm' and hour < 12:
            hour += 12
        time_range = {"start": "00:00", "end": f"{hour:02d}:00"}
    between_match = re.search(r'between\s+(\d{1,2})\s*(pm|am)?\s*(?:and|to|-)\s*(\d{1,2})\s*(pm|am)?', text_lower)
    if between_match:
        h1 = int(between_match.group(1))
        if between_match.group(2) == 'pm' and h1 < 12:
            h1 += 12
        h2 = int(between_match.group(3))
        if between_match.group(4) == 'pm' and h2 < 12:
            h2 += 12
        time_range = {"start": f"{h1:02d}:00", "end": f"{h2:02d}:00"}

    # Build conditions
    parsed = {
        "domains": domains,
        "ips": ips,
        "ports": ports,
        "app_names": app_names,
    }
    if time_range:
        parsed["time_range"] = time_range
    if geo_countries:
        parsed["geo_countries"] = geo_countries

    # Generate explanation
    parts = []
    action_word = "Block" if purpose == "block" else "Allow"
    if app_names:
        parts.append(f"{action_word} {', '.join(app_names)}")
    else:
        parts.append(f"{action_word} traffic")
    if domains:
        parts.append(f"to/from {', '.join(domains)}")
    if ips:
        parts.append(f"to/from IPs {', '.join(ips)}")
    if ports:
        parts.append(f"on port(s) {', '.join(str(p['port']) for p in ports)}")
    if geo_countries:
        parts.append(f"from countries {', '.join(geo_countries)}")
    if time_range:
        parts.append(f"during {time_range['start']}-{time_range['end']}")
    explanation = " ".join(parts)

    # Confidence based on how much we extracted
    extracted_count = sum([bool(app_names), bool(domains), bool(ips), bool(ports), bool(geo_countries), bool(time_range)])
    confidence = min(0.95, 0.5 + extracted_count * 0.15)

    return NLPPolicyParseResponse(
        name=f"{action_word}: {text[:60]}",
        description=text,
        purpose=purpose,
        parsed=parsed,
        confidence=round(confidence, 2),
        explanation=explanation,
    )
