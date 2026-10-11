import streamlit as st
from supabase import create_client, Client

# Hardcoding the public endpoints directly to avoid cached panel errors
@st.cache_resource
def get_supabase_client() -> Client:
    url = "https://supabase.co"
    key = "sb_publishable_ro3Lwte8OjXAgO5lMU3d_g_OGHg1"
    return create_client(url, key)

def check_password():
    """Manages the full login, signup, and email verification workflows via Supabase."""
    supabase = get_supabase_client()
    
    auth_mode = st.radio("Choose Option", ["Login", "Sign Up", "Forgot Password"], horizontal=True)

    # 1. SIGN UP FLOW
    if auth_mode == "Sign Up":
        with st.form("signup_form"):
            email = st.text_input("Email Address")
            password = st.text_input("Choose Password", type="password")
            submitted = st.form_submit_button("Create Account")
            
            if submitted:
                try:
                    # Automatically sends a confirmation email to the user
                    supabase.auth.sign_up({"email": email, "password": password})
                    st.success("Account created! Please check your email inbox to verify your address.")
                except Exception as e:
                    st.error(f"Sign Up Failed: {e}")
        return False

    # 2. FORGOT PASSWORD FLOW
    elif auth_mode == "Forgot Password":
        if "reset_email_sent" not in st.session_state:
            with st.form("forgot_form"):
                email = st.text_input("Enter your registered email address")
                submitted = st.form_submit_button("Send Reset Email")
                
                if submitted:
                    try:
                        # Triggers an automated password reset email immediately
                        supabase.auth.reset_password_for_email(email)
                        st.session_state["reset_email_sent"] = email
                        st.success("A secure code has been sent to your email address!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
        else:
            with st.form("verify_reset_form"):
                st.info(f"Verification sent to {st.session_state['reset_email_sent']}")
                token = st.text_input("Enter the 6-digit code from your email")
                new_password = st.text_input("Enter New Password", type="password")
                submitted = st.form_submit_button("Update Password")
                
                if submitted:
                    try:
                        # Verifies the user's secure token code
                        supabase.auth.verify_otp({
                            "email": st.session_state["reset_email_sent"],
                            "token": token,
                            "type": "recovery"
                        })
                        # Updates the password permanently in the database
                        supabase.auth.update_user({"password": new_password})
                        st.success("Password changed successfully! You can now switch to Login.")
                        del st.session_state["reset_email_sent"]
                    except Exception as e:
                        st.error(f"Verification Failed: {e}")
        return False

    # 3. LOGIN FLOW
    elif auth_mode == "Login":
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if res.user:
                        st.session_state["user_authenticated"] = True
                        st.rerun()
                except Exception as e:
                    st.error("Invalid email or password.")
                    
        if st.session_state.get("user_authenticated"):
            if st.sidebar.button("Logout"):
                supabase.auth.sign_out()
                st.session_state["user_authenticated"] = False
                st.rerun()
            return True
        return False
