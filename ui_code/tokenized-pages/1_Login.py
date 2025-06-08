import streamlit as st
from streamlit_lottie import st_lottie
import json
import boto3
import logging
from PIL import Image

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(page_title="Login", layout="wide")

# Apply custom CSS styling
st.markdown("""
    <style>
    body {
        background-color: #f0f2f6;
    }

    .center-content {
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
    }

    .stTextInput>div>div>input {
        border-radius: 10px;
        padding: 10px;
        border: 1px solid #d3d3d3;
    }

    .stPasswordInput>div>div>input {
        border-radius: 10px;
        padding: 10px;
        border: 1px solid #d3d3d3;
    }

    .stButton>button {
        background-color: #4CAF50;
        color: white;
        padding: 10px 20px;
        margin: 10px 0px;
        border: none;
        border-radius: 10px;
        cursor: pointer;
        font-size: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: background-color 0.3s ease;
    }

    .stButton>button:hover {
        background-color: #45a049;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 16px;
        padding: 8px 16px;
    }

    .stImage img {
        border-radius: 50%;
    }
    </style>
""", unsafe_allow_html=True)

# Load Lottie animation from local file
def load_lottie_file(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)

# Load animation and logo
lottie_animation = load_lottie_file("ui_code/assets/Animation - 1749331073505.json")
logo = Image.open("ui_code/assets/Workmates-Pic.png")

# Display logo
st.markdown("<div class='center-content'>", unsafe_allow_html=True)
st.image(logo, width=150)
st.markdown("</div>", unsafe_allow_html=True)

# Display animation
st.markdown("<div class='center-content'>", unsafe_allow_html=True)
st_lottie(lottie_animation, height=250, key="welcome")
st.markdown("</div>", unsafe_allow_html=True)

# Cognito config
COGNITO_USER_POOL_ID = st.secrets.get("COGNITO_USER_POOL_ID")
COGNITO_APP_CLIENT_ID = st.secrets.get("COGNITO_APP_CLIENT_ID")
COGNITO_REGION = st.secrets.get("COGNITO_REGION")

if not COGNITO_USER_POOL_ID or not COGNITO_APP_CLIENT_ID or not COGNITO_REGION:
    st.error("Cognito configuration is missing.")
    st.stop()

# Authentication function
def authenticate(username, password):
    client = boto3.client('cognito-idp', region_name=COGNITO_REGION)
    try:
        resp = client.initiate_auth(
            ClientId=COGNITO_APP_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={'USERNAME': username, 'PASSWORD': password}
        )
        return True, username
    except client.exceptions.NotAuthorizedException:
        return False, None
    except client.exceptions.UserNotFoundException:
        return False, None
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return False, None

# Login page content
st.title('Login')

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if st.session_state['authenticated']:
    st.success(f"Welcome back, {st.session_state['username']}!")
    if st.button('Logout'):
        st.session_state['authenticated'] = False
        st.session_state.pop('username', None)
        st.rerun()
else:
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        login_button = st.button("Login")

        if login_button:
            if username and password:
                success, name = authenticate(username, password)
                if success:
                    st.session_state['authenticated'] = True
                    st.session_state['username'] = name
                    st.rerun()
                else:
                    st.warning("Invalid username or password.")
            else:
                st.warning("Please enter both username and password.")

    with tab2:
        st.info("Please contact your Admin to get registered.")

# Navigation options
if st.session_state['authenticated']:
    st.write("Please select where you'd like to go:")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button('  New WAFR Review    '):
            st.switch_page("pages/1_New_WAFR_Review.py")
    with col2:
        if st.button('  Existing WAFR Reviews    '):
            st.switch_page("pages/2_Existing_WAFR_Reviews.py")
    with col3:
        if st.button('  System Architecture    '):
            st.switch_page("pages/3_System_Architecture.py")
