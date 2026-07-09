# ui/pages/code_migration.py
import streamlit as st
import os
from google.genai import Client
from google.genai import types

def render():
    st.markdown("<h1 class='gradient-text'>AI Code Refactoring Engine</h1>", unsafe_allow_html=True)
    st.write("Beyond infrastructure lift-and-shift, use Gemini to automatically modernize legacy applications. Convert monolithic codebases into cloud-native microservices, modernize outdated frameworks, and auto-generate unit tests.")
    st.write("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Source Code (Legacy)")
        source_language = st.selectbox("Legacy Framework", [
            "Java 8 (Monolith / Spring)",
            "PL/SQL (Oracle / SQL Server)",
            ".NET Framework 4.x (C#)",
            "Python 2.7 (Django)",
            "PHP (Legacy LAMP)"
        ])
        
        default_code = ""
        if "Java" in source_language:
            default_code = """// Legacy Java 8 Monolithic Service
public class OrderService {
    private DatabaseConnection db;
    
    public OrderService() {
        this.db = new DatabaseConnection("jdbc:oracle:thin:@prod-db:1521:ORCL");
    }
    
    public String processOrder(String orderId) {
        try {
            db.connect();
            String sql = "SELECT * FROM ORDERS WHERE ID = " + orderId;
            ResultSet rs = db.executeQuery(sql);
            if (rs.next()) {
                // Process payment synchronously
                PaymentGateway pg = new PaymentGateway();
                pg.charge(rs.getDouble("amount"));
                
                // Update inventory
                String update = "UPDATE INVENTORY SET qty = qty - 1 WHERE ID = " + rs.getString("item_id");
                db.executeUpdate(update);
                
                return "Order Processed";
            }
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            db.disconnect();
        }
        return "Failed";
    }
}"""
        elif "PL/SQL" in source_language:
            default_code = """-- Legacy Oracle Stored Procedure
CREATE OR REPLACE PROCEDURE calculate_monthly_revenue (
    p_month IN VARCHAR2,
    p_year IN NUMBER,
    p_total_revenue OUT NUMBER
) AS
    CURSOR c_orders IS 
        SELECT amount FROM orders WHERE TO_CHAR(order_date, 'MM') = p_month AND EXTRACT(YEAR FROM order_date) = p_year;
    v_amount NUMBER;
BEGIN
    p_total_revenue := 0;
    OPEN c_orders;
    LOOP
        FETCH c_orders INTO v_amount;
        EXIT WHEN c_orders%NOTFOUND;
        p_total_revenue := p_total_revenue + v_amount;
    END LOOP;
    CLOSE c_orders;
    
    -- Insert audit log
    INSERT INTO audit_log (action_name, action_date) VALUES ('Revenue Calc', SYSDATE);
    COMMIT;
END calculate_monthly_revenue;
"""

        source_code = st.text_area("Paste legacy code snippet here:", value=default_code, height=400)
        
    with col2:
        st.subheader("Target Architecture (Cloud-Native)")
        target_language = st.selectbox("Target Modern Framework", [
            "Go (Microservice / Cloud Run)",
            "Python (Cloud Functions / FastAPI)",
            "Java 21 (Spring Boot 3 / Reactive)",
            "BigQuery SQL (Standard SQL)"
        ])
        
        generate_tests = st.checkbox("Include Unit Tests in output", value=True)
        explain_code = st.checkbox("Provide explanation of changes", value=True)
        
        if st.button("🚀 Refactor to Cloud-Native", type="primary", use_container_width=True):
            if not source_code.strip():
                st.error("Please paste source code.")
            else:
                with st.spinner("Gemini is analyzing and refactoring code..."):
                    api_key = os.getenv("GEMINI_API_KEY")
                    if api_key:
                        genai_client = Client(api_key=api_key)
                        model_name = "gemini-2.5-pro"
                    else:
                        genai_client = Client(enterprise=True)
                        model_name = f"projects/{os.getenv('VERTEX_PROJECT_ID', 'gcp-experiments-490315')}/locations/{os.getenv('VERTEX_AI_LOCATION', 'us-central1')}/publishers/google/models/gemini-2.5-pro"
                        
                    prompt = f"""
                    You are a Staff-level Cloud Migration Architect. Refactor the following legacy {source_language} code into modern, cloud-native {target_language}.
                    
                    Guidelines:
                    - Decouple monolithic components.
                    - Fix obvious security vulnerabilities (like SQL injection).
                    - Use modern async/reactive patterns if applicable.
                    - If targeting BigQuery, convert legacy procedural cursors into set-based analytical SQL.
                    - {'Include standard unit tests using the standard testing library for the target language.' if generate_tests else 'Do NOT include unit tests.'}
                    - {'Provide a brief markdown explanation of the architectural improvements.' if explain_code else 'Output ONLY the code.'}
                    
                    Legacy Code:
                    ```
                    {source_code}
                    ```
                    """
                    
                    try:
                        response = genai_client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                            config=types.GenerateContentConfig(temperature=0.2)
                        )
                        st.session_state["refactored_code"] = response.text
                    except Exception as e:
                        st.error(f"API Error: {e}")
                        
        if "refactored_code" in st.session_state:
            st.markdown("### Refactored Output")
            st.markdown(st.session_state["refactored_code"])

if __name__ == "__main__":
    render()
