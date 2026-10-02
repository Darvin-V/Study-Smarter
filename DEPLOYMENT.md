# Study Smarter — Production Deployment Guide

This guide walks through deploying the Study Smarter application to **Streamlit Community Cloud** with a cloud-hosted **MySQL Database** and the **Google Gemini API**.

---

## 1. Prerequisites

Before starting, ensure you have:
1. A **GitHub account** (to host the repository).
2. A **Streamlit Community Cloud account** (free at [streamlit.io/cloud](https://streamlit.io/cloud)).
3. A **Cloud MySQL database instance** (e.g., [Aiven](https://aiven.io), [PlanetScale](https://planetscale.com), [AWS RDS](https://aws.amazon.com/rds/), [DigitalOcean Managed MySQL](https://www.digitalocean.com/products/managed-databases-mysql), or [Clever Cloud](https://www.clever-cloud.com/)).
4. A **Google Gemini API Key** (from [Google AI Studio](https://aistudio.google.com/)).

---

## 2. GitHub Repository Preparation

1. Open your terminal in the project root directory.
2. Initialize Git (if not already done) and check status:
   ```bash
   git init
   git status
   ```
3. Verify that your `.env` file is **NOT** tracked (it is ignored by `.gitignore`):
   ```bash
   git status --ignored
   ```
4. Stage and commit the project files:
   ```bash
   git add .
   git commit -m "feat: prepare Study Smarter for cloud production deployment"
   ```
5. Create a new private (or public) repository on GitHub and push your code:
   ```bash
   git remote add origin https://github.com/your-username/study-smarter.git
   git branch -M main
   git push -u origin main
   ```

> [!IMPORTANT]
> Never commit `.env` or files containing real database passwords or API keys to GitHub.

---

## 3. Cloud MySQL Database Setup

1. Create a MySQL database instance with your cloud provider (e.g. Aiven, AWS RDS, DigitalOcean).
2. Note down your cloud database parameters:
   - **Host**: e.g., `mysql-your-instance.aivencloud.com`
   - **Port**: e.g., `3306` (or provider port like `23456`)
   - **Database Name**: e.g., `defaultdb` or `study_smarter_db`
   - **User**: e.g., `avnadmin` or `admin`
   - **Password**: your secure database password

3. Ensure public networking / IP allowlists permit connections from Streamlit Cloud (or set allowlist to `0.0.0.0/0` with strong password).

---

## 4. Cloud Database Schema Initialization

Before launching the web app, initialize the tables and indexes on your cloud database:

### Option A: Using the Automated Initializer Script (Recommended)
Set the environment variables for your cloud database temporarily and run:
```bash
python initialize_database.py
```
This script runs non-destructive `CREATE TABLE IF NOT EXISTS` for all 5 core tables (`users`, `question_banks`, `quizzes`, `questions`, `attempts`) and verifies connectivity.

### Option B: Using SQL Client / Web Console
Open your cloud provider's SQL query editor or standard MySQL client (e.g. DBeaver, MySQL Workbench) and execute the contents of `schema.sql`:
```bash
mysql -h <your_cloud_host> -P <your_port> -u <your_user> -p <your_db_name> < schema.sql
```

---

## 5. Streamlit Community Cloud Deployment

1. Log in to [share.streamlit.io](https://share.streamlit.io/).
2. Click **New app**.
3. Select your GitHub repository:
   - **Repository**: `your-username/study-smarter`
   - **Branch**: `main`
   - **Main file path**: `main.py`
4. Click **Advanced settings...** (bottom left of dialog) before deploying.
5. In the **Secrets** text area, paste your production secrets:

```toml
# Google Gemini API Key
GEMINI_API_KEY = "your_real_gemini_api_key"

# Cloud MySQL Database
DB_HOST = "your_cloud_mysql_host"
DB_PORT = "3306"
DB_USER = "your_cloud_mysql_user"
DB_PASSWORD = "your_cloud_mysql_password"
DB_NAME = "your_cloud_database_name"

# Optional Settings
APP_ENV = "production"
DB_TIMEOUT = "15"
```

6. Click **Save** and then click **Deploy!**.

---

## 6. Required Secrets Checklist

| Secret Name | Description | Example / Default |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | Google AI Studio API Key for answer solving & explanations | `AIzaSy...` |
| `DB_HOST` | Remote MySQL hostname or IP address | `mysql.provider.com` |
| `DB_PORT` | Remote MySQL port | `3306` |
| `DB_USER` | Remote MySQL database username | `admin` |
| `DB_PASSWORD` | Remote MySQL database password | `******` |
| `DB_NAME` | Target database name | `study_smarter_db` |
| `DB_TIMEOUT` | *(Optional)* Connection timeout in seconds | `15` |
| `DB_SSL_CA` | *(Optional)* Path to CA certificate if required by host | `/path/to/ca.pem` |

---

## 7. Post-Deployment Verification

Once deployed, verify the application flow:
1. **Home Page**: Check that the dashboard loads with navbar links (`Home`, `Progress`, `History`).
2. **Database Status**: Navigate to **Practice**; verify your question banks populate from MySQL.
3. **Practice Quiz**: Select a question bank and complete 1 question; verify immediate feedback and explanations render.
4. **History & Progress**: Complete a quiz and verify the attempt is saved to MySQL and appears in **History** and **Progress**.
5. **PDF Upload**: Test uploading a sample question bank PDF on the **Upload** page; verify questions are extracted and saved.

---

## 8. Troubleshooting Common Errors

### 1. Database Connection Timeout / Refused
- **Cause**: Cloud database firewall / IP allowlist is blocking Streamlit Cloud's dynamic IP range.
- **Fix**: In your cloud database management panel, allow incoming connections from all IPs (`0.0.0.0/0`) or use a VPC peering setup. Ensure `DB_PORT` is correctly configured.

### 2. Access Denied / Authentication Failed
- **Cause**: Incorrect username or password in Streamlit Cloud Secrets.
- **Fix**: Verify secrets in Streamlit Cloud App Settings -> **Secrets**. Make sure values are enclosed in quotes.

### 3. Gemini API 404 / Quota Exceeded
- **Cause**: Outdated model name or invalid API key.
- **Fix**: The application defaults to `gemini-flash-lite-latest` and falls back automatically. Verify your `GEMINI_API_KEY` is active in Google AI Studio.

### 4. Database Schema Incomplete
- **Cause**: App launched before running `schema.sql`.
- **Fix**: Run `python initialize_database.py` or execute `schema.sql` directly on the database to create all required tables.
