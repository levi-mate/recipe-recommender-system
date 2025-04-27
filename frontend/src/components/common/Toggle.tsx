import React from "react";

interface ToggleSwitchProps {
    isOn: boolean;
    toggle: () => void;
    label?: string;
    labelPosition?: "left" | "right";
}

const ToggleSwitch: React.FC<ToggleSwitchProps> = ({ 
    isOn, 
    toggle, 
    label = "",
    labelPosition = "left"
}) => {
    const switch_button = (
        <button onClick={toggle} type="button" className={`cursor-pointer relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${isOn ? 'bg-emerald-400' : 'bg-gray-200'}`}>
            <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${isOn ? 'translate-x-6' : 'translate-x-1'}`}/>
        </button>
    );

    if (!label) return switch_button;

    return (
        <div className="flex items-center gap-2">
            {labelPosition === "left" && <span>{label}</span>}
            {switch_button}
            {labelPosition === "right" && <span>{label}</span>}
        </div>
    );
};

export default ToggleSwitch;