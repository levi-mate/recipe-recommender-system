import React, { useState, useEffect, useRef } from "react";
import axios from "axios";

import Button from "../../components/common/Button";
import ConfirmDialog from "../../components/common/Confirm";
import AutoComplete from "../../components/common/AutoComplete";
import PageHeader from "../../components/common/Header";

const Shopping: React.FC = () => {
    const [searchQuery, setSearchQuery] = useState("");
    const [recipeSuggestions, setRecipeSuggestions] = useState<{ recipe_id: number; recipe_name: string }[]>([]);
    const [selectedRecipe, setSelectedRecipe] = useState<{ recipe_id: number; recipe_name: string } | null>(null);
    const [ingredients, setIngredients] = useState<{ name: string; quantity: string | null }[]>([]);
    const [shoppingList, setShoppingList] = useState<{ name: string; quantity: number; unit: string | null }[]>([]);
    const [selectedShoppingItems, setSelectedShoppingItems] = useState<Set<string>>(new Set());
    const [ingredientToDelete, setIngredientToDelete] = useState<{ name: string; quantity: number; unit: string | null } | null>(null);
    const [isDeletePopupVisible, setIsDeletePopupVisible] = useState(false);
    const searchAutocompleteRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const fetchShoppingList = async () => {
            try {
                const response = await axios.get("http://localhost:5077/get_shopping_list", { withCredentials: true });
                
                if (response.data && response.data.data) {
                    setShoppingList(response.data.data);
                } else if (Array.isArray(response.data)) {
                    setShoppingList(response.data);
                } else {
                    console.error("Unexpected API response format:", response.data);
                    setShoppingList([]);
                }
            } catch (error) {
                console.error("Failed to fetch shopping list:", error);

                if (axios.isAxiosError(error) && error.response) {
                    console.error("Server response:", error.response.data);
                }

                setShoppingList([]);
            }
        };
    
        fetchShoppingList();
    }, []);

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (
                searchAutocompleteRef.current && 
                !searchAutocompleteRef.current.contains(event.target as Node)
            ) {
                setRecipeSuggestions([]);
            }
        }
        
        document.addEventListener('mousedown', handleClickOutside);

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    const handleSearchChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const query = e.target.value;
        setSearchQuery(query);

        if (!query) {
            setRecipeSuggestions([]);
            return;
        }

        try {
            const response = await axios.get("http://localhost:5077/autocomplete_recipes", {
                params: { query },
                withCredentials: true,
            });

            const recipesData = response.data.data || response.data;
            
            if (!recipesData) {
                console.error("No recipe data found in response:", response.data);
                setRecipeSuggestions([]);
                return;
            }

            const processedSuggestions = response.data.map((recipe: { recipe_id: number; recipe_name: string }) => ({
                recipe_id: recipe.recipe_id,
                recipe_name: recipe.recipe_name
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
                    .replace(/&aelig;/g, 'ae')
            }));

            setRecipeSuggestions(processedSuggestions);
        } catch (error) {
            console.error("Failed to fetch recipe suggestions:", error);

            if (axios.isAxiosError(error) && error.response) {
                console.error("Server response:", error.response.data);
            }

            setRecipeSuggestions([]);
        }
    };

    const handleRecipeSelect = async (recipe: { recipe_id: number; recipe_name: string }) => {
        setSelectedRecipe(recipe);
        setRecipeSuggestions([]);
    
        try {
            const response = await axios.get(`http://localhost:5077/get_recipe_ingredients/${recipe.recipe_id}`, {
                withCredentials: true,
            });
            
            if (response.data && response.data.data) {
                setIngredients(response.data.data);
            } else if (Array.isArray(response.data)) {
                setIngredients(response.data);
            } else {
                console.error("Unexpected ingredients API response format:", response.data);
                setIngredients([]);
            }
        } catch (error) {
            console.error("Failed to fetch recipe ingredients:", error);

            if (axios.isAxiosError(error) && error.response) {
                console.error("Server response:", error.response.data);
            }

            setIngredients([]);
        }
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

    const handleAddToShoppingList = async () => {
        const updatedShoppingList = [...shoppingList];
    
        ingredients.forEach((ingredient) => {
            const parsedQuantity = parseQuantity(ingredient.quantity);
            
            const existingIngredientIndex = updatedShoppingList.findIndex(
                (item) => item.name.toLowerCase() === ingredient.name.toLowerCase()
            );
    
            if (existingIngredientIndex !== -1) {
                updatedShoppingList[existingIngredientIndex].quantity = 
                    Number(updatedShoppingList[existingIngredientIndex].quantity) + parsedQuantity;
            } else {
                updatedShoppingList.push({
                    name: ingredient.name,
                    quantity: parsedQuantity,
                    unit: null
                });
            }
        });
    
        try {
            const response = await axios.post(
                "http://localhost:5077/update_shopping_list",
                { ingredients: updatedShoppingList },
                { withCredentials: true }
            );
    
            if (response.data.success) {
                console.log("Shopping list updated successfully:", response.data.message);
                setShoppingList(updatedShoppingList);
                setSelectedRecipe(null);
                setIngredients([]);
            } else {
                console.error("Failed to update shopping list:", response.data.error);
                alert(response.data.error || "Failed to update shopping list");
            }
        } catch (error) {
            console.error("Failed to update shopping list:", error);

            if (axios.isAxiosError(error) && error.response) {
                const errorMessage = error.response.data.error || "Server error";
                console.error("Server response:", error.response.data);
                alert(errorMessage);
            } else {
                alert("Failed to connect to server. Please try again later.");
            }
        }
    };

    const handleDeleteClick = (ingredient: { name: string; quantity: number; unit: string | null }) => {
        setIngredientToDelete(ingredient);
        setIsDeletePopupVisible(true);
    };

    const cancelDelete = () => {
        setIsDeletePopupVisible(false);
        setIngredientToDelete(null);
    };

    const confirmDelete = async () => {
        if (!ingredientToDelete) return;

        try {
            const updatedShoppingList = shoppingList.filter((item) => item.name !== ingredientToDelete.name);
            setShoppingList(updatedShoppingList);

            const response = await axios.post(
                "http://localhost:5077/update_shopping_list",
                { ingredients: updatedShoppingList },
                { withCredentials: true }
            );

            if (response.data.success) {
                console.log("Item deleted successfully:", response.data.message);
                setShoppingList(updatedShoppingList);
            } else {
                console.error("Failed to delete item:", response.data.error);
                alert(response.data.error || "Failed to delete item");
            }
        } catch (error) {
            console.error("Failed to delete ingredient:", error);

            if (axios.isAxiosError(error) && error.response) {
                const errorMessage = error.response.data.error || "Server error";
                console.error("Server response:", error.response.data);
                alert(errorMessage);
            } else {
                alert("Failed to connect to server. Please try again later.");
            }
        } finally {
            setIsDeletePopupVisible(false);
            setIngredientToDelete(null);
        }
    };

    const handleCheckboxChange = (ingredientName: string) => {
        setSelectedShoppingItems((prev) => {
            const updated = new Set(prev);
            if (updated.has(ingredientName)) {
                updated.delete(ingredientName);
            } else {
                updated.add(ingredientName);
            }
            return updated;
        });
    };

    const handleMoveToUserIngredients = async () => {
        const selectedIngredients = shoppingList.filter((item) => selectedShoppingItems.has(item.name));
    
        try {
            const response = await axios.post(
                "http://localhost:5077/move_to_user_ingredients",
                { ingredients: selectedIngredients },
                { withCredentials: true }
            );
    
            if (response.data.success) {
                console.log("Ingredients moved to user ingredients:", response.data.message);
                
                const shoppingListResponse = await axios.get("http://localhost:5077/get_shopping_list", { 
                    withCredentials: true 
                });
                
                if (shoppingListResponse.data && shoppingListResponse.data.data) {
                    setShoppingList(shoppingListResponse.data.data);
                } else if (Array.isArray(shoppingListResponse.data)) {
                    setShoppingList(shoppingListResponse.data);
                } else {
                    console.error("Unexpected shopping list API response:", shoppingListResponse.data);
                    setShoppingList([]);
                }
                
                setSelectedShoppingItems(new Set());
            } else {
                console.error("Failed to move ingredients:", response.data.error);
                alert(response.data.error || "Failed to move ingredients");
            }
        } catch (error) {
            console.error("Failed to move ingredients to user ingredients:", error);

            if (axios.isAxiosError(error) && error.response) {
                const errorMessage = error.response.data.error || "Server error";
                console.error("Server response:", error.response.data);
                alert(errorMessage);
            } else {
                alert("Failed to connect to server. Please try again later.");
            }
        }
    };

    return (
        <div className="flex flex-col items-center gap-5 m-5 max-w-[600px] lg:min-w-[600px] md:mx-auto rounded-lg shadow-[0_0_10px_rgba(0,0,0,0.2)] bg-slate-50">
            <PageHeader title="Shopping List" />

            <div className="w-full p-5">
                <AutoComplete<{recipe_id: number; recipe_name: string}>
                    value={searchQuery}
                    onChange={handleSearchChange}
                    onSelect={handleRecipeSelect}
                    suggestions={recipeSuggestions}
                    displayProperty="recipe_name"
                    placeholder="Search for recipes..."
                    className="border-gray-300"
                />
            </div>

            {selectedRecipe && (
                <div className="flex flex-col items-center mt-5 w-full">
                    <h2 className="text-xl font-bold mb-3">Ingredients for {selectedRecipe.recipe_name}</h2>

                    <ul className="list-disc pl-5">
                        {ingredients.map((ingredient, index) => (
                            <li key={index}>{ingredient.name} {ingredient.quantity && `- ${ingredient.quantity}`}</li>
                        ))}
                    </ul>

                    <Button variant="blue" onClick={handleAddToShoppingList} className="mt-3">Add to Shopping List</Button>
                </div>
            )}

            <div className="flex flex-col justify-center p-5 w-full">
                <ul className="divide-y divide-dashed divide-gray-300">
                    {shoppingList.map((item, index) => (
                        <li key={index} className={`flex items-center justify-between gap-3 mx-2 mb-2 p-1 rounded-lg ${selectedShoppingItems.has(item.name) ? 'bg-blue-100' : ''}`}>
                            <div className="flex gap-2 items-center flex-grow cursor-pointer" onClick={() => handleCheckboxChange(item.name)}>
                                <input type="checkbox" checked={selectedShoppingItems.has(item.name)} onChange={() => handleCheckboxChange(item.name)} onClick={(e) => e.stopPropagation()}/>
                                <span className="select-none">{item.name} {item.quantity && `- ${item.quantity}`} {item.unit && item.unit}</span>
                            </div>

                            <button onClick={(e) => { e.stopPropagation(); handleDeleteClick(item); }} className="cursor-pointer text-red-500 hover:text-red-700">✕</button>
                        </li>
                    ))}
                </ul>

                {shoppingList.length > 0 && (
                    <Button onClick={handleMoveToUserIngredients} className="place-self-center mt-3">Move Selected to My Ingredients</Button>
                )}
            </div>

            <ConfirmDialog
                isVisible={isDeletePopupVisible}
                onConfirm={confirmDelete}
                onCancel={cancelDelete}
                title="Delete Item"
                message={ingredientToDelete ? `Are you sure you want to delete "${ingredientToDelete.name}"?` : ""}
                confirmText="Delete"
                confirmVariant="danger"
            />
        </div>
    );
};

export default Shopping;