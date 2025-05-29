import os
from dotenv import load_dotenv
from flask import Flask, request, redirect, jsonify, render_template, session, url_for
import requests
from datetime import datetime, timedelta
from diet_recommendation import analyze_and_recommend
from ml_model import recommend_workout  # Import the workout recommendation function
from ml_model import predict_recommendations

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# Google API Credentials from environment variables
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:5000/callback"
TOKEN_URL = "https://oauth2.googleapis.com/token"
FITNESS_URL = "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate"

SCOPES = [
    "https://www.googleapis.com/auth/fitness.activity.read",
    "https://www.googleapis.com/auth/fitness.body.read"
]

# Temporary user profile store
user_profiles = {}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login")
def login():
    auth_url = (
        "https://accounts.google.com/o/oauth2/auth?"
        f"client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&response_type=code"
        "&scope=https://www.googleapis.com/auth/fitness.activity.read https://www.googleapis.com/auth/fitness.body.read email profile"
        "&access_type=offline"
        "&prompt=consent"
    )
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return redirect(url_for("home"))

    data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    token_response = requests.post(TOKEN_URL, data=data)
    tokens = token_response.json()

    if "access_token" not in tokens:
        return "Login failed", 400

    session["ACCESS_TOKEN"] = tokens["access_token"]
    session["REFRESH_TOKEN"] = tokens.get("refresh_token")

    user_info = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    ).json()

    email = user_info.get("email")
    session["EMAIL"] = email

    if email not in user_profiles:
        return redirect(url_for("setup_profile"))

    return redirect(url_for("dashboard"))

@app.route("/setup_profile", methods=["GET", "POST"])
def setup_profile():
    if request.method == "POST":
        email = session.get("EMAIL")
        if not email:
            return redirect(url_for("login"))

        user_profiles[email] = {
            "name": request.form.get("name"),
            "age": int(request.form.get("age")),
            "target": request.form.get("target"),
            "activity_level": request.form.get("activity_level"),
            "weight": float(request.form.get("weight")),
            "height": float(request.form.get("height"))
        }

        # Redirect to the dashboard after saving the profile
        return redirect(url_for("dashboard"))

    return render_template("setup_profile.html")

@app.route("/dashboard")
def dashboard():
    email = session.get("EMAIL")
    if not email:
        return redirect(url_for("login"))
    profile = user_profiles.get(email)
    return render_template("dashboard.html", profile=profile)

@app.route("/profile")
def profile():
    email = session.get("EMAIL")
    profile = user_profiles.get(email)
    return render_template("profile.html", profile=profile)

@app.route("/steps")
def steps():
    return render_template("steps.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/api/fitness")
def get_fitness_data():
    access_token = session.get("ACCESS_TOKEN")
    if not access_token:
        return jsonify({"error": "User not authenticated"}), 401

    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)

    request_body = {
        "aggregateBy": [
            {"dataTypeName": "com.google.step_count.delta"},
            {"dataTypeName": "com.google.weight"},
            {"dataTypeName": "com.google.height"},
            {"dataTypeName": "com.google.calories.expended"}
        ],
        "bucketByTime": {"durationMillis": 86400000},
        "startTimeMillis": start_time,
        "endTimeMillis": end_time
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(FITNESS_URL, headers=headers, json=request_body)
    data = response.json()

    steps, calories = [], []
    weight = height = None

    for bucket in data.get("bucket", []):
        for dataset in bucket.get("dataset", []):
            for point in dataset.get("point", []):
                dtype = point.get("dataTypeName")
                value = point["value"][0]
                if dtype == "com.google.step_count.delta":
                    steps.append(value.get("intVal", 0))
                elif dtype == "com.google.calories.expended":
                    calories.append(value.get("fpVal", 0.0))
                elif dtype == "com.google.weight":
                    weight = value.get("fpVal")
                elif dtype == "com.google.height":
                    height = value.get("fpVal")

    return jsonify({
        "total_steps": sum(steps),
        "daily_steps": steps,
        "total_calories_burned": sum(calories),
        "daily_calories_burned": calories,
        "weight": weight,
        "height": height
    })

@app.route("/diet_planner")
def diet_planner():
    email = session.get("EMAIL")
    if not email:
        return redirect(url_for("login"))

    profile = user_profiles.get(email)
    if not profile:
        return redirect(url_for("setup_profile"))

    # Simulate Google Fit data for demo purposes
    fitness_data = {
        "total_steps": 8500,
        "total_calories_burned": 2200,
        "weight": profile["weight"],
        "height": profile["height"],
        "target": profile["target"],
        "activity_level": profile["activity_level"]
    }

    diet = analyze_and_recommend(fitness_data)
    return render_template("diet_planner.html", diet=diet)

@app.route("/workout_planner")
def workout_planner():
    email = session.get("EMAIL")
    if not email:
        return redirect(url_for("login"))

    profile = user_profiles.get(email)
    if not profile:
        return redirect(url_for("setup_profile"))

    # Generate a workout plan based on the user's profile
    workout_plan = recommend_workout(profile)

    # Pass the workout plan to the recommendations.html template
    return render_template("recommendations.html", recommendations={"workout": workout_plan})

@app.route("/recommendations")
def recommendations():
    email = session.get("EMAIL")
    if not email:
        return redirect(url_for("login"))

    profile = user_profiles.get(email)
    if not profile:
        return redirect(url_for("setup_profile"))

    # Generate recommendations (diet and workout)
    recommendations = predict_recommendations(profile)
    return render_template("recommendations.html", recommendations=recommendations)

def refresh_access_token():
    if "REFRESH_TOKEN" in session:
        refresh_data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": session["REFRESH_TOKEN"],
            "grant_type": "refresh_token"
        }
        response = requests.post(TOKEN_URL, data=refresh_data)
        new_tokens = response.json()
        if "access_token" in new_tokens:
            session["ACCESS_TOKEN"] = new_tokens["access_token"]
            return True
    return False

if __name__ == "__main__":
    app.run(debug=True)
