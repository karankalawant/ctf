package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
)

func ScoreboardHandler(w http.ResponseWriter, r *http.Request) {
	pd := newPage(r, "Scoreboard")
	token := getToken(r)

	ub, _, _ := apiGet("/api/scoreboard/users/", token)
	tb, _, _ := apiGet("/api/scoreboard/teams/", token)

	var users, teams []map[string]interface{}
	json.Unmarshal(ub, &users)
	json.Unmarshal(tb, &teams)

	pd.Data = map[string]interface{}{"users": users, "teams": teams}
	renderTemplate(w, "scoreboard.html", pd)
}

func TeamsHandler(w http.ResponseWriter, r *http.Request) {
	pd := newPage(r, "Teams")
	token := getToken(r)

	body, _, err := apiGet("/api/teams/", token)
	if err != nil {
		pd.Error = "Failed to load teams"
		renderTemplate(w, "teams.html", pd)
		return
	}
	var teams []map[string]interface{}
	json.Unmarshal(body, &teams)

	var myTeam map[string]interface{}
	if token != "" {
		mb, _, _ := apiGet("/api/teams/my/", token)
		var myResp map[string]interface{}
		json.Unmarshal(mb, &myResp)
		if t, ok := myResp["team"]; ok && t != nil {
			myTeam, _ = t.(map[string]interface{})
		}
	}
	pd.Data = map[string]interface{}{"teams": teams, "my_team": myTeam}
	renderTemplate(w, "teams.html", pd)
}

func TeamCreateHandler(w http.ResponseWriter, r *http.Request) {
	pd := newPage(r, "Create Team")
	if getToken(r) == "" {
		http.Redirect(w, r, "/login", http.StatusSeeOther)
		return
	}
	if r.Method == "POST" {
		r.ParseForm()
		maxMembers := 5
		if mm := r.FormValue("max_members"); mm != "" {
			fmt.Sscanf(mm, "%d", &maxMembers)
		}
		body, code, err := apiPost("/api/teams/create/", getToken(r), map[string]interface{}{
			"name": r.FormValue("name"), "description": r.FormValue("description"), "max_members": maxMembers,
		})
		if err != nil || code != 201 {
			pd.Error = "Failed to create team"
			if err == nil {
				var e map[string]interface{}
				json.Unmarshal(body, &e)
				if msg, ok := e["error"].(string); ok { pd.Error = msg }
				if msgs, ok := e["name"].([]interface{}); ok && len(msgs) > 0 { pd.Error = msgs[0].(string) }
			}
			renderTemplate(w, "team_create.html", pd)
			return
		}
		http.Redirect(w, r, "/teams", http.StatusSeeOther)
		return
	}
	renderTemplate(w, "team_create.html", pd)
}

func TeamJoinHandler(w http.ResponseWriter, r *http.Request) {
	if token := getToken(r); token != "" && r.Method == "POST" {
		r.ParseForm()
		apiPost("/api/teams/join/", token, map[string]string{"invite_code": r.FormValue("invite_code")})
	}
	http.Redirect(w, r, "/teams", http.StatusSeeOther)
}

func TeamLeaveHandler(w http.ResponseWriter, r *http.Request) {
	if token := getToken(r); token != "" {
		apiPost("/api/teams/leave/", token, nil)
	}
	http.Redirect(w, r, "/teams", http.StatusSeeOther)
}

func UserDetailHandler(w http.ResponseWriter, r *http.Request) {
	username := strings.TrimSuffix(strings.TrimPrefix(r.URL.Path, "/users/"), "/")
	if username == "" {
		http.Redirect(w, r, "/scoreboard", http.StatusSeeOther)
		return
	}
	pd := newPage(r, username)
	body, code, err := apiGet("/api/auth/users/"+username+"/", getToken(r))
	if err != nil || code == 404 {
		http.NotFound(w, r)
		return
	}
	var user map[string]interface{}
	json.Unmarshal(body, &user)
	pd.Data = user
	renderTemplate(w, "user_detail.html", pd)
}
