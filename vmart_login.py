
import streamlit as st
import requests
from supabase import create_client



def get_user_supabase():
    """Create a Supabase client authenticated as the current user."""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    token = st.session_state.get("access_token")

    if not token or not st.session_state.get("user_id"):
        return None

    client = create_client(url, key)
    client.postgrest.auth(token)
    return client



def send_discord_alert(email, action):
    try:
        webhook = st.secrets.get("DISCORD_WEBHOOK_URL")
        if not webhook:
            return

        response = requests.post(
            webhook,
            json={
                "content": (
                    "🔔 **V-Mart Security Notification**\n"
                    f"Account: `{email}`\n"
                    f"Action: **{action}**"
                )
            },
            timeout=10,
        )
        response.raise_for_status()
    except Exception:
        # A notification failure should not stop login or registration.
        pass


def check_password():
    if st.session_state.get("user_id"):
        return True

    supabase = get_supabase()
    mode = st.radio(
        "Choose Option",
        ["Login", "Sign Up", "Forgot Password"],
        horizontal=True,
    )

    if mode == "Sign Up":
        with st.form("signup_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create Account")

        if submitted:
            if not email or not password:
                st.error("Enter your email and password.")
            elif password != confirm:
                st.error("Passwords do not match.")
            else:
                try:
                    result = supabase.auth.sign_up({
                        "email": email.strip(),
                        "password": password,
                    })
                    user = result.user
                    if user:
                        send_discord_alert(email.strip(), "created a new account")
                        st.success(
                            "Account created. Check your email for a "
                            "confirmation link if email confirmation is enabled."
                        )
                    else:
                        st.info("Check your email for the next steps.")
                except Exception:
                    st.error(
                        "Sign-up failed. Check the email, password requirements, "
                        "and Supabase Auth settings."
                    )

    elif mode == "Login":
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

        if submitted:
            try:
                result = supabase.auth.sign_in_with_password({
                    "email": email.strip(),
                    "password": password,
                })
                if result.user and result.session:
                    st.session_state["user_id"] = result.user.id
                    st.session_state["user_email"] = result.user.email
                    st.session_state["access_token"] = result.session.access_token
                    st.session_state["refresh_token"] = result.session.refresh_token
                    send_discord_alert(email.strip(), "logged in")
                    st.rerun()
            except Exception:
                st.error("Login failed. Check your email, password, or email confirmation.")

    else:
        with st.form("forgot_form"):
            email = st.text_input("Account email")
            submitted = st.form_submit_button("Send Reset Link")

        if submitted:
            try:
                supabase.auth.reset_password_for_email(email.strip())
                send_discord_alert(email.strip(), "requested a password reset")
                st.success("If the account exists, a password reset email will be sent.")
            except Exception:
                st.success("If the account exists, a password reset email will be sent.")

    if st.session_state.get("user_id"):
        st.sidebar.write(
            f"Signed in: {st.session_state.get('user_email', '')}"
        )
        if st.sidebar.button("Logout"):
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
            for key in [
                "user_id",
                "user_email",
                "access_token",
                "refresh_token",
            ]:
                st.session_state.pop(key, None)
            st.rerun()
        return True

    return False
