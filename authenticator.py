import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import smtplib
from email.mime.text import MIMEText

def send_login_alert(username, name):
    sender_email = st.secrets["SMTP_USER"]
    receiver_email = st.secrets["ALERT_RECEIVER"]
    password = st.secrets["SMTP_PASSWORD"]
    
    msg = MIMEText(f"Hello, user {name} ({username}) has successfully logged into v-mart.streamlit.app.")
    msg['Subject'] = '⚠️ V-Mart Login Alert'
    msg['From'] = sender_email
    msg['To'] = receiver_email
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
    except Exception as e:
        st.error(f"Failed to send email alert: {e}")

def check_password():
    """Manages the registration and login flows. Returns True if authenticated."""
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

    # Add a visual selection toggle at the top of the authentication screen
    auth_mode = st.radio("Choose Option", ["Login", "Sign Up"], horizontal=True)

    if auth_mode == "Sign Up":
        try:
            # Renders a complete new user signup widget
            # Set pre_authorized=None to allow absolutely anyone to register
            email, username, name = authenticator.register_user(location='main', pre_authorized=None)
            if username:
                # CRITICAL: Save the newly created user credentials back into your config.yaml
                with open('config.yaml', 'w') as file:
                    yaml.dump(config, file, default_flow_style=False)
                st.success('Registration successful! You can now switch to Login mode.')
        except Exception as e:
            st.error(f"Registration Error: {e}")
        return False

    elif auth_mode == "Login":
        login_result = authenticator.login(location='main')
        
        if isinstance(login_result, tuple):
            name, authentication_status, username = login_result
        else:
            authentication_status = st.session_state.get('authentication_status')
            name = st.session_state.get('name')
            username = st.session_state.get('username')

        if authentication_status:
            if 'logged_in_alert_sent' not in st.session_state:
                send_login_alert(username, name)
                st.session_state['logged_in_alert_sent'] = True
                
            authenticator.logout('Logout', 'sidebar')
            return True
        elif authentication_status is False:
            st.error('Username/password is incorrect')
            return False
        else:
            st.warning('Please enter your username and password')
            return False
