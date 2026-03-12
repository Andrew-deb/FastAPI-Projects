import streamlit as st
import requests
import base64
import urllib.parse
from datetime import datetime

st.set_page_config(page_title="Simple Social", layout="wide")

# Initialize session state
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user' not in st.session_state:
    st.session_state.user = None
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False


def apply_theme_styles():
    """Apply app-level theme styles based on dark_mode session state."""
    if st.session_state.dark_mode:
        st.markdown(
            """
            <style>
                :root {
                    --app-bg: #0f1116;
                    --panel-bg: #171a22;
                    --text-main: #f3f4f6;
                    --text-muted: #9ca3af;
                    --border: #2a2f3a;
                    --accent: #38bdf8;
                }

                .stApp {
                    background-color: var(--app-bg);
                    color: var(--text-main);
                }

                .profile-card {
                    background: var(--panel-bg);
                    border: 1px solid var(--border);
                    border-radius: 12px;
                    padding: 16px;
                    margin-bottom: 12px;
                }

                .profile-muted {
                    color: var(--text-muted);
                    margin: 2px 0;
                }

                .profile-headline {
                    color: var(--text-main);
                    margin: 0 0 8px 0;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
                :root {
                    --app-bg: #f8fafc;
                    --panel-bg: #ffffff;
                    --text-main: #0f172a;
                    --text-muted: #475569;
                    --border: #dbe2ea;
                    --accent: #0ea5e9;
                }

                .stApp {
                    background-color: var(--app-bg);
                    color: var(--text-main);
                }

                .profile-card {
                    background: var(--panel-bg);
                    border: 1px solid var(--border);
                    border-radius: 12px;
                    padding: 16px;
                    margin-bottom: 12px;
                }

                .profile-muted {
                    color: var(--text-muted);
                    margin: 2px 0;
                }

                .profile-headline {
                    color: var(--text-main);
                    margin: 0 0 8px 0;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )


def get_headers():
    """Get authorization headers with token"""
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}


def format_datetime(value):
    """Safely format ISO datetime-like strings from the API."""
    if not value:
        return "N/A"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError, AttributeError):
        return str(value)


def login_page():
    st.title("🚀 Welcome to Simple Social")

    # Simple form with two buttons
    username = st.text_input("Username: ")
    email = st.text_input("Email:")
    password = st.text_input("Password:", type="password")

    if email and password:
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Login", type="primary", use_container_width=True):
                # Login using FastAPI Users JWT endpoint
                login_data = {"username": email, "password": password}
                response = requests.post("http://localhost:8000/api/auth/jwt/login", data=login_data)

                if response.status_code == 200:
                    token_data = response.json()
                    st.session_state.token = token_data["access_token"]

                    # Get user info
                    user_response = requests.get("http://localhost:8000/users/me", headers=get_headers())
                    if user_response.status_code == 200:
                        st.session_state.user = user_response.json()
                        st.rerun()
                    else:
                        st.error("Failed to get user info")
                else:
                    st.error("Invalid email or password!")

        with col2:
            if st.button("Sign Up", type="secondary", use_container_width=True):
                # Register using FastAPI Users
                signup_data = {"email": email, "password": password, "username": username}
                response = requests.post("http://localhost:8000/api/auth/register", json=signup_data)

                if response.status_code == 201:
                    st.success("Account created! Click Login now.")
                else:
                    error_detail = response.json().get("detail", "Registration failed")
                    st.error(f"Registration failed: {error_detail}")
    else:
        st.info("Enter your email and password above")


def upload_page():
    st.title("📸 Share Something")

    uploaded_file = st.file_uploader("Choose media", type=['png', 'jpg', 'jpeg', 'mp4', 'avi', 'mov', 'mkv', 'webm'])
    caption = st.text_area("Caption:", placeholder="What's on your mind?")

    if uploaded_file and st.button("Share", type="primary"):
        with st.spinner("Uploading..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            data = {"caption": caption}
            response = requests.post("http://localhost:8000/posts/upload", files=files, data=data, headers=get_headers())

            if response.status_code == 200:
                st.success("Posted!")
                st.rerun()
            else:
                st.error("Upload failed!")


def encode_text_for_overlay(text):
    """Encode text for ImageKit overlay - base64 then URL encode"""
    if not text:
        return ""
    # Base64 encode the text
    base64_text = base64.b64encode(text.encode('utf-8')).decode('utf-8')
    # URL encode the result
    return urllib.parse.quote(base64_text)


def create_transformed_url(original_url, transformation_params, caption=None):
    if caption:
        encoded_caption = encode_text_for_overlay(caption)
        # Add text overlay at bottom with semi-transparent background
        text_overlay = f"l-text,ie-{encoded_caption},ly-N20,lx-20,fs-100,co-white,bg-000000A0,l-end"
        transformation_params = text_overlay

    if not transformation_params:
        return original_url

    parts = original_url.split("/")

    imagekit_id = parts[3]
    file_path = "/".join(parts[4:])
    base_url = "/".join(parts[:4])
    return f"{base_url}/tr:{transformation_params}/{file_path}"


def feed_page():
    st.title("🏠 Feed")

    response = requests.get("http://localhost:8000/posts/feed", headers=get_headers())
    if response.status_code == 200:
        posts = response.json()["posts"]

        if not posts:
            st.info("No posts yet! Be the first to share something.")
            return

        for post in posts:
            st.markdown("---")

            # Header with user, date, and delete button (if owner)
            col1, col2 = st.columns([4, 1])
            with col1:
                author = post.get('username') or post.get('email') or 'Unknown user'
                created_at = str(post.get('created_at', ''))[:10] if post.get('created_at') else 'N/A'
                st.markdown(f"**{author}** • {created_at}")
            with col2:
                if post.get('is_owner', False):
                    if st.button("🗑️", key=f"delete_{post['id']}", help="Delete post"):
                        # Delete the post
                        response = requests.delete(f"http://localhost:8000/posts/{post['id']}", headers=get_headers())
                        if response.status_code == 200:
                            st.success("Post deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete post!")

            # Uniform media display with caption overlay
            caption = post.get('caption', '')
            if post['file_type'] == 'image':
                uniform_url = create_transformed_url(post['url'], "", caption)
                st.image(uniform_url, width=300)
            else:
                # For videos: specify only height to maintain aspect ratio + caption overlay
                uniform_video_url = create_transformed_url(post['url'], "w-400,h-200,cm-pad_resize,bg-blurred")
                st.video(uniform_video_url, width=300)
                st.caption(caption)

            st.markdown("")  # Space between posts
    else:
        st.error("Failed to load feed")


def profile_page():
    st.title("🙍 Profile")

    response = requests.get("http://localhost:8000/users/profile", headers=get_headers())
    if response.status_code != 200:
        st.error("Failed to load profile")
        return

    profile = response.json()

    if profile.get("cover_image_url"):
        st.image(profile["cover_image_url"], use_container_width=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        if profile.get("profile_image_url"):
            st.image(profile["profile_image_url"], width=170)
        else:
            st.info("No profile image")

    with col2:
        display_name = profile.get("full_name") or profile.get("username") or "User"
        st.markdown(f"### {display_name}")
        st.markdown(f"@{profile.get('username', 'unknown')}")
        st.markdown(profile.get("bio") or "No bio yet")

    stats_col1, stats_col2, stats_col3 = st.columns(3)
    stats_col1.metric("Posts", profile.get("post_count", 0))
    stats_col2.metric("Active", "Yes" if profile.get("is_active") else "No")
    stats_col3.metric("Verified", "Yes" if profile.get("is_verified") else "No")

    st.markdown("### Details")
    st.markdown(
        f"""
        <div class="profile-card">
            <p class="profile-headline"><strong>{profile.get('email', 'N/A')}</strong></p>
            <p class="profile-muted">Location: {profile.get('location') or 'N/A'}</p>
            <p class="profile-muted">Website: {profile.get('website') or 'N/A'}</p>
            <p class="profile-muted">Joined: {format_datetime(profile.get('created_at'))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    with st.expander("✏️ Edit Profile"):
        new_username = st.text_input("Username", value=profile.get("username") or "")
        new_full_name = st.text_input("Full Name", value=profile.get("full_name") or "")
        new_bio = st.text_area("Bio", value=profile.get("bio") or "")
        new_location = st.text_input("Location", value=profile.get("location") or "")
        new_website = st.text_input("Website", value=profile.get("website") or "")

        if st.button("Save Changes", type="primary"):
            update_data = {k: v or None for k, v in {
                "username": new_username,
                "full_name": new_full_name,
                "bio": new_bio,
                "location": new_location,
                "website": new_website,
            }.items()}
            resp = requests.patch(
                "http://localhost:8000/users/profile",
                json=update_data,
                headers=get_headers(),
            )
            if resp.status_code == 200:
                st.success("Profile updated!")
                st.rerun()
            else:
                st.error(f"Update failed: {resp.json().get('detail', 'Unknown error')}")


# Main app logic
if st.session_state.user is None:
    login_page()
else:
    apply_theme_styles()

    # Sidebar navigation
    st.sidebar.title(f"👋 Hi {st.session_state.user['username']}!")
    st.sidebar.checkbox("Dark mode", key="dark_mode")

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.token = None
        st.session_state.dark_mode = False
        st.rerun()

    st.sidebar.markdown("---")
    page = st.sidebar.radio("Navigate:", ["🏠 Feed", "📸 Upload", "🙍 Profile"])

    if page == "🏠 Feed":
        feed_page()
    elif page == "📸 Upload":
        upload_page()
    else:
        profile_page()