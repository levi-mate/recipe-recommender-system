import React, { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import axios from "axios";

interface ProtectedRouteProps {
    children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
    const [isLoggedIn, setIsLoggedIn] = useState<boolean | null>(null);

    useEffect(() => {
        const checkLoginStatus = async () => {
            try {
                const response = await axios.get("http://localhost:5077/check_login", {
                    withCredentials: true,
                });
                
                const isUserLoggedIn = response.data.data?.loggedIn || false;
                console.log("Login check response:", response.data);
                console.log("Is logged in:", isUserLoggedIn);
                
                setIsLoggedIn(isUserLoggedIn);
            } catch (error) {
                console.error("Failed to check login status:", error);
                setIsLoggedIn(false);
            }
        };

        checkLoginStatus();
    }, []);

    if (isLoggedIn === null) {
        return <div>Loading...</div>;
    }

    return isLoggedIn ? <>{children}</> : <Navigate to="/error" />;
};

export default ProtectedRoute;