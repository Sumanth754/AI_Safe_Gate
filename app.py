import streamlit as st
import pandas as pd
import sys
import os

# Add current directory to path so it can find 'backend'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.scrubber import PIIScrubber
from backend.db import init_db, SessionLocal, AuditLog, TokenUsage
from backend.proxy import forward_to_openai, calculate_cost
import datetime

# Page Config
st.set_page_config(page_title="SafeGate AI Proxy", page_icon="🛡️", layout="wide")

# Initialize Database
init_db()
db = SessionLocal()

# Initialize Scrubber (Cached to prevent reloading)
@st.cache_resource
def get_scrubber():
    return PIIScrubber()

scrubber = get_scrubber()

# --- SIDEBAR STATS ---
st.sidebar.title("🛡️ SafeGate Governance")
stats_placeholder = st.sidebar.empty()

def update_stats():
    try:
        logs = db.query(AuditLog).all()
        total_pii = sum([log.pii_count for log in logs])
        
        usage_records = db.query(TokenUsage).all()
        total_tokens = sum([u.total_tokens for u in usage_records])
        total_cost = sum([u.cost for u in usage_records])
        
        with stats_placeholder.container():
            st.metric("PII Leaks Prevented", total_pii, delta="Critical Risk", delta_color="inverse")
            st.metric("Tokens Processed", total_tokens)
            st.metric("Total Cost (USD)", f"${total_cost:.4f}")
    except Exception as e:
        st.sidebar.error(f"Stats Error: {e}")

update_stats()

# --- MAIN UI ---
st.title("SafeGate: AI Security & Governance")
st.markdown("""
This demo acts as a **Secure Proxy**. Enter text with sensitive data (names, emails, SSNs, API keys) 
to see how SafeGate **scrubs** it before it ever reaches an LLM.
""")

col_input, col_output = st.columns([1, 1])

with col_input:
    st.subheader("📝 Input (Unsafe)")
    input_text = st.text_area("Test with PII:", 
                             placeholder="Hi, I'm John Doe. My SSN is 123-45-6789 and my email is john@example.com", 
                             height=200)
    
    model_choice = st.selectbox("Select Model:", ["gemini-flash-latest", "gemini-pro-latest", "gemini-2.0-flash-lite"])
    
    run_btn = st.button("Run Safe Request 🚀", type="primary", use_container_width=True)

if run_btn:
    if input_text:
        with st.spinner("Scrubbing & Forwarding..."):
            # 1. Scrub PII
            scrubbed_text, pii_count = scrubber.scrub(input_text)
            
            # 2. Forward to LLM (Mocked if no API Key)
            # SafeGate checks for GOOGLE_API_KEY in environment
            api_key = os.getenv("GOOGLE_API_KEY")
            payload = {
                "messages": [{"role": "user", "content": scrubbed_text}], 
                "model": model_choice
            }
            
            try:
                # We use a simplified call here or the one from proxy.py
                import asyncio
                # Since streamlit is sync, we run the async function
                response = asyncio.run(forward_to_openai(payload, api_key=api_key))
                
                # 3. Log to DB
                audit_log = AuditLog(
                    user_id="streamlit_user", 
                    original_text=input_text, 
                    scrubbed_text=scrubbed_text, 
                    pii_count=pii_count
                )
                db.add(audit_log)
                
                usage = response.get("usage", {})
                token_usage = TokenUsage(
                    user_id="streamlit_user", 
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0), 
                    cost=calculate_cost(usage.get("total_tokens", 0), model=model_choice)
                )
                db.add(token_usage)
                db.commit()

                # 4. Display Results in second column
                with col_output:
                    st.subheader("🛡️ Safe Output")
                    st.info("**Scrubbed Text (Sent to LLM):**")
                    st.code(scrubbed_text)
                    
                    st.success("**AI Response:**")
                    st.write(response['choices'][0]['message']['content'])
                    
                    if pii_count > 0:
                        st.warning(f"⚠️ SafeGate prevented **{pii_count}** PII leaks in this request.")
                
                update_stats()
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("Please enter some text first!")

# --- AUDIT TRAIL ---
st.divider()
st.subheader("📋 Real-time Audit Trail (Latest 10)")
logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all()
if logs:
    log_data = [{
        "Time": log.timestamp.strftime("%H:%M:%S"),
        "Scrubbed Preview": log.scrubbed_text[:70] + "...",
        "Leaks": log.pii_count
    } for log in logs]
    st.table(pd.DataFrame(log_data))
else:
    st.write("No logs recorded yet.")

# Close DB session at end
db.close()
