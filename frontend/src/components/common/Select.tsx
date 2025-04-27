import React, { SelectHTMLAttributes } from "react";

interface Option {
    value: string;
    label: string;
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
    label?: string;
    options: Option[];
    error?: string;
    placeholder?: string;
}

const Select: React.FC<SelectProps> = ({ 
    label, 
    options, 
    error, 
    placeholder,
    className = "",
    ...props 
}) => {
    return (
        <div className="mb-4">
            {label && (
                <label className="block mb-2 font-medium">{label}</label>
            )}
            
            <select className={`w-full p-2 border-2 rounded-lg ${error ? "border-red-500" : "border-gray-300"} ${className}`} {...props}>
                {placeholder && (
                    <option value="" disabled hidden>{placeholder}</option>
                )}
                
                {options.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                ))}
            </select>
            
            {error && (
                <p className="mt-1 text-sm text-red-500">{error}</p>
            )}
        </div>
    );
};

export default Select;