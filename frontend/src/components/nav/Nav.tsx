import React, { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";

import Auth from "../auth/Auth";

import pers_icon from "../../assets/pers_icon.svg";

const Nav: React.FC = () => {
    const [isBurgerMenuOpen, setIsBurgerMenuOpen] = useState(false);
    const [isAuthPopupVisible, setIsAuthPopupVisible] = useState(false);
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
    const profileMenuRef = useRef<HTMLDivElement>(null);
    const navigate = useNavigate();

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
                
                if (axios.isAxiosError(error) && error.response) {
                    console.error("Server response:", error.response.data);
                }
                
                setIsLoggedIn(false);
            }
        };
    
        checkLoginStatus();
    }, []);

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (profileMenuRef.current && !profileMenuRef.current.contains(event.target as Node)) {
                setIsProfileMenuOpen(false);
            }
        }
        
        if (isProfileMenuOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }
        
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isProfileMenuOpen]);

    const toggleBurgerMenu = () => {
        setIsBurgerMenuOpen((prev) => !prev);
        document.body.style.overflow = isBurgerMenuOpen ? "auto" : "hidden";
    };

    const toggleAuthPopup = () => {
        setIsAuthPopupVisible((prev) => !prev);
    };

    const toggleProfileMenu = () => {
        setIsProfileMenuOpen((prev) => !prev);
    };

    const handleLogout = async () => {
        try {
            const response = await axios.post("http://localhost:5077/logout", {}, { 
                withCredentials: true 
            });
            
            if (response.data.success || response.status === 200) {
                console.log("Logout successful");
                setIsLoggedIn(false);
                setIsProfileMenuOpen(false);
                setIsAuthPopupVisible(false);
                navigate("/");
            } else {
                console.error("Logout failed:", response.data.error || "Unknown error");
            }
        } catch (error) {
            console.error("Failed to log out:", error);
            
            if (axios.isAxiosError(error) && error.response) {
                console.error("Server response:", error.response.data);
            }
        }
    };

    return (
        <div className="relative w-full">
            <div id="navBar" className="sticky flex flex-row items-center justify-between w-full top-0 p-2 h-[60px] shadow-lg bg-emerald-400 z-40">
                {isLoggedIn && (
                    <div className="relative">
                        <img src={pers_icon} alt="Profile Icon" className="p-1 w-12 h-12 cursor-pointer rounded-full border-2 border-white hover:bg-white/30 transition-colors" onClick={toggleProfileMenu}/>

                        {isProfileMenuOpen && (
                            <div ref={profileMenuRef} className="absolute left-0 mt-2 w-40 shadow-[0_0_10px_rgba(0,0,0,0.2)] rounded-b-lg rounded-tr-lg border-2 border-emerald-400 divide-y divide-white font-bold text-white bg-emerald-400 z-50">
                                <button onClick={() => { setIsProfileMenuOpen(false); navigate("/profile"); }} className="cursor-pointer block w-full text-left px-4 py-2 hover:rounded-tr-lg hover:bg-emerald-300 transition-colors">Profile</button>
                                <button onClick={handleLogout} className="cursor-pointer block w-full text-left px-4 py-2 hover:rounded-b-lg hover:bg-emerald-300 transition-colors">Logout</button>
                            </div>
                        )}
                    </div>
                )}

                {!isLoggedIn && (
                    <div className="p-1 w-12 h-12 border-2 border-emerald-400 bg-emerald-400"></div>
                )}

                <Link to="/" className={`text-xl font-bold p-1 rounded-md text-white border-2 border-white hover:bg-white/30 transition-colors absolute left-1/2 transform -translate-x-1/2 ${isLoggedIn ? 'lg:left-27' : 'lg:left-12'}`}>Recipla.</Link>

                <div className="flex items-center">
                    <Link to="/" className="hidden md:flex font-bold text-white text-xl mr-5 p-2 rounded-lg hover:bg-emerald-300 transition-colors">Home</Link>

                    {isLoggedIn && (
                        <>
                            <Link to="/account" className="hidden md:flex font-bold text-white text-xl mr-5 p-2 rounded-lg hover:bg-emerald-300 transition-colors">Meal Plan</Link>
                            <Link to="/account/ingredients" className="hidden md:flex font-bold text-white text-xl mr-5 p-2 rounded-lg hover:bg-emerald-300 transition-colors">My Ingredients</Link>
                            <Link to="/account/shopping" className="hidden md:flex font-bold text-white text-xl mr-5 p-2 rounded-lg hover:bg-emerald-300 transition-colors">Shopping List</Link>
                            <Link to="/account/recipes" className="hidden md:flex font-bold text-white text-xl mr-5 p-2 rounded-lg hover:bg-emerald-300 transition-colors">Meal Recipes</Link>
                        </>
                    )}

                    {!isLoggedIn && (
                        <button onClick={toggleAuthPopup} className="cursor-pointer hidden md:flex font-bold text-white text-xl mr-5 p-2 rounded-lg hover:bg-emerald-300 transition-colors">Login</button>
                    )}

                    <button id="burgerButton" className="lg:hidden p-2 rounded-lg" onClick={toggleBurgerMenu}>
                        <div className="space-y-2">
                            <div className="w-10 h-1 bg-white"></div>
                            <div className="w-10 h-1 bg-white"></div>
                            <div className="w-10 h-1 bg-white"></div>
                        </div>
                    </button>
                </div>
            </div>

            {isBurgerMenuOpen && (
                <div className="fixed inset-0 bg-black-20 backdrop-blur-sm z-40" onClick={toggleBurgerMenu}></div>
            )}

            <div id="burgerMenu" className={`fixed inset-y-0 right-0 w-1/2 h-screen shadow-xl text-white bg-emerald-400 z-50 transform transition-transform duration-200 ${ isBurgerMenuOpen ? "translate-x-0" : "translate-x-full" }`}>
                <button className="m-4 flex justify-center items-center" onClick={toggleBurgerMenu}>
                    <div className="space-y-2">
                        <div className="w-10 h-1 bg-white rotate-45 translate-y-3"></div>
                        <div className="w-10 h-1 bg-white opacity-0"></div>
                        <div className="w-10 h-1 bg-white -rotate-45 -translate-y-3"></div>
                    </div>
                </button>

                <div className="p-5 text-xl font-bold">
                    <div className="m-5 w-max">
                        <Link to="/" onClick={toggleBurgerMenu}>Home</Link>
                    </div>

                    {isLoggedIn && (
                        <>
                            <div className="m-5 mt-10 w-max">
                                <Link to="/account" onClick={toggleBurgerMenu}>Meal Plan</Link>
                            </div>

                            <div className="m-5 w-max">
                                <Link to="/account/ingredients" onClick={toggleBurgerMenu}>My Ingredients</Link>
                            </div>

                            <div className="m-5 w-max">
                                <Link to="/account/shopping" onClick={toggleBurgerMenu}>Shopping List</Link>
                            </div>

                            <div className="m-5 w-max">
                                <Link to="/account/recipes" onClick={toggleBurgerMenu}>Meal Recipes</Link>
                            </div>
                        </>
                    )}

                    <div className="m-5 w-max">
                        {!isLoggedIn && (
                            <button onClick={() => { toggleAuthPopup(); toggleBurgerMenu(); }}>Login</button>
                        )}
                    </div>
                </div>
            </div>

            <Auth isVisible={isAuthPopupVisible} onClose={toggleAuthPopup} onLoginSuccess={() => setIsLoggedIn(true)} />
        </div>
    );
};

export default Nav;