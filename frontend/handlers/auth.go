package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
)

// =======================
// LOGIN
// =======================

func LoginHandler(w http.ResponseWriter, r *http.Request) {
	pd := newPage(r, "Login")

	if r.Method == "POST" {
		r.ParseForm()

		body, code, err := apiPost("/api/auth/login/", "", map[string]string{
			"username": r.FormValue("username"),
			"password": r.FormValue("password"),
		})

		if err != nil || code != 200 {
			pd.Error = "Invalid credentials"
			renderTemplate(w, "login.html", pd)
			return
		}

		var resp struct {
			Access  string `json:"access"`
			Refresh string `json:"refresh"`
			User struct {
				Username string `json:"username"`
				IsStaff  bool   `json:"is_staff"`
			} `json:"user"`
		}

		json.Unmarshal(body, &resp)

		setAuthCookies(w, resp.Access, resp.Refresh, resp.User.Username, resp.User.IsStaff)

		http.Redirect(w, r, "/challenges", http.StatusSeeOther)
		return
	}

	renderTemplate(w, "login.html", pd)
}


// =======================
// REGISTER (NOW WITH OTP)
// =======================

func RegisterHandler(w http.ResponseWriter, r *http.Request) {
	pd := newPage(r, "Register")

	if r.Method == "POST" {
		r.ParseForm()

		body, code, err := apiPost("/api/auth/register/", "", map[string]string{
			"username":         r.FormValue("username"),
			"email":            r.FormValue("email"),
			"password":         r.FormValue("password"),
			"password_confirm": r.FormValue("password_confirm"),
			"country":          r.FormValue("country"),
		})

		if err != nil || code != 201 {
			// Parse the validation errors from Django DRF
			var errMap map[string]interface{}
			if err := json.Unmarshal(body, &errMap); err == nil && len(errMap) > 0 {
				// Grab the first error message
				for field, msgs := range errMap {
					if msgList, ok := msgs.([]interface{}); ok && len(msgList) > 0 {
						if strMsg, ok := msgList[0].(string); ok {
							pd.Error = fmt.Sprintf("%s: %s", field, strMsg)
							break
						}
					} else if strMsg, ok := msgs.(string); ok {
						pd.Error = strMsg
						break
					}
				}
			}
			if pd.Error == "" {
				pd.Error = "Registration failed: Invalid input or user already exists"
			}
			renderTemplate(w, "register.html", pd)
			return
		}

		// Backend now returns message + user_id (NOT tokens)
		var resp struct {
			Message string `json:"message"`
			UserID  int    `json:"user_id"`
		}

		json.Unmarshal(body, &resp)

		// Redirect to OTP verification page
		http.Redirect(w, r, fmt.Sprintf("/verify-otp?user_id=%d", resp.UserID), http.StatusSeeOther)
		return
	}

	renderTemplate(w, "register.html", pd)
}


// =======================
// VERIFY OTP
// =======================

func VerifyOTPHandler(w http.ResponseWriter, r *http.Request) {
	pd := newPage(r, "Verify OTP")

	userID := r.URL.Query().Get("user_id")

	if r.Method == "POST" {
		r.ParseForm()

		body, code, err := apiPost("/api/auth/verify-otp/", "", map[string]string{
			"user_id": userID,
			"otp":     r.FormValue("otp"),
		})

		if err != nil || code != 200 {
			pd.Error = "Invalid or expired OTP"
			renderTemplate(w, "verify_otp.html", pd)
			return
		}

		var resp struct {
			Access  string `json:"access"`
			Refresh string `json:"refresh"`
			Message string `json:"message"`
		}

		json.Unmarshal(body, &resp)

		// Now set cookies AFTER verification
		setAuthCookies(w, resp.Access, resp.Refresh, "", false)

		http.Redirect(w, r, "/challenges", http.StatusSeeOther)
		return
	}

	renderTemplate(w, "verify_otp.html", pd)
}


// =======================
// LOGOUT
// =======================

func LogoutHandler(w http.ResponseWriter, r *http.Request) {
	if t := getToken(r); t != "" {
		apiPost("/api/auth/logout/", t, nil)
	}
	clearAuthCookies(w)
	http.Redirect(w, r, "/", http.StatusSeeOther)
}


// =======================
// PROFILE
// =======================

func ProfileHandler(w http.ResponseWriter, r *http.Request) {
	pd := newPage(r, "Profile")

	token := getToken(r)
	if token == "" {
		http.Redirect(w, r, "/login", http.StatusSeeOther)
		return
	}

	body, code, err := apiGet("/api/auth/profile/", token)
	if err != nil || code != 200 {
		clearAuthCookies(w)
		http.Redirect(w, r, "/login", http.StatusSeeOther)
		return
	}

	var profile map[string]interface{}
	json.Unmarshal(body, &profile)

	pd.Data = profile
	renderTemplate(w, "profile.html", pd)
}

func ProfileUpdateHandler(w http.ResponseWriter, r *http.Request) {
    token := getToken(r)
    if token == "" {
        http.Error(w, `{"error":"Unauthorized"}`, 401)
        return
    }
    var payload map[string]interface{}
    json.NewDecoder(r.Body).Decode(&payload)
    body, code, err := apiPut("/api/auth/profile/", token, payload)
    if err != nil {
        http.Error(w, `{"error":"API error"}`, 500)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(code)
    w.Write(body)
}