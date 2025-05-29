def analyze_and_recommend(data):
    """
    Analyze fitness data and recommend a diet plan.

    Args:
        data (dict): Fitness data from the Google Fit API.

    Returns:
        dict: Recommended diet plan.
    """
    total_steps = data.get("total_steps", 0)
    total_calories_burned = data.get("total_calories_burned", 0)
    weight = data.get("weight", None)
    height = data.get("height", None)
    target = data.get("target", "fit")
    activity_level = data.get("activity_level", "moderate")

    # Calculate BMI (if weight and height are available)
    bmi = None
    if weight and height:
        height_in_meters = height / 100  # Convert height to meters
        bmi = weight / (height_in_meters ** 2)

    # Determine activity level based on steps
    if total_steps < 5000:
        activity_level = "low"
    elif 5000 <= total_steps < 10000:
        activity_level = "moderate"
    else:
        activity_level = "high"

    # Recommend a diet based on activity level and BMI
    diet_plan = {}
    if activity_level == "low":
        diet_plan = {
            "breakfast": "Oatmeal with fruits and a cup of green tea",
            "lunch": "Grilled chicken salad with a small portion of brown rice",
            "dinner": "Steamed vegetables with grilled fish",
            "snacks": "A handful of nuts or a fruit"
        }
    elif activity_level == "moderate":
        diet_plan = {
            "breakfast": "Scrambled eggs with whole-grain toast and a banana",
            "lunch": "Grilled chicken wrap with a side of quinoa salad",
            "dinner": "Baked salmon with sweet potatoes and steamed broccoli",
            "snacks": "Greek yogurt with honey and berries"
        }
    elif activity_level == "high":
        diet_plan = {
            "breakfast": "Protein smoothie with oats, banana, and peanut butter",
            "lunch": "Grilled steak with roasted vegetables and brown rice",
            "dinner": "Chicken stir-fry with whole-grain noodles",
            "snacks": "Protein bar or a boiled egg"
        }

    # Add hydration recommendation
    diet_plan["hydration"] = "Drink at least 2-3 liters of water daily"

    # Add BMI information (if available)
    if bmi:
        diet_plan["bmi"] = round(bmi, 2)
        if bmi < 18.5:
            diet_plan["bmi_status"] = "Underweight"
        elif 18.5 <= bmi < 24.9:
            diet_plan["bmi_status"] = "Normal weight"
        elif 25 <= bmi < 29.9:
            diet_plan["bmi_status"] = "Overweight"
        else:
            diet_plan["bmi_status"] = "Obese"

    return diet_plan