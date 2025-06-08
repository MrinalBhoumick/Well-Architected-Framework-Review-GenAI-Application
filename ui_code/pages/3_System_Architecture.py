import streamlit as st
from PIL import Image

# ---------------- Session Check -------------------
if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.warning('You are not logged in. Please log in to access this page.')
    st.switch_page("pages/1_Login.py")

# ---------------- CSS Styling -------------------
st.markdown("""
    <style>
        /* General body styling */
        body {
            font-family: 'Segoe UI', sans-serif;
        }

        /* Center the logo */
        .logo-container {
            display: flex;
            justify-content: center;
            margin-bottom: 1rem;
        }

        /* Card container */
        .card {
            background-color: #ffffff;
            padding: 2rem;
            border-radius: 1rem;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }

        /* Tailwind-style title */
        .title {
            font-size: 2.5rem;
            font-weight: 700;
            color: #111827;
            text-align: center;
            margin-bottom: 1.5rem;
        }

        .header {
            font-size: 1.75rem;
            font-weight: 600;
            color: #1f2937;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
        }

        .text {
            font-size: 1rem;
            line-height: 1.6;
            color: #374151;
        }

        /* Logout button */
        .logout-button {
            background-color: #ef4444;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            font-size: 1rem;
            border-radius: 0.5rem;
            cursor: pointer;
            margin-top: 2rem;
        }

        .logout-button:hover {
            background-color: #dc2626;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------- Logo -------------------
logo = Image.open("ui_code/assets/Workmates-Pic.png")
st.markdown("<div class='logo-container'>", unsafe_allow_html=True)
st.image(logo, width=150)
st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Architecture Section -------------------
def architecture():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='title'>Architecture</div>", unsafe_allow_html=True)

    st.markdown("<div class='header'>AWS Well-Architected Acceleration with Generative AI Architecture</div>", unsafe_allow_html=True)
    st.image("sys-arch.png", use_container_width=True)

    st.markdown("<div class='header'>Components</div>", unsafe_allow_html=True)
    st.markdown("""
        <div class='text'>
        <ul>
            <li><strong>Frontend:</strong> Streamlit UI for user-friendly review interaction.</li>
            <li><strong>Backend:</strong> Python-based logic integrating AWS services.</li>
            <li><strong>Database:</strong> DynamoDB + OpenSearch serverless for Bedrock knowledge base.</li>
            <li><strong>Integration Services:</strong> AWS WAF Tool API, Bedrock, DynamoDB.</li>
            <li><strong>Security:</strong> Amazon Cognito for user management and access control.</li>
        </ul>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    architecture()

# ---------------- Logout Function -------------------
def logout():
    st.session_state['authenticated'] = False
    st.session_state.pop('username', None)
    st.rerun()

# ---------------- Logout Button -------------------
st.sidebar.markdown(
    '<button class="logout-button" onclick="window.location.reload();">Logout</button>',
    unsafe_allow_html=True
)
if st.sidebar.button("Logout"):
    logout()
