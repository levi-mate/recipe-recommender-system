import React, { useState, useRef, useEffect } from "react";

interface AutoCompleteProps<T> {
    value: string;
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onSelect: (item: T) => void;
    suggestions: T[];
    displayProperty: keyof T;
    placeholder?: string;
    className?: string;
}

function AutoComplete<T>({
    value,
    onChange,
    onSelect,
    suggestions,
    displayProperty,
    placeholder = "",
    className = "",
}: AutoCompleteProps<T>) {
    const [isFocused, setIsFocused] = useState(false);
    const autoCompleteRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (
                autoCompleteRef.current && 
                !autoCompleteRef.current.contains(event.target as Node)
            ) {
                setIsFocused(false);
            }
        }
        
        document.addEventListener('mousedown', handleClickOutside);
        
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    return (
        <div className="relative" ref={autoCompleteRef}>
            <input type="text" value={value} onChange={onChange} onFocus={() => setIsFocused(true)} placeholder={placeholder} className={`w-full p-2 border-2 rounded-lg ${className}`}/>

            {suggestions.length > 0 && isFocused && value && (
                <ul className="absolute mt-1 w-full bg-white border rounded-lg shadow-md max-h-60 overflow-y-auto z-10">
                    {suggestions.map((item, index) => (
                        <li key={index} onClick={() => { onSelect(item); setIsFocused(false); }} className="p-2 cursor-pointer hover:bg-gray-100">{String(item[displayProperty])}</li>
                    ))}
                </ul>
            )}
        </div>
    );
}

export default AutoComplete;