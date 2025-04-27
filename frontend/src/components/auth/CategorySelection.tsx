import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

import Button from "../common/Button";

const CategorySelection: React.FC<{ isUpdating?: boolean }> = ({ isUpdating = false }) => {
    const [categories, setCategories] = useState<string[]>([]);
    const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
    const [allSelectedCategories, setAllSelectedCategories] = useState<string[]>([]);
    const [currentBatch, setCurrentBatch] = useState<number>(0);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchCategories = async () => {
            try {
                setIsLoading(true);

                const response = await axios.get("http://localhost:5077/get_categories", { withCredentials: true });
                
                if (response.data && response.data.data) {
                    setCategories(response.data.data);
                } else if (Array.isArray(response.data)) {
                    setCategories(response.data);
                } else {
                    console.error("Unexpected API response format:", response.data);
                    setCategories([]);
                }
            } catch (error) {
                console.error("Failed to fetch categories:", error);
                
                if (axios.isAxiosError(error) && error.response) {
                    console.error("Server response:", error.response.data);
                }
                
                setCategories([]);
            } finally {
                setIsLoading(false);
            }
        };

        fetchCategories();
    }, []);

    const handleCategoryClick = (category: string) => {
        if (selectedCategories.includes(category)) {
            setSelectedCategories((prev) => prev.filter((c) => c !== category));
        } else if (selectedCategories.length < 5) {
            setSelectedCategories((prev) => [...prev, category]);
        }
    };

    const handleNext = () => {
        if (selectedCategories.length !== 5) {
            alert("Please select exactly 5 categories.");
            return;
        }

        setAllSelectedCategories((prev) => [...prev, ...selectedCategories]);

        if (currentBatch === 1) {
            savePreferredCategories([...allSelectedCategories, ...selectedCategories]);
        } else {
            setCurrentBatch((prev) => prev + 1);
            setSelectedCategories([]);
        }
    };

    const savePreferredCategories = async (categoriesToSave: string[]) => {
        try {
            setIsLoading(true);
            const response = await axios.post(
                "http://localhost:5077/save_preferred_categories",
                { preferred_categories: categoriesToSave },
                { withCredentials: true }
            );
            
            console.log("Preferred categories saved:", response.data);
            
            if (response.data.success) {
                navigate(isUpdating ? "/profile" : "/account");
            } else {
                const errorMessage = response.data.error || "Failed to save categories.";
                console.error("Failed to save categories:", errorMessage);
                alert(errorMessage);
            }
        } catch (error) {
            console.error("Failed to save preferred categories:", error);
            
            if (axios.isAxiosError(error) && error.response) {
                const errorMessage = error.response.data.error || "Server error occurred.";
                console.error("Server response:", error.response.data);
                alert(errorMessage);
            } else {
                alert("Failed to save preferred categories. Please try again.");
            }
        } finally {
            setIsLoading(false);
        }
    };

    const getBatchCategories = () => {
        const start = currentBatch * 10;
        const end = start + 10;
        return categories.slice(start, end);
    };

    return (
        <div className="flex flex-col items-center gap-5 m-5 p-5 max-w-[600px] lg:min-w-[600px] md:mx-auto rounded-lg shadow-[0_0_10px_rgba(0,0,0,0.2)] bg-slate-50">
            <h2 className="font-bold text-3xl text-center">Select Your Preferred Categories</h2>

            <p className="text-gray-700">Select 5 categories from the list below:</p>

            {isLoading ? (
                <p>Loading categories...</p>
            ) : (
                <>
                    <div className="grid grid-cols-2 gap-4">
                        {getBatchCategories().map((category) => (
                            <Button key={category} onClick={() => handleCategoryClick(category)} variant={selectedCategories.includes(category) ? "primary" : "secondary"}disabled={isLoading}>{category}</Button>
                        ))}
                    </div>
                    
                    <Button variant="blue" onClick={handleNext} disabled={isLoading}>{isLoading ? "Processing..." : currentBatch === 1 ? "Finish" : "Next"}</Button>
                </>
            )}
        </div>
    );
};

export default CategorySelection;