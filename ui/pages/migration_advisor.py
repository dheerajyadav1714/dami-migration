# ui/pages/migration_advisor.py
"""
D.A.M.I. Database & App Migration Advisor Page

Shows migration path recommendations with:
- Complexity scoring and effort estimation
- Side-by-side migration path comparison
- Oracle → AlloyDB/BMS/CloudSQL routing
- App modernization recommendations
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from agents.migration_advisor import MigrationAdvisor


def render():
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 4px;">
        <span style="font-size: 2rem;">🧭</span>
        <div>
            <h2 style="margin: 0; color: #e2e8f0;">Migration Advisor</h2>
            <p style="margin: 0; color: #94a3b8; font-size: 0.85rem;">
                AI-powered database & app migration path recommendations with effort estimation
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.spinner("Analyzing databases and applications..."):
        try:
            advisor = MigrationAdvisor()
            results = advisor.analyze_all()
        except Exception as e:
            st.error(f"Migration analysis failed: {e}")
            return
    
    summary = results["summary"]
    databases = results["databases"]
    applications = results["applications"]
    
    # ── Summary KPIs ──
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(0,0,0,0)); 
             border: 1px solid rgba(99,102,241,0.25); border-radius: 10px; padding: 16px; text-align: center;">
            <div style="font-size: 1.6rem; font-weight: 800; color: #818cf8;">{summary['total_databases']}</div>
            <div style="font-size: 0.75rem; color: #94a3b8;">Databases Analyzed</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(139,92,246,0.12), rgba(0,0,0,0)); 
             border: 1px solid rgba(139,92,246,0.25); border-radius: 10px; padding: 16px; text-align: center;">
            <div style="font-size: 1.6rem; font-weight: 800; color: #a78bfa;">{summary['total_applications']}</div>
            <div style="font-size: 0.75rem; color: #94a3b8;">Applications Analyzed</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(251,191,36,0.12), rgba(0,0,0,0)); 
             border: 1px solid rgba(251,191,36,0.25); border-radius: 10px; padding: 16px; text-align: center;">
            <div style="font-size: 1.6rem; font-weight: 800; color: #fbbf24;">{summary['total_estimated_effort_weeks']}</div>
            <div style="font-size: 0.75rem; color: #94a3b8;">Estimated Effort (Weeks)</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(34,211,238,0.12), rgba(0,0,0,0)); 
             border: 1px solid rgba(34,211,238,0.25); border-radius: 10px; padding: 16px; text-align: center;">
            <div style="font-size: 1.6rem; font-weight: 800; color: #22d3ee;">{summary['total_estimated_effort_months']}</div>
            <div style="font-size: 0.75rem; color: #94a3b8;">Estimated Duration (Months)</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("---")
    
    # ── Database Migration Recommendations ──
    st.markdown("### 🗄️ Database Migration Paths")
    
    if databases:
        # Complexity overview chart
        ch1, ch2 = st.columns([3, 2])
        with ch1:
            db_names = [d.get("db_name", d.get("db_id", "?"))[:20] for d in databases]
            scores = [d.get("complexity_score", 0) for d in databases]
            colors = ["#ef4444" if s >= 70 else "#fbbf24" if s >= 40 else "#10b981" for s in scores]
            
            fig = go.Figure(data=[go.Bar(
                x=db_names, y=scores, marker_color=colors,
                text=[f"{s}" for s in scores], textposition="outside",
                textfont=dict(color="#e2e8f0", size=10),
                hovertemplate="%{x}<br>Complexity: %{y}/100<extra></extra>"
            )])
            fig.update_layout(
                title=dict(text="Migration Complexity Score (0-100)", font=dict(color="#e2e8f0", size=13)),
                yaxis_range=[0, 110], paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"), height=320, margin=dict(l=40, r=20, t=40, b=60),
                yaxis=dict(gridcolor="rgba(100,116,139,0.1)"),
                xaxis=dict(tickangle=-30),
            )
            fig.add_hline(y=70, line_dash="dash", line_color="#ef4444",
                          annotation_text="High Complexity", annotation_font_color="#ef4444")
            fig.add_hline(y=40, line_dash="dash", line_color="#fbbf24",
                          annotation_text="Medium", annotation_font_color="#fbbf24")
            st.plotly_chart(fig, use_container_width=True)
        
        with ch2:
            # Effort estimation pie
            effort_by_engine = {}
            for d in databases:
                eng = d.get("engine", "other").upper()
                effort_by_engine[eng] = effort_by_engine.get(eng, 0) + d.get("estimated_effort_weeks", 0)
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=list(effort_by_engine.keys()),
                values=list(effort_by_engine.values()),
                hole=0.5,
                marker_colors=["#ef4444", "#10b981", "#3b82f6", "#fbbf24"],
                textinfo="label+value",
                textfont=dict(color="#e2e8f0", size=11),
                hovertemplate="%{label}: %{value} weeks<extra></extra>"
            )])
            fig_pie.update_layout(
                title=dict(text="Effort by Engine (Weeks)", font=dict(color="#e2e8f0", size=13)),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"), height=320, margin=dict(l=20, r=20, t=40, b=20),
                showlegend=False,
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Individual database cards
        for db in databases:
            engine_icon = "🟠" if db["engine"] == "oracle" else "🐬" if db["engine"] == "mysql" else "🗄️"
            level = db.get("complexity_level", "LOW")
            level_color = "#ef4444" if level == "HIGH" else "#fbbf24" if level == "MEDIUM" else "#10b981"
            
            with st.expander(
                f"{engine_icon} {db.get('db_name', db['db_id'])} — "
                f"{db['engine'].upper()} {db['edition']} | "
                f"Complexity: {db['complexity_score']}/100 | "
                f"~{db['estimated_effort_weeks']} weeks"
            ):
                # Details row
                d1, d2, d3 = st.columns(3)
                with d1:
                    st.markdown(f"""
                    **Database Details:**
                    - Engine: `{db['engine'].upper()} {db['edition']} {db.get('version', '')}`
                    - Size: `{db['size_gb']:.0f} GB` | Tables: `{db['table_count']}`
                    - Connections: `{db['connection_count']}`
                    - RTO: `{db['rto_hours']}h` | RPO: `{db['rpo_hours']}h`
                    """)
                with d2:
                    st.markdown(f"""
                    **Complexity Factors:**
                    - Stored Procs: `{'✅ Yes' if db['has_stored_procedures'] else '❌ No'}`
                    - Linked Servers: `{'✅ Yes' if db['has_linked_servers'] else '❌ No'}`
                    - Custom Ext: `{'✅ Yes' if db['has_custom_extensions'] else '❌ No'}`
                    """)
                    st.markdown(f"**Score:** <span style='color:{level_color}; font-weight:700;'>{db['complexity_score']}/100 ({level})</span>", unsafe_allow_html=True)
                with d3:
                    st.markdown(f"""
                    **Estimation:**
                    - Effort: **~{db['estimated_effort_weeks']} person-weeks**
                    - Environment: `{db.get('environment', 'N/A')}`
                    - Server: `{db.get('server_name', 'N/A')}`
                    """)
                
                # Complexity factors breakdown
                if db.get("complexity_factors"):
                    st.caption("Complexity breakdown: " + " | ".join(db["complexity_factors"]))
                
                # Migration paths
                st.markdown("**Recommended Migration Paths:**")
                for idx, path in enumerate(db.get("migration_paths", [])):
                    badge = "RECOMMENDED" if idx == 0 else f"Option {idx + 1}"
                    badge_bg = "rgba(16,185,129,0.15)" if idx == 0 else "rgba(59,130,246,0.1)"
                    badge_color = "#10b981" if idx == 0 else "#3b82f6"
                    
                    st.markdown(f"""
                    <div style="background: rgba(30,30,47,0.4); border: 1px solid rgba(99,102,241,0.15); 
                         border-radius: 8px; padding: 10px 14px; margin-bottom: 6px;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span>{path.get('icon', '📦')}</span>
                            <strong style="color: #e2e8f0;">{path['target']}</strong>
                            <span style="background: {badge_bg}; color: {badge_color}; font-size: 0.65rem; 
                                  padding: 2px 6px; border-radius: 3px; font-weight: 600;">{badge}</span>
                            <span style="color: #94a3b8; font-size: 0.75rem; margin-left: auto;">
                                Effort: {path.get('effort', 'Medium')}
                            </span>
                        </div>
                        <div style="color: #cbd5e1; font-size: 0.82rem; margin: 4px 0 4px 28px;">
                            {path['description']}
                        </div>
                        <div style="margin-left: 28px; font-size: 0.75rem;">
                            <span style="color: #10b981;">✓ {' ✓ '.join(path.get('pros', []))}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    # ── Application Modernization ──
    if applications:
        st.write("---")
        st.markdown("### 🚀 Application Modernization Paths")
        
        for app in applications:
            crit = app.get("business_criticality", 0)
            crit_color = "#ef4444" if crit >= 4 else "#fbbf24" if crit >= 3 else "#10b981"
            rec = app.get("recommended_path", {})
            
            with st.expander(
                f"📱 {app.get('name', app['app_id'])} — "
                f"{app['language']} / {app.get('framework', 'N/A')} | "
                f"→ {rec.get('target', 'TBD')}"
            ):
                a1, a2 = st.columns(2)
                with a1:
                    st.markdown(f"""
                    **Application Details:**
                    - Language: `{app['language']}` | Framework: `{app.get('framework', 'N/A')}`
                    - Tech Stack: `{', '.join(app.get('tech_stack', [])) or 'N/A'}`
                    - Tier: `{app.get('tier', 'N/A')}` | Users: `{app['user_count']:,}`
                    - Revenue Impact: `${app['annual_revenue_impact']:,.0f}/yr`
                    """)
                with a2:
                    st.markdown(f"""
                    **Migration Info:**
                    - Criticality: <span style="color:{crit_color}; font-weight:700;">{crit}/5</span>
                    - Owner: `{app.get('owner', 'N/A')}`
                    - Estimated Effort: **~{app['estimated_effort_weeks']} weeks**
                    """, unsafe_allow_html=True)
                
                st.markdown("**Modernization Options:**")
                for idx, path in enumerate(app.get("modernization_paths", [])):
                    fit_color = "#10b981" if path.get("fit") == "Best" else "#3b82f6" if path.get("fit") == "Good" else "#94a3b8"
                    st.markdown(f"""
                    <div style="background: rgba(30,30,47,0.3); border-left: 3px solid {fit_color};
                         border-radius: 0 6px 6px 0; padding: 8px 12px; margin-bottom: 4px;">
                        <strong style="color: #e2e8f0;">{path['target']}</strong>
                        <span style="color: {fit_color}; font-size: 0.75rem; margin-left: 8px;">
                            [{path.get('fit', 'Good')}] Effort: {path.get('effort', 'Medium')}
                        </span>
                        <div style="color: #94a3b8; font-size: 0.8rem;">{path['description']}</div>
                    </div>
                    """, unsafe_allow_html=True)


if __name__ == "__main__":
    render()
