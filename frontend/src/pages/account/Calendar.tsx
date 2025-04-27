import React, { useState, useRef, useEffect } from "react";
import axios from "axios";

import Button from "../../components/common/Button";
import ConfirmDialog from "../../components/common/Confirm";

import left_arrow from "../../assets/left_arrow.svg";
import calendar from "../../assets/calendar.svg";
import right_arrow from "../../assets/right_arrow.svg";
import upvote from "../../assets/upvote.svg";
import downvote from "../../assets/downvote.svg";

interface FinishedStates {
    [key: string]: boolean;
    breakfast_finished: boolean;
    lunch_finished: boolean;
    dinner_finished: boolean;
}

const Calendar: React.FC = () => {
    const [weekMealPlanStatus, setWeekMealPlanStatus] = useState<boolean[]>(Array(7).fill(false));
    const [selectedDate, setSelectedDate] = useState(new Date());
    const [isDatePickerVisible, setIsDatePickerVisible] = useState(false);
    const [popupData, setPopupData] = useState<any | null>(null);
    const [mealPlan, setMealPlan] = useState<any | null>(null);
    const datePickerRef = useRef<HTMLInputElement>(null);
    const [recipeInteractions, setRecipeInteractions] = useState<Map<number, 'like' | 'dislike'>>(new Map());
    const [isDeleteConfirmVisible, setIsDeleteConfirmVisible] = useState<boolean>(false);
    const [finishedStates, setFinishedStates] = useState<FinishedStates>({
        breakfast_finished: false,
        lunch_finished: false,
        dinner_finished: false
    });

    useEffect(() => {
        fetchMealPlan(selectedDate);
        fetchWeekMealPlanStatus(selectedDate);
    }, [selectedDate]);

    useEffect(() => {
        const fetchUserInteractions = async () => {
            try {
                const response = await axios.get("http://localhost:5077/get_user_interactions", { withCredentials: true });
                const interactions = response.data.data?.interactions || [];
                
                const interactionsMap = new Map();
                for (const interaction of interactions) {
                    interactionsMap.set(interaction.recipe_id, interaction.interaction_type);
                }
                
                setRecipeInteractions(interactionsMap);
            } catch (error) {
                console.error("Failed to fetch user interactions:", error);
            }
        };
    
        fetchUserInteractions();
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

    const fetchMealPlan = async (date: Date) => {
        try {
            const response = await axios.get("http://localhost:5077/get_meal_plan", {
                params: { meal_date: formatDate(date) },
                withCredentials: true,
            });
            
            const mealPlanData = response.data;
            
            if (mealPlanData.breakfast && mealPlanData.breakfast.recipe_name) {
                mealPlanData.breakfast.recipe_name = decodeHtmlEntities(mealPlanData.breakfast.recipe_name);
            }
            
            if (mealPlanData.lunch && mealPlanData.lunch.recipe_name) {
                mealPlanData.lunch.recipe_name = decodeHtmlEntities(mealPlanData.lunch.recipe_name);
            }
            
            if (mealPlanData.dinner && mealPlanData.dinner.recipe_name) {
                mealPlanData.dinner.recipe_name = decodeHtmlEntities(mealPlanData.dinner.recipe_name);
            }
            
            setMealPlan(mealPlanData);
            
            setFinishedStates({
                breakfast_finished: mealPlanData.breakfast_finished || false,
                lunch_finished: mealPlanData.lunch_finished || false,
                dinner_finished: mealPlanData.dinner_finished || false
            });
        } catch (error) {
            console.error("Failed to fetch meal plan:", error);
            setMealPlan(null);
            setFinishedStates({
                breakfast_finished: false,
                lunch_finished: false,
                dinner_finished: false
            });
        }
    };

    const parseIngredients = (ingredientText: string): string[] => {
        if (!ingredientText) return [];
        
        return ingredientText
            .split(/,|\n/)
            .map(item => item.trim())
            .filter(item => item.length > 0);
    };

    const formatTime = (timeString: string): string => {
        if (!timeString) return "0s";
        
        let formattedTime = timeString.replace("PT", "");
        
        if (formattedTime.includes("H")) {
          formattedTime = formattedTime.replace("H", "H ");
        }
        
        return formattedTime || "0S";
    };

    const fetchWeekMealPlanStatus = async (currentDate: Date) => {
        try {
            const startOfWeek = getMondayOfWeek(currentDate);
            
            const weekDates = Array(7).fill(0).map((_, i) => {
                const date = new Date(startOfWeek);
                date.setDate(startOfWeek.getDate() + i);
                return formatDate(date);
            });
            
            const response = await axios.post(
                "http://localhost:5077/check_meal_plan_dates",
                { dates: weekDates },
                { withCredentials: true }
            );
            
            setWeekMealPlanStatus(response.data.data?.results || Array(7).fill(false));
        } catch (error) {
            console.error("Failed to fetch week meal plan status:", error);
            setWeekMealPlanStatus(Array(7).fill(false));
        }
    };

    const getMondayOfWeek = (date: Date): Date => {
        const result = new Date(date);
        const day = date.getDay();
        const diff = day === 0 ? 6 : day - 1;
        result.setDate(date.getDate() - diff);
        return result;
    };

    const formatDate = (date: Date) => {
        const day = String(date.getDate()).padStart(2, "0");
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const year = date.getFullYear();
        return `${year}-${month}-${day}`;
    };

    const formatDisplayDate = (date: Date): string => {
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(today.getDate() - 1);
        const tomorrow = new Date(today);
        tomorrow.setDate(today.getDate() + 1);
        
        const isSameDay = (d1: Date, d2: Date): boolean => {
            return  d1.getDate() === d2.getDate() && 
                    d1.getMonth() === d2.getMonth() && 
                    d1.getFullYear() === d2.getFullYear();
        };
        
        if (isSameDay(date, today)) {
            return "Today";
        } else if (isSameDay(date, yesterday)) {
            return "Yesterday";
        } else if (isSameDay(date, tomorrow)) {
            return "Tomorrow";
        } else {
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        }
    };

    const handlePreviousDay = () => {
        setSelectedDate((prevDate) => {
            const newDate = new Date(prevDate);
            newDate.setDate(newDate.getDate() - 1);
            return newDate;
        });
    };

    const handleNextDay = () => {
        setSelectedDate((prevDate) => {
            const newDate = new Date(prevDate);
            newDate.setDate(newDate.getDate() + 1);
            return newDate;
        });
    };

    const handleDateChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const newDate = new Date(event.target.value);
        setSelectedDate(newDate);
        setIsDatePickerVisible(false);
    };

    const handleDotClick = (dayOffset: number) => {
        const startOfWeek = getMondayOfWeek(selectedDate);
        
        const newDate = new Date(startOfWeek);
        newDate.setDate(startOfWeek.getDate() + dayOffset);
        
        setSelectedDate(newDate);
    };

    const handleShowPopup = (meal: any) => {
        if (meal && meal.recipe_name) {
            const decodedMeal = {...meal};
            decodedMeal.recipe_name = decodeHtmlEntities(meal.recipe_name);
            
            if (decodedMeal.instructions) {
                decodedMeal.instructions = decodeHtmlEntities(decodedMeal.instructions);
            }
            
            setPopupData(decodedMeal);
        } else {
            setPopupData(meal);
        }
    };

    const handleMarkMealFinished = async (mealType: string) => {
        try {
            await axios.post(
                "http://localhost:5077/mark_meal_finished",
                { 
                    meal_date: formatDate(selectedDate),
                    meal_type: mealType
                },

                { withCredentials: true }
            );
            
            setFinishedStates(prev => ({
                ...prev,
                [`${mealType}_finished`]: true
            }));
            
            console.log(`${mealType} marked as finished`);
        } catch (error) {
            console.error(`Failed to mark ${mealType} as finished:`, error);
            alert(`Failed to mark ${mealType} as finished. Please try again.`);
        }
    };

    const handleInteraction = async (recipeId: number, interactionType: "like" | "dislike") => {
        if (!recipeId) return;
    
        try {
            const response = await axios.post(
                "http://localhost:5077/save_interaction",
                { recipe_id: recipeId, interaction_type: interactionType },
                { withCredentials: true }
            );
            console.log("Interaction saved:", response.data);
    
            setRecipeInteractions(prev => {
                const newMap = new Map(prev);
                newMap.set(recipeId, interactionType);
                return newMap;
            });
        } catch (error) {
            console.error("Failed to save interaction:", error);
            alert("Failed to save interaction.");
        }
    };

    const handleDeleteMealPlan = async () => {
        try {
            await axios.post(
                "http://localhost:5077/delete_meal_plan",
                { meal_date: formatDate(selectedDate) },
                { withCredentials: true }
            );
            
            setMealPlan(null);
            setFinishedStates({
                breakfast_finished: false,
                lunch_finished: false,
                dinner_finished: false
            });
            
            fetchWeekMealPlanStatus(selectedDate);
            
            setIsDeleteConfirmVisible(false);
            
            console.log(`Meal plan deleted for ${formatDate(selectedDate)}`);
        } catch (error) {
            console.error("Failed to delete meal plan:", error);
            alert("Failed to delete meal plan. Please try again.");
        }
    };

    const renderPopup = () => {
        if (!popupData) return null;

        const ingredients = parseIngredients(popupData.ingredient_parts);
        const quantities = popupData.ingredient_quantity ? parseIngredients(popupData.ingredient_quantity) : [];

        return (
            <div className="fixed inset-0 flex items-start justify-center py-10 bg-black/20 backdrop-blur-sm overflow-y-auto z-50">
                <div className="flex flex-col gap-5 p-5 rounded-lg shadow-[0_0_10px_rgba(0,0,0,0.2)] w-11/12 max-w-2xl bg-white">
                    <h4 className="font-bold text-xl text-center">{popupData.recipe_name}</h4>

                    <div className="flex flex-row justify-center text-center gap-10">
                        <div>
                            <p className="font-bold text-xl">{popupData.calories} kcal</p>
                            <p>Calories</p>
                        </div>

                        <div>
                            <p className="font-bold text-xl">{popupData.recipe_servings === 0 ? 1 : popupData.recipe_servings}</p>
                            <p>Serving(s)</p>
                        </div>
                    </div>

                    <div className="flex flex-row justify-center text-center gap-10">
                        <div>
                            <p className="font-bold text-xl">{formatTime(popupData.prep_time)}</p>
                            <p>Prep</p>
                        </div>

                        <div>
                            <p className="font-bold text-xl">{formatTime(popupData.cook_time)}</p>
                            <p>Cook</p>
                        </div>

                        <div>
                            <p className="font-bold text-xl">{formatTime(popupData.total_time)}</p>
                            <p>Total</p>
                        </div>
                    </div>

                    <div>
                        <p className="font-bold text-xl mb-2">Ingredients</p>
                        <div className="flex flex-wrap gap-1">
                            {ingredients.map((ingredient, index) => (
                                <span key={index} className="px-2 py-1 rounded-lg bg-gray-200 text-gray-800 inline-block">
                                    {quantities[index] ? `${quantities[index]} ${ingredient}` : ingredient}
                                </span>
                            ))}
                        </div>
                    </div>

                    <div>
                        <p className="font-bold text-xl mb-2">Instructions</p>
                        <p>{popupData.instructions}</p>
                    </div>
                    
                    <div className="flex flex-col gap-3">
                        <p className="font-bold text-xl mb-2">Nutrition</p>

                        <div className="mx-auto w-full max-w-md">
                            <div className="flex flex-row justify-between text-center gap-4 mb-3">
                                <div className="text-orange-500 p-2 rounded-lg bg-orange-100 w-1/3">
                                    <p className="font-bold">{popupData.carbohydrates} g</p>
                                    <p>Carbohydrates</p>
                                </div>

                                <div className="text-sky-500 p-2 rounded-lg bg-sky-100 w-1/3">
                                    <p className="font-bold">{popupData.protein} g</p>
                                    <p>Protein</p>
                                </div>

                                <div className="text-purple-500 p-2 rounded-lg bg-purple-100 w-1/3">
                                    <p className="font-bold">{popupData.fat} g</p>
                                    <p>Fat</p>
                                </div>
                            </div>
                            
                            <div className="flex flex-row justify-evenly text-center gap-4 mb-3">
                                <div className="p-2 rounded-lg bg-gray-100 w-1/2">
                                    <p className="font-bold">{popupData.sugar} g</p>
                                    <p>Sugar</p>
                                </div>

                                <div className="p-2 rounded-lg bg-gray-100 w-1/2">
                                    <p className="font-bold">{popupData.fiber} g</p>
                                    <p>Fiber</p>
                                </div>
                            </div>

                            <div className="flex flex-row justify-between text-center gap-2">
                                <div className="p-2 rounded-lg bg-gray-100 flex-1">
                                    <p className="font-bold text-sm">{popupData.saturated_fat} g</p>
                                    <p className="text-sm">Saturated Fat</p>
                                </div>

                                <div className="p-2 rounded-lg bg-gray-100 flex-1">
                                    <p className="font-bold text-sm">{popupData.cholesterol} mg</p>
                                    <p className="text-sm">Cholesterol</p>
                                </div>

                                <div className="p-2 rounded-lg bg-gray-100 flex-1">
                                    <p className="font-bold text-sm">{popupData.sodium} mg</p>
                                    <p className="text-sm">Sodium</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <Button variant="secondary" onClick={() => setPopupData(null)} className="place-self-center">Close</Button>
                </div>
            </div>
        );
    };

    return (
        <div className="flex flex-col max-w-[1024px] lg:min-w-[600px]">
            <div className="flex flex-col gap-5 m-5 p-3 rounded-lg shadow-[0_0_10px_rgba(0,0,0,0.2)] bg-slate-50">
                <div className="flex flex-col items-center justify-between pb-3">
                    <h1 className="font-bold text-4xl text-center p-2 w-full rounded-tl-lg rounded-tr-lg text-white bg-emerald-400">Meal Plan</h1>

                    <div className="flex flex-row items-center justify-between gap-5 rounded-bl-lg rounded-br-lg p-2 w-full bg-emerald-400">
                        <button onClick={handlePreviousDay}><img src={left_arrow} alt="Left Arrow" width="30px" height="30px" className="cursor-pointer" /></button>

                        <div className="flex flex-row gap-3">
                            <div className="relative">
                                <img src={calendar} alt="Calendar" width="30px" height="30px" className="cursor-pointer" 
                                    onClick={() => {
                                        setIsDatePickerVisible(true);
                                        setTimeout(() => {
                                            if (datePickerRef.current) {
                                                datePickerRef.current.focus();
                                                datePickerRef.current.showPicker();
                                            }
                                        }, 10);
                                    }}/>

                                {isDatePickerVisible && (
                                    <input ref={datePickerRef} type="date" className="absolute opacity-0 w-1 h-1" onChange={handleDateChange} onBlur={() => setIsDatePickerVisible(false)} value={formatDate(selectedDate)}/>
                                )}
                            </div>

                            <h1 className="font-bold text-xl text-white">{formatDisplayDate(selectedDate)}</h1>

                            {mealPlan && (
                                <button onClick={() => setIsDeleteConfirmVisible(true)} className="cursor-pointer px-2 rounded-full font-bold text-lg text-emerald-400 bg-white hover:bg-gray-100 transition-colors">✕</button>
                            )}
                        </div>

                        <button onClick={handleNextDay}><img src={right_arrow} alt="Right Arrow" width="30px" height="30px" className="cursor-pointer" /></button>
                    </div>
                </div>

                <div className="flex items-center justify-center w-full">
                    <div className="flex items-center">
                        {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((day, index) => {
                            const startOfWeek = getMondayOfWeek(selectedDate);
                            
                            const dotDate = new Date(startOfWeek);
                            dotDate.setDate(startOfWeek.getDate() + index);
                            
                            const isSelectedDay = 
                                dotDate.getDate() === selectedDate.getDate() && 
                                dotDate.getMonth() === selectedDate.getMonth() && 
                                dotDate.getFullYear() === selectedDate.getFullYear();
                            
                            return (
                                <div key={index} className="flex flex-col items-center mx-2">
                                    <span className={`text-xs mb-2 ${isSelectedDay ? 'text-emerald-400 font-medium' : 'text-gray-500'}`}>{day}</span>

                                    <div 
                                        onClick={() => handleDotClick(index)} 
                                        className={`w-6 h-6 rounded-full cursor-pointer ${isSelectedDay ? 'ring-2 ring-offset-2 ring-emerald-400' : ''} ${weekMealPlanStatus[index] ? 'bg-emerald-400 hover:bg-emerald-300 transition-colors' : 'bg-gray-300 hover:bg-gray-200 transition-colors'}`}>
                                    </div>

                                    <span className={`text-xs mt-2 ${isSelectedDay ? 'text-emerald-400 font-medium' : 'text-gray-500'}`}>{dotDate.getDate()}</span>
                                </div>
                            );
                        })}
                    </div>
                </div>

                <div className="flex flex-col gap-5 divide-y divide-dashed divide-slate-400">
                    {mealPlan ? (
                        ["breakfast", "lunch", "dinner"].map((mealType) => (
                            <div key={mealType} className="p-3">
                                <div className="flex flex-row items-center justify-between gap-2">
                                    <div className="flex flex-col gap-2 text-wrap max-w-3/4">
                                        <h2 className="font-bold text-2xl capitalize">{mealType}</h2>

                                        <p className="font-semibold text-gray-700">{mealPlan[mealType]?.recipe_name || "No recipe selected"}</p>
                                        <p className="text-gray-700">{mealPlan[mealType]?.calories || "N/A"} kcal</p>

                                        <div className="flex gap-3 mt-3">
                                            {finishedStates[`${mealType}_finished`] ? (
                                                <Button disabled>Finished</Button>
                                            ) : (
                                                <Button onClick={() => handleMarkMealFinished(mealType)}>Finish</Button>
                                            )}

                                            {mealPlan[mealType]?.recipe_id && recipeInteractions && recipeInteractions.get(mealPlan[mealType]?.recipe_id) !== 'dislike' && (
                                                <button onClick={() => handleInteraction(mealPlan[mealType].recipe_id, "like")} 
                                                    disabled={recipeInteractions.get(mealPlan[mealType].recipe_id) === 'like'}
                                                    className={`p-1 rounded-lg text-white ${recipeInteractions.get(mealPlan[mealType].recipe_id) === 'like' ? 'bg-gray-300' : 'cursor-pointer bg-emerald-400 hover:bg-emerald-300 transition-colors'}`}>
                                                    <img src={upvote} alt="Upvote" width="30px" height="30px"/>
                                                </button>
                                            )}

                                            {mealPlan[mealType]?.recipe_id && recipeInteractions && recipeInteractions.get(mealPlan[mealType]?.recipe_id) !== 'like' && (
                                                <button onClick={() => handleInteraction(mealPlan[mealType].recipe_id, "dislike")} 
                                                    disabled={recipeInteractions.get(mealPlan[mealType].recipe_id) === 'dislike'}
                                                    className={`p-1 rounded-lg text-white ${recipeInteractions.get(mealPlan[mealType].recipe_id) === 'dislike' ? 'bg-gray-300' : 'cursor-pointer bg-emerald-400 hover:bg-emerald-300 transition-colors'}`}>
                                                    <img src={downvote} alt="Downvote" width="30px" height="30px"/>
                                                </button>
                                            )}
                                        </div>
                                    </div>

                                    {mealPlan[mealType] && (
                                        <button onClick={() => handleShowPopup(mealPlan[mealType])} className="cursor-pointer p-1 bg-emerald-400 text-white rounded-full hover:bg-emerald-300 transition-colors"><img src={right_arrow} alt="Details" width="50px" height="50px" /></button>
                                    )}
                                </div>
                            </div>
                        ))
                    ) : (
                        <p className="py-10 text-center text-gray-700">No meal plan found for this date.</p>
                    )}
                </div>
            </div>

            <ConfirmDialog
                isVisible={isDeleteConfirmVisible}
                onConfirm={handleDeleteMealPlan}
                onCancel={() => setIsDeleteConfirmVisible(false)}
                title="Delete Meal Plan"
                message={`Are you sure you want to delete the meal plan for ${formatDisplayDate(selectedDate)}?`}
                confirmText="Delete"
                confirmVariant="danger"
            />

            {renderPopup()}
        </div>
    );
};

export default Calendar;