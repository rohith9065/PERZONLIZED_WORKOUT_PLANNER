document.addEventListener("DOMContentLoaded", function () {
    fetchFitnessData();
});

function fetchFitnessData() {
    document.getElementById("loader").style.display = "block";

    fetch("/api/fitness")
        .then(response => response.json())
        .then(data => {
            document.getElementById("steps").textContent = data.total_steps + " steps";
            document.getElementById("calories").textContent = data.total_calories_burned + " kcal";
            document.getElementById("weight").textContent = data.weight ? data.weight + " kg" : "Not Available";
            document.getElementById("height").textContent = data.height ? data.height + " cm" : "Not Available";
        })
        .catch(error => {
            console.error("Error fetching fitness data:", error);
            document.getElementById("steps").textContent = "Error fetching data";
        })
        .finally(() => {
            document.getElementById("loader").style.display = "none";
        });
}
