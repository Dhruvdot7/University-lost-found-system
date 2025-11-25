# 🏫 University Lost & Found System  
A modern, fast, and user-friendly **Lost & Found management system** built using **Streamlit**, designed specifically for universities and campuses.

This system allows students to report lost items, search for found items, and enables authorized admins to manage found objects and resolve lost cases.

---

## 🌟 Key Features

### 👥 For Public Users  
- Submit **Lost Item** reports  
- Upload item images  
- Search through **Lost** and **Found** items  
- Filter by keyword, category, date, and status  

### 🔐 For Admins  
- Secure login (password-based)  
- Submit **Found Item** reports  
- Convert **Lost → Found** when someone turns in the item  
- Remove resolved/claimed **Found** items  
- Full database dashboard to view all items  

---

## 🏛 Workflow (How the System Works)
1. **Student loses item → submits lost report**  
2. **Admin receives lost report**  
3. **Someone finds the item → admin adds it as FOUND**  
4. Admin can:  
   - Mark a LOST item as FOUND  
   - Remove an item that has been claimed  

This keeps the system organized and avoids duplicates.

---

## 📸 Screenshots (Add later)
lost-found-app/
│── app.py # Main Streamlit app
│── requirements.txt # Python dependencies
│── README.md # Project documentation
│── images/ # Uploaded images stored here
│ └── .gitkeep # Keeps folder in GitHub

---

## ⚙️ Tech Stack
- **Python 3**
- **Streamlit** – Web framework  
- **SQLite** – Local lightweight database  
- **Pillow (PIL)** – Image processing  
- **Hashlib** – Unique image filenames  

---

## 🚀 Installation & Local Setup

Clone the repository:

```bash
git clone https://github.com/your-username/lost-found-app.git
cd lost-found-app
Install dependencies:
pip install -r requirements.txt
Run the app:
streamlit run app.py
