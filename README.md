# 📚 Bookshop Web - Online Bookshop & Catalog Management System

A full-featured web application and relational catalog management platform built with Python. Runs seamlessly with zero external dependencies using the Python standard library, featuring dual-engine support for both MySQL 8.0 and embedded SQLite.

---

## 🚀 Key Features

- **Relational Search Engine**: Multi-field search across titles, authors, categories, and descriptions with server-side filtering.
- **Dynamic Aggregations**: Real-time rating averages and review counts computed via relational joins and grouping.
- **Cart & Order Processing**: Interactive shopping cart with transactional order placement.
- **User Authentication**: Secure role-based authentication and password recovery workflows.
- **Query Performance Inspector**: Live visualization of relational algebra mappings and execution metrics.
- **Zero-Config Dual Database**: Automatically connects to MySQL 8.0 if configured, or initializes an embedded SQLite catalog.

---

## 📂 Project Structure

```text
bookshop-web/
├── app.py                     # HTTP server, routing, and RESTful API controller
├── config.py                  # Global server configuration and environment loader
├── db_adapter.py              # Relational database adapter (SQLite / MySQL dual-mode)
├── requirements.txt           # Optional drivers for MySQL deployments
├── .env.example               # Safe template for environment variables
├── .gitignore                 # Production git ignore rules
├── README.md                  # Project documentation & setup instructions
├── database/                  # SQL schema and benchmark scripts
│   ├── schema.sql             # 3NF relational schema definitions
│   ├── seed_data.sql          # Sample catalog dataset
│   ├── stored_procedures.sql  # Database routines
│   ├── triggers_and_views.sql # Automated audit triggers and views
│   └── explain_benchmark.sql  # Performance benchmarks and indexes
├── static/                    # Frontend client assets
│   ├── css/                   # Stylesheets and visual inspector styling
│   ├── js/                    # Client-side scripts (search, cart, auth)
│   └── img/                   # Branding and vector assets
└── templates/                 # HTML templates
    └── index.html             # Storefront interface
```

---

## 🛠️ Quickstart

### 1. Prerequisites
- Python 3.10+ installed on your system.

### 2. Setup & Configuration (Optional)
Copy the environment template if you wish to customize port or connect to MySQL:
```bash
cp .env.example .env
```

### 3. Run the Application
Start the server:
```bash
python app.py
```
Visit `http://127.0.0.1:8080/` in your browser.

---

## 📄 License
This project is open-source and available under the MIT License.
