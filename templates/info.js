document.addEventListener("DOMContentLoaded", function () {
    const urlParams = new URLSearchParams(window.location.search);
    const recipeName = urlParams.get("recipe");

    if (!recipeName) {
        document.querySelector(".recipe-wrapper").innerHTML = "<h2>Recipe not found</h2>";
        return;
    }

    // Fetch recipes from JSON file
    fetch("templates/recipies.json")  // Fixed file path
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to load recipes.json");
            }
            return response.json();
        })
        .then(data => {
            const recipes = data.recipes; // Access the recipes array

            // Find recipe by title
            const recipe = recipes.find(r => r.title === recipeName);

            if (recipe) {
                document.getElementById("recipe-title").textContent = recipe.title;
                document.getElementById("recipe-image").src = recipe.image;
                document.getElementById("recipe-image").alt = recipe.title;

                // Update Ingredients
                const ingredientsList = document.getElementById("ingredients-list");
                ingredientsList.innerHTML = "";
                recipe.ingredients.forEach(ingredient => {
                    const li = document.createElement("li");
                    li.textContent = ingredient;
                    ingredientsList.appendChild(li);
                });

                // Update Instructions
                const instructionsList = document.getElementById("instructions-list");
                instructionsList.innerHTML = "";
                recipe.instructions.forEach(step => {
                    const li = document.createElement("li");
                    li.textContent = step;
                    instructionsList.appendChild(li);
                });

                // Optional: Add Benefits Section
                const benefitsList = document.getElementById("benefits-list");
                if (benefitsList) {
                    benefitsList.innerHTML = "";
                    recipe.benefits.forEach(benefit => {
                        const li = document.createElement("li");
                        li.textContent = benefit;
                        benefitsList.appendChild(li);
                    });
                }
            } else {
                document.querySelector(".recipe-wrapper").innerHTML = "<h2>Recipe not found</h2>";
            }
        })
        .catch(error => {
            console.error("Error fetching recipes:", error);
            document.querySelector(".recipe-wrapper").innerHTML = "<h2>Error loading recipe</h2>";
        });
});
