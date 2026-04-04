package handlers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"html/template"
	"io"
	"net/http"
)

var apiURL string

func SetAPIURL(u string) { apiURL = u }

func apiGet(path, token string) ([]byte, int, error) {
	req, err := http.NewRequest("GET", apiURL+path, nil)
	if err != nil {
		return nil, 0, err
	}
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, 0, err
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	return body, resp.StatusCode, err
}

func apiPost(path, token string, payload interface{}) ([]byte, int, error) {
	var bodyReader io.Reader
	if payload != nil {
		data, err := json.Marshal(payload)
		if err != nil {
			return nil, 0, err
		}
		bodyReader = bytes.NewBuffer(data)
	}
	req, err := http.NewRequest("POST", apiURL+path, bodyReader)
	if err != nil {
		return nil, 0, err
	}
	req.Header.Set("Content-Type", "application/json")
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, 0, err
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	return body, resp.StatusCode, err
}

func getToken(r *http.Request) string {
	c, err := r.Cookie("ctf_access")
	if err != nil {
		return ""
	}
	return c.Value
}

func getUsername(r *http.Request) string {
	c, err := r.Cookie("ctf_username")
	if err != nil {
		return ""
	}
	return c.Value
}

func isAdmin(r *http.Request) bool {
	c, err := r.Cookie("ctf_admin")
	if err != nil {
		return false
	}
	return c.Value == "1"
}

func setAuthCookies(w http.ResponseWriter, access, refresh, username string, admin bool) {
	maxAge := 86400 * 7

	http.SetCookie(w, &http.Cookie{
		Name:     "ctf_access",
		Value:    access,
		Path:     "/",
		MaxAge:   maxAge,
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
	})

	http.SetCookie(w, &http.Cookie{
		Name:     "ctf_refresh",
		Value:    refresh,
		Path:     "/",
		MaxAge:   maxAge,
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
	})

	http.SetCookie(w, &http.Cookie{
		Name:     "ctf_username",
		Value:    username,
		Path:     "/",
		MaxAge:   maxAge,
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
	})

	av := "0"
	if admin {
		av = "1"
	}

	http.SetCookie(w, &http.Cookie{
		Name:     "ctf_admin",
		Value:    av,
		Path:     "/",
		MaxAge:   maxAge,
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
	})
}

func clearAuthCookies(w http.ResponseWriter) {
	http.SetCookie(w, &http.Cookie{Name: "ctf_access", Path: "/", MaxAge: -1})
	http.SetCookie(w, &http.Cookie{Name: "ctf_refresh", Path: "/", MaxAge: -1})
	http.SetCookie(w, &http.Cookie{Name: "ctf_username", Path: "/", MaxAge: -1})
	http.SetCookie(w, &http.Cookie{Name: "ctf_admin", Path: "/", MaxAge: -1})
}

type PageData struct {
	Title    string
	Username string
	IsAdmin  bool
	Token    string
	Data     interface{}
	Error    string
	Success  string
}

func newPage(r *http.Request, title string) PageData {
	return PageData{
		Title:    fmt.Sprintf("%s | HackArena CTF", title),
		Username: getUsername(r),
		IsAdmin:  isAdmin(r),
		Token:    getToken(r),
	}
}

var tmplFuncs = template.FuncMap{
	"safeHTML": func(s string) template.HTML { return template.HTML(s) },
	"add":      func(a, b int) int { return a + b },
}

func renderTemplate(w http.ResponseWriter, tmpl string, data interface{}) {
	t, err := template.New("base").Funcs(tmplFuncs).ParseFiles(
		"templates/base.html",
		"templates/"+tmpl,
	)
	if err != nil {
		http.Error(w, "Template error: "+err.Error(), 500)
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	if err := t.ExecuteTemplate(w, "base", data); err != nil {
		http.Error(w, "Render error: "+err.Error(), 500)
	}
}

func proxyAPIGet(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Path
	if r.URL.RawQuery != "" {
		path += "?" + r.URL.RawQuery
	}
	body, status, err := apiGet(path, getToken(r))
	if err != nil {
		http.Error(w, "API error", 500)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	w.Write(body)
}

// Generic API proxy for frontend JS fetch calls
func APIChallengesProxy(w http.ResponseWriter, r *http.Request) {
	proxyAPIGet(w, r)
}

func APIScoreboardProxy(w http.ResponseWriter, r *http.Request) {
	proxyAPIGet(w, r)
}

func apiPut(path, token string, payload interface{}) ([]byte, int, error) {
    data, err := json.Marshal(payload)
    if err != nil {
        return nil, 0, err
    }
    req, err := http.NewRequest("PUT", apiURL+path, bytes.NewBuffer(data))
    if err != nil {
        return nil, 0, err
    }
    req.Header.Set("Content-Type", "application/json")
    if token != "" {
        req.Header.Set("Authorization", "Bearer "+token)
    }
    resp, err := http.DefaultClient.Do(req)
    if err != nil {
        return nil, 0, err
    }
    defer resp.Body.Close()
    body, err := io.ReadAll(resp.Body)
    return body, resp.StatusCode, err
}