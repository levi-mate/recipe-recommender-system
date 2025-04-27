import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useModal } from "../../hooks/useModal";

import Button from "../../components/common/Button";
import Input from "../../components/common/Input";
import ConfirmDialog from "../../components/common/Confirm";
import PageHeader from "../../components/common/Header";
import Modal from "../../components/common/Modal";

import left_arrow from "../../assets/left_arrow.svg";
import right_arrow from "../../assets/right_arrow.svg";
import calendar from "../../assets/calendar.svg";

const Recipes: React.FC = () => {
    const [nutritionRecommendationsEnabled, setNutritionRecommendationsEnabled] = useState<boolean>(false);
    const [userTargetCalories, setUserTargetCalories] = useState<number | null>(null);
    const [userIngredients, setUserIngredients] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [recommendations, setRecommendations] = useState<any | null>(null);
    const [currentIndex, setCurrentIndex] = useState({ breakfast: 0, lunch: 0, dinner: 0 });
    const [selectedRecipe, setSelectedRecipe] = useState<any | null>(null);
    const [mealPlans, setMealPlans] = useState<any[]>([]);
    const [days, setDays] = useState(1);
    const [currentDay, setCurrentDay] = useState(0);
    const [targetCalories, setTargetCalories] = useState(2000);
    const [isValidationPopupVisible, setIsValidationPopupVisible] = useState<boolean>(false);
    const [missingSelections, setMissingSelections] = useState<string[]>([]);
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const twoWeeksLater = new Date();
    twoWeeksLater.setDate(twoWeeksLater.getDate() + 15);
    const [startDate, setStartDate] = useState<Date>(tomorrow);
    const navigate = useNavigate();

    const daysModal = useModal();

    useEffect(() => {
        const fetchNutritionInfo = async () => {
            try {
                const response = await axios.get("http://localhost:5077/get_nutrition_info", {
                    withCredentials: true,
                });
                
                const nutritionData = response.data.data || response.data;
                setNutritionRecommendationsEnabled(nutritionData.nutri_state);
                
                if (nutritionData.nutri_state) {
                    setUserTargetCalories(nutritionData.target_calories);
                    setTargetCalories(nutritionData.target_calories || 2000);
                }
                
                console.log("Nutrition settings loaded:", nutritionData);
            } catch (error) {
                console.error("Failed to fetch nutrition settings:", error);

                if (axios.isAxiosError(error) && error.response) {
                    console.error("Server response:", error.response.data);
                }
            }
        };
    
        fetchNutritionInfo();
    }, []);

    useEffect(() => {
        const fetchUserIngredients = async () => {
            try {
                const response = await axios.get("http://localhost:5077/account_ingredients/", {
                    withCredentials: true,
                });

                const ingredientsData = response.data.data || response.data;

                const ingredientNames = ingredientsData.map((ingredient: any) => 
                    ingredient.ingredient_name.toLowerCase().trim()
                );

                setUserIngredients(ingredientNames);
                console.log("User ingredients:", ingredientNames);
            } catch (error) {
                console.error("Failed to fetch user ingredients:", error);

                if (axios.isAxiosError(error) && error.response) {
                    console.error("Server response:", error.response.data);
                }
            }
        };

        fetchUserIngredients();
    }, []);

    const decodeHtmlEntities = (text: string): string => {
        if (!text) return "";
        
        return text
            .replace(/&Amp;/g, '&')
            .replace(/&amp;/g, '&')
            .replace(/&Quot;/g, '"')
            .replace(/&quot;/g, '"')
            .replace(/&Ldquo;/g, '"')
            .replace(/&ldquo;/g, '"')
            .replace(/&Rdquo;/g, '"')
            .replace(/&rdquo;/g, '"')
            .replace(/&Auml;/g, 'A')
            .replace(/&auml;/g, 'a')
            .replace(/&Uuml;/g, 'U')
            .replace(/&uuml;/g, 'u')
            .replace(/&AElig;/g, 'AE')
            .replace(/&aelig;/g, 'ae');
    };

    const hasIngredient = (ingredientText: string): boolean => {
        const cleanedText = ingredientText.toLowerCase().trim();
        
        return userIngredients.some(userIngredient => 
            cleanedText.includes(userIngredient)
        );
    };

    const parseIngredients = (ingredientText: string): string[] => {
        return ingredientText
            .split(/,|\n/)
            .map(item => item.trim())
            .filter(item => item.length > 0);
    };

    const fetchRecipeDetails = async (recipeIds: number[]) => {
        try {
            const response = await axios.post("http://localhost:5077/fetch_recipe_details", { recipeIds }, {
                withCredentials: true,
            });
            
            const recipesData = response.data.data || response.data;
            
            if (Array.isArray(recipesData)) {
                recipesData.forEach((recipe: any) => {
                    if (recipe && recipe.recipe_name) {
                        recipe.recipe_name = decodeHtmlEntities(recipe.recipe_name);
                    }
                    
                    if (recipe && recipe.instructions) {
                        recipe.instructions = decodeHtmlEntities(recipe.instructions);
                    }
                });
            }
            
            return recipesData;
        } catch (error) {
            console.error("Failed to fetch recipe details:", error);

            if (axios.isAxiosError(error) && error.response) {
                console.error("Server response:", error.response.data);
            }

            return [];
        }
    };

    const formatTime = (timeString: string): string => {
        if (!timeString) return "0S";
        
        let formattedTime = timeString.replace("PT", "");
        
        if (formattedTime.includes("H")) {
          formattedTime = formattedTime.replace("H", "H ");
        }
        
        return formattedTime || "0S";
    };

    const formatDate = (date: Date) => {
        const day = String(date.getDate()).padStart(2, "0");
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const year = date.getFullYear();
        return `${year}-${month}-${day}`;
    };

    const formatDisplayDate = (date: Date): string => {
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };

    const handleGenerateClick = () => {
        daysModal.open();
    };

    const handleStartGeneration = async () => {
        daysModal.close();
        setIsLoading(true);
        setRecommendations(null);
    
        try {
            const caloriesValue = nutritionRecommendationsEnabled && userTargetCalories 
            ? userTargetCalories 
            : targetCalories;
        
            console.log("Sending days and targetCalories to backend:", days, formatDate(startDate), caloriesValue);

            const response = await axios.get("http://localhost:5077/generate_recommendations", {
                params: { 
                    days, 
                    startDate: formatDate(startDate),
                    targetCalories: caloriesValue
                },

                withCredentials: true,
            });

            const recommendationsData = response.data.data || response.data;
            console.log("Recommendations received:", recommendationsData);
    
            const detailedRecommendations = await Promise.all(
                recommendationsData.days.map(async (day: any) => {
                    const breakfastDetails = await fetchRecipeDetails(day.breakfast);
                    const lunchDetails = await fetchRecipeDetails(day.lunch);
                    const dinnerDetails = await fetchRecipeDetails(day.dinner);
    
                    return {
                        breakfast: breakfastDetails,
                        lunch: lunchDetails,
                        dinner: dinnerDetails,
                    };
                })
            );
    
            setRecommendations(detailedRecommendations);
        } catch (error) {
            console.error("Failed to generate recommendations:", error);

            if (axios.isAxiosError(error) && error.response) {
                console.error("Server response:", error.response.data);
                alert(error.response.data.error || "Failed to generate recommendations");
            } else {
                alert("Failed to connect to the server. Please try again later.");
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleNextDay = () => {
        if (currentDay < days - 1) {
            setCurrentDay((prev) => prev + 1);
        }
    };

    const handlePreviousDay = () => {
        if (currentDay > 0) {
            setCurrentDay((prev) => prev - 1);
        }
    };

    const handleNext = (category: keyof typeof currentIndex) => {
        setCurrentIndex((prev) => ({
            ...prev,
            [category]: (prev[category] + 1) % 5,
        }));
    };

    const handlePrevious = (category: keyof typeof currentIndex) => {
        setCurrentIndex((prev) => ({
            ...prev,
            [category]: (prev[category] - 1 + 5) % 5,
        }));
    };

    const parseQuantity = (quantity: string | null): number => {
        if (!quantity) return 0;
        
        const trimmedQuantity = quantity.trim();
        
        if (trimmedQuantity.includes(" ") && trimmedQuantity.includes("/")) {
            const [wholeNumber, fraction] = trimmedQuantity.split(" ");
            const [numerator, denominator] = fraction.split("/").map(Number);
            
            if (!isNaN(Number(wholeNumber)) && !isNaN(numerator) && !isNaN(denominator) && denominator !== 0) {
                return Number(wholeNumber) + (numerator / denominator);
            }
        }
        
        if (trimmedQuantity.includes("/") && !trimmedQuantity.includes(" ")) {
            const [numerator, denominator] = trimmedQuantity.split("/").map(Number);
            
            if (!isNaN(numerator) && !isNaN(denominator) && denominator !== 0) {
                return numerator / denominator;
            }
        }
        
        const parsed = parseFloat(trimmedQuantity);
        return isNaN(parsed) ? 0 : parsed;
    };

    const handleSelectRecipe = (category: 'breakfast' | 'lunch' | 'dinner', recipe: any) => {
        setMealPlans((prev) => {
            const updatedMealPlans = [...prev];

            if (!updatedMealPlans[currentDay]) {
                updatedMealPlans[currentDay] = { breakfast: null, lunch: null, dinner: null };
            }

            updatedMealPlans[currentDay][category] = recipe;
            return updatedMealPlans;
        });
    };

    const calculateDayCalories = () => {
        if (!mealPlans[currentDay]) return 0;
        
        let totalCalories = 0;
        
        if (mealPlans[currentDay].breakfast) {
            totalCalories += mealPlans[currentDay].breakfast.calories || 0;
        }
        
        if (mealPlans[currentDay].lunch) {
            totalCalories += mealPlans[currentDay].lunch.calories || 0;
        }
        
        if (mealPlans[currentDay].dinner) {
            totalCalories += mealPlans[currentDay].dinner.calories || 0;
        }
        
        return totalCalories;
    };

    const validateMealPlanSelections = (): boolean => {
        const missing: string[] = [];
        
        for (let day = 0; day < days; day++) {
            const dayPlan = mealPlans[day];
            
            if (!dayPlan) {
                missing.push(`Day ${day + 1}: All meals`);
                continue;
            }
            
            if (!dayPlan.breakfast) {
                missing.push(`Day ${day + 1}: Breakfast`);
            }
            
            if (!dayPlan.lunch) {
                missing.push(`Day ${day + 1}: Lunch`);
            }
            
            if (!dayPlan.dinner) {
                missing.push(`Day ${day + 1}: Dinner`);
            }
        }
        
        if (missing.length > 0) {
            setMissingSelections(missing);
            return false;
        }
        
        return true;
    };

    const handleSaveAllMealPlans = async () => {
        if (!validateMealPlanSelections()) {
            setIsValidationPopupVisible(true);
            return;
        }

        const mealPlansToSave = mealPlans.map((dayPlan, index) => ({
            day: index + 1,
            breakfast_id: dayPlan?.breakfast?.recipe_id || null,
            lunch_id: dayPlan?.lunch?.recipe_id || null,
            dinner_id: dayPlan?.dinner?.recipe_id || null,
        }));
    
        console.log("Meal plans to save:", mealPlansToSave);
    
        try {
            const response = await axios.post("http://localhost:5077/save_meal_plans", { mealPlans: mealPlansToSave }, {
                withCredentials: true,
            });

            if (!response.data.success) {
                throw new Error(response.data.error || "Failed to save meal plans");
            }

            console.log("Meal plans saved:", response.data);
    
            const recipeIds = new Set<number>();

            mealPlans.forEach(dayPlan => {
                if (dayPlan?.breakfast?.recipe_id) recipeIds.add(dayPlan.breakfast.recipe_id);
                if (dayPlan?.lunch?.recipe_id) recipeIds.add(dayPlan.lunch.recipe_id);
                if (dayPlan?.dinner?.recipe_id) recipeIds.add(dayPlan.dinner.recipe_id);
            });
    
            const shoppingListResponse = await axios.get("http://localhost:5077/get_shopping_list", {
                withCredentials: true,
            });

            const currentShoppingList = shoppingListResponse.data.data || shoppingListResponse.data || [];
            
            const newIngredients: { name: string; quantity: number; unit: string | null }[] = [];
            
            for (const recipeId of Array.from(recipeIds)) {
                const ingredientsResponse = await axios.get(`http://localhost:5077/get_recipe_ingredients/${recipeId}`, {
                    withCredentials: true,
                });
                
                const recipeIngredients = ingredientsResponse.data.data || ingredientsResponse.data;
                
                for (const ingredient of recipeIngredients) {
                    if (!hasIngredient(ingredient.name)) {
                        const parsedQuantity = parseQuantity(ingredient.quantity);
                        
                        const existingIndex = newIngredients.findIndex(
                            i => i.name.toLowerCase() === ingredient.name.toLowerCase()
                        );
                        
                        if (existingIndex !== -1) {
                            newIngredients[existingIndex].quantity += parsedQuantity;
                        } else {
                            newIngredients.push({
                                name: ingredient.name,
                                quantity: parsedQuantity,
                                unit: null
                            });
                        }
                    }
                }
            }
            
            for (const newIngredient of newIngredients) {
                const existingIndex: number = currentShoppingList.findIndex(
                    (item: { name: string; quantity: number; unit: string | null }) => 
                        item.name.toLowerCase() === newIngredient.name.toLowerCase()
                );
                
                if (existingIndex !== -1) {
                    const existingQty = Number(currentShoppingList[existingIndex].quantity);
                    const newQty = Number(newIngredient.quantity);
                    currentShoppingList[existingIndex].quantity = parseFloat((existingQty + newQty).toFixed(2));
                } else {
                    newIngredient.quantity = parseFloat(newIngredient.quantity.toFixed(2));
                    currentShoppingList.push(newIngredient);
                }
            }
            
            if (newIngredients.length > 0) {
                const updateResponse = await axios.post(
                    "http://localhost:5077/update_shopping_list",
                    { ingredients: currentShoppingList },
                    { withCredentials: true }
                );

                if (!updateResponse.data.success) {
                    throw new Error(updateResponse.data.error || "Failed to update shopping list");
                }
                
                console.log("Shopping list updated with missing ingredients:", newIngredients);
                navigate("/account");
            } else {
                alert("Meal plans saved successfully!");
            }
        } catch (error) {
            console.error("Failed to save meal plans or update shopping list:", error);
            
            if (axios.isAxiosError(error) && error.response) {
                console.error("Server response:", error.response.data);
                alert(error.response.data.error || "Failed to save meal plans or update shopping list");
            } else if (error instanceof Error) {
                alert(error.message);
            } else {
                alert("Failed to save meal plans or update shopping list.");
            }
        }
    };

    const renderDaysPopup = () => {
        return (
            <Modal isVisible={daysModal.isOpen} onClose={() => daysModal.close()} title="Meal Plan Settings">
                <div className="flex flex-col gap-5 mb-5">
                    <label className="font-bold">Start Date
                        <div className="mt-2 relative">
                            <div className="flex items-center gap-2 p-2 rounded-lg cursor-pointer bg-gray-100 hover:bg-gray-200"
                                onClick={() => {
                                    const datePicker = document.getElementById('start-date-picker') as HTMLInputElement;
                                    if (datePicker) datePicker.showPicker();
                                }}>

                                <div className="flex items-center gap-5">
                                    <img src={calendar} alt="Calendar" width="30px" height="30px" className="rounded-md bg-emerald-400" />
                                    <span className="font-bold text-lg">{formatDisplayDate(startDate)}</span>
                                </div>
                            </div>
                            
                            <input
                                id="start-date-picker"
                                type="date"
                                value={formatDate(startDate)}
                                min={formatDate(tomorrow)}
                                max={formatDate(twoWeeksLater)}
                                onChange={(e) => {
                                    const selectedDate = new Date(e.target.value);
                                    if (selectedDate >= tomorrow && selectedDate <= twoWeeksLater) {
                                        setStartDate(selectedDate);
                                    } else {
                                        setStartDate(tomorrow);
                                    }
                                }}
                                className="absolute opacity-0 w-1 h-1"
                            />
                        </div>
                    </label>

                    <label className="font-bold">Number of Days
                        <div className="flex items-center gap-2 mt-5 px-[2px]">
                            <input type="range" min="1" max="7" value={days} onChange={(e) => setDays(Number(e.target.value))} className="flex-grow h-2 accent-emerald-400 bg-gray-200 rounded-lg appearance-none cursor-pointer"/>
                        </div>
                        
                        <div className="flex justify-between py-3">
                            {[1, 2, 3, 4, 5, 6, 7].map(day => (
                                <div key={day} className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${days === day ? 'bg-emerald-400 text-white' : 'bg-gray-200 hover:bg-gray-300'} cursor-pointer transition-colors`} onClick={() => setDays(day)}>{day}</div>
                            ))}
                        </div>
                    </label>
                    
                    <label className="font-bold">Target Calories
                        {nutritionRecommendationsEnabled ? (
                            <div className="mt-2 p-3 bg-gray-100 rounded-lg">
                                <div className="flex items-center justify-between">
                                    <span>{userTargetCalories || 2000} kcal</span>
                                    <span className="text-xs text-gray-500">(Nutritional Mode)</span>
                                </div>
                            </div>
                        ) : (
                            <Input type="number" min="500" max="5000" value={targetCalories} onChange={(e) => setTargetCalories(Number(e.target.value))} className="mt-2"/>
                        )}
                    </label>
                </div>

                <div className="flex justify-between gap-4">
                    <Button variant="secondary" onClick={() => daysModal.close()}>Cancel</Button>
                    <Button onClick={handleStartGeneration}>Start Generation</Button>
                </div>
            </Modal>
        );
    };

    const renderRecipe = (category: 'breakfast' | 'lunch' | 'dinner') => {
        if (!recommendations || !recommendations[currentDay] || !recommendations[currentDay][category]) return null;
    
        const recipe = recommendations[currentDay][category][currentIndex[category]];
    
        const isSelected =
            mealPlans[currentDay] &&
            mealPlans[currentDay][category] &&
            mealPlans[currentDay][category].recipe_id === recipe.recipe_id;
    
        return (
            <div className="flex flex-col items-center justify-center gap-3 m-5 w-full min-h-[250px] rounded-lg shadow-[0_0_10px_rgba(0,0,0,0.2)] bg-gray-100">
                <div className="flex justify-between items-center w-full px-2">
                    <button onClick={() => handlePrevious(category)} className="cursor-pointer p-1 h-[100px] rounded-lg bg-emerald-400 hover:bg-emerald-300 transition-colors"><img src={left_arrow} alt="Details" width="30px" height="30px" /></button>
    
                    <div className="flex flex-col gap-3 max-w-3/4">
                        <div className="flex flex-col gap-5 p-2">
                            <h4 className="font-bold text-lg text-center flex-grow">{recipe.recipe_name}</h4>
                            <p className="self-center text-gray-700"><strong>Calories:</strong> {recipe.calories} kcal</p>
                        </div>

                        <div className="flex flex-row gap-5 self-center">
                            <Button variant="blue" onClick={() => setSelectedRecipe(recipe)}>Details</Button>
                            <button onClick={() => handleSelectRecipe(category, recipe)} className={`cursor-pointer px-4 py-2 rounded-lg font-bold text-white ${isSelected ? "bg-emerald-400" : "bg-gray-400 hover:bg-gray-300 transition-colors"}`}>{isSelected ? "Selected" : "Select"}</button>
                        </div>
                    </div>

                    <button onClick={() => handleNext(category)} className="cursor-pointer p-1 h-[100px] rounded-lg bg-emerald-400 hover:bg-emerald-300 transition-colors"><img src={right_arrow} alt="Details" width="30px" height="30px" /></button>
                </div>
            </div>
        );
    };

    const renderPopup = () => {
        if (!selectedRecipe) return null;

        const ingredients = parseIngredients(selectedRecipe.ingredient_parts);
        const quantities = selectedRecipe.ingredient_quantity ? parseIngredients(selectedRecipe.ingredient_quantity) : [];

        return (
            <div className="fixed inset-0 flex items-start justify-center py-10 bg-black/20 backdrop-blur-sm overflow-y-auto z-50">
                <div className="flex flex-col gap-5 p-5 rounded-lg shadow-[0_0_10px_rgba(0,0,0,0.2)] w-11/12 max-w-2xl bg-white">
                    <h4 className="font-bold text-xl text-center">{selectedRecipe.recipe_name}</h4>
                    
                    <div className="flex flex-row justify-center text-center gap-10">
                        <div>
                            <p className="font-bold text-xl">{selectedRecipe.calories} kcal</p>
                            <p>Calories</p>
                        </div>

                        <div>
                            <p className="font-bold text-xl">{selectedRecipe.recipe_servings === 0 ? 1 : selectedRecipe.recipe_servings}</p>
                            <p>Serving(s)</p>
                        </div>
                    </div>

                    <div className="flex flex-row justify-center text-center gap-10">
                        <div>
                            <p className="font-bold text-xl">{formatTime(selectedRecipe.prep_time)}</p>
                            <p>Prep</p>
                        </div>

                        <div>
                            <p className="font-bold text-xl">{formatTime(selectedRecipe.cook_time)}</p>
                            <p>Cook</p>
                        </div>

                        <div>
                            <p className="font-bold text-xl">{formatTime(selectedRecipe.total_time)}</p>
                            <p>Total</p>
                        </div>
                    </div>

                    <div>
                        <p className="font-bold text-xl mb-2">Ingredients</p>
                        <div className="flex flex-wrap gap-1">
                            {ingredients.map((ingredient, index) => (
                                <span key={index} className={`px-2 py-1 rounded-lg inline-block ${hasIngredient(ingredient) ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                                    {quantities[index] ? `${quantities[index]} ${ingredient}` : ingredient}
                                </span>
                            ))}
                        </div>
                    </div>

                    <div>
                        <p className="font-bold text-xl mb-2">Instructions</p>
                        <p>{selectedRecipe.instructions}</p>
                    </div>
                    
                    <div className="flex flex-col gap-3">
                        <p className="font-bold text-xl mb-2">Nutrition</p>

                        <div className="mx-auto w-full max-w-md">
                            <div className="flex flex-row justify-between text-center gap-4 mb-3">
                                <div className="text-orange-500 p-2 rounded-lg bg-orange-100 w-1/3">
                                    <p className="font-bold">{selectedRecipe.carbohydrates} g</p>
                                    <p>Carbohydrates</p>
                                </div>

                                <div className="text-sky-500 p-2 rounded-lg bg-sky-100 w-1/3">
                                    <p className="font-bold">{selectedRecipe.protein} g</p>
                                    <p>Protein</p>
                                </div>

                                <div className="text-purple-500 p-2 rounded-lg bg-purple-100 w-1/3">
                                    <p className="font-bold">{selectedRecipe.fat} g</p>
                                    <p>Fat</p>
                                </div>
                            </div>
                            
                            <div className="flex flex-row justify-evenly text-center gap-4 mb-3">
                                <div className="p-2 rounded-lg bg-gray-100 w-1/2">
                                    <p className="font-bold">{selectedRecipe.sugar} g</p>
                                    <p>Sugar</p>
                                </div>

                                <div className="p-2 rounded-lg bg-gray-100 w-1/2">
                                    <p className="font-bold">{selectedRecipe.fiber} g</p>
                                    <p>Fiber</p>
                                </div>
                            </div>

                            <div className="flex flex-row justify-between text-center gap-2">
                                <div className="p-2 rounded-lg bg-gray-100 flex-1">
                                    <p className="font-bold text-sm">{selectedRecipe.saturated_fat} g</p>
                                    <p className="text-sm">Saturated Fat</p>
                                </div>

                                <div className="p-2 rounded-lg bg-gray-100 flex-1">
                                    <p className="font-bold text-sm">{selectedRecipe.cholesterol} mg</p>
                                    <p className="text-sm">Cholesterol</p>
                                </div>

                                <div className="p-2 rounded-lg bg-gray-100 flex-1">
                                    <p className="font-bold text-sm">{selectedRecipe.sodium} mg</p>
                                    <p className="text-sm">Sodium</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <Button variant="secondary" onClick={() => setSelectedRecipe(null)} className="place-self-center">Close</Button>
                </div>
            </div>
        );
    };

    const renderValidationPopup = () => {
        if (!isValidationPopupVisible) return null;
    
        return (
            <ConfirmDialog
                isVisible={isValidationPopupVisible}
                onConfirm={() => setIsValidationPopupVisible(false)}
                onCancel={() => setIsValidationPopupVisible(false)}
                title="Incomplete Meal Plan"
                message={
                    <>
                        <div className="mb-2">Please select recipes for all meals and days before saving:</div>
                        <div className="max-h-60 overflow-y-auto">
                            <ul className="list-disc pl-5">
                                {missingSelections.map((item, index) => (
                                    <li key={index} className="text-red-500">{item}</li>
                                ))}
                            </ul>
                        </div>
                    </>
                }
                confirmText="OK"
                confirmVariant="primary"
                showCancelButton={false}
            />
        );
    };

    return (
        <>
            {!recommendations && (
                <div className="flex flex-col items-center gap-5 m-5 max-w-[600px] lg:min-w-[600px] md:mx-auto rounded-lg shadow-[0_0_10px_rgba(0,0,0,0.2)] bg-slate-50">
                    <PageHeader title="Generate Recipes" />

                    <button id="generateRecommendations" onClick={handleGenerateClick} className="cursor-pointer m-5 mb-10 p-5 rounded-lg font-bold text-5xl text-white bg-gradient-to-r from-indigo-400 to-teal-400 hover:from-indigo-300 hover:to-teal-300 transition-colors">{isLoading ? "Generating..." : "Generate"}</button>
                </div>
            )}

            {recommendations && (
                <div className="flex flex-col items-center gap-5 m-5 p-5 max-w-[600px] lg:min-w-[600px] md:mx-auto rounded-lg shadow-[0_0_10px_rgba(0,0,0,0.2)] bg-slate-50">
                    <h3 className="p-2 rounded-lg w-full font-bold text-2xl text-center text-white bg-emerald-400">Day {currentDay + 1} ({new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate() + currentDay).toLocaleDateString()})</h3>

                    {(["breakfast", "lunch", "dinner"] as const).map((category) => (
                        <div key={category} className="flex flex-col items-center w-full">
                            <h3 className="font-bold text-2xl capitalize">{category}</h3>

                            {renderRecipe(category)}
                        </div>
                    ))}

                    <div className="flex flex-col items-center gap-3 p-3 w-full">
                        <p className="font-bold text-lg">Daily Total Calories</p>

                        <div className="flex items-center gap-2">
                            <span className="text-2xl font-bold">{calculateDayCalories().toFixed(1)}</span>
                            <span className="text-gray-500">/ {targetCalories} kcal</span>
                        </div>
                        
                        <div className="w-full h-4 bg-gray-200 rounded-full mt-2 overflow-hidden">
                            <div className="h-full rounded-full transition-all duration-500 bg-emerald-400" style={{ width: `${Math.min(100, (calculateDayCalories() / targetCalories) * 100)}%` }}></div>
                        </div>
                    </div>

                    <div className="flex justify-center mt-10 gap-5">
                        {currentDay > 0 && (
                            <Button variant="blue" onClick={handlePreviousDay}>Previous Day</Button>
                        )}

                        {currentDay < days - 1 ? (
                            <Button onClick={handleNextDay}>Next Day</Button>
                        ) : (
                            <Button onClick={handleSaveAllMealPlans}>Save Meal Plan</Button>
                        )}
                    </div>
                </div>
            )}

            {renderDaysPopup()}
            {renderPopup()}
            {renderValidationPopup()}
        </>
    );
};

export default Recipes;