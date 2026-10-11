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
        with smtplib.SMTP_SSL('://gmail.com', 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
    except Exception as e:
        st.error(f"Failed to send email alert: {e}")

def check_password():
    """Returns True if the user is authenticated, otherwise False."""
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

    name, authentication_status, username = authenticator.login('main')

    if authentication_status:
        if 'logged_in_alert_sent' not in st.session_state:
            send_login_alert(username, name)
            st.session_state['logged_in_alert_sent'] = True
            
        authenticator.logout('Logout', 'sidebar')
        return True
    elif authentication_status is False:
        st.error('Username/password is incorrect')
        return False
    elif authentication_status is None:
        st.warning('Please enter your username and password')
        return False
