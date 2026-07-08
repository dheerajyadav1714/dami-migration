# ui/pages/cutover.py
"""
D.A.M.I. Cutover Simulation & Runbook Page

Visual timeline with:
- Phase-by-phase Gantt chart
- Minute-by-minute runbook
- Downtime estimation
- Rollback planning
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import plotly.graph_objects as go
from agents.cutover_simulator import CutoverSimulator


def render():
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 4px;">
        <span style="font-size: 2rem;">🚀</span>
        <div>
            <h2 style="margin: 0; color: #e2e8f0;">Cutover Simulation</h2>
            <p style="margin: 0; color: #94a3b8; font-size: 0.85rem;">
                Simulated migration cutover with timeline, runbook, and rollback planning
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.spinner("Simulating cutover for all waves..."):
        try:
            simulator = CutoverSimulator()
            all_sims = simulator.simulate_all_waves()
        except Exception as e:
            st.error(f"Cutover simulation failed: {e}")
            return
    
    if not all_sims:
        st.warning("No migration waves found. Run the Wave Planner agent first.")
        return
    
    # Wave selector
    wave_options = {f"{s['wave_name']} ({s['total_servers']} servers, {s['total_databases']} DBs)": i 
                    for i, s in enumerate(all_sims)}
    selected_label = st.selectbox("Select Migration Wave", list(wave_options.keys()))
    sim = all_sims[wave_options[selected_label]]
    
    st.write("---")
    
    # ── Summary KPIs ──
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        hrs = sim["total_duration_hours"]
        color = "#ef4444" if hrs > 4 else "#fbbf24" if hrs > 2 else "#10b981"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(0,0,0,0)); 
             border: 1px solid rgba(99,102,241,0.25); border-radius: 10px; padding: 16px; text-align: center;">
            <div style="font-size: 1.6rem; font-weight: 800; color: {color};">{hrs}h</div>
            <div style="font-size: 0.75rem; color: #94a3b8;">Estimated Downtime</div>
            <div style="font-size: 0.65rem; color: #64748b;">{sim['total_duration_minutes']} minutes</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(239,68,68,0.12), rgba(0,0,0,0)); 
             border: 1px solid rgba(239,68,68,0.25); border-radius: 10px; padding: 16px; text-align: center;">
            <div style="font-size: 1.6rem; font-weight: 800; color: #ef4444;">{sim['rollback_time_hours']}h</div>
            <div style="font-size: 0.75rem; color: #94a3b8;">Rollback Time</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(34,211,238,0.12), rgba(0,0,0,0)); 
             border: 1px solid rgba(34,211,238,0.25); border-radius: 10px; padding: 16px; text-align: center;">
            <div style="font-size: 1.6rem; font-weight: 800; color: #22d3ee;">{sim['data_volume_gb']:.0f} GB</div>
            <div style="font-size: 0.75rem; color: #94a3b8;">Data Volume</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        window = sim.get("recommended_window", {})
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(16,185,129,0.12), rgba(0,0,0,0)); 
             border: 1px solid rgba(16,185,129,0.25); border-radius: 10px; padding: 16px; text-align: center;">
            <div style="font-size: 1.2rem; font-weight: 800; color: #10b981;">{window.get('recommended_hours', 4)}h</div>
            <div style="font-size: 0.75rem; color: #94a3b8;">Recommended Window</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("---")
    
    # ── Cutover Timeline (Gantt-like) ──
    st.markdown("### Cutover Timeline")
    
    phases = sim["phases"]
    phase_names = [p["phase"] for p in phases]
    durations = [p["duration_min"] for p in phases]
    icons = [p["icon"] for p in phases]
    
    # Build cumulative start times
    starts = []
    cumulative = 0
    for d in durations:
        starts.append(cumulative)
        cumulative += d
    
    colors = ["#6366f1", "#8b5cf6", "#3b82f6", "#ef4444", "#22d3ee", "#fbbf24", "#10b981", "#f97316"]
    
    fig = go.Figure()
    for i, (name, start, dur) in enumerate(zip(phase_names, starts, durations)):
        fig.add_trace(go.Bar(
            y=[name],
            x=[dur],
            base=[start],
            orientation="h",
            name=name,
            marker_color=colors[i % len(colors)],
            text=f"{dur}min",
            textposition="inside",
            textfont=dict(color="white", size=10),
            hovertemplate=f"<b>{icons[i]} {name}</b><br>Start: T+{start}min<br>Duration: {dur}min<extra></extra>",
        ))
    
    fig.update_layout(
        xaxis_title="Minutes from Start (T+0)",
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0"),
        height=max(250, len(phases) * 40),
        margin=dict(l=180, r=20, t=20, b=40),
        xaxis=dict(gridcolor="rgba(100,116,139,0.1)"),
        yaxis=dict(autorange="reversed"),
        barmode="stack",
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # ── Maintenance Window ──
    window = sim.get("recommended_window", {})
    st.markdown(f"""
    <div style="background: rgba(16,185,129,0.06); border: 1px solid rgba(16,185,129,0.2); 
         border-radius: 8px; padding: 12px 16px; margin: 8px 0;">
        <strong style="color: #10b981;">📅 Recommended Window:</strong>
        <span style="color: #e2e8f0;">{window.get('suggested_window', 'Saturday 02:00-06:00 UTC')}</span>
        <div style="color: #94a3b8; font-size: 0.8rem; margin-top: 4px;">
            Minimum: {window.get('minimum_hours', 2)}h | 
            Recommended: {window.get('recommended_hours', 4)}h (includes {window.get('includes_buffer', '50%')} buffer)
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("---")
    
    # ── Runbook ──
    st.markdown("### 📋 Cutover Runbook")
    
    for step in sim.get("runbook", []):
        icon = step.get("icon", "📌")
        owner = step.get("owner", "TBD")
        
        st.markdown(f"""
        <div style="display: flex; align-items: flex-start; gap: 12px; margin-bottom: 8px;
             background: rgba(30,30,47,0.3); border-left: 3px solid rgba(99,102,241,0.4);
             border-radius: 0 8px 8px 0; padding: 10px 14px;">
            <div style="min-width: 70px; text-align: center;">
                <div style="font-size: 1.2rem;">{icon}</div>
                <div style="font-size: 0.7rem; color: #818cf8; font-weight: 600;">{step['time']}</div>
            </div>
            <div style="flex: 1;">
                <div style="font-weight: 600; color: #e2e8f0; font-size: 0.9rem;">{step['phase']}</div>
                <div style="color: #94a3b8; font-size: 0.8rem;">{step['description']}</div>
            </div>
            <div style="min-width: 80px; text-align: right;">
                <div style="font-size: 0.75rem; color: #fbbf24;">{step['duration_min']} min</div>
                <div style="font-size: 0.7rem; color: #64748b;">{owner}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("---")
    
    # ── Cross-Wave Comparison ──
    st.markdown("### Wave Duration Comparison")
    
    wave_names = [s["wave_name"] for s in all_sims]
    wave_durations = [s["total_duration_minutes"] for s in all_sims]
    wave_rollbacks = [s["rollback_time_minutes"] for s in all_sims]
    
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(
        name="Cutover Duration", x=wave_names, y=wave_durations,
        marker_color="#6366f1", text=[f"{d}min" for d in wave_durations],
        textposition="outside", textfont=dict(color="#e2e8f0", size=10),
    ))
    fig_comp.add_trace(go.Bar(
        name="Rollback Time", x=wave_names, y=wave_rollbacks,
        marker_color="#ef4444", text=[f"{d}min" for d in wave_rollbacks],
        textposition="outside", textfont=dict(color="#e2e8f0", size=10),
    ))
    fig_comp.update_layout(
        yaxis_title="Duration (minutes)", barmode="group",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0"), height=320,
        margin=dict(l=50, r=20, t=20, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
        yaxis=dict(gridcolor="rgba(100,116,139,0.1)"),
    )
    st.plotly_chart(fig_comp, use_container_width=True)


if __name__ == "__main__":
    render()
