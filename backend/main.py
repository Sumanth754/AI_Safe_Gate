from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from backend.scrubber import PIIScrubber
from backend.db import get_db, init_db, AuditLog, TokenUsage
from backend.proxy import forward_to_openai, calculate_cost

app = FastAPI(title="SafeGate API Proxy")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB on startup
@app.on_event("startup")
def startup():
    init_db()

scrubber = PIIScrubber()

@app.post("/chat")
async def chat_proxy(payload: dict, x_api_key: Optional[str] = Header(None), db: Session = Depends(get_db)):
    user_id = payload.get("user_id", "anonymous")
    messages = payload.get("messages", [])
    
    if not messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    # 1. Scrub PII from the user's latest message
    original_text = messages[-1]['content']
    scrubbed_text, pii_count = scrubber.scrub(original_text)
    
    # Update payload with scrubbed text
    messages[-1]['content'] = scrubbed_text
    
    # 2. Forward to LLM
    try:
        response = await forward_to_openai(payload, api_key=x_api_key)
        
        # 3. Log Audit Trail
        audit_log = AuditLog(
            user_id=user_id,
            original_text=original_text,
            scrubbed_text=scrubbed_text,
            pii_count=pii_count
        )
        db.add(audit_log)
        
        # 4. Log Token Usage
        usage = response.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)
        cost = calculate_cost(total_tokens, payload.get("model", "gpt-4o"))

        token_usage = TokenUsage(
            user_id=user_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost
        )
        db.add(token_usage)
        db.commit()

        return {
            "response": response,
            "pii_stats": {"leaks_prevented": pii_count},
            "scrubbed_preview": scrubbed_text if pii_count > 0 else None
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total_leaks = db.query(AuditLog).count()
    total_pii_prevented = sum([log.pii_count for log in db.query(AuditLog).all()])
    total_tokens = sum([u.total_tokens for u in db.query(TokenUsage).all()])
    total_cost = sum([u.cost for u in db.query(TokenUsage).all()])
    
    return {
        "total_requests": total_leaks,
        "pii_leaks_prevented": total_pii_prevented,
        "total_tokens_used": total_tokens,
        "total_cost_usd": round(total_cost, 4)
    }

@app.get("/logs")
def get_logs(db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all()
    return logs
