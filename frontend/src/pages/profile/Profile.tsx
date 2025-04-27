import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { useModal } from "../../hooks/useModal";

import Button from "../../components/common/Button";
import Input from "../../components/common/Input";
import ConfirmDialog from "../../components/common/Confirm";
import AutoComplete from "../../components/common/AutoComplete";
import PageHeader from "../../components/common/Header";
import ToggleSwitch from "../../components/common/Toggle";
import Modal from "../../components/common/Modal";
import ProfileSection from "../../components/common/ProfileSection";
import CategoryBadge from "../../components/common/CategoryBadge";

import pers_icon from "../../assets/pers_icon.svg";

const Profile: React.FC = () => {
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [updateError, setUpdateError] = useState<string | null>(null);
    
    const [username, setUsername] = useState<string>("");
    const [currentUsername, setCurrentUsername] = useState<string>("");
    const [newUsername, setNewUsername] = useState<string>("");
    const [currentEmail, setCurrentEmail] = useState<string>("");
    const [newEmail, setNewEmail] = useState<string>("");
    const [currentPassword, setCurrentPassword] = useState<string>("");
    const [newPassword, setNewPassword] = useState<string>("");
    const [confirmPassword, setConfirmPassword] = useState<string>("");
    
    const [showNutritionStats, setShowNutritionStats] = useState<boolean>(false);
    const [isNutritionConfirmVisible, setIsNutritionConfirmVisible] = useState<boolean>(false);
    //const [isEditStatsPopupVisible, setIsEditStatsPopupVisible] = useState<boolean>(false);
    const [useMetricUnits, setUseMetricUnits] = useState<boolean>(true);
    const [sex, setSex] = useState<'male' | 'female' | ''>('');
    const [age, setAge] = useState<number | ''>('');
    const [heightCm, setHeightCm] = useState<number | ''>('');
    const [heightFeet, setHeightFeet] = useState<number | ''>('');
    const [heightInches, setHeightInches] = useState<number | ''>('');
    const [weightKg, setWeightKg] = useState<number | ''>('');
    const [weightGoal, setWeightGoal] = useState<'lose' | 'maintain' | 'gain'>('maintain');
    const [targetCalories, setTargetCalories] = useState<number>(2000);
    const [activityLevel, setActivityLevel] = useState<'sedentary' | 'low' | 'moderate' | 'heavy'>('low');
    
    const [preferredCategories, setPreferredCategories] = useState<string[]>([]);
    const [isDeletePopupVisible, setIsDeletePopupVisible] = useState<boolean>(false);
    const [categoryToDelete, setCategoryToDelete] = useState<string>("");
    //const [isAddPopupVisible, setIsAddPopupVisible] = useState<boolean>(false);
    const [searchQuery, setSearchQuery] = useState<string>("");
    const [categorySuggestions, setCategorySuggestions] = useState<string[]>([]);
    const [selectedCategory, setSelectedCategory] = useState<string>("");

    const [excludedCategories, setExcludedCategories] = useState<string[]>([]);
    const [isExcludedDeletePopupVisible, setIsExcludedDeletePopupVisible] = useState<boolean>(false);
    const [categoryToDeleteFromExcluded, setCategoryToDeleteFromExcluded] = useState<string>("");
    //const [isAddExcludedPopupVisible, setIsAddExcludedPopupVisible] = useState<boolean>(false);
    const [excludedSearchQuery, setExcludedSearchQuery] = useState<string>("");
    const [excludedCategorySuggestions, setExcludedCategorySuggestions] = useState<string[]>([]);
    const [selectedExcludedCategory, setSelectedExcludedCategory] = useState<string>("");

    const preferredCategoryAutocompleteRef = useRef<HTMLDivElement>(null);
    const excludedCategoryAutocompleteRef = useRef<HTMLDivElement>(null);

    const usernameModal = useModal();
    const emailModal = useModal();
    const passwordModal = useModal();
    const statsModal = useModal();
    const addCategoryModal = useModal();
    const addExcludedCategoryModal = useModal();

    useEffect(() => {
        const fetchUserData = async () => {
            try {
                setIsLoading(true);
                const profileResponse = await axios.get("http://localhost:5077/get_user_profile", {
                    withCredentials: true,
                });

                const profileData = profileResponse.data.data || {};
                setUsername(profileData.username || "User");
                setCurrentUsername(profileData.username || "");
                setCurrentEmail(profileData.email || "");
                
                const categoriesResponse = await axios.get("http://localhost:5077/get_preferred_categories", {
                    withCredentials: true,
                });

                setPreferredCategories(categoriesResponse.data.data || []);

                const excludedCategoriesResponse = await axios.get("http://localhost:5077/get_excluded_categories", {
                    withCredentials: true,
                });

                setExcludedCategories(excludedCategoriesResponse.data.data || []);
                
                const nutritionResponse = await axios.get("http://localhost:5077/get_nutrition_info", {
                    withCredentials: true,
                });
                
                const nutritionData = nutritionResponse.data.data || {};
                setShowNutritionStats(nutritionData.nutri_state);
                setSex(nutritionData.sex || '');
                setAge(nutritionData.age || '');
                setHeightCm(nutritionData.height || '');
                setWeightKg(nutritionData.weight || '');
                setWeightGoal(nutritionData.goal || 'maintain');
                setTargetCalories(nutritionData.target_calories || 2000);
                setActivityLevel(nutritionData.activity_level || 'low');
                
            } catch (error) {
                console.error("Failed to fetch user data:", error);

                if (axios.isAxiosError(error) && error.response?.data?.error) {
                    console.error("Server error:", error.response.data.error);
                }
            } finally {
                setIsLoading(false);
            }
        };

        fetchUserData();
    }, []);

    const handleUpdateUsername = () => {
        setNewUsername(currentUsername);
        setUpdateError(null);
        usernameModal.open();
    };

    const submitUsernameUpdate = async () => {
        if (!newUsername.trim()) {
            setUpdateError("Username cannot be empty");
            return;
        }

        try {
            const response = await axios.post(
                "http://localhost:5077/update_username",
                { username: newUsername },
                { withCredentials: true }
            );

            if (response.data.success) {
                setUsername(newUsername);
                setCurrentUsername(newUsername);
                usernameModal.close();
            } else if (response.data.error) {
                setUpdateError(response.data.error);
            }
        } catch (error) {
            console.error("Failed to update username:", error);

            if (axios.isAxiosError(error) && error.response?.data?.error) {
                setUpdateError(error.response.data.error);
            } else {
                setUpdateError("Failed to update username");
            }
        }
    };

    const handleUpdateEmail = () => {
        setNewEmail(currentEmail);
        setUpdateError(null);
        emailModal.open();
    };

    const isValidEmail = (email: string) => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    };

    const submitEmailUpdate = async () => {
        if (!newEmail.trim() || !isValidEmail(newEmail)) {
            setUpdateError("Please enter a valid email address");
            return;
        }

        try {
            const response = await axios.post(
                "http://localhost:5077/update_email",
                { email: newEmail },
                { withCredentials: true }
            );

            if (response.data.success) {
                setCurrentEmail(newEmail);
                emailModal.close();
            } else if (response.data.error) {
                setUpdateError(response.data.error);
            }
        } catch (error) {
            console.error("Failed to update email:", error);

            if (axios.isAxiosError(error) && error.response?.data?.error) {
                setUpdateError(error.response.data.error);
            } else {
                setUpdateError("Failed to update email");
            }
        }
    };

    const handleUpdatePassword = () => {
        setCurrentPassword("");
        setNewPassword("");
        setConfirmPassword("");
        setUpdateError(null);
        passwordModal.open();
    };

    const submitPasswordUpdate = async () => {
        if (!currentPassword) {
            setUpdateError("Please enter your current password");
            return;
        }

        if (!newPassword) {
            setUpdateError("Please enter a new password");
            return;
        }

        if (newPassword !== confirmPassword) {
            setUpdateError("New passwords do not match");
            return;
        }

        try {
            const response = await axios.post(
                "http://localhost:5077/update_password",
                { 
                    current_password: currentPassword,
                    new_password: newPassword 
                },
                { withCredentials: true }
            );

            if (response.data.success) {
                passwordModal.close();
            } else if (response.data.error) {
                setUpdateError(response.data.error);
            }
        } catch (error) {
            console.error("Failed to update password:", error);

            if (axios.isAxiosError(error) && error.response?.data?.error) {
                setUpdateError(error.response.data.error);
            } else {
                setUpdateError("Failed to update password");
            }
        }
    };

    const toggleNutritionStats = () => {
        setIsNutritionConfirmVisible(true);
    };
    
    const confirmToggleNutritionStats = async () => {
        const newState = !showNutritionStats;
        setShowNutritionStats(newState);
        
        try {
            const response = await axios.post(
                "http://localhost:5077/update_nutrition_info",
                {
                    nutri_state: newState,
                    sex,
                    age: age !== '' ? Number(age) : null,
                    height: heightCm !== '' ? Number(heightCm) : null,
                    weight: weightKg !== '' ? Number(weightKg) : null,
                    bmi: calculateBMI(),
                    goal: weightGoal,
                    activity_level: activityLevel,
                    target_calories: targetCalories
                },

                { withCredentials: true }
            );

            if (!response.data.success) {
                console.error("Failed to update nutrition state:", response.data.error);
                setShowNutritionStats(!newState);
            }
        } catch (error) {
            console.error("Failed to update nutrition state:", error);

            if (axios.isAxiosError(error) && error.response?.data?.error) {
                console.error("Server error:", error.response.data.error);
            }

            setShowNutritionStats(!newState);
        } finally {
            setIsNutritionConfirmVisible(false);
        }
    };

    const cmToFeetInches = (cm: number): { feet: number, inches: number } => {
        const totalInches = cm / 2.54;
        const feet = Math.floor(totalInches / 12);
        const inches = Math.round(totalInches % 12);
        return { feet, inches };
    };
    
    const kgToLbs = (kg: number): number => {
        return Math.round(kg * 2.20462 * 10) / 10;
    };

    const calculateBMI = (): number | null => {
        if (typeof heightCm === 'number' && typeof weightKg === 'number' && heightCm > 0) {
            // BMI = weight(kg) / (height(m))^2
            const heightM = heightCm / 100;
            return Number((weightKg / (heightM * heightM)).toFixed(1));
        }
        return null;
    };

    const getBMICategory = (bmi: number): string => {
        if (bmi < 18.5) return 'Underweight';
        if (bmi < 25) return 'Normal Weight';
        if (bmi < 30) return 'Overweight';
        return 'Obese';
    };
    
    const calculateTargetCalories = async (
        sexVal: 'male' | 'female', 
        ageVal: number, 
        heightVal: number, 
        weightVal: number, 
        goalVal: string,
        activityVal: string
    ) => {
        try {
            const response = await axios.post(
                "http://localhost:5077/calculate_target_calories",
                {
                    sex: sexVal,
                    age: ageVal,
                    height: heightVal,
                    weight: weightVal,
                    goal: goalVal,
                    activity_level: activityVal
                },

                { withCredentials: true }
            );
            
            const data = response.data.data || {};

            return {
                targetCalories: data.target_calories || 2000,
                bmi: data.bmi || calculateBMI()
            };
        } catch (error) {
            console.error("Failed to calculate target calories:", error);

            if (axios.isAxiosError(error) && error.response?.data?.error) {
                console.error("Server error:", error.response.data.error);
            }

            return {
                targetCalories: 2000,
                bmi: calculateBMI()
            };
        }
    };
    
    const handleSaveStats = async () => {
        let finalHeightCm = heightCm;
        let finalWeightKg = weightKg;
        
        if (!useMetricUnits && typeof heightFeet === 'number' && typeof heightInches === 'number' && typeof weightKg === 'number') {
            finalHeightCm = Math.round((heightFeet * 30.48) + (heightInches * 2.54));
            setHeightCm(finalHeightCm);
            
            finalWeightKg = Math.round((weightKg * 0.453592) * 10) / 10;
            setWeightKg(finalWeightKg);
        }
        
        if (sex && age !== '' && finalHeightCm && finalWeightKg) {
            const { targetCalories: newTargetCalories, bmi: newBmi } = 
                await calculateTargetCalories(
                    sex, 
                    Number(age), 
                    Number(finalHeightCm), 
                    Number(finalWeightKg), 
                    weightGoal,
                    activityLevel
                );
            
            setTargetCalories(newTargetCalories);
            
            try {
                const response = await axios.post(
                    "http://localhost:5077/update_nutrition_info",
                    {
                        nutri_state: showNutritionStats,
                        sex: sex,
                        age: Number(age),
                        height: Number(finalHeightCm),
                        weight: Number(finalWeightKg),
                        bmi: newBmi,
                        goal: weightGoal,
                        activity_level: activityLevel,
                        target_calories: newTargetCalories
                    },

                    { withCredentials: true }
                );
                
                if (response.data.success) {
                    console.log("Nutrition data saved successfully");
                } else {
                    console.error("Failed to save nutrition data:", response.data.error);
                }
            } catch (error) {
                console.error("Failed to save nutrition data:", error);

                if (axios.isAxiosError(error) && error.response?.data?.error) {
                    console.error("Server error:", error.response.data.error);
                }
            }
        }
        
        statsModal.close();
    };

    const handleDeleteCategory = (category: string) => {
        setCategoryToDelete(category);
        setIsDeletePopupVisible(true);
    };

    const cancelDelete = () => {
        setIsDeletePopupVisible(false);
        setCategoryToDelete("");
    };

    const confirmDeleteCategory = async () => {
        try {
            const response = await axios.post(
                "http://localhost:5077/delete_preferred_category",
                { category: categoryToDelete },
                { withCredentials: true }
            );

            if (response.data.success) {
                setPreferredCategories(prev => prev.filter(cat => cat !== categoryToDelete));
            } else {
                console.error("Failed to delete category:", response.data.error);
                alert("Failed to delete category: " + response.data.error);
            }
        } catch (error) {
            console.error("Failed to delete category:", error);

            if (axios.isAxiosError(error) && error.response?.data?.error) {
                console.error("Server error:", error.response.data.error);
                alert("Failed to delete category: " + error.response.data.error);
            } else {
                alert("Failed to delete category");
            }
        } finally {
            setIsDeletePopupVisible(false);
            setCategoryToDelete("");
        }
    };

    const handleAddCategoryClick = () => {
        addCategoryModal.open();
    };

    const handleSearchChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const query = e.target.value;
        setSearchQuery(query);

        if (!query) {
            setCategorySuggestions([]);
            return;
        }

        try {
            const response = await axios.get("http://localhost:5077/autocomplete_categories", {
                params: { query },
                withCredentials: true,
            });
            
            let categories = [];
            if (response.data && response.data.data) {
                categories = response.data.data;
            } else if (Array.isArray(response.data)) {
                categories = response.data;
            } else {
                console.error("Unexpected API response format:", response.data);
                categories = [];
            }

            const filteredCategories = categories
                .filter((category: string) => !preferredCategories.includes(category))
                .slice(0, 10);
                
            setCategorySuggestions(filteredCategories);
        } catch (error) {
            console.error("Failed to fetch category suggestions:", error);

            if (axios.isAxiosError(error) && error.response?.data?.error) {
                console.error("Server error:", error.response.data.error);
            }

            setCategorySuggestions([]);
        }
    };

    const handleCategorySelect = (category: string) => {
        setSelectedCategory(category);
        setSearchQuery(category);
        setCategorySuggestions([]);
    };

    const cancelAdd = () => {
        addCategoryModal.close();
        setSelectedCategory("");
        setSearchQuery("");
    };

    const handleAddCategory = async () => {
        if (!selectedCategory) return;

        try {
            const response = await axios.post(
                "http://localhost:5077/add_preferred_category",
                { category: selectedCategory },
                { withCredentials: true }
            );

            if (response.data.success) {
                setPreferredCategories(prev => [...prev, selectedCategory]);
            } else {
                console.error("Failed to add category:", response.data.error);
                alert("Failed to add category: " + response.data.error);
            }
        } catch (error) {
            console.error("Failed to add category:", error);

            if (axios.isAxiosError(error) && error.response?.data?.error) {
                console.error("Server error:", error.response.data.error);
                alert("Failed to add category: " + error.response.data.error);
            } else {
                alert("Failed to add category");
            }
        } finally {
            addCategoryModal.close();
            setSelectedCategory("");
            setSearchQuery("");
        }
    };

    const handleDeleteExcludedCategory = (category: string) => {
        setCategoryToDeleteFromExcluded(category);
        setIsExcludedDeletePopupVisible(true);
    };

    const cancelDeleteExcluded = () => {
        setIsExcludedDeletePopupVisible(false);
        setCategoryToDeleteFromExcluded("");
    };
    
    const confirmDeleteExcludedCategory = async () => {
        try {
            const response = await axios.post(
                "http://localhost:5077/delete_excluded_category",
                { category: categoryToDeleteFromExcluded },
                { withCredentials: true }
            );
    
            if (response.data.success) {
                setExcludedCategories(prev => prev.filter(cat => cat !== categoryToDeleteFromExcluded));
            } else {
                console.error("Failed to delete excluded category:", response.data.error);
                alert("Failed to delete excluded category: " + response.data.error);
            }
        } catch (error) {
            console.error("Failed to delete excluded category:", error);

            if (axios.isAxiosError(error) && error.response?.data?.error) {
                console.error("Server error:", error.response.data.error);
                alert("Failed to delete excluded category: " + error.response.data.error);
            } else {
                alert("Failed to delete excluded category");
            }
        } finally {
            setIsExcludedDeletePopupVisible(false);
            setCategoryToDeleteFromExcluded("");
        }
    };
    
    const handleAddExcludedCategoryClick = () => {
        addExcludedCategoryModal.open();
    };
    
    const handleExcludedSearchChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const query = e.target.value;
        setExcludedSearchQuery(query);
    
        if (!query) {
            setExcludedCategorySuggestions([]);
            return;
        }
    
        try {
            const response = await axios.get("http://localhost:5077/autocomplete_categories", {
                params: { query },
                withCredentials: true,
            });
            
            let categories = [];
            if (response.data && response.data.data) {
                categories = response.data.data;
            } else if (Array.isArray(response.data)) {
                categories = response.data;
            } else {
                console.error("Unexpected API response format:", response.data);
                categories = [];
            }

            const filteredCategories = categories
                .filter((category: string) => !preferredCategories.includes(category))
                .slice(0, 10);
                
            setExcludedCategorySuggestions(filteredCategories);
        } catch (error) {
            console.error("Failed to fetch category suggestions:", error);

            if (axios.isAxiosError(error) && error.response?.data?.error) {
                console.error("Server error:", error.response.data.error);
            }

            setExcludedCategorySuggestions([]);
        }
    };
    
    const handleExcludedCategorySelect = (category: string) => {
        setSelectedExcludedCategory(category);
        setExcludedSearchQuery(category);
        setExcludedCategorySuggestions([]);
    };

    const cancelAddExcluded = () => {
        addExcludedCategoryModal.close();
        setSelectedExcludedCategory("");
        setExcludedSearchQuery("");
    };
    
    const handleAddExcludedCategory = async () => {
        if (!selectedExcludedCategory) return;
    
        try {
            const response = await axios.post(
                "http://localhost:5077/add_excluded_category",
                { category: selectedExcludedCategory },
                { withCredentials: true }
            );
    
            if (response.data.success) {
                setExcludedCategories(prev => [...prev, selectedExcludedCategory]);
            } else {
                console.error("Failed to add excluded category:", response.data.error);
                alert("Failed to add excluded category: " + response.data.error);
            }
        } catch (error) {
            console.error("Failed to add excluded category:", error);

            if (axios.isAxiosError(error) && error.response?.data?.error) {
                console.error("Server error:", error.response.data.error);
                alert(error.response.data.error);
            } else {
                alert("Failed to add excluded category");
            }
        } finally {
            addExcludedCategoryModal.close();
            setSelectedExcludedCategory("");
            setExcludedSearchQuery("");
        }
    };

    return (
        <>
            <div className="flex flex-col items-center gap-3 m-5 max-w-[600px] lg:min-w-[600px] md:mx-auto rounded-lg shadow-[0_0_10px_rgba(0,0,0,0.2)] bg-slate-50">
                <PageHeader title="Profile" />
                
                <div className="flex flex-col p-5 w-full divide-y-2 divide-gray-300">
                    <ProfileSection title="">
                        <img src={pers_icon} alt="Profile Icon" className="p-1 w-32 h-32 mb-5 rounded-full border-2 border-emerald-400 bg-emerald-400"/>
                        <p className="font-bold text-xl">{isLoading ? "Loading..." : username}</p>
                    </ProfileSection>

                    <ProfileSection title="Account Management">
                        <Button onClick={handleUpdateUsername} className="w-[200px]">Update Username</Button>
                        <Button onClick={handleUpdateEmail} className="w-[200px]">Update Email</Button>
                        <Button onClick={handleUpdatePassword} className="w-[200px]">Update Password</Button>
                    </ProfileSection>

                    <ProfileSection title="Nutrition Stats" description="Nutrition-based recommendations will be based on these stats">
                        <div className="flex justify-between w-full items-center">
                            <div></div>
                            <ToggleSwitch isOn={showNutritionStats} toggle={toggleNutritionStats}/>
                        </div>
                        
                        {showNutritionStats && (
                            <>
                                <div className="w-full grid grid-cols-1 lg:grid-cols-2 gap-3 bg-gray-50 rounded-lg">
                                    {sex && (
                                        <div className="flex flex-col items-center justify-center gap-2 p-1 rounded-lg bg-gray-200">
                                            <p>{sex === 'male' ? 'Male' : 'Female'}</p>
                                            <p className="font-bold">Sex</p>
                                        </div>
                                    )}

                                    {age !== '' && (
                                        <div className="flex flex-col items-center justify-center gap-2 p-1 rounded-lg bg-gray-200">
                                            <p>{age}</p>
                                            <p className="font-bold">Age</p>
                                        </div>
                                    )}

                                    {heightCm !== '' && (
                                        <div className="flex flex-col items-center justify-center gap-2 p-1 rounded-lg bg-gray-200">
                                            <div className="flex flex-row gap-1 text-center">
                                                <p>{heightCm} cm</p>
                                                <p>•</p>
                                                {typeof heightCm === 'number' && (
                                                    <p>{cmToFeetInches(heightCm).feet}'{cmToFeetInches(heightCm).inches}"</p>
                                                )}
                                            </div>
                                            <p className="font-bold">Height</p>
                                        </div>
                                    )}

                                    {weightKg !== '' && (
                                        <div className="flex flex-col items-center justify-center gap-2 p-1 rounded-lg bg-gray-200">
                                            <div className="flex flex-row gap-1 text-center">
                                                <p>{weightKg} kg</p>
                                                <p>•</p>
                                                {typeof weightKg === 'number' && (
                                                    <p>{kgToLbs(weightKg)} lbs</p>
                                                )}
                                            </div>
                                            <p className="font-bold">Weight</p>
                                        </div>
                                    )}

                                    {calculateBMI() && (
                                        <div className="flex flex-col items-center justify-center gap-2 p-1 rounded-lg bg-gray-200">
                                            <p>{calculateBMI()} ({getBMICategory(calculateBMI() as number)})</p>
                                            <p className="font-bold">BMI</p>
                                        </div>
                                    )}

                                    {weightGoal && (
                                        <div className="flex flex-col items-center justify-center gap-2 p-1 rounded-lg bg-gray-200">
                                            <p>{weightGoal === 'lose' ? 'Lose Weight' : weightGoal === 'gain' ? 'Gain Weight' : 'Maintain Weight'}</p>
                                            <p className="font-bold">Goal</p>
                                        </div>
                                    )}

                                    {activityLevel && (
                                        <div className="flex flex-col items-center justify-center gap-2 p-1 rounded-lg bg-gray-200">
                                            <p>{activityLevel.charAt(0).toUpperCase() + activityLevel.slice(1)}</p>
                                            <p className="font-bold">Activity</p>
                                        </div>
                                    )}

                                    <div className="flex flex-col items-center justify-center gap-2 p-1 rounded-lg bg-gray-200">
                                        <p>{targetCalories} kcal/ day</p>
                                        <p className="font-bold">Calories</p>
                                    </div>
                                </div>
                                
                                <Button onClick={() => statsModal.open()}>Update Stats</Button>
                            </>
                        )}
                    </ProfileSection>

                    <ProfileSection title="Preferred Categories" description="Recipes with these categories will be prioritised for recommendations">
                        {isLoading ? (
                            <p>Loading categories...</p>
                        ) : preferredCategories.length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 w-full">
                                {preferredCategories.map((category, index) => (
                                    <CategoryBadge key={index} category={category} onDelete={() => handleDeleteCategory(category)}/>
                                ))}
                            </div>
                        ) : (
                            <p className="text-gray-500">No preferred categories found.</p>
                        )}
                        
                        <Button onClick={handleAddCategoryClick}>Add Category</Button>
                    </ProfileSection>

                    <ProfileSection title="Excluded Categories" description="Recipes with these categories will never be recommended">
                        {isLoading ? (
                            <p>Loading categories...</p>
                        ) : excludedCategories.length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 w-full">
                                {excludedCategories.map((category, index) => (
                                    <CategoryBadge key={index} category={category} onDelete={() => handleDeleteExcludedCategory(category)} variant="danger"/>
                                ))}
                            </div>
                        ) : (
                            <p className="text-gray-500">No excluded categories set.</p>
                        )}
                        
                        <Button variant="danger" onClick={handleAddExcludedCategoryClick}>Exclude Category</Button>
                    </ProfileSection>
                </div>

                <Modal isVisible={usernameModal.isOpen} onClose={usernameModal.close} title="Update Username">
                    <div className="mb-4">
                        <label className="block mb-2 font-medium">Current Username</label>
                        <p className="p-2 border rounded-lg bg-gray-50">{currentUsername}</p>
                    </div>
                    
                    <Input type="text" value={newUsername} onChange={(e) => setNewUsername(e.target.value)} label="New Username" placeholder="Enter new username" error={updateError || undefined}/>
                    
                    <div className="flex justify-between gap-3 mt-5">
                        <Button variant="secondary" onClick={usernameModal.close}>Cancel</Button>
                        <Button onClick={submitUsernameUpdate}>Update</Button>
                    </div>
                </Modal>

                <Modal isVisible={emailModal.isOpen} onClose={emailModal.close} title="Update Email">  
                    <div className="mb-4">
                        <label className="block mb-2 font-medium">Current Email</label>
                        <p className="p-2 border rounded-lg bg-gray-50">{currentEmail}</p>
                    </div>
                    
                    <Input type="email" value={newEmail} onChange={(e) => setNewEmail(e.target.value)} label="New Email" placeholder="Enter new email" error={updateError || undefined}/>
                    
                    {updateError && <p className="text-red-500 mb-4">{updateError}</p>}
                    
                    <div className="flex justify-between gap-3">
                        <Button variant="secondary" onClick={emailModal.close}>Cancel</Button>
                        <Button onClick={submitEmailUpdate}>Update</Button>
                    </div>
                </Modal>

                <Modal isVisible={passwordModal.isOpen} onClose={passwordModal.close} title="Update Password">
                    <Input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} label="Current Password" placeholder="Enter current password"/>
                    <Input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} label="New Password" placeholder="Enter new password"/>
                    <Input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} label="Confirm New Password" placeholder="Confirm new password" error={updateError || undefined}/>
                    
                    {updateError && <p className="text-red-500 mb-4">{updateError}</p>}
                    
                    <div className="flex justify-between gap-3">
                        <Button variant="secondary" onClick={passwordModal.close}>Cancel</Button>
                        <Button onClick={submitPasswordUpdate}>Update</Button>
                    </div>
                </Modal>

                <ConfirmDialog
                    isVisible={isNutritionConfirmVisible}
                    onConfirm={confirmToggleNutritionStats}
                    onCancel={() => setIsNutritionConfirmVisible(false)}
                    title="Nutrition Based Recommendations"
                    message={showNutritionStats 
                        ? "Do you want to turn off nutrition-based recommendations?" 
                        : "Do you want to turn on nutrition-based recommendations?"}
                    confirmText={showNutritionStats ? "Turn Off" : "Turn On"}
                    confirmVariant="primary"
                />

                <Modal isVisible={statsModal.isOpen} onClose={statsModal.close} title="Update Nutrition Stats">
                    <div className="mb-4 flex justify-end items-center">
                        <div className="flex items-center gap-2">
                            <span className={!useMetricUnits ? "font-bold" : ""}>Imperial</span>
                            <ToggleSwitch isOn={useMetricUnits} toggle={() => setUseMetricUnits(!useMetricUnits)}/>
                            <span className={useMetricUnits ? "font-bold" : ""}>Metric</span>
                        </div>
                    </div>
                    
                    <div className="flex flex-row gap-3">
                        <div className="mb-4 flex-1">
                            <p className="mb-2 font-medium">Sex</p>
                            <div className="flex gap-2">
                                <label className={`flex items-center gap-2 rounded-lg px-3 py-2 cursor-pointer ${sex === 'male' ? 'bg-emerald-100 border-2 border-emerald-400' : 'border-2 border-gray-300'}`}>
                                    <input type="radio" checked={sex === 'male'} onChange={() => setSex('male')} className="accent-emerald-400"/>
                                    <span className={sex === 'male' ? 'font-medium' : ''}>Male</span>
                                </label>

                                <label className={`flex items-center gap-2 rounded-lg px-3 py-2 cursor-pointer ${sex === 'female' ? 'bg-emerald-100 border-2 border-emerald-400' : 'border-2 border-gray-300'}`}>
                                    <input type="radio" checked={sex === 'female'} onChange={() => setSex('female')} className="accent-emerald-400"/>
                                    <span className={sex === 'female' ? 'font-medium' : ''}>Female</span>
                                </label>
                            </div>
                        </div>
                        
                        <div className="mb-4 flex-1">
                            <Input type="number" min="1" max="120" value={age} placeholder="Years" onChange={(e) => setAge(e.target.value ? Number(e.target.value) : '')} label="Age"/>
                        </div>
                    </div>
                    
                    <div className="flex flex-row gap-3">
                        <div className="mb-4 flex-1">
                            <label className="block mb-2 font-medium">Height</label>
                            {useMetricUnits ? (
                                <div className="flex items-center">
                                    <Input type="number" min="1" value={heightCm} placeholder="Cm" onChange={(e) => setHeightCm(e.target.value ? Number(e.target.value) : '')}/>
                                </div>
                            ) : (
                                <div className="flex gap-2">
                                    <div className="flex items-center flex-1">
                                        <Input type="number" min="0" value={heightFeet} placeholder="Feet" onChange={(e) => setHeightFeet(e.target.value ? Number(e.target.value) : '')}/>
                                    </div>

                                    <div className="flex items-center flex-1">
                                        <Input type="number" min="0" max="11" value={heightInches} placeholder="Inches" onChange={(e) => setHeightInches(e.target.value ? Number(e.target.value) : '')}/>
                                    </div>
                                </div>
                            )}
                        </div>
                        
                        <div className="mb-6 flex-1">
                            <label className="block mb-2 font-medium">Weight</label>
                            <div className="flex items-center">
                                <Input type="number" min="1" value={weightKg} placeholder={useMetricUnits ? "Kg" : "Lbs"} onChange={(e) => setWeightKg(e.target.value ? Number(e.target.value) : '')}/>
                            </div>
                        </div>
                    </div>
                    
                    <div className="mb-6">
                        <p className="mb-2 font-medium">Weight Goal</p>
                        <div className="flex justify-between w-full bg-gray-200 p-1 rounded-lg">
                            <button className={`cursor-pointer py-2 px-4 rounded-lg ${weightGoal === 'lose' ? 'bg-emerald-400 text-white' : ''}`} onClick={() => setWeightGoal('lose')} type="button">Lose</button>
                            <button className={`cursor-pointer py-2 px-4 rounded-lg ${weightGoal === 'maintain' ? 'bg-emerald-400 text-white' : ''}`} onClick={() => setWeightGoal('maintain')} type="button">Maintain</button>
                            <button className={`cursor-pointer py-2 px-4 rounded-lg ${weightGoal === 'gain' ? 'bg-emerald-400 text-white' : ''}`} onClick={() => setWeightGoal('gain')} type="button">Gain</button>
                        </div>
                    </div>

                    <div className="mb-6">
                        <p className="mb-2 font-medium">Activity Level</p>
                        <div className="flex justify-between w-full bg-gray-200 p-1 rounded-lg">
                            <button className={`cursor-pointer py-2 px-2 text-sm rounded-lg ${activityLevel === 'sedentary' ? 'bg-emerald-400 text-white' : ''}`} onClick={() => setActivityLevel('sedentary')} type="button">Sedentary</button>
                            <button className={`cursor-pointer py-2 px-2 text-sm rounded-lg ${activityLevel === 'low' ? 'bg-emerald-400 text-white' : ''}`} onClick={() => setActivityLevel('low')} type="button">Low</button>
                            <button className={`cursor-pointer py-2 px-2 text-sm rounded-lg ${activityLevel === 'moderate' ? 'bg-emerald-400 text-white' : ''}`} onClick={() => setActivityLevel('moderate')} type="button">Moderate</button>
                            <button className={`cursor-pointer py-2 px-2 text-sm rounded-lg ${activityLevel === 'heavy' ? 'bg-emerald-400 text-white' : ''}`} onClick={() => setActivityLevel('heavy')} type="button">Heavy</button>
                        </div>
                    </div>
                    
                    <div className="flex justify-between gap-3">
                        <Button variant="secondary" onClick={statsModal.close}>Cancel</Button>
                        <Button onClick={handleSaveStats}>Update Stats</Button>
                    </div>
                </Modal>

                <Modal isVisible={addCategoryModal.isOpen} onClose={addCategoryModal.close} title="Add Category">
                    <div className="mb-4" ref={preferredCategoryAutocompleteRef}>
                        <AutoComplete<{name: string}>
                            value={searchQuery}
                            onChange={handleSearchChange}
                            onSelect={(item) => handleCategorySelect(item.name)}
                            suggestions={categorySuggestions.map(category => ({ name: category }))}
                            displayProperty="name"
                            placeholder="Search categories..."
                            className="border-gray-300"
                        />
                    </div>

                    <div className="flex justify-between gap-3">
                        <Button variant="secondary" onClick={cancelAdd}>Cancel</Button>
                        <Button onClick={handleAddCategory} disabled={!selectedCategory}>Add</Button>
                    </div>
                </Modal>

                <ConfirmDialog
                    isVisible={isDeletePopupVisible}
                    onConfirm={confirmDeleteCategory}
                    onCancel={cancelDelete}
                    title="Delete Category"
                    message={`Are you sure you want to remove "${categoryToDelete}" from your preferred categories?`}
                    confirmText="Delete"
                    confirmVariant="danger"
                />

                <Modal isVisible={addExcludedCategoryModal.isOpen} onClose={addExcludedCategoryModal.close} title="Exclude Category">
                    <div className="mb-4" ref={excludedCategoryAutocompleteRef}>
                        <AutoComplete<{name: string}>
                            value={excludedSearchQuery}
                            onChange={handleExcludedSearchChange}
                            onSelect={(item) => handleExcludedCategorySelect(item.name)}
                            suggestions={excludedCategorySuggestions.map(category => ({ name: category }))}
                            displayProperty="name"
                            placeholder="Search categories to exclude..."
                            className="border-gray-300"
                        />
                    </div>

                    <div className="flex justify-between gap-3">
                        <Button variant="secondary" onClick={cancelAddExcluded}>Cancel</Button>
                        <Button onClick={handleAddExcludedCategory} disabled={!selectedExcludedCategory}>Exclude</Button>
                    </div>
                </Modal>

                <ConfirmDialog
                    isVisible={isExcludedDeletePopupVisible}
                    onConfirm={confirmDeleteExcludedCategory}
                    onCancel={cancelDeleteExcluded}
                    title="Remove Excluded Category"
                    message={`Are you sure you want to remove "${categoryToDeleteFromExcluded}" from your excluded categories?`}
                    confirmText="Remove"
                    confirmVariant="danger"
                />
            </div>
        </>
    );
};

export default Profile;