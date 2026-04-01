# 🛡️ HackArena – CTF Competition Platform

HackArena is a full-featured web-based Capture The Flag (CTF) platform designed for hosting cybersecurity competitions. It supports individual and team participation, real-time scoring, challenge management, JWT authentication, and OTP-based email verification.

---

## 🚀 Features

### 🔐 Authentication & Security
- JWT-based authentication (Access + Refresh tokens)
- Email OTP verification during registration
- Account activation after OTP verification
- Rate-limited OTP attempts (2 attempts → 1 min lock)
- Django password validation
- CORS protection
- Secure middleware headers

### 👥 User & Team System
- User registration & login
- User profiles with score tracking
- Create / Join / Leave teams
- Team invite codes
- Team-based scoring

### 🧩 Challenges
- Categorized challenges (Web, Crypto, etc.)
- Difficulty levels (Easy → Insane)
- Dynamic scoring
- Flag validation system
- Hint unlock system with cost deduction
- Admin challenge management

### 📊 Scoreboard
- Real-time user leaderboard
- Team leaderboard
- Points calculated dynamically

---

## 🏗️ Architecture

### Backend
- Django 4.2
- Django REST Framework
- JWT (SimpleJWT)
- SQLite (development)
- Email OTP verification
- Gunicorn (production-ready)

### Frontend
- Go (net/http)
- HTML templates
- API proxy system
- Secure cookie-based JWT storage

### Database
- SQLite (default)
- Easily switchable to PostgreSQL

---

## 📁 Project Structure

```
HackArena/
│
├── backend/
│   ├── users/
│   ├── teams/
│   ├── challenges/
│   ├── submissions/
│   ├── requirements.txt
│   └── manage.py
│
├── frontend/
│   ├── handlers/
│   ├── templates/
│   └── main.go
│
└── README.md
```

---

## ⚙️ Setup Guide (Without Docker)

### 📌 Requirements
- Python 3.10+
- Go 1.20+

---

## 🔹 1️⃣ Clone Repository

```bash
git clone https://github.com/karankalawant/CTF.git
cd CTF
```

---

## 🔹 2️⃣ Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Backend runs at:

```
http://localhost:8000
```

Admin panel:

```
http://localhost:8000/admin
```

---

## 🔹 3️⃣ Frontend Setup

Open new terminal:

```bash
cd frontend
go mod tidy
go run .
```

Frontend runs at:

```
http://localhost:3000
```

---

## 🔐 OTP Registration Flow

1. User registers
2. OTP is generated and sent via email (console backend in dev)
3. User verifies OTP
4. Account activated
5. JWT tokens issued

Security:
- OTP expires in 5 minutes
- 2 wrong attempts → locked for 1 minute

---

## 🛡️ Security Features

- JWT authentication
- Access/Refresh token system
- Rate-limited OTP attempts
- Account inactive until verified
- CORS restrictions
- Secure cookies (HttpOnly)
- Middleware security headers

---

## 🔧 Environment Variables (Optional)

Create `backend/.env`:

```
SECRET_KEY=your-secret-key
DEBUG=True
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

---

## 🚀 Production Recommendations

- Switch SQLite → PostgreSQL
- Set DEBUG=False
- Use secure SECRET_KEY
- Configure proper SMTP backend
- Deploy with Gunicorn + Nginx
- Enable HTTPS

---

## 📈 Future Improvements

- WebSocket live scoreboard
- SMS OTP support
- Two-factor login
- Docker deployment
- Event start/end locking
- Admin analytics dashboard

---

## 👨‍💻 Author

Aryan Tembhurne  
HackArena CTF Platform Project  

---

## 🏆 License

This project is developed for educational and cybersecurity competition purposes.