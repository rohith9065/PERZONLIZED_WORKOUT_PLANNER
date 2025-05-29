import pandas as pd
from sklearn.tree import DecisionTreeClassifier


data = pd.DataFrame({
    "age": [20, 25, 30, 35, 40, 45],
    "weight": [55, 70, 90, 65, 85, 100],
    "height": [160, 175, 180, 170, 165, 185],
    "activity_level": [0, 1, 2, 0, 1, 2],  # 0: low, 1: moderate, 2: high
    "target": [0, 1, 2, 0, 2, 1],          # 0: lean, 1: bulk, 2: fit
    "diet_plan": [0, 1, 2, 0, 2, 1],       # 0: lean diet, 1: bulk diet, 2: fit diet
    "workout_plan": [0, 1, 2, 0, 2, 1]     # 0: light workout, 1: heavy workout, 2: balanced workout
})


X = data[["age", "weight", "height", "activity_level", "target"]]
y_diet = data["diet_plan"]
y_workout = data["workout_plan"]


diet_model = DecisionTreeClassifier().fit(X, y_diet)
workout_model = DecisionTreeClassifier().fit(X, y_workout)

def recommend_workout(profile):
    """
    Generate a workout plan based on the user's profile.

    Args:
        profile (dict): User's profile containing weight, height, target, and activity level.

    Returns:
        dict: A weekly workout plan.
    """
    target = profile.get("target", "fit")
    activity_level = profile.get("activity_level", "moderate")

    # Define workout plans based on target and activity level
    workout_plans = {
        "fit": {
            "low": [
                "Monday: 20-minute walk",
                "Tuesday: Rest",
                "Wednesday: 20-minute yoga",
                "Thursday: Rest",
                "Friday: 20-minute walk",
                "Saturday: Light stretching",
                "Sunday: Rest"
            ],
            "moderate": [
                "Monday: 30-minute jog",
                "Tuesday: Bodyweight exercises (push-ups, squats, planks)",
                "Wednesday: 30-minute yoga",
                "Thursday: Rest",
                "Friday: 30-minute jog",
                "Saturday: Light stretching or swimming",
                "Sunday: Rest"
            ],
            "high": [
                "Monday: 45-minute run",
                "Tuesday: Strength training (upper body)",
                "Wednesday: 30-minute yoga",
                "Thursday: Strength training (lower body)",
                "Friday: 45-minute run",
                "Saturday: HIIT workout",
                "Sunday: Rest"
            ]
        },
        "weight_loss": {
            "low": [
                "Monday: 20-minute brisk walk",
                "Tuesday: Rest",
                "Wednesday: 20-minute yoga",
                "Thursday: Rest",
                "Friday: 20-minute brisk walk",
                "Saturday: Light stretching",
                "Sunday: Rest"
            ],
            "moderate": [
                "Monday: 30-minute jog",
                "Tuesday: Bodyweight exercises (push-ups, squats, planks)",
                "Wednesday: 30-minute yoga",
                "Thursday: Rest",
                "Friday: 30-minute jog",
                "Saturday: Light stretching or swimming",
                "Sunday: Rest"
            ],
            "high": [
                "Monday: 45-minute run",
                "Tuesday: Strength training (upper body)",
                "Wednesday: 30-minute yoga",
                "Thursday: Strength training (lower body)",
                "Friday: 45-minute run",
                "Saturday: HIIT workout",
                "Sunday: Rest"
            ]
        }
    }

    
    return workout_plans.get(target, {}).get(activity_level, [])

def predict_recommendations(profile):
    """
    Predict diet and workout recommendations based on the user's profile.

    Args:
        profile (dict): User's profile containing age, weight, height, activity_level, and target.

    Returns:
        dict: Predicted diet and workout recommendations.
    """
    #
    activity_map = {"low": 0, "moderate": 1, "high": 2}
    target_map = {"lean": 0, "bulk": 1, "fit": 2}

    
    x_input = [[
        profile["age"],
        profile["weight"],
        profile["height"],
        activity_map.get(profile["activity_level"], 1),  # Default to "moderate"
        target_map.get(profile["target"], 2)            # Default to "fit"
    ]]

    # Predict diet and workout plans
    diet_label = diet_model.predict(x_input)[0]
    workout_label = workout_model.predict(x_input)[0]

    # Map predictions to human-readable recommendations
    diet_map = {
        0: "Lean diet: High protein, low carbs",
        1: "Bulk diet: High calories & protein",
        2: "Fit diet: Balanced meals"
    }

    workout_map = {
        0: "Light workout: Walk, yoga",
        1: "Heavy workout: Weight training, HIIT",
        2: "Balanced workout: Cardio + strength"
    }

    return {
        "diet": diet_map[diet_label],
        "workout": workout_map[workout_label]
    }