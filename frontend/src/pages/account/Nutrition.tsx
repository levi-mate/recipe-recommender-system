import React, { useState, useEffect, useRef } from "react";
import axios from "axios";

import left_arrow from "../../assets/left_arrow.svg";
import calendar from "../../assets/calendar.svg";
import right_arrow from "../../assets/right_arrow.svg";

const Nutrition: React.FC = () => {
    const [selectedDate, setSelectedDate] = useState(new Date());
    const [mealPlan, setMealPlan] = useState<any | null>(null);
    const [weeklyStats, setWeeklyStats] = useState<any | null>(null);
    const [isDatePickerVisible, setIsDatePickerVisible] = useState(false);
    const datePickerRef = useRef<HTMLInputElement>(null);
    const [targetCalories, setTargetCalories] = useState<number>(2000);
    const [nutritionEnabled, setNutritionEnabled] = useState<boolean>(false);

    useEffect(() => {
        const fetchNutritionInfo = async () => {
            try {
                const response = await axios.get("http://localhost:5077/get_nutrition_info", {
                    withCredentials: true,
                });

                const nutritionData = response.data.data || response.data;
                
                if (nutritionData) {
                    setTargetCalories(nutritionData.target_calories || 2000);
                    setNutritionEnabled(nutritionData.nutri_state || false);
                }
            } catch (error) {
                console.error("Failed to fetch nutrition info:", error);

                if (axios.isAxiosError(error) && error.response) {
                    console.error("Server response:", error.response.data);
                }
            }
        };
    
        fetchNutritionInfo();
    }, []);

    useEffect(() => {
        fetchMealPlan(selectedDate);
        fetchWeeklyStats(selectedDate);
    }, [selectedDate]);

    const fetchMealPlan = async (date: Date) => {
        try {
            const response = await axios.get("http://localhost:5077/get_meal_plan", {
                params: { meal_date: formatDate(date) },
                withCredentials: true,
            });

            setMealPlan(response.data.data || response.data);
        } catch (error) {
            console.error("Failed to fetch meal plan:", error);

            if (axios.isAxiosError(error) && error.response) {
                console.error("Server response:", error.response.data);
            }

            setMealPlan(null);
        }
    };

    const fetchWeeklyStats = async (date: Date) => {
        const startOfWeek = new Date(date);
        const day = date.getDay();
        const diff = day === 0 ? 6 : day - 1;
        startOfWeek.setDate(date.getDate() - diff);
        
        const endOfWeek = new Date(startOfWeek);
        endOfWeek.setDate(startOfWeek.getDate() + 6);
        
        try {
            const response = await axios.get("http://localhost:5077/get_weekly_meal_plan", {
                params: { start_date: formatDate(startOfWeek), end_date: formatDate(endOfWeek) },
                withCredentials: true,
            });

            setWeeklyStats(response.data.data || response.data);
        } catch (error) {
            console.error("Failed to fetch weekly stats:", error);

            if (axios.isAxiosError(error) && error.response) {
                console.error("Server response:", error.response.data);
            }
            
            setWeeklyStats(null);
        }
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

    const toggleDatePicker = () => {
        setIsDatePickerVisible(true);

        setTimeout(() => {
            if (datePickerRef.current) {
                datePickerRef.current.focus();
                datePickerRef.current.showPicker();
            }
        }, 10);
    };

    const calculateDailyStats = () => {
        if (!mealPlan) return null;
    
        const stats = {
            calories: 0,
            protein: 0,
            fat: 0,
            carbohydrates: 0,
            sugar: 0,
            fiber: 0,
            saturated_fat: 0,
            cholesterol: 0,
            sodium: 0,
        };
    
        ["breakfast", "lunch", "dinner"].forEach((mealType) => {
            const meal = mealPlan[mealType];
            if (meal) {
                stats.calories += meal.calories || 0;
                stats.protein += meal.protein || 0;
                stats.fat += meal.fat || 0;
                stats.carbohydrates += meal.carbohydrates || 0;
                stats.sugar += meal.sugar || 0;
                stats.fiber += meal.fiber || 0;
                stats.saturated_fat += meal.saturated_fat || 0;
                stats.cholesterol += meal.cholesterol || 0;
                stats.sodium += meal.sodium || 0;
            }
        });
    
        (Object.keys(stats) as (keyof typeof stats)[]).forEach((key) => {
            stats[key] = parseFloat((stats[key] as number).toFixed(1));
        });
    
        return stats;
    };

    const calculateWeeklyStats = () => {
        if (!weeklyStats) return null;
    
        const stats = {
            calories: 0,
            protein: 0,
            fat: 0,
            carbohydrates: 0,
            sugar: 0,
            fiber: 0,
            saturated_fat: 0,
            cholesterol: 0,
            sodium: 0,
        };
    
        weeklyStats.forEach((day: any) => {
            ["breakfast", "lunch", "dinner"].forEach((mealType) => {
                const meal = day[mealType];
                if (meal) {
                    stats.calories += meal.calories || 0;
                    stats.protein += meal.protein || 0;
                    stats.fat += meal.fat || 0;
                    stats.carbohydrates += meal.carbohydrates || 0;
                    stats.sugar += meal.sugar || 0;
                    stats.fiber += meal.fiber || 0;
                    stats.saturated_fat += meal.saturated_fat || 0;
                    stats.cholesterol += meal.cholesterol || 0;
                    stats.sodium += meal.sodium || 0;
                }
            });
        });
    
        (Object.keys(stats) as (keyof typeof stats)[]).forEach((key) => {
            stats[key] = parseFloat((stats[key] as number).toFixed(1));
        });
    
        return stats;
    };

    const dailyStats = calculateDailyStats();
    const weeklyStatsSummary = calculateWeeklyStats();

    return (
        <div className="flex flex-col max-w-[1024px] lg:min-w-[600px]">
            <div className="flex flex-col gap-5 m-5 p-3 rounded-lg shadow-[0_0_10px_rgba(0,0,0,0.2)] bg-slate-50">
                <div className="flex flex-col items-center justify-between pb-3">
                    <h1 className="font-bold text-4xl text-center p-2 w-full rounded-tl-lg rounded-tr-lg text-white bg-emerald-400">Nutrition</h1>

                    <div className="flex flex-row items-center justify-between gap-5 rounded-bl-lg rounded-br-lg p-2 w-full bg-emerald-400">
                        <button onClick={handlePreviousDay}><img src={left_arrow} alt="Left Arrow" width="30px" height="30px" className="cursor-pointer" /></button>

                        <div className="flex flex-row gap-2">
                            <div className="relative">
                                <img src={calendar} alt="Calendar" width="30px" height="30px" className="cursor-pointer" onClick={toggleDatePicker}/>

                                {isDatePickerVisible && (
                                    <input ref={datePickerRef} type="date" className="absolute opacity-0 w-1 h-1" onChange={handleDateChange} onBlur={() => setIsDatePickerVisible(false)} value={formatDate(selectedDate)}/>
                                )}
                            </div>

                            <h1 className="font-bold text-xl text-white">{formatDisplayDate(selectedDate)}</h1>
                        </div>

                        <button onClick={handleNextDay}><img src={right_arrow} alt="Right Arrow" width="30px" height="30px" className="cursor-pointer" /></button>
                    </div>
                </div>

                <div className="flex flex-col justify-between gap-5 divide-y divide-dashed divide-slate-400">
                    {dailyStats ? (
                        <div className="flex flex-col gap-3 pb-10">
                            <div className="flex flex-row gap-3 items-center justify-evenly text-center mb-3">
                                <h2 className="font-bold text-2xl flex-1">Daily</h2>

                                <div className="p-2 rounded-lg flex-1">
                                    <div className="flex items-center gap-2 justify-center">
                                        <span className="font-bold text-2xl">{dailyStats.calories}</span>

                                        {nutritionEnabled ? (
                                            <span className="text-gray-500">/ {targetCalories} kcal</span>
                                        ) : (
                                            <span className="text-gray-500"> kcal</span>
                                        )}
                                    </div>

                                    {nutritionEnabled && (
                                        <div className="w-full h-4 bg-gray-200 rounded-full mt-2 overflow-hidden">
                                            <div className="h-full bg-emerald-400 rounded-full transition-all duration-500" style={{ width: `${Math.min(100, (dailyStats.calories / targetCalories) * 100)}%` }}></div>
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div className="flex flex-row gap-3 justify-between text-center mb-3">
                                <div className="p-2 flex-1">
                                    <p className="font-bold text-lg text-orange-500">{dailyStats.carbohydrates} g</p>
                                    <p className="text-orange-500">Carbohydrates</p>
                                </div>

                                <div className="w-1 bg-gray-200 self-stretch"></div>

                                <div className="p-2 flex-1">
                                    <p className="font-bold text-lg text-sky-500">{dailyStats.protein} g</p>
                                    <p className="text-sky-500">Protein</p>
                                </div>

                                <div className="w-1 bg-gray-200 self-stretch"></div>

                                <div className="p-2 flex-1">
                                    <p className="font-bold text-lg text-purple-500">{dailyStats.fat} g</p>
                                    <p className="text-purple-500">Fat</p>
                                </div>
                            </div>

                            <div className="rounded-lg bg-gray-200 divide-y-4 divide-solid divide-white">
                                <div className="flex flex-row gap-3 justify-evenly text-center mb-3">
                                    <div className="p-2 rounded-lg">
                                        <p className="font-bold text-lg">{dailyStats.sugar} g</p>
                                        <p>Sugar</p>
                                    </div>

                                    <div className="p-2 rounded-lg">
                                        <p className="font-bold text-lg">{dailyStats.fiber} g</p>
                                        <p>Fiber</p>
                                    </div>
                                </div>
                                
                                <div className="flex flex-row gap-3 justify-between text-center">
                                    <div className="p-2 rounded-lg text-sm flex-1">
                                        <p className="font-bold">{dailyStats.saturated_fat} g</p>
                                        <p>Saturated Fat</p>
                                    </div>

                                    <div className="p-2 rounded-lg text-sm flex-1">
                                        <p className="font-bold">{dailyStats.cholesterol} mg</p>
                                        <p>Cholesterol</p>
                                    </div>

                                    <div className="p-2 rounded-lg text-sm flex-1">
                                        <p className="font-bold">{dailyStats.sodium} mg</p>
                                        <p>Sodium</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="flex flex-col gap-3">
                            <h2 className="font-bold text-2xl text-center flex-1">Daily</h2>
                            <p className="py-5 text-center text-gray-500">No nutritional data available for this day.</p>
                        </div>
                    )}

                    {weeklyStatsSummary ? (
                        <div className="flex flex-col gap-3">
                            <div className="flex flex-row gap-3 items-center justify-evenly text-center mb-3">
                                <h2 className="font-bold text-2xl flex-1">Weekly</h2>

                                <div className="p-2 rounded-lg flex-1">
                                    <div className="flex items-center gap-2 justify-center">
                                        <span className="font-bold text-2xl">{weeklyStatsSummary.calories}</span>

                                        {nutritionEnabled ? (
                                            <span className="text-gray-500">/ {targetCalories * 7} kcal</span>
                                        ) : (
                                            <span className="text-gray-500"> kcal</span>
                                        )}
                                    </div>

                                    {nutritionEnabled && (
                                        <div className="w-full h-4 bg-gray-200 rounded-full mt-2 overflow-hidden">
                                            <div className="h-full bg-emerald-400 rounded-full transition-all duration-500" style={{ width: `${Math.min(100, (weeklyStatsSummary.calories / (targetCalories * 7)) * 100)}%` }}></div>
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div className="flex flex-row gap-3 justify-between text-center mb-3">
                                <div className="p-2 flex-1">
                                    <p className="font-bold text-lg text-orange-500">{weeklyStatsSummary.carbohydrates} g</p>
                                    <p className="text-orange-500">Carbohydrates</p>
                                </div>

                                <div className="w-1 bg-gray-200 self-stretch"></div>

                                <div className="p-2 flex-1">
                                    <p className="font-bold text-lg text-sky-500">{weeklyStatsSummary.protein} g</p>
                                    <p className="text-sky-500">Protein</p>
                                </div>

                                <div className="w-1 bg-gray-200 self-stretch"></div>

                                <div className="p-2 flex-1">
                                    <p className="font-bold text-lg text-purple-500">{weeklyStatsSummary.fat} g</p>
                                    <p className="text-purple-500">Fat</p>
                                </div>
                            </div>

                            <div className="rounded-lg bg-gray-200 divide-y-4 divide-solid divide-white">
                                <div className="flex flex-row gap-3 justify-evenly text-center mb-3">
                                    <div className="p-2 rounded-lg">
                                        <p className="font-bold text-lg">{weeklyStatsSummary.sugar} g</p>
                                        <p>Sugar</p>
                                    </div>

                                    <div className="p-2 rounded-lg">
                                        <p className="font-bold text-lg">{weeklyStatsSummary.fiber} g</p>
                                        <p>Fiber</p>
                                    </div>
                                </div>
                                
                                <div className="flex flex-row gap-3 justify-between text-center">
                                    <div className="p-2 rounded-lg text-sm flex-1">
                                        <p className="font-bold">{weeklyStatsSummary.saturated_fat} g</p>
                                        <p>Saturated Fat</p>
                                    </div>

                                    <div className="p-2 rounded-lg text-sm flex-1">
                                        <p className="font-bold">{weeklyStatsSummary.cholesterol} mg</p>
                                        <p>Cholesterol</p>
                                    </div>

                                    <div className="p-2 rounded-lg text-sm flex-1">
                                        <p className="font-bold">{weeklyStatsSummary.sodium} mg</p>
                                        <p>Sodium</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="flex flex-col gap-3">
                            <h2 className="font-bold text-2xl text-center flex-1">Weekly</h2>
                            <p className="py-5 text-center text-gray-500">No nutritional data available for this week.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Nutrition;