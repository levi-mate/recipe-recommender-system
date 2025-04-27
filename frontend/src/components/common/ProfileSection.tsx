import React, { ReactNode } from "react";

interface ProfileSectionProps {
    title: string;
    description?: string;
    children: ReactNode;
}

const ProfileSection: React.FC<ProfileSectionProps> = ({ 
    title, 
    description, 
    children 
}) => {
    return (
        <div className="flex flex-col items-center gap-5 p-5">
            <div className="flex flex-col items-start justify-center w-full">
                <h2 className="font-bold text-lg">{title}</h2>
                {description && <span className="text-sm text-gray-500">{description}</span>}
            </div>
            {children}
        </div>
    );
};

export default ProfileSection;