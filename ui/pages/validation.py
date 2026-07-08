# ui/pages/validation.py
"""
D.A.M.I. Migration Validation & Go/No-Go Engine

Per-wave auto-generated checklists with:
- Contextual checks based on assessment data
- Critical vs non-critical categorization
- Traffic light Go/No-Go decision
- Interactive checkbox tracking
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import plotly.graph_objects as go
from agents.validation_agent import ValidationAgent


def render():
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 4px;">
        <span style="font-size: 2rem;">✅</span>
        <div>
            <h2 style="margin: 0; color: #e2e8f0;">Migration Validation & Go/No-Go</h2>
            <p style="margin: 0; color: #94a3b8; font-size: 0.85rem;">
                Auto-generated checklists from assessment data — not generic templates
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state for checked items
    if "validation_checks" not in st.session_state:
        st.session_state.validation_checks = {}
    
    # Load checklists
    with st.spinner("Generating validation checklists from assessment data..."):
        try:
            agent = ValidationAgent()
            checklists = agent.generate_wave_checklists()
        except Exception as e:
            st.error(f"Validation engine failed: {e}")
            return
    
    if not checklists:
        st.warning("No migration waves found. Run the Wave Planner agent first to create waves.")
        return
    
    # Wave selector
    wave_options = {f"{c['wave_name']} ({c['total_servers']} servers)": c['wave_id'] for c in checklists}
    selected_label = st.selectbox("Select Migration Wave", list(wave_options.keys()))
    selected_wave_id = wave_options[selected_label]
    
    # Get selected checklist
    checklist = next(c for c in checklists if c["wave_id"] == selected_wave_id)
    
    # Initialize checks for this wave
    if selected_wave_id not in st.session_state.validation_checks:
        st.session_state.validation_checks[selected_wave_id] = set()
    
    checked = st.session_state.validation_checks[selected_wave_id]
    
    st.write("---")
    
    # ── Go/No-Go Traffic Light ──
    critical_items = [i for i in checklist["items"] if i["critical"]]
    critical_done = [i for i in critical_items if i["id"] in checked]
    all_done = len(checked) >= checklist["total_checks"]
    all_critical_done = len(critical_done) == len(critical_items)
    
    if all_done:
        status, light_color, light_emoji = "GO", "#10b981", "🟢"
        status_msg = "All validation checks passed. Migration wave approved to proceed."
        bg = "rgba(16,185,129,0.08)"
        border = "rgba(16,185,129,0.3)"
    elif all_critical_done:
        status, light_color, light_emoji = "CONDITIONAL GO", "#fbbf24", "🟡"
        remaining = checklist["total_checks"] - len(checked)
        status_msg = f"All critical checks passed. {remaining} non-critical items remaining."
        bg = "rgba(251,191,36,0.08)"
        border = "rgba(251,191,36,0.3)"
    else:
        status, light_color, light_emoji = "BLOCKED", "#ef4444", "🔴"
        blocked = len(critical_items) - len(critical_done)
        status_msg = f"{blocked} critical check(s) incomplete. Migration CANNOT proceed."
        bg = "rgba(239,68,68,0.08)"
        border = "rgba(239,68,68,0.3)"
    
    # Traffic light display
    t1, t2 = st.columns([1, 3])
    with t1:
        st.markdown(f"""
        <div style="background: rgba(15,15,26,0.8); border: 2px solid {border}; border-radius: 16px; 
             padding: 24px; text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 8px;">{light_emoji}</div>
            <div style="font-size: 1.4rem; font-weight: 800; color: {light_color};">{status}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with t2:
        st.markdown(f"""
        <div style="background: {bg}; border: 1px solid {border}; border-radius: 12px; padding: 16px;">
            <div style="font-size: 1.1rem; font-weight: 600; color: #e2e8f0; margin-bottom: 8px;">
                Decision: {status}
            </div>
            <div style="color: #cbd5e1; font-size: 0.9rem; margin-bottom: 12px;">{status_msg}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Progress metrics
        p1, p2, p3, p4 = st.columns(4)
        with p1:
            st.metric("Total Checks", checklist["total_checks"])
        with p2:
            st.metric("Completed", len(checked))
        with p3:
            st.metric("Critical", f"{len(critical_done)}/{len(critical_items)}")
        with p4:
            pct = (len(checked) / max(checklist["total_checks"], 1)) * 100
            st.metric("Progress", f"{pct:.0f}%")
    
    # Progress bar
    st.progress(len(checked) / max(checklist["total_checks"], 1))
    
    st.write("---")
    
    # ── Wave Context ──
    ctx = checklist.get("context", {})
    context_items = []
    if ctx.get("environments"):
        context_items.append(f"**Environments:** {', '.join(ctx['environments'])}")
    if ctx.get("has_databases"):
        engines = ctx.get("db_engines", [])
        context_items.append(f"**Databases:** {', '.join(engines) if engines else 'Yes'}")
    if ctx.get("has_commercial_license"):
        context_items.append("**Commercial Licenses:** Oracle/SQL Server detected")
    
    if context_items:
        st.markdown(f"""
        <div style="background: rgba(99,102,241,0.06); border: 1px solid rgba(99,102,241,0.2); 
             border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; font-size: 0.85rem;">
            <strong style="color: #818cf8;">Wave Context</strong> (auto-detected from assessment data)
            <div style="color: #cbd5e1; margin-top: 4px;">{'  •  '.join(context_items)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # ── Checklist Items by Category ──
    categories = {}
    for item in checklist["items"]:
        cat = item["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    
    category_icons = {
        "Data Protection": "🛡️", "Network": "🌐", "Database": "🗄️",
        "Compliance": "📋", "Communication": "📢", "Operations": "⚙️",
        "Security": "🔒", "Testing": "🧪", "Dependencies": "🔗",
    }
    
    for cat_name, items in categories.items():
        icon = category_icons.get(cat_name, "📎")
        cat_done = sum(1 for i in items if i["id"] in checked)
        
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 8px; margin: 12px 0 4px 0;">
            <span style="font-size: 1.1rem;">{icon}</span>
            <span style="font-size: 0.95rem; font-weight: 600; color: #e2e8f0;">{cat_name}</span>
            <span style="font-size: 0.75rem; color: #64748b; background: rgba(0,0,0,0.3); 
                  padding: 2px 8px; border-radius: 4px;">{cat_done}/{len(items)}</span>
        </div>
        """, unsafe_allow_html=True)
        
        for item in items:
            col_check, col_label = st.columns([1, 15])
            
            with col_check:
                is_checked = st.checkbox(
                    label=item["id"],
                    value=item["id"] in checked,
                    key=f"val_{selected_wave_id}_{item['id']}",
                    label_visibility="collapsed",
                )
                if is_checked:
                    checked.add(item["id"])
                elif item["id"] in checked:
                    checked.discard(item["id"])
            
            with col_label:
                critical_badge = ""
                if item["critical"]:
                    critical_badge = '<span style="background: rgba(239,68,68,0.15); color: #ef4444; font-size: 0.65rem; padding: 1px 6px; border-radius: 3px; margin-left: 6px; font-weight: 600;">CRITICAL</span>'
                
                done_style = "text-decoration: line-through; color: #64748b;" if is_checked else "color: #e2e8f0;"
                st.markdown(f"""
                <div style="{done_style} font-size: 0.9rem;">
                    {item['title']}{critical_badge}
                    <div style="font-size: 0.75rem; color: #64748b; margin-top: 1px;">{item['detail']}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Update session state
    st.session_state.validation_checks[selected_wave_id] = checked
    
    # ── Blockers Summary ──
    if not all_critical_done:
        st.write("---")
        st.markdown("### 🚫 Blockers")
        for item in critical_items:
            if item["id"] not in checked:
                st.markdown(f"""
                <div style="background: rgba(239,68,68,0.06); border: 1px solid rgba(239,68,68,0.2);
                     border-radius: 6px; padding: 8px 12px; margin-bottom: 6px;">
                    <span style="color: #ef4444; font-weight: 600;">⛔ {item['title']}</span>
                    <div style="color: #94a3b8; font-size: 0.8rem;">{item['detail']}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # ── Validation Summary Chart ──
    st.write("---")
    st.markdown("### Validation Progress Across All Waves")
    
    wave_names = []
    wave_progress = []
    wave_colors = []
    
    for cl in checklists:
        wid = cl["wave_id"]
        w_checked = st.session_state.validation_checks.get(wid, set())
        pct = (len(w_checked) / max(cl["total_checks"], 1)) * 100
        wave_names.append(cl["wave_name"])
        wave_progress.append(pct)
        
        if pct >= 100:
            wave_colors.append("#10b981")
        elif pct > 50:
            wave_colors.append("#fbbf24")
        else:
            wave_colors.append("#ef4444")
    
    fig = go.Figure(data=[go.Bar(
        x=wave_names, y=wave_progress,
        marker_color=wave_colors,
        text=[f"{p:.0f}%" for p in wave_progress],
        textposition="outside",
        textfont=dict(color="#e2e8f0", size=11),
    )])
    fig.update_layout(
        yaxis_title="Validation Progress (%)",
        yaxis_range=[0, 110],
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0"), height=300,
        margin=dict(l=50, r=20, t=20, b=50),
        yaxis=dict(gridcolor="rgba(100,116,139,0.1)"),
        xaxis=dict(gridcolor="rgba(100,116,139,0.1)"),
    )
    fig.add_hline(y=100, line_dash="dash", line_color="#10b981", annotation_text="GO Threshold")
    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    render()
