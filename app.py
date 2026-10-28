import os
import json
import base64
import urllib.parse
from io import BytesIO
from typing import Dict, Any, Optional

import streamlit as st
from PIL import Image
import requests

# Optional Gemini SDK import with graceful handling
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


# ==============================================================================
# 1. PAGE SETUP & MODERN INDUSTRIAL UI THEME (CSS)
# ==============================================================================
st.set_page_config(
    page_title="ConstruxIQ | Multimodal Construction Intelligence",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Tech Construction Theme
st.markdown("""
<style>
    /* Global styles */
    .stApp {
        background-color: #0f141c;
        color: #e2e8f0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Headers & Badges */
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #f8fafc;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #94a3b8;
        font-size: 1.0rem;
        margin-bottom: 1.5rem;
    }
    .badge-tag {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-critical { background-color: #7f1d1d; color: #fca5a5; border: 1px solid #ef4444; }
    .badge-high { background-color: #7c2d12; color: #fdba74; border: 1px solid #f97316; }
    .badge-medium { background-color: #713f12; color: #fde047; border: 1px solid #eab308; }
    .badge-low { background-color: #14532d; color: #86efac; border: 1px solid #22c55e; }
    
    /* Card Containers */
    .metric-card {
        background: #182232;
        border: 1px solid #2d3b52;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 500;
        color: #94a3b8;
        margin-bottom: 6px;
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f8fafc;
    }
    
    /* Alert Boxes */
    .weather-alert {
        border-left: 4px solid;
        border-radius: 0 8px 8px 0;
        padding: 14px 18px;
        margin-bottom: 12px;
        background-color: #1a2333;
    }
    .alert-wind { border-color: #38bdf8; }
    .alert-rain { border-color: #818cf8; }
    .alert-heat { border-color: #f97316; }
    .alert-normal { border-color: #10b981; }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 2. MOCK DEMO RESPONSES (Zero-Failure Fallback Mode)
# ==============================================================================
MOCK_PPE_RESPONSE = {
    "safety_score": 68,
    "overall_status": "Non-Compliant (Violations Detected)",
    "standards_audited": ["OSHA 1926 Subpart E", "IS 456 / IS 3786"],
    "ppe_detection": {
        "hard_hats": {"detected": True, "compliant": True, "notes": "3 of 4 observed workers wearing hard hats."},
        "high_vis_vests": {"detected": True, "compliant": False, "notes": "1 worker missing high-visibility fluorescent vest."},
        "safety_boots": {"detected": True, "compliant": True, "notes": "Steel-toe footwear standard verified."},
        "fall_harness": {"detected": False, "compliant": False, "notes": "Workers detected on scaffolding (>6ft) without tethered harnesses."}
    },
    "hazards": [
        {
            "id": "HAZ-001",
            "hazard": "Fall Protection Non-Compliance on Elevated Platform",
            "severity": "Critical",
            "code_ref": "OSHA 1926.501 / IS 13416",
            "remedy": "Cease height operations immediately. Issue full-body harnesses with double lanyard shock absorbers."
        },
        {
            "id": "HAZ-002",
            "hazard": "Missing High-Vis Vest in Vehicle Transit Zone",
            "severity": "Medium",
            "code_ref": "OSHA 1926.201",
            "remedy": "Equip worker with Class 2 reflective safety vest prior to zone entry."
        }
    ]
}

MOCK_CRACK_RESPONSE = {
    "defect_type": "Structural Shear / Settlement Crack",
    "estimated_width_mm": 4.2,
    "urgency": "Immediate",
    "structural_risk_level": "High",
    "root_cause_analysis": "Differential foundation settlement combined with cyclic thermal expansion and lateral loading.",
    "repair_protocol": [
        "Core sampling to determine crack propagation depth and rebar corrosion.",
        "Low-viscosity epoxy injection under high pressure for hairline junctions.",
        "High-performance polyurethane structural re-grouting for active water ingress zones.",
        "External carbon fiber reinforced polymer (CFRP) wrap reinforcement."
    ],
    "applicable_standard": "IS 456:2000 Section 35 (Crack Control Specifications)"
}


# ==============================================================================
# 3. HELPER FUNCTIONS & GEMINI MULTIMODAL INVOCATION
# ==============================================================================
def get_gemini_client(api_key: str):
    """Initializes Google GenAI if a key is provided."""
    if GEMINI_AVAILABLE and api_key.strip():
        genai.configure(api_key=api_key.strip())
        return True
    return False

def analyze_multimodal(image: Image.Image, prompt: str, api_key: str) -> Dict[str, Any]:
    """Sends image and structured JSON schema prompt to Gemini, with demo fallback."""
    if not get_gemini_client(api_key):
        return None  # Trigger fallback mode

    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )
        response = model.generate_content([prompt, image])
        return json.loads(response.text)
    except Exception as e:
        st.warning(f"Live API call encountered an error: {e}. Switching to calibrated simulation.")
        return None

def generate_render_url(prompt: str) -> str:
    """Generates a stable architectural render URL using Pollinations AI."""
    clean_prompt = urllib.parse.quote(prompt.strip())
    return f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1024&height=640&nologo=true&seed=42"


# ==============================================================================
# 4. SIDEBAR SETUP & ARCHITECTURE
# ==============================================================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/worker-shield.png", width=64)
    st.title("ConstruxIQ")
    st.caption("Multimodal Construction Intelligence | ID: `6ac4c98d`")
    
    st.markdown("---")
    st.subheader("🔑 Engine Configuration")
    user_gemini_key = st.text_input(
        "Google Gemini API Key",
        type="password",
        placeholder="AIzaSy...",
        help="Paste Gemini key for real-time multimodal inference. Leave blank for calibrated offline demo mode."
    )
    
    is_live = bool(user_gemini_key.strip() and GEMINI_AVAILABLE)
    if is_live:
        st.success("🟢 Multimodal Engine: Live (Gemini 1.5)", icon="⚡")
    else:
        st.info("🟡 Multimodal Engine: Demonstration Mode (Zero-Token Simulation)", icon="ℹ️")

    st.markdown("---")
    st.markdown("""
    **Standards Adherence:**
    - OSHA 1926 Subpart E & M
    - IS 456:2000 (Plain & Reinforced Concrete)
    - CPWD Indian Building Specifications
    """)
    st.markdown("---")
    st.caption("ConstruxIQ Enterprise Decision Support System")


# ==============================================================================
# 5. MAIN HEADER & TAB NAVIGATION
# ==============================================================================
st.markdown('<div class="main-title">🏗️ Multimodal Construction Intelligence Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Real-Time Site Safety Auditing, Structural Diagnostics, Valuation Forecasting & Field Protocols</div>', unsafe_allow_html=True)

tabs = st.tabs([
    "🦺 PPE Safety Vision", 
    "🔍 Crack Diagnostics", 
    "📊 Planning & Valuation (INR)", 
    "🌤️ Site Assistant & Weather Protocols"
])


# ==============================================================================
# TAB 1: SITE SAFETY & PPE AUDIT (EPIC 2 & 4)
# ==============================================================================
with tabs[0]:
    st.subheader("Automated PPE Compliance & Hazard Detection")
    st.caption("Compliant with OSHA 1926 and Bureau of Indian Standards (IS 456 / IS 3786).")
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        uploaded_safety_img = st.file_uploader(
            "Upload Site Photo (JPG/PNG)", 
            type=["jpg", "jpeg", "png"],
            key="ppe_upload"
        )
        if uploaded_safety_img:
            img_safety = Image.open(uploaded_safety_img)
            st.image(img_safety, caption="Uploaded Site Capture", use_container_width=True)
            run_safety_audit = st.button("Run Comprehensive Safety Audit", type="primary", key="btn_ppe")
        else:
            st.info("Upload an active construction site snapshot containing workers or scaffolding to begin audit.")
            run_safety_audit = False

    with col2:
        if uploaded_safety_img and run_safety_audit:
            with st.spinner("Analyzing image against OSHA/IS 456 safety matrices..."):
                prompt = """
                Analyze this construction site photo for PPE compliance and safety hazards under OSHA 1926 and IS 456.
                Return ONLY a JSON response conforming strictly to this format:
                {
                    "safety_score": <integer 0-100>,
                    "overall_status": "<Compliant | Minor Violations | Critical Risk>",
                    "standards_audited": ["OSHA 1926", "IS 456"],
                    "ppe_detection": {
                        "hard_hats": {"detected": true/false, "compliant": true/false, "notes": "..."},
                        "high_vis_vests": {"detected": true/false, "compliant": true/false, "notes": "..."},
                        "safety_boots": {"detected": true/false, "compliant": true/false, "notes": "..."},
                        "fall_harness": {"detected": true/false, "compliant": true/false, "notes": "..."}
                    },
                    "hazards": [
                        {
                            "id": "HAZ-001",
                            "hazard": "...",
                            "severity": "Low | Medium | High | Critical",
                            "code_ref": "...",
                            "remedy": "..."
                        }
                    ]
                }
                """
                safety_data = analyze_multimodal(img_safety, prompt, user_gemini_key) or MOCK_PPE_RESPONSE

            # Top KPI metrics
            m_col1, m_col2 = st.columns(2)
            with m_col1:
                score = safety_data.get("safety_score", 0)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">COMPLIANCE SAFETY SCORE</div>
                    <div class="metric-val" style="color: {'#22c55e' if score >= 80 else '#f59e0b' if score >= 60 else '#ef4444'};">
                        {score} / 100
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with m_col2:
                status = safety_data.get("overall_status", "Audited")
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">OVERALL SITE STATUS</div>
                    <div class="metric-val" style="font-size: 1.25rem; color: #38bdf8;">
                        {status}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("### 🦺 PPE Checklist")
            ppe_info = safety_data.get("ppe_detection", {})
            for ppe_item, details in ppe_info.items():
                is_comp = details.get("compliant", False)
                icon = "✅" if is_comp else "❌"
                item_name = ppe_item.replace("_", " ").title()
                st.write(f"**{icon} {item_name}**: {details.get('notes', 'N/A')}")

            st.markdown("### ⚠️ Identified Hazards & Directives")
            for haz in safety_data.get("hazards", []):
                sev = haz.get("severity", "Medium")
                badge_class = f"badge-{sev.lower()}"
                st.markdown(f"""
                <div style="background:#131d2e; border: 1px solid #23354d; border-radius:8px; padding:12px; margin-bottom:10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <strong>{haz.get('id', 'HAZ')}: {haz.get('hazard')}</strong>
                        <span class="badge-tag {badge_class}">{sev}</span>
                    </div>
                    <div style="font-size: 0.85rem; color: #94a3b8; margin: 6px 0;">Standard: {haz.get('code_ref')}</div>
                    <div style="font-size: 0.9rem; color: #cbd5e1;"><strong>Remedy:</strong> {haz.get('remedy')}</div>
                </div>
                """, unsafe_allow_html=True)

            # Download JSON Report
            st.download_button(
                label="📥 Export Structured Audit Contract (JSON)",
                data=json.dumps(safety_data, indent=2),
                file_name="site_safety_audit_contract.json",
                mime="application/json"
            )


# ==============================================================================
# TAB 2: CRACK DIAGNOSTICS & STRUCTURAL INTEGRITY (EPIC 2 & 4)
# ==============================================================================
with tabs[1]:
    st.subheader("Structural Integrity & Concrete Defect Classifier")
    st.caption("Engineering analysis for crack width, root cause failure mechanisms, and remediation.")
    
    c_col1, c_col2 = st.columns([1, 1], gap="large")
    
    with c_col1:
        uploaded_crack_img = st.file_uploader(
            "Upload Concrete / Wall Defect Photo", 
            type=["jpg", "jpeg", "png"],
            key="crack_upload"
        )
        if uploaded_crack_img:
            img_crack = Image.open(uploaded_crack_img)
            st.image(img_crack, caption="Concrete Surface Capture", use_container_width=True)
            run_crack_diag = st.button("Execute Defect Diagnostic", type="primary", key="btn_crack")
        else:
            st.info("Upload high-resolution photography of masonry, beam, slab, or column cracking.")
            run_crack_diag = False

    with c_col2:
        if uploaded_crack_img and run_crack_diag:
            with st.spinner("Analyzing structural fracture mechanics & IS 456 tolerances..."):
                prompt = """
                Analyze this concrete/masonry crack photo.
                Return ONLY a JSON response strictly formatted as:
                {
                    "defect_type": "<Hairline | Settlement | Structural Shear | Thermal Expansion | Spalling>",
                    "estimated_width_mm": <float>,
                    "urgency": "<Routine | Priority | Immediate>",
                    "structural_risk_level": "<Low | Moderate | High>",
                    "root_cause_analysis": "...",
                    "repair_protocol": [
                        "...",
                        "..."
                    ],
                    "applicable_standard": "IS 456:2000 Section 35"
                }
                """
                crack_data = analyze_multimodal(img_crack, prompt, user_gemini_key) or MOCK_CRACK_RESPONSE

            # Defect Metrics
            k1, k2, k3 = st.columns(3)
            with k1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">ESTIMATED APERTURE</div>
                    <div class="metric-val">{crack_data.get('estimated_width_mm', 0.0)} mm</div>
                </div>
                """, unsafe_allow_html=True)
            with k2:
                urgency = crack_data.get("urgency", "Moderate")
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">INTERVENTION URGENCY</div>
                    <div class="metric-val" style="color: {'#ef4444' if urgency == 'Immediate' else '#f59e0b'};">
                        {urgency}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with k3:
                risk = crack_data.get("structural_risk_level", "Moderate")
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">STRUCTURAL RISK</div>
                    <div class="metric-val" style="color: {'#ef4444' if risk == 'High' else '#38bdf8'};">
                        {risk}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"#### Primary Classification: **{crack_data.get('defect_type')}**")
            st.write(f"**Root Cause Diagnosis:** {crack_data.get('root_cause_analysis')}")
            st.info(f"**Reference Standard:** {crack_data.get('applicable_standard')}")

            st.markdown("#### Recommended Engineering Remediation:")
            for step in crack_data.get("repair_protocol", []):
                st.markdown(f"- 🔧 {step}")

            st.download_button(
                label="📥 Export Crack Diagnostic Report (JSON)",
                data=json.dumps(crack_data, indent=2),
                file_name="structural_crack_diagnostic.json",
                mime="application/json"
            )


