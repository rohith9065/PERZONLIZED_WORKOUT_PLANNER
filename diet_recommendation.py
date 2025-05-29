from flask import Flask, request, redirect, jsonify, render_template, session, url_for
from datetime import datetime, timedelta
import requests

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# Google API Credentials
CLIENT_ID = "620527182020-m20qmmc2b7mohm12redh7egdn5bb5pq5.apps.googleusercontent.com"
CLIENT_SECRET = "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"
REDIRECT_URI = "http://localhost:5000/callback"
TOKEN_URL = "https://oauth2.googleapis.com/token"
FITNESS_URL = "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate"

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

    # Dummy profile if not exists
    if email not in user_profiles:
        user_profiles[email] = {
            "weight": 70,
            "height": 175,
            "target": "fit",
            "activity_level": "moderate"
        }

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

        return redirect(url_for("dashboard"))

    return render_template("setup_profile.html")

@app.route("/dashboard")
def dashboard():
    email = session.get("EMAIL")
    if not email:
        return redirect(url_for("login"))
    profile = user_profiles.get(email)
    return render_template("dashboard.html", profile=profile)

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

    fit_response = requests.post(FITNESS_URL, headers=headers, json=request_body)
    fit_data = fit_response.json()

    steps, calories = [], []
    weight = height = None

    for bucket in fit_data.get("bucket", []):
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
        return redirect(url_for("dashboard"))

    fitness_data = {
        "weight": profile["weight"],
        "height": profile["height"],
        "target": profile["target"],
        "activity_level": profile["activity_level"]
    }

    diet = analyze_and_recommend(fitness_data)
    return render_template("diet_planner.html", diet=diet)

def analyze_and_recommend(data):
    weight = data.get("weight")
    height = data.get("height")  # in cm
    target = data.get("target", "fit")
    activity_level = data.get("activity_level", "moderate")

    if not weight or not height:
        return {"error": "Missing height or weight data"}

    height_m = height / 100
    bmi = round(weight / (height_m ** 2), 2)

    if bmi < 18.5:
        bmi_status = "Underweight"
        adjustment = "Increase protein and calorie intake"
    elif 18.5 <= bmi < 24.9:
        bmi_status = "Normal"
        adjustment = "Maintain current weight"
    elif 25 <= bmi < 29.9:
        bmi_status = "Overweight"
        adjustment = "Include cardio and reduce calorie intake"
    else:
        bmi_status = "Obese"
        adjustment = "Focus on fat burning and eat clean"

    if target == "lean":
        breakfast = "Oats with banana and boiled eggs"
        lunch = "Grilled chicken with veggies"
        dinner = "Salad with tofu"
        snacks = "Almonds, fruit bowl"
    elif target == "bulk":
        breakfast = "Peanut butter toast and milk"
        lunch = "Rice, dal, chicken curry"
        dinner = "Chapati with paneer curry"
        snacks = "Protein shake, potatoes"
    else:
        breakfast = "Idli with sambar or oats"
        lunch = "Rice with dal & veg curry"
        dinner = "Chapati with mixed vegetables"
        snacks = "Fruit or yogurt"

    hydration = "Drink at least 2.5 to 3 liters of water daily"

    return {
        "bmi": bmi,
        "bmi_status": bmi_status,
        "adjustment": adjustment,
        "breakfast": breakfast,
        "lunch": lunch,
        "dinner": dinner,
        "snacks": snacks,
        "hydration": hydration
    }

if __name__ == "__main__":
    app.run(debug=True)
