import { useState, useEffect, forwardRef, useImperativeHandle } from "react";
import axios from "axios";

import Button from "../../components/common/Button";
import Input from "../../components/common/Input";
import Select from "../../components/common/Select";
import ConfirmDialog from "../../components/common/Confirm";
import Modal from "../../components/common/Modal";
import { useModal } from "../../hooks/useModal";

interface Ingredient {
    ingredient_id: number;
    ingredient_name: string;
    quantity: number;
    unit: string;
    category: string;
}

const IngredientList = forwardRef<{ fetchIngredients: () => void }, {}>((_, ref) => {
    const [ingredients, setIngredients] = useState<Ingredient[]>([]);
    const [editingIngredientId, setEditingIngredientId] = useState<number | null>(null);
    const [editQuantity, setEditQuantity] = useState<string>("");
    const [editUnit, setEditUnit] = useState<string>("");
    const [editCategory, setEditCategory] = useState<string>("");
    const [isDeletePopupVisible, setIsDeletePopupVisible] = useState(false);
    const [ingredientToDelete, setIngredientToDelete] = useState<Ingredient | null>(null);

    const editModal = useModal();

    useEffect(() => {
        fetchIngredients();
    }, []);

    const fetchIngredients = async () => {
        try {
            const response = await axios.get("http://localhost:5077/account_ingredients/", {
                withCredentials: true,
            });
    
            console.log("Fetched ingredients:", response.data);
            
            if (response.data && response.data.data) {
                setIngredients(response.data.data);
            } else if (Array.isArray(response.data)) {
                setIngredients(response.data);
            } else {
                console.error("Unexpected API response format:", response.data);
                setIngredients([]);
            }
        } catch (error) {
            console.error("Failed to fetch ingredients:", error);

            if (axios.isAxiosError(error) && error.response) {
                console.error("Server response:", error.response.data);
            }

            setIngredients([]);
        }
    };

    useImperativeHandle(ref, () => ({
        fetchIngredients,
    }));

    const openEditPopup = (ingredient: Ingredient) => {
        setEditingIngredientId(ingredient.ingredient_id);
        setEditQuantity(ingredient.quantity.toString());
        setEditUnit(ingredient.unit);
        setEditCategory(ingredient.category === "TBD" ? "" : ingredient.category);
        editModal.open();
    };

    const closeEditPopup = () => {
        editModal.close();
        setEditingIngredientId(null);
    };

    const isValidQuantity = (value: string) => {
        if (!isNaN(Number(value))) {
            return true;
        }
    
        const fractionRegex = /^\d+\/\d+$/;
        return fractionRegex.test(value);
    };

    const handleSaveClick = async () => {
        if (!editCategory) {
            alert("Please select a category.");
            return;
        }
    
        if (!isValidQuantity(editQuantity.toString())) {
            alert("Please enter a valid quantity (e.g., 1, 0.5, or 1/2).");
            return;
        }
    
        try {
            console.log("Saving ingredient with category:", editCategory);
    
            let quantityToSave = editQuantity;

            if (editQuantity.includes("/")) {
                const [numerator, denominator] = editQuantity.split("/").map(Number);
                quantityToSave = (numerator / denominator).toString();
            }
    
            const response = await axios.post(
                `http://localhost:5077/update_ingredient/${editingIngredientId}`,
                {
                    quantity: quantityToSave,
                    unit: editUnit,
                    category: editCategory,
                },
                {
                    withCredentials: true,
                }
            );
    
            if (response.data.success) {
                console.log("Ingredient updated successfully:", response.data.message);
                
                setIngredients((prevIngredients) =>
                    prevIngredients.map((ingredient) =>
                        ingredient.ingredient_id === editingIngredientId
                            ? { ...ingredient, quantity: parseFloat(quantityToSave), unit: editUnit, category: editCategory }
                            : ingredient
                    )
                );
                
                closeEditPopup();
            } else {
                console.error("Failed to update ingredient:", response.data.error);
                alert(response.data.error || "Failed to update ingredient");
            }
        } catch (error) {
            console.error("Failed to update ingredient:", error);

            if (axios.isAxiosError(error) && error.response) {
                const errorMessage = error.response.data.error || "Error updating ingredient";
                console.error("Server response:", error.response.data);
                alert(errorMessage);
            } else {
                alert("Failed to connect to server. Please try again later.");
            }
        }
    };

    const openDeletePopup = (ingredient: Ingredient) => {
        setIngredientToDelete(ingredient);
        setIsDeletePopupVisible(true);
    };

    const closeDeletePopup = () => {
        setIsDeletePopupVisible(false);
        setIngredientToDelete(null);
    };

    const handleDeleteClick = async () => {
        if (!ingredientToDelete) return;

        try {
            const response = await axios.post(
                `http://localhost:5077/delete_ingredient/${ingredientToDelete.ingredient_id}`,
                {},
                {
                    withCredentials: true,
                }
            );

            if (response.data.success) {
                console.log("Ingredient deleted successfully:", response.data.message);
                
                setIngredients((prevIngredients) =>
                    prevIngredients.filter(
                        (ingredient) => ingredient.ingredient_id !== ingredientToDelete.ingredient_id
                    )
                );
                
                setIsDeletePopupVisible(false);
                setIngredientToDelete(null);
            } else {
                console.error("Failed to delete ingredient:", response.data.error);
                alert(response.data.error || "Failed to delete ingredient");
            }
        } catch (error) {
            console.error("Failed to delete ingredient:", error);

            if (axios.isAxiosError(error) && error.response) {
                const errorMessage = error.response.data.error || "Error deleting ingredient";
                console.error("Server response:", error.response.data);
                alert(errorMessage);
            } else {
                alert("Failed to connect to server. Please try again later.");
            }
        }
    };

    return (
        <>
            <div className="p-5">
                {["Ambient", "Chilled", "Frozen", "TBD"].map((category) => (
                    <div key={category} className="mb-5">
                        <h3 className="font-bold text-2xl mb-3">{category}</h3>

                        <ul className="divide-y divide-dashed divide-gray-300">
                            {ingredients.filter((ingredient) => ingredient.category === category).map((ingredient) => (
                                <li key={ingredient.ingredient_id} className="flex justify-between items-center mx-2 mb-2">
                                    <div className="flex gap-2">
                                        <button onClick={() => openDeletePopup(ingredient)} className="cursor-pointer text-red-400 hover:text-red-300">✕</button>
                                        <span>{ingredient.ingredient_name} - {ingredient.quantity} {ingredient.unit}</span>
                                    </div>

                                    <div className="flex gap-2">
                                        <button onClick={() => openEditPopup(ingredient)} className="cursor-pointer text-blue-400 hover:text-blue-300">Edit</button>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    </div>
                ))}

                <Modal isVisible={editModal.isOpen && editingIngredientId !== null} onClose={closeEditPopup} title="Edit Ingredient">
                    <p className="text-gray-700 font-semibold mb-3">{ingredients.find(i => i.ingredient_id === editingIngredientId)?.ingredient_name}</p>

                    <div className="flex flex-col gap-3">
                        <Input type="text" value={editQuantity} onChange={(e) => setEditQuantity(e.target.value)} placeholder="Quantity" className="w-full"/>

                        <Select value={editUnit} onChange={(e) => setEditUnit(e.target.value)}
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

                        <Select value={editCategory} onChange={(e) => setEditCategory(e.target.value)} placeholder="Select..."
                            options={[
                                { value: "Ambient", label: "Ambient" },
                                { value: "Chilled", label: "Chilled" },
                                { value: "Frozen", label: "Frozen" }
                            ]}
                        />
                    </div>

                    <div className="flex justify-between gap-3 mt-5">
                        <Button variant="secondary" onClick={closeEditPopup}>Cancel</Button>
                        <Button onClick={handleSaveClick}>Save</Button>
                    </div>
                </Modal>

                <ConfirmDialog
                    isVisible={isDeletePopupVisible}
                    onConfirm={handleDeleteClick}
                    onCancel={closeDeletePopup}
                    title="Delete Ingredient"
                    message={ingredientToDelete ? `Are you sure you want to delete "${ingredientToDelete.ingredient_name}"?` : ""}
                    confirmText="Delete"
                    confirmVariant="danger"
                />
            </div>
        </>
    );
});

export default IngredientList;