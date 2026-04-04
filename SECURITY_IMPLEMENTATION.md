# HackArena CTF - Security Implementations

This document outlines all security hardening features currently implemented across the Django backend and Go frontend of the HackArena CTF platform.

## 1. Environment Variable Management (The `.env` file)
Instead of forcing you to export the App Password or secret key via terminal every time, the application now securely uses a `.env` file!

**How to use it:**
At the root of your `backend/` directory, create a `.env` file (this file never gets pushed to git since it's in `.gitignore`) and define:
```properties
SECRET_KEY=your-django-insecure-secret-key...
DEBUG=True
EMAIL_HOST_PASSWORD=otxi oujb kqoh mmne
```
The Django application automatically loads these via the `python-dotenv` package into `os.environ` upon startup. No need to export anything in your terminal!

---

## 2. Authentication & Session Security
* **JWT Tokens (`simplejwt`)**: Short-lived Access Tokens (reduced to critically short **10 minutes** to minimize impact on token theft) and 7-day Refresh Tokens, stored securely by the Go frontend. Both use rotation and are automatically blacklisted upon rotation or explicit logout.
* **Account Lockout Control**: If an attacker fails to log in 5 times continuously, the account username triggers a **15-minute temporary lockout**.
* **IP + User-Agent Tracking**: Implemented via a `LoginAttempt` logging engine which tracks where a user tries to authenticate from.

## 3. Web Attack Protections
* **SQL Injection**: We fully map all database interactions strictly using the Django ORM bindings, stopping SQL injections.
* **Cross-Site Scripting (XSS)**: 
  - Restored proper sanitization on Go Templates by replacing raw `safeHTML(...)` bypasses with strict `html/template.HTML`.
  - Added X-XSS-Protection `1; mode=block` headers in responses.
* **CSRF (Cross-Site Request Forgery)**: Added `CSRF_TRUSTED_ORIGINS` for cross-origins and enabled CSRF token checks across Django configurations.
* **Clickjacking**: Blocked via headers (`X-Frame-Options: DENY` and CSP `frame-ancestors 'none'`) making it impossible for other sites to `<iframe>` the application for phishing.

## 4. OTP Bruteforce Protections
* **SHA-256 Hashing**: OTPs are no longer stored in the Database as plain text. Instead, we hash the 6-digit code via SHA-256 upon generation.
* **Verification Rate-Limits & Expiration**: 
  - OTPs completely expire in strictly 5 minutes.
  - A user gets **max 3 attempts** at guessing an active OTP. Failing 3 times triggers an OTP lock, forcing the user to re-generate an entirely new verification procedure.

## 5. Security Middlewares & Headers
Added dedicated `SecurityHeadersMiddleware` (Django) and `SecurityHeaders` (Go) modifying responses globally:
* **HSTS (Strict-Transport-Security)**: `max-age=31536000; includeSubDomains`. Enforces absolute HTTPS communication over 12 months.
* **CSP (Content-Security-Policy)**: Only allowed to execute internal logic, or trusted external scripts (e.g. CDNs like Cloudflare/jsDelivr), mitigating harmful injected code.
* **Referrer Policy**: `strict-origin-when-cross-origin`
* **MIME Sniffing Prevention**: `X-Content-Type-Options: nosniff`.
* **Hardware Restrictions (Permissions-Policy)**: Restricts the webpage from requesting mic, camera, usb, payment features automatically.

## 6. Endpoints Rate Limiting (Abuse Prevention)
Used DRF `AnonRateThrottle` & `UserRateThrottle` effectively:
* **Login Endpoints**: `5 requests/minute` (IP Based).
* **Register/SignUp**: `3 requests/minute` (IP Based).
* **OTP Verification**: `5 requests/minute` (IP Based).
* **Global Unknown endpoints**: Defaults to 30 requests/minute.

## 7. Cookie Hardening
Go Auth cookies (`ctf_access`, `ctf_refresh`, `ctf_username`, and `ctf_admin`) now enforce:
* `HttpOnly` flag: Completely prevents JS logic from accessing the credentials via `document.cookie`.
* `SameSite=Lax`: Restricts sending cookies together with third-party domain requests.

## 8. Password Strength & Structure Restrictions
We integrated strong hashing, moving beyond default configurations:
* **Hashing Factorization**: **Argon2** is currently primary (via `django.contrib.auth.hashers.Argon2PasswordHasher`), gracefully falling back to PBKDF2/Bcrypt when strictly necessary.
* Strong Password complexities are now enforced on the backend Serializers (Min. length 8, Max 128 + Must contain combinations of Uppercase, Lowercase, Digit, and distinct Special Character identifiers).

## 9. Security Logging & Auditing (`security.log`)
Added `security_logger`, tracking:
* Valid Login flows vs Login failures & Triggers of temporary lockouts `(Event: LOCKOUT)`.
* Suspicious requests: Checks incoming traffic for `UNION SELECT`, `../` traversing, and `<script` payloads natively within `RequestMonitorMiddleware`.
* Fake form field (A hidden generic `website` text input for bots to accidentally fill out). Identifying this payload rejects the user with a silent success (Flagging the event internally as `HONEYPOT`).
* These logs pipe securely to your Django Admin Console (`SecurityLog` entity model).

---
## How To Start Services Now?
Because `.env` handles the secrets automatically, your local start workflow is strictly:

**Terminal 1 (Backend):**
```bash
cd backend
source venv/bin/activate
python manage.py runserver
```

**Terminal 2 (Frontend):**
```bash
cd frontend
go run .
```
