import React from "react";
import { Link } from "react-router-dom";

const ErrorPage: React.FC = () => {
    return (
        <div className="flex flex-col items-center pt-5 h-screen bg-gray-100">
            <div className="flex flex-col items-center justify-center p-5 rounded-lg shadow-[0_0_10px_rgba(0,0,0,0.2)] border-4 border-red-500">
                <h1 className="text-5xl font-bold text-red-500 mb-10">Access Denied</h1>
                <p className="text-lg mb-6">Oops, you got a bit lost.</p>
                <Link to="/" className="px-4 py-2 text-white rounded-md bg-blue-500 hover:bg-blue-400 transition-colors">Back to Home Page →</Link>
            </div>
        </div>
    );
};

export default ErrorPage;