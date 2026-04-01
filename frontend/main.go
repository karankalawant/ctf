package main

import (
	"log"
	"net/http"
	"os"

	"ctf-frontend/handlers"
	"ctf-frontend/middleware"
)

func main() {

	apiURL := os.Getenv("API_URL")
	if apiURL == "" {
		apiURL = "http://localhost:8000"
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "3000"
	}

	handlers.SetAPIURL(apiURL)

	mux := http.NewServeMux()

	// =========================
	// Static files
	// =========================
	mux.Handle("/static/", http.StripPrefix("/static/", http.FileServer(http.Dir("./static"))))

	// =========================
	// Page Routes
	// =========================
	mux.HandleFunc("/", handlers.HomeHandler)
	mux.HandleFunc("/login", handlers.LoginHandler)
	mux.HandleFunc("/register", handlers.RegisterHandler)
	mux.HandleFunc("/verify-otp", handlers.VerifyOTPHandler) // ✅ ADDED OTP ROUTE
	mux.HandleFunc("/logout", handlers.LogoutHandler)

	mux.HandleFunc("/challenges", handlers.ChallengesHandler)
	mux.HandleFunc("/challenges/", handlers.ChallengeDetailHandler)

	mux.HandleFunc("/scoreboard", handlers.ScoreboardHandler)

	mux.HandleFunc("/teams", handlers.TeamsHandler)
	mux.HandleFunc("/teams/create", handlers.TeamCreateHandler)
	mux.HandleFunc("/teams/join", handlers.TeamJoinHandler)
	mux.HandleFunc("/teams/leave", handlers.TeamLeaveHandler)

	mux.HandleFunc("/profile", handlers.ProfileHandler)
	mux.HandleFunc("/api/profile/update", handlers.ProfileUpdateHandler)
	mux.HandleFunc("/users/", handlers.UserDetailHandler)

	// =========================
	// API Proxies (JS Fetch Calls)
	// =========================
	mux.HandleFunc("/api/submit/", handlers.SubmitFlagHandler)
	mux.HandleFunc("/api/hint/", handlers.UnlockHintHandler)
	mux.HandleFunc("/api/challenges/", handlers.APIChallengesProxy)
	mux.HandleFunc("/api/scoreboard/", handlers.APIScoreboardProxy)

	// =========================
	// Middleware
	// =========================
	handler := middleware.Logger(middleware.SecurityHeaders(mux))

	log.Printf("🚀 CTF Frontend → http://localhost:%s  (API: %s)", port, apiURL)

	log.Fatal(http.ListenAndServe(":"+port, handler))
}