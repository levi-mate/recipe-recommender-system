import React, { InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
}

const Input: React.FC<InputProps> = ({ 
    label, 
    error, 
    className = "",
    ...props 
}) => {
    return (
        <div className="mb-4">
            {label && (
                <label className="block mb-2 font-medium">{label}</label>
            )}

            <input className={`w-full p-2 border-2 rounded-lg ${error ? "border-red-500" : "border-gray-300"} ${className}`} {...props}/>

            {error && (
                <p className="mt-1 text-sm text-red-500">{error}</p>
            )}
        </div>
    );
};

export default Input;