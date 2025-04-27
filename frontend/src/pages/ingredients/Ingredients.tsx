import React, { useState, useRef } from "react";

import IngredientList from "./IngredientList";
import IngredientForm from "./IngredientForm";

import Button from "../../components/common/Button";
import PageHeader from "../../components/common/Header";

const Ingredients: React.FC = () => {
    const [isFormVisible, setIsFormVisible] = useState(false);
    const ingredientListRef = useRef<{ fetchIngredients: () => void } | null>(null);

    const toggleFormVisibility = () => {
        setIsFormVisible((prev) => !prev);
    };

    const handleIngredientAdded = () => {
        if (ingredientListRef.current) {
            ingredientListRef.current.fetchIngredients();
        }
    };

    return (
        <div className="flex flex-col gap-5 m-5 max-w-[1024px] lg:min-w-[600px] md:mx-auto rounded-lg shadow-[0_0_10px_rgba(0,0,0,0.2)] bg-slate-50">
            <div className="flex flex-col justify-between items-center gap-5">
                <PageHeader title="My Ingredients" />

                <Button onClick={toggleFormVisibility} className="text-2xl">Add Ingredient</Button>
            </div>

            {isFormVisible && (
                <IngredientForm toggleFormVisibility={toggleFormVisibility} onIngredientAdded={handleIngredientAdded} />
            )}

            <IngredientList ref={ingredientListRef} />
        </div>
    );
};

export default Ingredients;