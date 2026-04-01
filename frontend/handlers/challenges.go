package handlers

import (
	"encoding/json"
	"net/http"
	"strings"
)

func HomeHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		http.NotFound(w, r)
		return
	}
	renderTemplate(w, "home.html", newPage(r, "Home"))
}

func ChallengesHandler(w http.ResponseWriter, r *http.Request) {
	pd := newPage(r, "Challenges")
	token := getToken(r)

	catBody, _, _ := apiGet("/api/challenges/categories/", token)
	var cats []map[string]interface{}
	json.Unmarshal(catBody, &cats)

	q := r.URL.Query()
	path := "/api/challenges/?"
	if cat := q.Get("category"); cat != "" {
		path += "category=" + cat + "&"
	}
	if diff := q.Get("difficulty"); diff != "" {
		path += "difficulty=" + diff + "&"
	}

	body, _, err := apiGet(path, token)
	if err != nil {
		pd.Error = "Failed to load challenges"
		renderTemplate(w, "challenges.html", pd)
		return
	}
	var challenges []map[string]interface{}
	json.Unmarshal(body, &challenges)

	pd.Data = map[string]interface{}{
		"challenges":  challenges,
		"categories":  cats,
		"filter_cat":  q.Get("category"),
		"filter_diff": q.Get("difficulty"),
	}
	renderTemplate(w, "challenges.html", pd)
}

func ChallengeDetailHandler(w http.ResponseWriter, r *http.Request) {
	id := strings.TrimPrefix(r.URL.Path, "/challenges/")
	id = strings.TrimSuffix(id, "/")
	if id == "" {
		http.Redirect(w, r, "/challenges", http.StatusSeeOther)
		return
	}

	pd := newPage(r, "Challenge")
	token := getToken(r)

	body, code, err := apiGet("/api/challenges/"+id+"/", token)
	if err != nil || code == 404 {
		http.NotFound(w, r)
		return
	}

	var challenge map[string]interface{}
	json.Unmarshal(body, &challenge)
	if t, ok := challenge["title"].(string); ok {
		pd.Title = t + " | HackArena CTF"
	}

	if r.Method == "POST" && token != "" {
		r.ParseForm()
		flag := r.FormValue("flag")
		rb, _, serr := apiPost("/api/submissions/"+id+"/submit/", token, map[string]string{"flag": flag})
		if serr == nil {
			var res map[string]interface{}
			json.Unmarshal(rb, &res)
			if correct, ok := res["correct"].(bool); ok && correct {
				pd.Success = res["message"].(string)
				if fb, ok := res["first_blood"].(bool); ok && fb {
					pd.Success += " 🩸 FIRST BLOOD!"
				}
			} else if msg, ok := res["message"].(string); ok {
				pd.Error = msg
			} else if msg, ok := res["error"].(string); ok {
				pd.Error = msg
			}
		}
	}

	pd.Data = challenge
	renderTemplate(w, "challenge_detail.html", pd)
}

func SubmitFlagHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "Method not allowed", 405)
		return
	}
	token := getToken(r)
	if token == "" {
		http.Error(w, `{"error":"Unauthorized"}`, 401)
		return
	}
	id := strings.TrimPrefix(r.URL.Path, "/api/submit/")
	id = strings.TrimSuffix(id, "/")

	var payload map[string]string
	json.NewDecoder(r.Body).Decode(&payload)

	body, code, err := apiPost("/api/submissions/"+id+"/submit/", token, payload)
	if err != nil {
		http.Error(w, `{"error":"API error"}`, 500)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	w.Write(body)
}

func UnlockHintHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "Method not allowed", 405)
		return
	}
	token := getToken(r)
	if token == "" {
		http.Error(w, `{"error":"Unauthorized"}`, 401)
		return
	}
	id := strings.TrimPrefix(r.URL.Path, "/api/hint/")
	id = strings.TrimSuffix(id, "/")

	body, code, err := apiPost("/api/challenges/hints/"+id+"/unlock/", token, nil)
	if err != nil {
		http.Error(w, `{"error":"API error"}`, 500)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	w.Write(body)
}
