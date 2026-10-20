# University Event Management System (UEMS)

A centralized web application designed for university campuses to streamline event publishing, student registrations, attendance verification, and campus-wide announcements.

Developed as a **5th-Semester B.Tech Project**.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python Django 5+ (Model-View-Template architecture) |
| **Database** | PostgreSQL |
| **Frontend** | HTML5, Vanilla CSS3, Vanilla JavaScript (Server-rendered via Django Templates) |
| **Environment Configuration** | `python-dotenv` |
| **Database Adapter** | `psycopg2-binary` |

> **Note**: This project intentionally uses vanilla HTML/CSS/JavaScript with Django templates and avoids frontend frameworks (like React or Node.js) to adhere to university syllabus requirements and keep the codebase simple and maintainable.

---

## 📁 Project Architecture & Structure

```text
UEMS/
│
├── config/                      # Project-wide configuration folder
│   ├── __init__.py
│   ├── settings.py              # Central Django settings (env-driven database, apps, static)
│   ├── urls.py                  # Root URL router delegating to modular apps
│   ├── wsgi.py                  # WSGI entry point for web servers
│   └── asgi.py                  # ASGI entry point for async capabilities
│
├── accounts/                    # App 1: User authentication, roles (Student, Organizer, Admin)
│   └── urls.py
├── events/                      # App 2: Event creation, details, categories, scheduling
│   └── urls.py
├── registrations/               # App 3: Student registration & ticket management
│   └── urls.py
├── attendance/                  # App 4: Event check-ins and attendance records
│   └── urls.py
├── announcements/               # App 5: Broadcast notices and event notifications
│   └── urls.py
│
├── templates/                   # Global Django Templates
│   ├── base.html                # Base layout (header, nav, flash messages, footer)
│   ├── home.html                # Foundation welcome & verification landing page
│   ├── accounts/                # Template folder for accounts app
│   ├── events/                  # Template folder for events app
│   ├── registrations/           # Template folder for registrations app
│   ├── attendance/              # Template folder for attendance app
│   └── announcements/           # Template folder for announcements app
│
├── static/                      # Static Assets (CSS, JavaScript, Images)
│   ├── css/
│   │   └── style.css            # Global CSS styling
│   ├── js/
│   │   └── main.js              # Global vanilla JavaScript
│   └── images/                  # Static image assets (logos, icons)
│
├── media/                       # Uploaded files (event banners, posters)
├── .env.example                 # Template for environment variables
├── .env                         # Local environment variables (EXCLUDED from Git)
├── .gitignore                   # Excludes .env, virtual env, cache, and db files
├── requirements.txt             # Python dependencies
├── manage.py                    # Django management CLI script
└── README.md                    # Setup guide and documentation
```

---

## 💻 Windows Setup & Installation Guide

Follow these steps to set up and run the project locally on Windows using PowerShell or Command Prompt.

