# 📘 Study Smarter
> **NCERT Smart Quiz Generator & Performance Analyzer**  
> *A Python & MySQL based project for CBSE NCERT Class 10 & Class 12 Students.*

---

## 🎯 Target Audience & Core Idea
**Study Smarter** helps NCERT Class 10 and Class 12 students turn raw question-bank PDFs (without answer keys) into interactive, self-scoring practice quizzes.

- **Question Parsing & AI Answer Key:** Extracts MCQs, resolves correct answers using AI, and tags them by NCERT subject/chapter/topic.
- **Interactive Quizzes:** Converts questions into online multiple-choice quizzes with timer and instant feedback.
- **Performance Analytics:** Tracks student attempts, identifies weak topics (< 60% accuracy), and recommends targeted revision.

---

## 📂 Project Folder Structure

```text
Study Smarter/
├── .env.example              # Template for environment variables (DB, Port, API Keys)
├── .gitignore                # Excludes bytecode, .env secrets, logs, and venv
├── requirements.txt          # Python library dependencies
├── README.md                 # Project documentation and setup instructions
├── main.py                   # Main entry point (CLI diagnostic & Streamlit runner)
├── logs/                     # Log files directory (auto-created)
│   └── app.log               # Application operational logs
└── src/                      # Source code package
    ├── __init__.py
    ├── config.py             # Environment configuration manager (loads .env safely)
    ├── logger.py             # Centralized logging module (Console + File output)
    ├── database/             # Database connectivity & Schema management
    │   ├── __init__.py
    │   ├── connection.py     # MySQL connection handler with error handling
    │   └── schema.sql        # MySQL table definitions for Class 10 & 12 subjects
    ├── models/               # Data structures (Entities)
    │   ├── __init__.py
    │   └── schemas.py        # Dataclasses: QuestionModel, QuizModel, AttemptModel, etc.
    ├── services/             # Core business logic layer
    │   ├── __init__.py
    │   ├── quiz_service.py   # Quiz generation and scoring logic
    │   ├── analytics_service.py # Weak topic identifier and accuracy analytics
    │   ├── pdf_service.py    # (Placeholder) PDF text & MCQ extraction
    │   └── ai_service.py     # (Placeholder) AI answer key verification
    ├── utils/                # Custom exceptions & helpers
    │   ├── __init__.py
    │   └── exceptions.py     # Application exception hierarchy
    └── ui/                   # Web user interface layer
        ├── __init__.py
        └── app_ui.py         # Streamlit-based web interface and pages
```

---

## ⚙️ Installation & Setup Guide

### 1. Prerequisite
Ensure Python 3.8+ and MySQL Server are installed on your system.

### 2. Create Virtual Environment & Install Dependencies
Open your terminal in the project directory:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate virtual environment (Linux / macOS)
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration (`.env`)
Copy `.env.example` to create your local `.env` configuration file:
```bash
# Copy example configuration template
cp .env.example .env
```
Open `.env` in any text editor and update your local MySQL credentials:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=study_smarter_db
```

### 4. Database Setup (MySQL)
Run the SQL script provided in `src/database/schema.sql` inside your MySQL client (e.g., MySQL Workbench or Command Line):
```sql
SOURCE src/database/schema.sql;
```

---

## 🚀 How to Run the Application

### Option A: System Health & Diagnostic Check
Run `main.py` directly using Python to test configuration loading, imports, and MySQL database connection:
```bash
python main.py
```

### Option B: Launch Interactive Web Application
Launch the web user interface in your browser:
```bash
streamlit run main.py
```
The browser will automatically open at: `http://localhost:8501`.

---

## 🛡️ Foundation & Error Handling Features
- **Zero Secrets Hardcoded:** All database passwords and API keys are stored safely in `.env`.
- **Custom Exception Handling:** Custom exception classes in `src/utils/exceptions.py` handle missing DB drivers, connection timeouts, and query errors gracefully.
- **Centralized Logging:** Automatic file logging to `logs/app.log` and console logging for easy debugging.
