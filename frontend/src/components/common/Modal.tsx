import React, { ReactNode } from "react";

interface ModalProps {
    isVisible: boolean;
    onClose: () => void;
    title: string;
    children: ReactNode;
    size?: "sm" | "md" | "lg";
}

const Modal: React.FC<ModalProps> = ({ 
    isVisible, 
    onClose, 
    title, 
    children, 
    size = "md" 
}) => {
    if (!isVisible) return null;
    
    const sizes = {
        sm: "max-w-sm",
        md: "max-w-md",
        lg: "max-w-lg"
    };
    
    return (
        <div className="fixed inset-0 flex justify-center items-center p-5 bg-black/20 backdrop-blur-sm z-50">
            <div className={`bg-white p-5 rounded-lg shadow-[0_0_10px_rgba(0,0,0,0.2)] w-full ${sizes[size]}`}>
                <h3 className="text-lg font-bold mb-4 text-center">{title}</h3>
                {children}
            </div>
        </div>
    );
};

export default Modal;