# ==============================================================================
# TAB 3: PLANNING & REAL ESTATE VALUATION (INR) (EPIC 3)
# ==============================================================================
with tabs[2]:
    st.subheader("Construction Planning, Material Estimation & Valuation Engine")
    st.caption("Calibrated for the Indian Real Estate & Civil Engineering Sector (INR Metrics).")
    
    col_in1, col_in2, col_in3, col_in4 = st.columns(4)
    with col_in1:
        structure_type = st.selectbox(
            "Structure Classification",
            ["Residential High-Rise", "Commercial Grade A", "Industrial Warehouse", "Luxury Villa Cluster"]
        )
    with col_in2:
        city_tier = st.selectbox(
            "Geographic Location Tier",
            ["Tier 1 (Mumbai, Delhi-NCR, Bengaluru)", "Tier 2 (Pune, Hyderabad, Ahmedabad)", "Tier 3 (Emerging Urban Zones)"]
        )
    with col_in3:
        builtup_sqft = st.number_input(
            "Total Built-up Area (Sq. Ft.)",
            min_value=1000,
            max_value=2000000,
            value=25000,
            step=1000
        )
    with col_in4:
        completion_pct = st.slider("Milestone Completion (%)", 0, 100, 45)

    # Unit Cost Models (INR per sqft)
    tier_base_rates = {
        "Tier 1 (Mumbai, Delhi-NCR, Bengaluru)": {"cost_sqft": 2400, "val_sqft": 8500},
        "Tier 2 (Pune, Hyderabad, Ahmedabad)": {"cost_sqft": 1850, "val_sqft": 5500},
        "Tier 3 (Emerging Urban Zones)": {"cost_sqft": 1400, "val_sqft": 3600}
    }
    
    type_multipliers = {
        "Residential High-Rise": 1.0,
        "Commercial Grade A": 1.25,
        "Industrial Warehouse": 0.75,
        "Luxury Villa Cluster": 1.40
    }

    base = tier_base_rates[city_tier]
    multiplier = type_multipliers[structure_type]
    
    adjusted_cost_sqft = base["cost_sqft"] * multiplier
    adjusted_val_sqft = base["val_sqft"] * multiplier

    # Financial Calculations in INR
    total_budget_inr = builtup_sqft * adjusted_cost_sqft
    capex_incurred_inr = total_budget_inr * (completion_pct / 100.0)
    asset_valuation_inr = builtup_sqft * adjusted_val_sqft * (0.35 + (0.65 * (completion_pct / 100.0)))

    # Material Consumption Benchmarks
    cement_bags = int(builtup_sqft * 0.40)      # ~0.4 bags per sqft
    steel_metric_tonnes = (builtup_sqft * 3.8) / 1000.0 # ~3.8 kg per sqft

    def format_inr(amount):
        """Converts raw INR amount to Lakhs or Crores."""
        if amount >= 1e7:
            return f"₹{amount / 1e7:.2f} Cr"
        elif amount >= 1e5:
            return f"₹{amount / 1e5:.2f} Lakh"
        return f"₹{amount:,.0f}"

    st.markdown("---")
    
    # Financial Overview Row
    v1, v2, v3, v4 = st.columns(4)
    with v1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">TOTAL ESTIMATED BUDGET</div>
            <div class="metric-val">{format_inr(total_budget_inr)}</div>
        </div>
        """, unsafe_allow_html=True)
    with v2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">CAPEX INCURRED TO DATE</div>
            <div class="metric-val" style="color: #f59e0b;">{format_inr(capex_incurred_inr)}</div>
        </div>
        """, unsafe_allow_html=True)
    with v3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">CURRENT ASSET VALUATION</div>
            <div class="metric-val" style="color: #10b981;">{format_inr(asset_valuation_inr)}</div>
        </div>
        """, unsafe_allow_html=True)
    with v4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">STAGE OF COMPLETION</div>
            <div class="metric-val">{completion_pct}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.progress(completion_pct / 100.0, text=f"Milestone Execution: {completion_pct}% reached")

    # Material Requirement Metrics
    st.markdown("### 🧱 Material Quantities (Estimated Requirements)")
    m1, m2 = st.columns(2)
    with m1:
        st.metric("OPC/PPC Cement Requirement", f"{cement_bags:,} Bags (50kg)", delta="Standard IS 456 M25 Mix")
    with m2:
        st.metric("TMT Fe500D Reinforcement Steel", f"{steel_metric_tonnes:.1f} Metric Tonnes", delta="High Ductility Grade")

    # Pollinations AI Conceptual 3D Architectural Visualization
    st.markdown("---")
    st.markdown("### 🏛️ Conceptual Architectural 3D Rendering (AI Generated)")
    render_prompt = f"Modern architectural 3D elevation render of a {structure_type} in {city_tier.split(' ')[0]}, photorealistic, 8k raytracing, dramatic lighting, construction site progress {completion_pct} percent"
    render_url = generate_render_url(render_prompt)
    
    st.image(render_url, caption=f"Generative Visualization: {structure_type} ({completion_pct}% Milestone)", use_container_width=True)


# ==============================================================================
# TAB 4: DAILY SITE ASSISTANT & WEATHER PROTOCOLS (EPIC 5)
# ==============================================================================
with tabs[3]:
    st.subheader("Daily Weather Safety Directives & Multi-Turn Site Assistant")
    st.caption("Active environmental hazard mitigation combined with interactive civil advisory.")

    # Weather condition matrix
    weather_state = st.selectbox(
        "Current Site Weather Alert Status",
        ["Normal Conditions", "High Wind (>45 km/h)", "Heavy Rain / Monsoonal Downpour", "Extreme Heat Wave (>42°C)"]
    )

    if weather_state == "High Wind (>45 km/h)":
        st.markdown("""
        <div class="weather-alert alert-wind">
            <strong>CRITICAL PROTOCOL: HIGH WIND ADVISORY</strong><br>
            • Suspend all tower crane, mobile hoist, and aerial manlift operations immediately.<br>
            • Secure unanchored perimeter shuttering, ply sheets, and scaffolding netting.<br>
            • Prohibit facade installation, glazing, and external suspended cradles.
        </div>
        """, unsafe_allow_html=True)
    elif weather_state == "Heavy Rain / Monsoonal Downpour":
        st.markdown("""
        <div class="weather-alert alert-rain">
            <strong>CRITICAL PROTOCOL: HEAVY INUNDATION & ELECTRICAL SAFETY</strong><br>
            • Lockout/Tagout (LOTO) active surface dewatering feeder lines and ungrounded switchboards.<br>
            • Halt open-air concrete pours unless approved vacuum dewatering or protective tarp tents are fixed.<br>
            • Inspect retaining wall trenches and excavation shoring for hydrostatic soil slide risks.
        </div>
        """, unsafe_allow_html=True)
    elif weather_state == "Extreme Heat Wave (>42°C)":
        st.markdown("""
        <div class="weather-alert alert-heat">
            <strong>CRITICAL PROTOCOL: HEAT STRESS & CONCRETE CURING ADVISORY</strong><br>
            • Shift active heavy labor hours to double shifts: 06:00-11:00 and 16:00-19:00.<br>
            • Concrete pours require chilled batching water or wet hessian wrapping to avert plastic shrinkage cracking.<br>
            • Mandatory 15-minute electrolyte rehydration breaks every 90 minutes for all outdoor operatives.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="weather-alert alert-normal">
            <strong>STANDARD OPERATING PROTOCOL: NORMAL CONDITIONS</strong><br>
            • Standard daily tool-box talks (TBT) mandatory at shift start.<br>
            • Standard wet curing protocol on recent RCC castings (twice daily).
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 💬 Multi-Turn Construction Engineering Assistant")

    # Chat session memory initialization
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = [
            {"role": "assistant", "content": "Greetings Engineer. I am your site compliance and structural intelligence assistant. Ask me about concrete mix proportions, IS standards, OSHA safety, or daily site mitigation."}
        ]

    for message in st.session_state["chat_messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_query := st.chat_input("E.g., What is the minimum stripping time for vertical formwork of columns under IS 456?"):
        st.session_state["chat_messages"].append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            if is_live:
                try:
                    chat_model = genai.GenerativeModel("gemini-1.5-flash")
                    sys_prompt = "You are a licensed Senior Civil & Structural Engineer adhering to OSHA and IS 456 codes. Provide rigorous, concise, technical answers."
                    full_query = f"{sys_prompt}\nUser Question: {user_query}"
                    response = chat_model.generate_content(full_query)
                    answer = response.text
                except Exception as e:
                    answer = f"Simulation response: Under IS 456 (Table 5 & Clause 16), formwork removal depends on concrete grade and temperature. Vertical formwork to columns, walls, and beams is typically stripped after 16–24 hours. (Live call fallback: {e})"
            else:
                # Built-in knowledgeable response heuristics for offline demo
                q_low = user_query.lower()
                if "stripping" in q_low or "formwork" in q_low or "shuttering" in q_low:
                    answer = "**IS 456:2000 Clause 16.2 Guidelines:**\n- Vertical formwork to columns, walls, and beams: **16 to 24 hours**.\n- Soffit formwork to slabs (props left under): **3 days**.\n- Soffit formwork to beams (props left under): **7 days**.\n- Props to slabs spanning up to 4.5m: **7 days** (over 4.5m: **14 days**)."
                elif "curing" in q_low:
                    answer = "**IS 456 Concrete Curing Protocols:**\n- Ordinary Portland Cement (OPC): Minimum **7 days** under moist conditions.\n- Mineral admixtures / blended cements (PPC/GGBS): Minimum **10 days** (extends to **14 days** in hot/dry climates)."
                elif "slump" in q_low:
                    answer = "**Workability Slump Tolerances (IS 456):**\n- Shallow sections / pavements: 25–75 mm\n- Heavily reinforced sections (slabs, beams, columns): 75–100 mm\n- Pumped concrete & tremie casting: 100–150 mm."
                else:
                    answer = f"Acknowledged query regarding: *\"{user_query}\"*. For site execution, verify structural loads against IS 456:2000 and ensure safety measures follow OSHA 1926 standards. Detailed inspection documentation should be signed off by the site engineer."
            
            st.markdown(answer)
            st.session_state["chat_messages"].append({"role": "assistant", "content": answer})