# ui/pages/license_risk.py
"""
D.A.M.I. License Risk Analysis Page

Displays license compliance risks for database and OS migrations.
This is the #1 cause of cloud migration cost overruns — and no other
migration tool detects or warns about it.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from agents.license_advisor import LicenseAdvisor


def render():
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 4px;">
        <span style="font-size: 2rem;">🔒</span>
        <div>
            <h2 style="margin: 0; color: #e2e8f0;">License Risk Intelligence</h2>
            <p style="margin: 0; color: #94a3b8; font-size: 0.85rem;">
                AI-powered license cost risk detection for database and OS migrations
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.25); 
         border-radius: 8px; padding: 12px 16px; margin-bottom: 16px;">
        <span style="color: #ef4444; font-weight: 700;">Why this matters:</span>
        <span style="color: #cbd5e1;">
            Oracle licensing is the #1 cause of cloud migration cost overruns. 
            A 4-core on-prem Oracle server migrated to a 16-vCPU GCE instance can increase 
            license costs from $190K to $380K/year. D.A.M.I. detects these risks automatically.
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # Run analysis
    with st.spinner("Analyzing license risks across all databases and servers..."):
        try:
            advisor = LicenseAdvisor()
            results = advisor.analyze_all_licenses()
        except Exception as e:
            st.error(f"License analysis failed: {e}")
            return
    
    summary = results["summary"]
    db_risks = results["database_risks"]
    os_risks = results["os_risks"]
    recommendations = results["recommendations"]
    
    # ── Summary KPIs ──
    k1, k2, k3, k4 = st.columns(4)
    
    total_risk_usd = summary["total_annual_cost_risk_usd"]
    total_risk_inr = summary["total_annual_cost_risk_inr"]
    
    with k1:
        color = "#ef4444" if total_risk_usd > 100000 else "#fbbf24" if total_risk_usd > 0 else "#10b981"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(239,68,68,0.12), rgba(239,68,68,0.04)); 
             border: 1px solid rgba(239,68,68,0.25); border-radius: 10px; padding: 16px; text-align: center;">
            <div style="font-size: 1.6rem; font-weight: 800; color: {color};">
                ${total_risk_usd:,.0f}
            </div>
            <div style="font-size: 0.75rem; color: #94a3b8;">Annual License Risk (USD)</div>
            <div style="font-size: 0.65rem; color: #64748b; margin-top: 2px;">INR {total_risk_inr:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with k2:
        high = summary["high_risk_count"]
        bg = "rgba(239,68,68,0.12)" if high > 0 else "rgba(16,185,129,0.12)"
        clr = "#ef4444" if high > 0 else "#10b981"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {bg}, rgba(0,0,0,0)); 
             border: 1px solid {clr}33; border-radius: 10px; padding: 16px; text-align: center;">
            <div style="font-size: 1.6rem; font-weight: 800; color: {clr};">{high}</div>
            <div style="font-size: 0.75rem; color: #94a3b8;">High Risk Items</div>
        </div>
        """, unsafe_allow_html=True)
    
    with k3:
        med = summary["medium_risk_count"]
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(251,191,36,0.12), rgba(0,0,0,0)); 
             border: 1px solid rgba(251,191,36,0.25); border-radius: 10px; padding: 16px; text-align: center;">
            <div style="font-size: 1.6rem; font-weight: 800; color: #fbbf24;">{med}</div>
            <div style="font-size: 0.75rem; color: #94a3b8;">Medium Risk Items</div>
        </div>
        """, unsafe_allow_html=True)
    
    with k4:
        total = summary["total_databases_analyzed"]
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(0,0,0,0)); 
             border: 1px solid rgba(99,102,241,0.25); border-radius: 10px; padding: 16px; text-align: center;">
            <div style="font-size: 1.6rem; font-weight: 800; color: #818cf8;">{total}</div>
            <div style="font-size: 0.75rem; color: #94a3b8;">Databases Analyzed</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("")
    
    # ── Strategic Recommendations ──
    st.markdown("### Strategic Recommendations")
    for rec in recommendations:
        priority = rec["priority"]
        if priority == "CRITICAL":
            icon, bg, border = "🔴", "rgba(239,68,68,0.08)", "rgba(239,68,68,0.3)"
        elif priority == "HIGH":
            icon, bg, border = "🟠", "rgba(249,115,22,0.08)", "rgba(249,115,22,0.3)"
        elif priority == "MEDIUM":
            icon, bg, border = "🟡", "rgba(251,191,36,0.08)", "rgba(251,191,36,0.3)"
        else:
            icon, bg, border = "🔵", "rgba(99,102,241,0.08)", "rgba(99,102,241,0.3)"
        
        st.markdown(f"""
        <div style="background: {bg}; border: 1px solid {border}; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span>{icon}</span>
                <strong style="color: #e2e8f0;">{rec['title']}</strong>
                <span style="font-size: 0.7rem; color: #94a3b8; margin-left: auto; 
                      background: rgba(0,0,0,0.3); padding: 2px 8px; border-radius: 4px;">{priority}</span>
            </div>
            <div style="color: #cbd5e1; font-size: 0.85rem; margin: 4px 0 4px 28px;">{rec['detail']}</div>
            <div style="color: #94a3b8; font-size: 0.8rem; margin-left: 28px;">
                <strong style="color:#818cf8;">Action:</strong> {rec['action']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("---")
    
    # ── Database License Risk Details ──
    st.markdown("### Database License Risk Analysis")
    
    if db_risks:
        # Cost comparison chart
        chart_col, detail_col = st.columns([3, 2])
        
        with chart_col:
            # Group by risk level for visualization
            risk_df = pd.DataFrame(db_risks)
            
            # On-prem vs Cloud cost comparison bar chart
            fig = go.Figure()
            
            servers = [r.get("server_name", r.get("db_id", "Unknown")) for r in db_risks[:15]]
            onprem_costs = [r.get("annual_cost_onprem", 0) / 1000 for r in db_risks[:15]]
            cloud_costs = [r.get("annual_cost_cloud", 0) / 1000 for r in db_risks[:15]]
            
            fig.add_trace(go.Bar(
                name="On-Prem License ($K/yr)",
                x=servers, y=onprem_costs,
                marker_color="#3b82f6",
                hovertemplate="%{x}<br>On-Prem: $%{y:.0f}K/yr<extra></extra>"
            ))
            fig.add_trace(go.Bar(
                name="Cloud License ($K/yr)",
                x=servers, y=cloud_costs,
                marker_color="#ef4444",
                hovertemplate="%{x}<br>Cloud: $%{y:.0f}K/yr<extra></extra>"
            ))
            
            fig.update_layout(
                title=dict(text="License Cost: On-Prem vs Cloud", font=dict(color="#e2e8f0", size=14)),
                xaxis_title="Server / Database",
                yaxis_title="Annual License Cost ($K)",
                barmode="group",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                height=400,
                margin=dict(l=50, r=20, t=40, b=80),
                legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
                xaxis=dict(tickangle=-45, gridcolor="rgba(100,116,139,0.1)"),
                yaxis=dict(gridcolor="rgba(100,116,139,0.1)"),
                bargap=0.25,
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with detail_col:
            # Risk level distribution
            risk_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "SAFE": 0}
            for r in db_risks:
                level = r.get("risk_level", "LOW")
                if level in risk_counts:
                    risk_counts[level] += 1
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=list(risk_counts.keys()),
                values=list(risk_counts.values()),
                hole=0.55,
                marker_colors=["#ef4444", "#fbbf24", "#3b82f6", "#10b981"],
                textinfo="label+value",
                textfont=dict(size=12, color="#e2e8f0"),
            )])
            fig_pie.update_layout(
                title=dict(text="Risk Distribution", font=dict(color="#e2e8f0", size=14)),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                height=300,
                margin=dict(l=20, r=20, t=40, b=20),
                showlegend=False,
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # Quick stats
            oracle_count = len([r for r in db_risks if r.get("db_engine") == "oracle"])
            mysql_count = len([r for r in db_risks if r.get("db_engine") == "mysql"])
            st.markdown(f"""
            <div style="background: rgba(30,30,47,0.5); border-radius: 8px; padding: 12px; font-size: 0.8rem;">
                <div style="color: #e2e8f0; font-weight: 600; margin-bottom: 6px;">Engine Breakdown</div>
                <div style="color: #ef4444;">Oracle Enterprise: {oracle_count} databases</div>
                <div style="color: #10b981;">MySQL Community: {mysql_count} databases</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Detailed risk table
        st.markdown("#### Detailed Risk Assessment")
        
        # Show high risk items first with expandable details
        for risk in sorted(db_risks, key=lambda x: {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "SAFE": 3}.get(x.get("risk_level", "LOW"), 4)):
            level = risk.get("risk_level", "LOW")
            delta = risk.get("annual_cost_delta", 0)
            
            if level == "HIGH":
                badge_color, badge_bg = "#ef4444", "rgba(239,68,68,0.15)"
            elif level == "MEDIUM":
                badge_color, badge_bg = "#fbbf24", "rgba(251,191,36,0.15)"
            elif level == "SAFE":
                badge_color, badge_bg = "#10b981", "rgba(16,185,129,0.15)"
            else:
                badge_color, badge_bg = "#3b82f6", "rgba(59,130,246,0.15)"
            
            engine_icon = "🟠" if risk.get("db_engine") == "oracle" else "🐬" if risk.get("db_engine") == "mysql" else "🗄"
            
            with st.expander(
                f"{engine_icon} {risk.get('server_name', 'Unknown')} — "
                f"{risk.get('db_engine', '').upper()} {risk.get('edition', '')} | "
                f"{'$' + f'{delta:,.0f}/yr risk' if delta > 0 else 'SAFE'}"
            ):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f"""
                    **License Details:**
                    - Engine: `{risk.get('db_engine', '').upper()} {risk.get('edition', '')} {risk.get('version', '')}`
                    - Model: `{risk.get('licensing_model', 'N/A')}`
                    - DB Size: `{risk.get('size_gb', 0):.0f} GB`
                    - Stored Procs: `{'Yes' if risk.get('has_stored_procedures') else 'No'}`
                    """)
                with c2:
                    st.markdown(f"""
                    **Core Mapping:**
                    - On-Prem vCPUs: `{risk.get('onprem_vcpus', 0)}`
                    - Licensed Cores (on-prem): `{risk.get('onprem_cores_licensed', 0)}`
                    - Target: `{risk.get('target_machine_type', 'N/A')}`
                    - Licensed Cores (cloud): `{risk.get('cloud_cores_licensed', 0)}`
                    """)
                with c3:
                    st.markdown(f"""
                    **Cost Impact:**
                    - On-Prem: **${risk.get('annual_cost_onprem', 0):,.0f}**/yr
                    - Cloud: **${risk.get('annual_cost_cloud', 0):,.0f}**/yr
                    - Delta: **${delta:,.0f}**/yr
                    - Risk: `{level}`
                    """)
                
                if risk.get("recommendations"):
                    st.markdown("**Recommendations:**")
                    for rec in risk["recommendations"]:
                        st.markdown(f"  - {rec}")
    else:
        st.info("No database license risks detected.")
    
    # ── OS License Risks ──
    if os_risks:
        st.write("---")
        st.markdown("### Operating System License Risks")
        st.caption(f"Found {len(os_risks)} Windows Server instances with potential license implications.")
        
        os_df = pd.DataFrame([{
            "Server": r.get("server_name", "Unknown"),
            "OS": r.get("os", ""),
            "vCPUs": r.get("onprem_vcpus", 0),
            "Risk Level": r.get("risk_level", "LOW"),
            "Annual Delta": f"${r.get('annual_cost_delta', 0):,.0f}",
        } for r in os_risks])
        
        st.dataframe(os_df, use_container_width=True, hide_index=True)
    
    # ── License Cost Projection ──
    st.write("---")
    st.markdown("### 5-Year License Cost Projection")
    
    if db_risks:
        years = list(range(1, 6))
        total_onprem_annual = sum(r.get("annual_cost_onprem", 0) for r in db_risks)
        total_cloud_annual = sum(r.get("annual_cost_cloud", 0) for r in db_risks)
        # Assume 3% annual price increase
        onprem_5yr = [total_onprem_annual * (1.03 ** y) / 1000 for y in years]
        cloud_5yr = [total_cloud_annual * (1.03 ** y) / 1000 for y in years]
        # AlloyDB migration scenario (no Oracle license after year 2)
        alloydb_5yr = [total_cloud_annual * (1.03 ** y) / 1000 if y <= 1 
                       else 50 * (1.03 ** y)  # $50K/yr for AlloyDB managed service
                       for y in years]
        
        fig_proj = go.Figure()
        fig_proj.add_trace(go.Scatter(
            x=years, y=onprem_5yr, name="On-Prem (Current)",
            line=dict(color="#3b82f6", width=3), mode="lines+markers"
        ))
        fig_proj.add_trace(go.Scatter(
            x=years, y=cloud_5yr, name="Cloud (with Oracle BYOL)",
            line=dict(color="#ef4444", width=3), mode="lines+markers"
        ))
        fig_proj.add_trace(go.Scatter(
            x=years, y=alloydb_5yr, name="Cloud (AlloyDB Migration)",
            line=dict(color="#10b981", width=3, dash="dash"), mode="lines+markers"
        ))
        fig_proj.update_layout(
            xaxis_title="Year", yaxis_title="Annual License Cost ($K)",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0"), height=350,
            margin=dict(l=50, r=20, t=20, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
            xaxis=dict(gridcolor="rgba(100,116,139,0.1)", dtick=1),
            yaxis=dict(gridcolor="rgba(100,116,139,0.1)"),
        )
        st.plotly_chart(fig_proj, use_container_width=True)
        
        savings_5yr = sum(cloud_5yr) - sum(alloydb_5yr)
        st.caption(
            f"Migrating from Oracle to AlloyDB PostgreSQL could save approximately "
            f"**${savings_5yr:,.0f}K** over 5 years by eliminating Oracle license costs. "
            f"This projection assumes 3% annual price escalation."
        )


if __name__ == "__main__":
    render()
