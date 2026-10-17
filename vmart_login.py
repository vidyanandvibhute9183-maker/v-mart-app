
import streamlit as st
import requests
from supabase import create_client


def get_supabase():
    """Create the base Supabase client for authentication."""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def get_user_supabase():
    """Create a Supabase client using the signed-in user's access token."""
    token = st.session_state.get("access_token")
    user_id = st.session_state.get("user_id")

    if not token or not user_id:
        return None

    client = get_supabase()
    client.postgrest.auth(token)
    return client


def send_discord_alert(email, action):
    """Send a Discord notification without interrupting the app."""
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
        except Exception as e:
    st.error("Supabase sign-up error:")
    st.code(f"{type(e).__name__}: {e}") 

def clear_login_session():
    """Clear the local Streamlit login session."""
    for key in (
        "user_id",
        "user_email",
        "access_token",
        "refresh_token",
    ):
        st.session_state.pop(key, None)


def check_password():
    """Display authentication screens and maintain the login session."""

    # Handle an existing login first.
    if st.session_state.get("user_id") and st.session_state.get("access_token"):
        st.sidebar.write(
            f"Signed in: {st.session_state.get('user_email', '')}"
        )

        if st.sidebar.button("Logout"):
            clear_login_session()
            st.rerun()

        return True

    # Clear an incomplete or expired local session.
    if st.session_state.get("user_id") or st.session_state.get("access_token"):
        clear_login_session()

    try:
        supabase = get_supabase()
    except Exception:
        st.error(
            "Could not initialize Supabase. "
            "Check SUPABASE_URL and SUPABASE_KEY in Streamlit secrets."
        )
        return False

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
            email = email.strip()

            if not email or not password:
                st.error("Enter your email and password.")
            elif password != confirm:
                st.error("Passwords do not match.")
            else:
                try:
                    result = supabase.auth.sign_up({
                        "email": email,
                        "password": password,
                    })

                    if result.user:
                        send_discord_alert(
                            email, "created a new account"
                        )
                        st.success(
                            "Account created. Check your email for "
                            "a confirmation link if required."
                        )
                    else:
                        st.info(
                            "Check your email for the next steps."
                        )

except Exception as e:
    st.error("Supabase sign-up error:")
    st.code(f"{type(e).__name__}: {e}")"
                    

    elif mode == "Login":
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

        if submitted:
            email = email.strip()

            try:
                result = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password,
                })

                if result.user and result.session:
                    st.session_state["user_id"] = result.user.id
                    st.session_state["user_email"] = result.user.email
                    st.session_state["access_token"] = (
                        result.session.access_token
                    )
                    st.session_state["refresh_token"] = (
                        result.session.refresh_token
                    )

                    send_discord_alert(email, "logged in")
                    st.rerun()
                else:
                    st.error("Login failed. Please try again.")

            except Exception:
            except Exception as e:
    st.error("Supabase login error:")
    st.code(f"{type(e).__name__}: {e}")

    else:
        with st.form("forgot_form"):
            email = st.text_input("Account email")
            submitted = st.form_submit_button("Send Reset Link")

        if submitted:
            try:
                supabase.auth.reset_password_for_email(email.strip())
            except Exception:
                # Avoid exposing account existence or internal errors.
                pass

            st.success(
                "If the account exists, a password reset email "
                "will be sent."
            )

    return False
