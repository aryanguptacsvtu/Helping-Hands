import streamlit as st
import sqlite3
import bcrypt
from datetime import datetime

from streamlit_extras.stylable_container import stylable_container
import streamlit_extras

# ------------------ SESSION INIT ------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.user_name = ""
    st.session_state.user_role = ""

# ------------------ DATABASE SETUP ---------------------------------------
def create_tables():
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()

        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users(
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT,
                      email TEXT UNIQUE,
                      password BLOB,
                      role TEXT)''')
        
        # Events table
        c.execute('''CREATE TABLE IF NOT EXISTS events(
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      title TEXT,
                      description TEXT,
                      location TEXT,
                      date TEXT,
                      created_by TEXT)''')
        
        # Registrations table
        c.execute('''CREATE TABLE IF NOT EXISTS registrations(
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      event_id INTEGER,
                      volunteer_email TEXT,
                      UNIQUE(event_id, volunteer_email))''')
        
        conn.commit()


# ------------------ USER FUNCTIONS --------------------------------------------------------
def add_userdata(name, email, password, role):
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("INSERT INTO users(name, email, password, role) VALUES (?,?,?,?)",
                  (name, email, password, role))
        conn.commit()

def login_user(email, password):
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user = c.fetchone()

    if user:
        stored_pw = user[3]
        if isinstance(stored_pw, str):
            stored_pw = stored_pw.encode()
        if bcrypt.checkpw(password.encode(), stored_pw):
            return user
        
    return None

# ------------------ EVENT FUNCTIONS ------------------------------------------------------------------------
def add_event(title, desc, location, date, created_by):
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("INSERT INTO events(title, description, location, date, created_by) VALUES (?,?,?,?,?)",
                  (title, desc, location, date, created_by))
        conn.commit()

def get_all_events():
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM events ORDER BY date ASC")
        events = c.fetchall()
    return events

def get_events_by_creator(email):
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM events WHERE created_by=? ORDER BY date ASC", (email,))
        events = c.fetchall()
    return events

def update_event(event_id, title, desc, location, date):
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("UPDATE events SET title=?, description=?, location=?, date=? WHERE id=?",
                    (title, desc, location, str(date), event_id))
        conn.commit()

def delete_event(event_id):
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        # Also delete associated registrations to maintain data integrity
        c.execute("DELETE FROM registrations WHERE event_id=?", (event_id,))
        c.execute("DELETE FROM events WHERE id=?", (event_id,))
        conn.commit()

# ------------------ REGISTRATION FUNCTIONS -------------------------------------------------------
def join_event(event_id, volunteer_email):
    try:
        with sqlite3.connect("database.db") as conn:
            c = conn.cursor()
            c.execute("INSERT INTO registrations(event_id, volunteer_email) VALUES (?,?)",
                      (event_id, volunteer_email))
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def unjoin_event(event_id, volunteer_email):
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("DELETE FROM registrations WHERE event_id=? AND volunteer_email=?",
                    (event_id, volunteer_email))
        conn.commit()

def get_registrations_for_event(event_id):
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("SELECT volunteer_email FROM registrations WHERE event_id=?", (event_id,))
        volunteers = c.fetchall()
    return volunteers

def get_joined_events(volunteer_email):
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("""SELECT e.* FROM events e
                     JOIN registrations r ON e.id = r.event_id
                     WHERE r.volunteer_email = ? ORDER BY e.date""",
                  (volunteer_email,))
        rows = c.fetchall()
    return rows

# ------------------ STREAMLIT UI --------------------------------------------------------------------
create_tables()

st.set_page_config(layout="wide")

st.title("🌍 Helping Hands")
menu = ["Home", "Register", "Login"]
choice = st.sidebar.selectbox("Menu", menu)


# ---- Home ----
if choice == "Home":
    st.markdown(
        """
        <style>
        /* General Body Style */
        .stApp {
            background-color: #F0F2F6;
        }

        /* Hero Section */
        .hero-section {
            padding: 4rem 2rem;
            border-radius: 15px;
            text-align: center;
            color: white;
            background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)),
                        url('https://reintegrationfacility.eu/wp-content/uploads/2024/09/NGO-training-950x482.jpg');
            background-size: cover;
            background-position: center;
            margin-bottom: 2rem;
        }
        .hero-section h1 {
            font-size: 3.5rem;
            font-weight: 800;
        }
        .hero-section p {
            font-size: 1.5rem;
            max-width: 600px;
            margin: 0 auto 1rem auto;
        }

        /* How It Works Section */
        .how-it-works {
            text-align: center;
            padding: 2rem 0;
        }
        .how-it-works h2 {
            font-size: 2.5rem;
            color: #2C3E50;
            margin-bottom: 2rem;
        }

        /* Custom Cards for Steps */
        .step-card {
            background-color: #FFFFFF;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            height: 100%;
        }
        .step-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 12px 24px rgba(0,0,0,0.15);
        }
        .step-card .icon {
            font-size: 4rem;
            margin-bottom: 1rem;
        }
        .step-card h3 {
            font-size: 1.5rem;
            color: #3498DB;
            margin-bottom: 0.5rem;
        }
        .step-card p {
            color: #7F8C8D;
            font-size: 1rem;
        }

        /* Call to Action Section */
        .cta-section {
            background: linear-gradient(135deg, #74ebd5 0%, #ACB6E5 100%);
            padding: 3rem;
            border-radius: 15px;
            text-align: center;
            margin-top: 3rem;
        }
        .cta-section h3 {
            font-size: 2rem;
            color: #2C3E50;
            font-weight: 700;
        }
        .cta-section p {
            font-size: 1.2rem;
            color: #34495E;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    with st.container():
        st.markdown(
            """
            <div class="hero-section">
                <h1>Join the Movement. Be the Change.</h1>
                <p>Connecting compassionate volunteers with impactful NGOs and community events.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with st.container():
        st.markdown('<div class="how-it-works"><h2>How It Works</h2></div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3, gap="large")

        with col1:
            st.markdown(
                """
                <div class="step-card">
                    <div class="icon">✍️</div>
                    <h3>1. Register Your Profile</h3>
                    <p>Create an account as a <strong>Volunteer</strong> looking for opportunities or an <strong>NGO</strong> seeking help. It's quick, easy, and free!</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                """
                <div class="step-card">
                    <div class="icon">🔍</div>
                    <h3>2. Discover or Create</h3>
                    <p><strong>Volunteers:</strong> Browse a wide range of local events. <br><strong>NGOs:</strong> Post your events and detail your needs to attract the right volunteers.</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col3:
            st.markdown(
                """
                <div class="step-card">
                    <div class="icon">🤝</div>
                    <h3>3. Connect & Collaborate</h3>
                    <p>Join events that match your passion. NGOs can manage their events and see who's coming. Together, we build a stronger community.</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    with st.container():
        st.markdown(
            """
            <div class="cta-section">
                <h3>🚀 Ready to Make a Difference?</h3>
                <p>Use the sidebar menu to <strong>Register</strong> or <strong>Login</strong> and begin your journey with Helping Hands today!</p>
            </div>
            """,
            unsafe_allow_html=True
        )

# ---- Register --------------
elif choice == "Register":
    st.subheader("🔑 Create New Account")
    name = st.text_input("Full Name", key="reg_name")
    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Password", type="password", key="reg_pass")
    role = st.selectbox("Role", ["Volunteer", "NGO"], key="reg_role")

    if st.button("Register"):
        if name and email and password:
            hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            try:
                add_userdata(name, email, hashed_pw, role)
                st.success("✅ Account created successfully!")
                st.info("Now you can login from the Login Page.")
            except Exception:
                st.error("⚠️ Error: This email might already be registered.")
        else:
            st.warning("Please fill all fields before registering.")

# ---- Login / Dashboard ---------------
elif choice == "Login":
    if st.session_state.logged_in:
        st.success(f"Welcome back, {st.session_state.user_name} ({st.session_state.user_role})")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.session_state.user_name = ""
            st.session_state.user_role = ""
            st.rerun()

        # Volunteer Dashboard
        if st.session_state.user_role == "Volunteer":
            st.subheader("📌 Volunteer Dashboard")
            st.write("Here you can browse and join community events.")

            tab1, tab2 = st.tabs(["Browse Events", "My Joined Events"])

            with tab1:
                events = get_all_events()
                if events:
                    for e in events:
                        with st.container():
                            st.markdown(f"### 📍 {e[1]}")
                            st.write(f"**Description:** {e[2]}")
                            st.write(f"**Location:** {e[3]}")
                            st.write(f"**Date:** {e[4]}")
                            st.write(f"**Organized by:** {e[5]}")
                            if st.button(f"✅ Join {e[1]}", key=f"join_{e[0]}"):
                                if join_event(e[0], st.session_state.user_email):
                                    st.success(f"You have successfully joined {e[1]} 🎉")
                                else:
                                    st.warning("You already joined this event.")
                        st.divider()
                else:
                    st.info("No events available at the moment.")

            with tab2:
                st.subheader("My Upcoming Events")
                joined = get_joined_events(st.session_state.user_email)
                if joined:
                    for je in joined:
                        st.markdown(f"### 📍 {je[1]}")
                        st.write(f"**Description:** {je[2]}")
                        st.write(f"**Location:** {je[3]}")
                        st.write(f"**Date:** {je[4]}")
                        
                        # --- MODIFIED: Added Unjoin button ---
                        if st.button("❌ Unjoin Event", key=f"unjoin_{je[0]}"):
                            unjoin_event(je[0], st.session_state.user_email)
                            st.success(f"You have successfully unregistered from '{je[1]}'.")
                            st.rerun()
                        st.divider()
                else:
                    st.info("You have not joined any events yet.")

        # NGO Dashboard
        elif st.session_state.user_role == "NGO":
            st.subheader("🏢 NGO Dashboard")
            st.write("Here you can create and manage community service events.")

            with st.form("create_event_form"):
                st.markdown("### ➕ Create New Event")
                title = st.text_input("Event Title", key="ev_title")
                desc = st.text_area("Event Description", key="ev_desc")
                location = st.text_input("Location", key="ev_loc")
                date = st.date_input("Event Date", min_value=datetime.today(), key="ev_date")
                submitted = st.form_submit_button("Create Event")

                if submitted:
                    if title and desc and location:
                        add_event(title, desc, location, str(date), st.session_state.user_email)
                        st.success("✅ Event created successfully!")
                    else:
                        st.warning("Please fill all fields before creating event.")

            st.markdown("### 📋 Your Created Events")
            events = get_events_by_creator(st.session_state.user_email)
            if events:
                for e in events:
                    st.markdown(f"#### 📍 {e[1]} on {e[4]}")
                    
                    volunteers = get_registrations_for_event(e[0])
                    if volunteers:
                        with st.expander(f"View {len(volunteers)} Registered Volunteers"):
                            for v in volunteers:
                                st.write(f"- {v[0]}")
                    else:
                        st.info("No volunteers have joined this event yet.")

                    # --- NEW: Edit and Delete functionality ---
                    col1, col2 = st.columns([0.8, 0.2])
                    with col1:
                        with st.expander("✏️ Edit Event Details"):
                            with st.form(key=f"edit_form_{e[0]}"):
                                st.write("Modify event details below:")
                                new_title = st.text_input("Event Title", value=e[1], key=f"title_{e[0]}")
                                new_desc = st.text_area("Description", value=e[2], key=f"desc_{e[0]}")
                                new_loc = st.text_input("Location", value=e[3], key=f"loc_{e[0]}")
                                new_date_val = datetime.strptime(e[4], '%Y-%m-%d').date()
                                new_date = st.date_input("Date", value=new_date_val, min_value=datetime.today(), key=f"date_{e[0]}")
                                
                                if st.form_submit_button("Save Changes"):
                                    update_event(e[0], new_title, new_desc, new_loc, new_date)
                                    st.success(f"Event '{new_title}' has been updated.")
                                    st.rerun()
                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_{e[0]}"):
                            delete_event(e[0])
                            st.success(f"Event '{e[1]}' has been deleted.")
                            st.rerun()
                    st.divider()
                    # --- END of NEW section ---
            else:
                st.info("You haven’t created any events yet.")

    else:
        st.subheader("🔐 Login to Your Account")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login"):
            user = login_user(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_email = user[2]
                st.session_state.user_name = user[1]
                st.session_state.user_role = user[4]
                st.rerun()
            else:
                st.error("❌ Invalid email or password")