import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import requests

def send_discord_alert(username, name, action="logged into"):
    """Sends a clean message log to your Discord server channel."""
    webhook_url = st.secrets["DISCORD_WEBHOOK_URL"]
    
    payload = {
        "content": f"🔔 **V-Mart Security Notification**\nUser **{name}** (`{username}`) has successfully {action} **v-mart.streamlit.app**."
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code != 204 and response.status_code != 200:
            st.error(f"Webhook tracking error: {response.text}")
    except Exception as e:
        st.error(f"Could not connect to live alerts: {e}")

def check_password():
    """Manages the registration, login, and temporary password reset workflows."""
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

    auth_mode = st.radio("Choose Option", ["Login", "Sign Up", "Forgot Password"], horizontal=True)

    if auth_mode == "Sign Up":
        try:
            # FIXED: Added captcha=False to completely disable the broken captcha entry check
            email, username, name = authenticator.register_user(location='main', pre_authorized=None, captcha=False)
            if username:
                with open('config.yaml', 'w') as file:
                    yaml.dump(config, file, default_flow_style=False)
                
                send_discord_alert(username, name, action="created a new account on")
                st.success('Registration successful! Switch to Login mode to access your panel.')
        except Exception as e:
            st.error(f"Registration Error: {e}")
        return False

    elif auth_mode == "Forgot Password":
        try:
            username, email, new_password = authenticator.forgot_password(location='main')
            if username:
                with open('config.yaml', 'w') as file:
                    yaml.dump(config, file, default_flow_style=False)
                
                send_discord_alert(username, username, action="generated a temporary password reset on")
                st.success('Password updated successfully!')
                st.info(f"🔑 Your temporary login code is: **{new_password}**")
                st.caption("Copy this key, return to 'Login' mode, and use it to log back in.")
            elif username is False:
                st.error('Username not found')
        except Exception as e:
            st.error(f"Reset Error: {e}")
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
                send_discord_alert(username, name, action="logged into")
                st.session_state['logged_in_alert_sent'] = True
                
            authenticator.logout('Logout', 'sidebar')
            return True
        elif authentication_status is False:
            st.error('Username or password incorrect.')
            return False
        else:
            st.warning('Please input your credentials.')
            return False
