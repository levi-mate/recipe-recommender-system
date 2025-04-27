import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

import Button from "../common/Button";
import Input from "../common/Input";

interface AuthProps {
    isVisible: boolean;
    onClose: () => void;
    onLoginSuccess: () => void;
}

const Auth: React.FC<AuthProps> = ({ isVisible, onClose, onLoginSuccess }) => {
    const [isRegister, setIsRegister] = useState(false);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();

    if (!isVisible) return null;

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setIsLoading(true);
        setErrorMessage(null);

        const formData = new FormData(e.currentTarget);
        formData.set("form_type", isRegister ? "register" : "login");

        if (isRegister) {
            const password = formData.get("registerPwd") as string;
            const confirmPassword = formData.get("registerRepPwd") as string;

            if (password !== confirmPassword) {
                setErrorMessage("Passwords do not match.");
                setIsLoading(false);
                return;
            }
        }

        try {
            const response = await axios.post("http://localhost:5077/login/", formData, {
                withCredentials: true,
            });

            console.log("Auth response:", response.data);

            if (response.data.success) {
                console.log("Authentication successful");
                onLoginSuccess();

                if (isRegister) {
                    navigate("/select-categories");
                } else {
                    const redirectPath = response.data.data?.redirect || response.data.redirect || "/account";
                    navigate(redirectPath);
                }

                onClose();
            } else {
                const errorMsg = response.data.error || "Authentication failed. Please try again.";
                console.error("Authentication failed:", errorMsg);
                setErrorMessage(errorMsg);
            }
        } catch (error: any) {
            console.error("Authentication error:", error);
            
            if (axios.isAxiosError(error) && error.response?.data) {
                const errorMsg = error.response.data.error || error.response.data.message || "Authentication failed. Please try again.";
                
                console.error("Server error response:", error.response.data);
                
                setErrorMessage(errorMsg);
            } else {
                setErrorMessage("An unexpected error occurred. Please try again later.");
            }
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 flex justify-center items-center p-5 bg-black/50 backdrop-blur-sm z-50">
            <div className="relative flex flex-col justify-center gap-5 p-5 w-full max-w-md rounded-lg shadow-lg bg-white">
                <button onClick={onClose} className="absolute top-4 right-4 text-xl font-bold cursor-pointer" aria-label="Close">✕</button>

                {isRegister ? (
                    <div id="registerDetails" className="flex flex-col justify-center">
                        <h1 className="self-center font-bold text-3xl mb-5">Register</h1>

                        <form className="flex flex-col gap-4" onSubmit={(e) => handleSubmit(e)}>
                            <Input name="registerUser" label="Username" required/>
                            <Input type="email" name="registerEmail" label="Email" required/>
                            <Input type="password" name="registerPwd" label="Password" required/>
                            <Input type="password" name="registerRepPwd" label="Repeat Password" required/>

                            {errorMessage && (
                                <div className="text-red-500 text-center">{errorMessage}</div>
                            )}

                            <Button type="submit" disabled={isLoading}>{isLoading ? "Processing..." : "Register"}</Button>
                        </form>

                        <div className="flex justify-center mt-4">
                            <button onClick={() => setIsRegister(false)} className="cursor-pointer text-blue-500 hover:underline">Already have an account? Log in here.</button>
                        </div>
                    </div>
                ) : (
                    <div id="loginDetails" className="flex flex-col justify-center">
                        <h1 className="self-center font-bold text-3xl mb-5">Login</h1>

                        <form className="flex flex-col gap-4" onSubmit={(e) => handleSubmit(e)}>
                            <Input name="loginUser" label="Username" required/>
                            <Input type="password" name="loginPwd" label="Password" required/>

                            {errorMessage && (
                                <div className="text-red-500 text-center">{errorMessage}</div>
                            )}

                            <Button type="submit" disabled={isLoading}>{isLoading ? "Processing..." : "Login"}</Button>
                        </form>

                        <div className="flex justify-center mt-4">
                            <button onClick={() => setIsRegister(true)} className="cursor-pointer text-blue-500 hover:underline">Don't have an account? Register here.</button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Auth;