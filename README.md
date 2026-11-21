# 📚 PageVault — Online Bookshop & Inventory Management System

[![Live Demo](https://img.shields.io/badge/Live_Website-Render-00c7b7?style=for-the-badge&logo=render&logoColor=white)](https://pagevault.onrender.com)
[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Tamim-Tahmid-Islam/bookshop-web)
[![Python Runtime](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Database Dual Mode](https://img.shields.io/badge/Database-SQLite3%20%7C%20MySQL%208.0-4479A1?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License MIT](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)

> **Live Website**: [https://pagevault.onrender.com](https://pagevault.onrender.com)  
> *(Deployment Mirror: [https://bookshop-web.onrender.com](https://bookshop-web.onrender.com))*

PageVault is a full-stack, editorial online bookshop and catalog management web platform built in pure Python. It operates with zero mandatory third-party web frameworks, running on Python's built-in socket and HTTP server architecture while delivering an ultra-responsive client interface, transactional order processing, and dual-mode database support.

---

## 🌟 Key Highlights & Capabilities

### 1. Curated 100-Book Catalog Across 12 Disciplines
- **100 Active Titles**: Structured across 12 distinct categories including Computer Science, Systems Architecture, Artificial Intelligence, Fantasy, Classic Drama, Economics, and Contemporary Fiction.
- **Dedicated Cover Imagery**: Every title features its authentic cover art stored locally in high resolution (`static/img/covers/`), eliminating external CDN latency and broken image links.
- **Urgent Inventory Alert Rule**: Controlled inventory distribution where exactly 3 critical titles maintain `stock <= 20` to demonstrate the automated inventory warning workflow.

### 2. Interactive Digital Payment Gateway Simulation
- **Bangladeshi Mobile Banking**: Realistic interactive payment flows simulating bKash and Nagad payment screens with phone number validation, demo verification OTP (`123456`), and secure PIN input.
- **Credit / Debit Cards**: Visa and MasterCard sandbox with simulated card details, CVV validation, and 3D Secure OTP verification.
- **Transactional Consistency**: Generates unique system transaction references (e.g., `BK-XXXXXX`, `NG-XXXXXX`, `CRD-XXXXXX`) tied directly to placed orders.

### 3. Customer Help Desk & Inquiries
- **Floating Support Trigger**: Circular floating help button accessible from any page section.
- **Interactive Inquiry Modal**: Dedicated modal enabling customers to submit inquiries with automatic user pre-fill, categorized topic dropdowns, and message composition.
- **Real-Time Email Dispatch**:
  - Automatically delivers inquiry notifications to the store desk (`tamimtahmid270@gmail.com`).
  - Sends a confirmation auto-reply to the customer's email address.
  - Supports Brevo HTTPS REST API (port 443 compatible with cloud hosts) and standard SMTP.
  - Persists inquiries to the `customer_queries` database table for admin review.

### 4. Comprehensive Admin Control Center
- **Executive Metrics**: Live KPI tiles computing active inventory, total categories, low-stock warnings, cumulative orders, and gross revenue.
- **Urgent Inventory Alerts**: Dedicated tracking table isolating titles at or below the 20-unit threshold with one-click additive restocking (`+N` units accumulation).
- **Order Lifecycle Management**: Real-time status toggling across `Confirmed`, `On Transit`, `Delivered`, and `Cancelled`.
- **Security Audit Console**: Live view of active 6-digit password verification codes and expiry timestamps.
- **Full Catalog CRUD**: Add, edit, update, or soft-delete titles directly through the administrative interface.

### 5. Architectural & UX Foundations
- **Zero-Dependency Core**: Built with Python standard library modules (`http.server`, `socketserver`, `sqlite3`, `urllib`, `hashlib`, `json`).
- **Editorial Cinematic Reveal**: Warm introductory greeting animation welcoming readers on initial page load and refresh.
- **Dual Database Mode**: Seamlessly switches between embedded SQLite and external MySQL 8.0 without code modifications.

---

## 🏛️ System Architecture

```text
               +-----------------------------------------+
               |          Client Browser Interface       |
               |  (HTML5 / Modern CSS / Vanilla JS ES6)  |
               +-----------------------------------------+
                                    |
                    HTTP / JSON REST API Requests
                                    |
                                    v
               +-----------------------------------------+
               |        PageVault HTTP Controller        |
               |   (http.server / socketserver in app.py)|
               +-----------------------------------------+
                     /             |               \
                    /              |                \
                   v               v                 v
        +----------------+ +---------------+ +------------------+
        | Database Layer | | Mailer Engine | | Asset Controller |
        | db_adapter.py  | |  mailer.py    | |  static/ & img/  |
        +----------------+ +---------------+ +------------------+
          /           \            |
         v             v           v
    +---------+   +----------+  +-------------------------------+
    | SQLite  |   | MySQL 8  |  | Brevo API / SMTP Outbox Log   |
    | (Local) |   | (Remote) |  | (tamimtahmid270@gmail.com)    |
    +---------+   +----------+  +-------------------------------+
```

---

## 📂 Project Directory Structure

```text
bookshop-web/
├── app.py                     # HTTP server, REST request routing & controllers
├── config.py                  # Server configuration, ports & database credentials
├── db_adapter.py              # Relational database abstraction (Dual SQLite/MySQL)
├── mailer.py                  # Transactional email module (Brevo HTTPS API & SMTP)
├── populate_100_books.py      # Automated catalog population script (100 books)
├── download_all_covers.py     # High-resolution cover download and asset pipeline
├── pagevault.db               # Embedded SQLite production relational database
├── render.yaml                # Infrastructure as Code specification for Render
├── requirements.txt           # Python dependencies for deployment
├── .env.example               # Template for environment variables
├── database/                  # SQL schema definitions and benchmarks
│   ├── schema.sql             # 3NF relational schema
│   ├── seed_data.sql          # Seed dataset
│   ├── stored_procedures.sql  # Stored routines
│   └── triggers_and_views.sql # Automated audit triggers & reporting views
├── static/                    # Frontend client assets
│   ├── css/
│   │   └── style.css          # Design system & responsive layouts
│   ├── js/
│   │   ├── app.js             # Cart, checkout, admin & support modal controllers
│   │   ├── auth.js            # Authentication, session & password recovery
│   │   └── search.js          # Search engine, dynamic filters & pagination
│   └── img/
│       ├── book-placeholder.svg # Fallback Special Edition vector cover
│       └── covers/            # 100 dedicated book cover assets
└── templates/
    └── index.html             # Storefront and modal UI templates
```

---

## 📡 REST API Reference

| Method | Endpoint | Description | Access |
|---|---|---|---|
| `GET` | `/api/search` | Search catalog with multi-field filtering & pagination | Public |
| `GET` | `/api/suggestions` | Live typeahead search autocomplete | Public |
| `GET` | `/api/categories` | Retrieve all book categories with catalog counts | Public |
| `GET` | `/api/publishers` | Retrieve publisher records | Public |
| `GET` | `/api/authors` | Retrieve author directory | Public |
| `GET` | `/api/books/<id>` | Retrieve comprehensive details for a single book | Public |
| `POST` | `/api/orders` | Place transactional order with selected payment method | Public |
| `POST` | `/api/support/query` | Submit customer support inquiry with email dispatch | Public |
| `POST` | `/api/auth/register` | Register a new customer account | Public |
| `POST` | `/api/auth/login` | Authenticate user credentials | Public |
| `POST` | `/api/auth/forgot-password` | Request password reset code via email | Public |
| `POST` | `/api/auth/reset-password` | Submit new password with 6-digit verification code | Public |
| `GET` | `/api/admin/dashboard` | Retrieve admin KPIs, orders, alerts & queries | Admin |
| `POST` | `/api/books` | Add a new book to the catalog | Admin |
| `PUT` | `/api/books/<id>` | Update title, price, discount or stock units | Admin |
| `DELETE` | `/api/books/<id>` | Soft-delete a book from the active catalog | Admin |
| `POST` | `/api/orders/update-status`| Update customer order delivery status | Admin |
| `GET` | `/healthz` | Observability health check endpoint | Public |

---

## 🚀 Local Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Tamim-Tahmid-Islam/bookshop-web.git
cd bookshop-web
```

### 2. Environment Configuration (Optional)
Copy the example environment configuration:
```bash
cp .env.example .env
```
Key configuration parameters:
- `PORT`: Web server listen port (default: `8080` locally, `10000` on Render)
- `HOST`: Bind address (default: `127.0.0.1` locally, `0.0.0.0` on Render)
- `BREVO_API_KEY`: Optional Brevo API key for transactional emails
- `SMTP_USER` & `SMTP_PASSWORD`: Optional SMTP credentials for email delivery

### 3. Launch the Server
```bash
python app.py
```
Open your browser and navigate to:
```text
http://127.0.0.1:8080/
```

---

## ☁️ Deployment on Render

This repository includes a native [`render.yaml`](render.yaml) blueprint for automated deployments:

1. Sign in to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** and select **Blueprint**.
3. Connect your GitHub repository `Tamim-Tahmid-Islam/bookshop-web`.
4. Render will automatically detect `render.yaml` and configure the Web Service with:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Port**: `10000`
5. Click **Apply** to deploy your live website.

---

## 🔐 Administrative Access

- **Admin Email**: `tamimtahmid270@gmail.com`
- **Role**: `Admin`
- Access the management console by signing in with the designated administrator account and selecting **Admin Portal** from the user navigation menu.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

**Developed & Maintained by [Tamim Tahmid Islam](https://github.com/Tamim-Tahmid-Islam)**  
*Curated Books. Infinite Worlds.*
