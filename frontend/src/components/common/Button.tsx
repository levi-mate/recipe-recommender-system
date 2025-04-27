import React, { ButtonHTMLAttributes, ReactNode } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: "primary" | "secondary" | "danger" | "blue";
    children: ReactNode;
}

const Button: React.FC<ButtonProps> = ({ 
    variant = "primary", 
    children, 
    className = "",
    disabled,
    ...props 
}) => {
    const baseStyles = "px-4 py-2 rounded-lg font-bold";
    
    const variantStyles = {
        primary: `${disabled ? "cursor-default bg-gray-300" : "cursor-pointer bg-emerald-400 hover:bg-emerald-300 transition-colors"} text-white`,
        secondary: "cursor-pointer bg-gray-400 hover:bg-gray-300 transition-colors text-white",
        danger: "cursor-pointer bg-red-400 hover:bg-red-300 transition-colors text-white",
        blue: "cursor-pointer bg-blue-400 hover:bg-blue-300 transition-colors text-white",
    };

    return (
        <button className={`${baseStyles} ${variantStyles[variant]} ${className}`} disabled={disabled} {...props}>{children}</button>
    );
};

export default Button;