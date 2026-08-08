# 🚀 Freelancer Project Estimator & Marketplace

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Netlify-00C7B7?style=for-the-badge&logo=netlify)](https://freelancerestimator.netlify.app/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github)](https://github.com/Raviteja-864/Freelancer-Project-Estimator)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)

**🌐 Live Web Application**: [https://freelancerestimator.netlify.app/](https://freelancerestimator.netlify.app/)

A full-stack freelancer marketplace and project estimator web application. Built with a modular Python Flask backend architecture and a responsive static frontend optimized for single-page and multi-page routing on Netlify.

---

## 📁 Repository Architecture & Directory Structure

```
Freelancer-Project-Estimator/
├── public/                     # Frontend Distribution (Netlify Static Build)
│   ├── index.html              # Marketing Homepage
│   ├── login.html              # User Authentication Login
│   ├── register.html           # Account Registration
│   ├── dashboard.html          # Role-Based User Dashboard
│   ├── find-work.html          # Job Board & Freelance Bidding
│   ├── new-project.html        # Client Project Posting
│   ├── project_detail.html     # Project Bidding & Milestone View
│   ├── messages.html           # Project Chat & Communication
│   ├── payment.html            # Escrow & Payment Tracking
│   ├── admin.html              # Platform Management Console
│   ├── _redirects              # Netlify Routing & SPA Rewrite Rules
│   └── static/                 # CSS/JS Assets, Logos & Branding
│
├── backend/                    # Core Flask Microservice
│   ├── controllers/            # API Controllers (Auth, Project, Bid, Chat, Payment)
│   ├── routes/                 # Flask Blueprints & Route Definitions
│   ├── services/               # Database Queries & Business Logic
│   ├── utils/                  # Auth Decorators, Input Validators, API Responses
│   ├── models.py               # SQLAlchemy ORM Database Schemas
│   ├── app.py                  # Flask Application Factory
│   ├── config.py               # Environment & Database Configuration
│   ├── extensions.py           # SQLAlchemy, JWT, Bcrypt & CORS Setup
│   ├── blocklist.py            # JWT Token Revocation Registry
│   └── schema.sql              # Database DDL Schema Script
│
├── netlify/                    # Netlify Serverless Function Config
│   └── functions/
│       ├── app.py              # WSGI Serverless Gateway Handler
│       └── requirements.txt    # Netlify Function Dependencies
│
├── .gitignore                  # Git Exclusion Rules
├── netlify.toml                # Netlify Deployment Configuration
├── README.md                   # Project Documentation
├── requirements.txt            # Root Dependencies Manifest
└── runtime.txt                 # Python Runtime Specification (3.11)
```

---

## 🛠️ Key Features

* **JWT Authentication**: User login/registration with role-based access control (`client`, `freelancer`, `admin`).
* **Project Management**: Clients can post projects, view incoming bids, manage project status, and award contracts.
* **Bidding System**: Freelancers can browse open projects and submit competitive proposals.
* **Messaging & Chat**: Real-time project communication between clients and freelancers.
* **Payment & Escrow Tracking**: Manage payment milestones and status (`pending`, `paid`, `cancelled`).
* **Reviews & Ratings**: Mutual rating and review system post project completion.
* **Admin Control Panel**: System administration dashboard for platform monitoring.

---

## ⚡ Quick Start (Local Development)

```bash
# 1. Clone the repository
git clone https://github.com/Raviteja-864/Freelancer-Project-Estimator.git
cd Freelancer-Project-Estimator

# 2. Set up virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp backend/.env.example backend/.env

# 5. Run the Flask application
python backend/app.py
```

Open **http://localhost:5000** in your browser to access the application locally.

---

## 🌐 Deployment (Netlify)

This project is configured for automated build and deployment on **Netlify**:

* **Publish Directory**: `public`
* **Build Command**: Auto-detected via `netlify.toml`
* **Live Site**: [https://freelancerestimator.netlify.app/](https://freelancerestimator.netlify.app/)
