package middleware

import (
	"log"
	"net/http"
	"time"
)

func Logger(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		log.Printf("%s %s %v", r.Method, r.URL.Path, time.Since(start))
	})
}

func SecurityHeaders(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// ─── Clickjacking ───
		w.Header().Set("X-Frame-Options", "DENY")

		// ─── MIME Sniffing ───
		w.Header().Set("X-Content-Type-Options", "nosniff")

		// ─── XSS Protection (legacy fallback) ───
		w.Header().Set("X-XSS-Protection", "1; mode=block")

		// ─── Content Security Policy ───
		w.Header().Set("Content-Security-Policy",
			"default-src 'self'; "+
				"script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "+
				"style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "+
				"font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "+
				"img-src 'self' data: https:; "+
				"connect-src 'self' http://localhost:8000 https://restcountries.com; "+
				"frame-ancestors 'none'; "+
				"base-uri 'self'; "+
				"form-action 'self';")

		// ─── HSTS (Force HTTPS) ───
		w.Header().Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains")

		// ─── Referrer Policy ───
		w.Header().Set("Referrer-Policy", "strict-origin-when-cross-origin")

		// ─── Permissions Policy ───
		w.Header().Set("Permissions-Policy",
			"camera=(), microphone=(), geolocation=(), payment=(), usb=()")

		next.ServeHTTP(w, r)
	})
}
