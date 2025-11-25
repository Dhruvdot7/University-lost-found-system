# app.py
import streamlit as st
import sqlite3
from datetime import datetime, date
import os
from PIL import Image
import hashlib

# ---------- Configuration ----------
DB_PATH = "lostfound.db"
IMAGES_DIR = "images"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")  # change in production!
# -----------------------------------

os.makedirs(IMAGES_DIR, exist_ok=True)


# ---------- Database helpers ----------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT,
        status TEXT NOT NULL, -- 'lost' or 'found'
        reporter_name TEXT,
        reporter_contact TEXT,
        image_path TEXT,
        created_at TEXT NOT NULL
    )
    """
    )
    conn.commit()
    conn.close()


init_db()


# ---------- Core CRUD actions ----------
def save_image(uploaded_file):
    if uploaded_file is None:
        return None
    data = uploaded_file.getvalue()
    h = hashlib.sha1(data).hexdigest()[:12]
    ext = os.path.splitext(uploaded_file.name)[1] or ".jpg"
    fn = f"{int(datetime.utcnow().timestamp())}_{h}{ext}"
    path = os.path.join(IMAGES_DIR, fn)

    try:
        with open(path, "wb") as f:
            f.write(data)
        return path
    except Exception:
        return None


def add_item(title, description, category, status, reporter_name, reporter_contact, uploaded_file):
    img_path = save_image(uploaded_file)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO items (title, description, category, status, reporter_name, reporter_contact, image_path, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (title, description, category, status, reporter_name, reporter_contact, img_path, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def remove_item(item_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT image_path FROM items WHERE id=?", (item_id,))
    row = cur.fetchone()
    if row and row["image_path"]:
        try:
            os.remove(row["image_path"])
        except:
            pass

    cur.execute("DELETE FROM items WHERE id=?", (item_id,))
    conn.commit()
    conn.close()


def mark_as_found(item_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE items SET status='found' WHERE id=?", (item_id,))
    conn.commit()
    conn.close()


def search_items(keyword=None, status=None, start_date=None, end_date=None, category=None):
    conn = get_conn()
    cur = conn.cursor()
    q = "SELECT * FROM items WHERE 1=1"
    params = []

    if status:
        q += " AND status=?"
        params.append(status)

    if keyword:
        q += " AND (title LIKE ? OR description LIKE ?)"
        kw = f"%{keyword}%"
        params.extend([kw, kw])

    if category and category != "Any":
        q += " AND category=?"
        params.append(category)

    if start_date:
        q += " AND date(created_at) >= date(?)"
        params.append(start_date)

    if end_date:
        q += " AND date(created_at) <= date(?)"
        params.append(end_date)

    q += " ORDER BY created_at DESC"
    cur.execute(q, params)
    rows = cur.fetchall()
    conn.close()
    return rows


# ---------- UI helpers ----------
def show_item_card(row):
    st.write("---")
    cols = st.columns([1, 3])

    with cols[0]:
        if row["image_path"] and os.path.exists(row["image_path"]):
            try:
                img = Image.open(row["image_path"])
                st.image(img, use_container_width=True, caption=row["title"])
            except:
                st.text("Image cannot be opened")
        else:
            st.text("No image")

    with cols[1]:
        st.subheader(f"{row['title']} — {row['status'].upper()}")
        st.markdown(f"**Category:** {row['category'] or '—'}")
        st.markdown(f"**Reported:** {row['created_at']}")

        if row["description"]:
            st.markdown(f"**Description:** {row['description']}")

        if row["reporter_name"]:
            st.markdown(f"**Reporter:** {row['reporter_name']} — {row['reporter_contact'] or '—'}")

        # ----------- ADMIN ACTIONS -----------
        if st.session_state.get("admin_authenticated", False):

            # LOST ITEM → mark as FOUND
            if row["status"] == "lost":
                if st.button(f"✔ Mark as FOUND (#{row['id']})", key=f"mark-{row['id']}"):
                    mark_as_found(row["id"])
                    st.success("Item marked as FOUND!")
                    st.rerun()

            # FOUND ITEM → remove
            if row["status"] == "found":
                if st.button(f"❌ Remove item #{row['id']}", key=f"rm-{row['id']}"):
                    remove_item(row["id"])
                    st.rerun()


# ---------- STREAMLIT UI ----------
st.set_page_config(page_title="University Lost & Found", layout="centered")
st.title("🏫 University Lost & Found")

menu = st.sidebar.selectbox("Menu", ["Home", "Report Lost Item", "Search", "Admin"])

if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False


# ---------- HOME ----------
if menu == "Home":
    st.write("Welcome! Report lost items or search for them.")
    st.write("Admins can log in to submit found items and manage records.")

    st.header("Recent Reports")
    rows = search_items()
    if not rows:
        st.info("No reports yet.")
    else:
        for r in rows[:10]:
            show_item_card(r)


# ---------- REPORT LOST ----------
elif menu == "Report Lost Item":
    st.header("Report a Lost Item (Public)")

    with st.form("lost_form"):
        title = st.text_input("Title (e.g., Black Wallet, Laptop, ID Card)")
        description = st.text_area("Description (where lost, when, details)")
        category = st.selectbox("Category", ["Electronics", "Documents", "Accessories", "Clothing", "Others"])
        reporter_name = st.text_input("Your Name (optional)")
        reporter_contact = st.text_input("Contact (phone/email)")
        uploaded_file = st.file_uploader("Image (optional)", type=["jpg", "jpeg", "png"])
        submit = st.form_submit_button("Submit Lost Item")

    if submit:
        if not title.strip():
            st.error("Title is required.")
        else:
            add_item(title, description, category, "lost", reporter_name, reporter_contact, uploaded_file)
            st.success("Lost item reported successfully!")


# ---------- SEARCH ----------
elif menu == "Search":
    st.header("Search Lost & Found Items")

    col1, col2 = st.columns(2)
    with col1:
        keyword = st.text_input("Keyword")
        status_choice = st.selectbox("Status", ["Any", "Lost", "Found"])
        category = st.selectbox("Category", ["Any", "Electelectronics", "Documents", "Accessories", "Clothing", "Others"])
    with col2:
        date_filter = st.checkbox("Filter by Date")
        start_date = None
        end_date = None
        if date_filter:
            start_date = st.date_input("From", value=date.today())
            end_date = st.date_input("To", value=date.today())
            if start_date > end_date:
                st.warning("Start date is after end date.")

    if st.button("Search"):
        status_val = None if status_choice == "Any" else status_choice.lower()
        sd = start_date.isoformat() if start_date else None
        ed = end_date.isoformat() if end_date else None

        results = search_items(keyword, status_val, sd, ed, category)

        if not results:
            st.info("No results found.")
        else:
            for item in results:
                show_item_card(item)


# ---------- ADMIN ----------
elif menu == "Admin":
    st.header("Admin Panel")

    # --------- LOGIN ----------
    if not st.session_state.admin_authenticated:
        pwd = st.text_input("Enter Admin Password", type="password")
        if st.button("Login"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.success("Logged in!")
                st.rerun()
            else:
                st.error("Incorrect password.")

    # --------- AUTHENTICATED ADMIN ----------
    else:
        st.subheader("Submit Found Item")

        with st.form("found_form"):
            title = st.text_input("Title")
            description = st.text_area("Description")
            category = st.selectbox("Category", ["Electronics", "Documents", "Accessories", "Clothing", "Others"])
            reporter_name = st.text_input("Finder Name (optional)")
            reporter_contact = st.text_input("Finder Contact (optional)")
            uploaded_file = st.file_uploader("Image (optional)", type=["jpg", "jpeg", "png"])
            f_sub = st.form_submit_button("Submit Found Item")

        if f_sub:
            if title.strip():
                add_item(title, description, category, "found", reporter_name, reporter_contact, uploaded_file)
                st.success("Found item added!")
            else:
                st.error("Title is required.")

        st.subheader("Manage Items (Lost + Found)")
        all_rows = search_items()

        if not all_rows:
            st.info("No items available.")
        else:
            for r in all_rows:
                show_item_card(r)

        if st.button("Logout"):
            st.session_state.admin_authenticated = False
            st.rerun()
