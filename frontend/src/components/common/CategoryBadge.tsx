import React from "react";

interface CategoryBadgeProps {
    category: string;
    onDelete: (category: string) => void;
    variant?: "default" | "danger";
}

const CategoryBadge: React.FC<CategoryBadgeProps> = ({ 
    category, 
    onDelete, 
    variant = "default" 
}) => {
    const bgColor = variant === "danger" ? "bg-red-100" : "bg-gray-200";
    const buttonColor = variant === "danger" ? "bg-red-400 hover:bg-red-300" : "bg-gray-400 hover:bg-gray-300";
    
    return (
        <div className={`flex items-center ${bgColor} rounded-full p-2 relative`}>
            <div className={`h-7 w-8 rounded-full text-white font-bold ${bgColor}`}></div>
            <p className="w-full text-center pr-6">{category}</p>
            <button onClick={() => onDelete(category)} className={`cursor-pointer p-0.5 px-2 rounded-full text-white font-bold ${buttonColor} absolute right-2`}>✕</button>
        </div>
    );
};

export default CategoryBadge;