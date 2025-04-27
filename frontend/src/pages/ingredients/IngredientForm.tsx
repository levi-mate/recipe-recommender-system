import React, { useState, useEffect, useRef } from "react";
import axios from "axios";

import Button from "../../components/common/Button";
import Input from "../../components/common/Input";
import Select from "../../components/common/Select";
import AutoComplete from "../../components/common/AutoComplete";
import Modal from "../../components/common/Modal";

interface IngredientFormProps {
    toggleFormVisibility: () => void;
    onIngredientAdded: () => void;
}

const IngredientForm: React.FC<IngredientFormProps> = ({ toggleFormVisibility, onIngredientAdded }) => {
    const ingredientAutocompleteRef = useRef<HTMLDivElement>(null);

    const [ingredientName, setIngredientName] = useState("");
    const [suggestions, setSuggestions] = useState<string[]>([]);
    const [isDropdownVisible, setIsDropdownVisible] = useState(false);

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (
                ingredientAutocompleteRef.current && 
                !ingredientAutocompleteRef.current.contains(event.target as Node)
            ) {
                setIsDropdownVisible(false);
            }
        }
        
        document.addEventListener('mousedown', handleClickOutside);
        
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    const fetchSuggestions = async (query: string) => {
        if (!query) {
            setSuggestions([]);
            setIsDropdownVisible(false);
            return;
        }

        try {
            const response = await axios.get("http://localhost:5077/autocomplete_ingredients", {
                params: { query },
            });
    
            let suggestionData;

            if (response.data.data) {
                suggestionData = response.data.data;
            } else if (Array.isArray(response.data)) {
                suggestionData = response.data;
            } else {
                console.error("Unexpected API response format:", response.data);
                setSuggestions([]);

                return;
            }
    
            const processedSuggestions = suggestionData.map((suggestion: any) => {
                const text = typeof suggestion === 'object' && suggestion.name ? 
                    suggestion.name : suggestion;
                    
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
            });
    
            setSuggestions(processedSuggestions);
            setIsDropdownVisible(processedSuggestions.length > 0);
        } catch (error) {
            console.error("Failed to fetch ingredient suggestions:", error);

            if (axios.isAxiosError(error) && error.response) {
                console.error("Server response:", error.response.data);
            }

            setSuggestions([]);
        }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;

        setIngredientName(value);
        fetchSuggestions(value);
        setIsDropdownVisible(!!value);
    };

    const handleSuggestionClick = (suggestion: string) => {
        setIngredientName(suggestion);
        setIsDropdownVisible(false);
    };

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
    
        const formData = new FormData(e.currentTarget);
    
        const ingredientData = {
            ingredient_name: formData.get("ingredient_name"),
            quantity: formData.get("quantity"),
            unit: formData.get("unit"),
            category: formData.get("category"),
        };
    
        try {
            const response = await axios.post("http://localhost:5077/add_ingredient", ingredientData, {
                withCredentials: true,
            });
    
            if (response.data.success) {
                console.log("Ingredient added successfully:", response.data.message);
                onIngredientAdded();
                toggleFormVisibility();
            } else {
                console.error("Failed to add ingredient:", response.data.error);
                alert(response.data.error || "Failed to add ingredient");
            }
        } catch (error) {
            console.error("Error adding ingredient:", error);

            if (axios.isAxiosError(error) && error.response) {
                const errorMessage = error.response.data.error || "Server error occurred";
                console.error("Server response:", error.response.data);
                alert(errorMessage);
            } else {
                alert("Failed to connect to server. Please try again later.");
            }
        }
    };

    return (
        <Modal isVisible={true} onClose={toggleFormVisibility} title="Add Ingredient">
            <form className="flex flex-col gap-5" onSubmit={handleSubmit}>
                <div className="flex flex-col gap-2 mb-4">
                    <label htmlFor="ingredient_name" className="block mb-2 font-medium">Ingredient</label>
                    <AutoComplete<{name: string}>
                        value={ingredientName}
                        onChange={handleInputChange}
                        onSelect={(item) => handleSuggestionClick(item.name)}
                        suggestions={suggestions.map(suggestion => ({ name: suggestion }))}
                        displayProperty="name"
                        placeholder="Enter ingredient name"
                        className="border-gray-300"
                    />

                    <input type="hidden" id="ingredient_name" name="ingredient_name" value={ingredientName} />
                </div>

                <Input type="number" name="quantity" label="Quantity" required/>

                <Select name="unit" label="Unit" required
                    options={[
                        { value: "g", label: "g" },
                        { value: "kg", label: "kg" },
                        { value: "ml", label: "ml" },
                        { value: "l", label: "l" },
                        { value: "oz", label: "oz" },
                        { value: "lb", label: "lb" },
                        { value: "tsp", label: "tsp" },
                        { value: "tbsp", label: "tbsp" },
                        { value: "fl oz", label: "fl oz" },
                        { value: "cup", label: "cup" },
                        { value: "pint", label: "pint" }
                    ]}
                />

                <Select name="category" label="Category" required
                    options={[
                        { value: "Ambient", label: "Ambient" },
                        { value: "Chilled", label: "Chilled" },
                        { value: "Frozen", label: "Frozen" }
                    ]}
                />

                <div className="flex justify-between">
                    <Button variant="secondary" type="button" onClick={toggleFormVisibility}>Cancel</Button>
                    <Button type="submit">Add Ingredient</Button>
                </div>
            </form>
        </Modal>
    );
};

export default IngredientForm;