### Prerequisites
1. **Python 3.10+**: Download and install from [python.org](https://www.python.org/). (Make sure to check *"Add python.exe to PATH"* during installation).
2. **PostgreSQL**: Download and install from [postgresql.org](https://www.postgresql.org/download/windows/). Keep note of the superuser password configured during installation.
3. **Git**: Installed on your machine.

---

### Step 1: Open Terminal in Project Directory
Open **PowerShell** or **Command Prompt** and navigate to the project root:
```powershell
cd C:\Users\rohit\Desktop\UEMS
```

---

### Step 2: Create and Activate Virtual Environment
A virtual environment isolates project dependencies from your global Python installation.

**In PowerShell:**
```powershell
# Create the virtual environment
python -m venv .venv

# If PowerShell script execution is restricted, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1
```

**In Command Prompt (cmd.exe):**
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

*(You will see `(.venv)` appear at the beginning of your terminal prompt when activated).*

---

### Step 3: Install Required Packages
Install the required dependencies listed in `requirements.txt`:
```powershell
pip install -r requirements.txt
```

---

### Step 4: Configure Environment Variables (`.env`)
1. If `.env` is not present, create it by copying `.env.example`:
   ```powershell
   copy .env.example .env
   ```
2. Open `.env` in your code editor (e.g., VS Code or Notepad) and update the PostgreSQL database credentials to match your local PostgreSQL installation:
   ```env
   # PostgreSQL Configuration
   DB_NAME=uems_db
   DB_USER=postgres
   DB_PASSWORD=your_actual_postgres_password
   DB_HOST=localhost
   DB_PORT=5432
   ```

---

### Step 5: Create the PostgreSQL Database
Before running migrations, create the database in PostgreSQL.

**Using SQL Shell (`psql`):**
1. Open `SQL Shell (psql)` from the Windows Start menu.
2. Press Enter to accept defaults (`Server [localhost]`, `Database [postgres]`, `Port [5432]`, `Username [postgres]`).
3. Enter your PostgreSQL password when prompted.
4. Run the following SQL command:
   ```sql
   CREATE DATABASE uems_db;
   ```
5. Type `\q` to exit `psql`.

*(Alternatively, you can create the database using the pgAdmin 4 graphical tool: Right-click **Databases** &rarr; **Create** &rarr; **Database...** &rarr; Name it `uems_db`).*

---

### Step 6: Run Django System Check & Apply Migrations
Verify the project configuration:
```powershell
python manage.py check
```

Apply Django's initial migrations to set up the authentication, session, and admin tables in your PostgreSQL database:
```powershell
python manage.py migrate
```

---

### Step 7: Create an Admin Superuser (Optional but Recommended)
Create an administrator account to access Django's built-in administration portal:
```powershell
python manage.py createsuperuser
```
Follow the interactive prompts to set a username, email, and password.

---

### Step 8: Start the Local Development Server
Run the local server:
```powershell
python manage.py runserver
```

Once running, visit:
- **Project Landing Page**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Django Admin Portal**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

Press `Ctrl + C` in the terminal to stop the server.

---

## 🎓 B.Tech Project Viva / Technical Q&A Guide

When presenting this foundation to external examiners or professors, be prepared for these questions:

### 1. Why is the project split into separate Django apps?
> **Answer**: Django encourages the **Separation of Concerns (SoC)** principle. Instead of putting all models and views in one monolithic file, modular apps (`accounts`, `events`, `registrations`, `attendance`, `announcements`) keep domain logic isolated, easily testable, and reusable.

### 2. Why use environment variables (`.env`) for database credentials?
> **Answer**: Hardcoding database passwords or secret keys in source files is a severe security vulnerability. Storing configuration in environment variables follows the **Twelve-Factor App methodology**. It keeps credentials secret and prevents them from being committed to Git or public repositories.

### 3. What is CSRF and how does Django protect against it?
> **Answer**: **Cross-Site Request Forgery (CSRF)** is an attack where an unauthorized website tricks an authenticated user's browser into executing an unwanted action on a trusted site. Django provides `CsrfViewMiddleware` by default, requiring a unique, cryptographically-generated `{% csrf_token %}` with every `POST` request to ensure requests originate genuinely from our site.

### 4. What is the role of `manage.py`?
> **Answer**: `manage.py` is a Python CLI wrapper around Django's administrative commands. It sets the `DJANGO_SETTINGS_MODULE` environment variable to `config.settings` and invokes Django management tasks such as `migrate`, `createsuperuser`, `runserver`, and `startapp`.

### 5. How does Django locate static files and templates?
> **Answer**:
> - **Templates**: Django inspects the `TEMPLATES` setting in `settings.py`. We configured `'DIRS': [BASE_DIR / 'templates']`, which tells Django to look inside the global `templates/` folder first.
> - **Static Files**: `STATIC_URL = 'static/'` defines the public URL prefix, while `STATICFILES_DIRS = [BASE_DIR / 'static']` tells Django where static assets (`css`, `js`, `images`) are located during development.
