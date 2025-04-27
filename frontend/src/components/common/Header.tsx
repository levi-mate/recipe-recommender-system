import React from "react";

interface PageHeaderProps {
    title: string;
}

const PageHeader: React.FC<PageHeaderProps> = ({ title }) => {
    return (
        <div className="flex items-center justify-center w-full p-5 rounded-t-lg text-white bg-emerald-400">
            <h1 className="font-bold text-3xl text-center">{title}</h1>
        </div>
    );
};

export default PageHeader;