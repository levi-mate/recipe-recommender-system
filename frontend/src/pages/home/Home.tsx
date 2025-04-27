import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import Auth from "../../components/auth/Auth";

const Home: React.FC = () => {
    const [isAuthPopupVisible, setIsAuthPopupVisible] = useState(false);
    const [isLoggedIn, setIsLoggedIn] = useState<boolean | null>(null);
    const [targetPath, setTargetPath] = useState<string>("");
    const navigate = useNavigate();

    useEffect(() => {
        const checkLoginStatus = async () => {
            try {
                const response = await axios.get("http://localhost:5077/check_login", {
                    withCredentials: true,
                });
                
                const isUserLoggedIn = response.data.data?.loggedIn || false;
                console.log("Login check response:", response.data);
                setIsLoggedIn(isUserLoggedIn);
            } catch (error) {
                console.error("Failed to check login status:", error);
                setIsLoggedIn(false);
            }
        };

        checkLoginStatus();
    }, []);

    const handleLinkClick = (e: React.MouseEvent<HTMLAnchorElement>, path: string) => {
        if (!isLoggedIn) {
            e.preventDefault();
            setTargetPath(path);
            setIsAuthPopupVisible(true);
        }
    };

    const handleLoginSuccess = () => {
        setIsLoggedIn(true);
        setIsAuthPopupVisible(false);
        
        if (targetPath) {
            setTimeout(() => {
                navigate(targetPath);
                window.location.reload();
            }, 100);
        } else {
            window.location.reload();
        }
    };

    const SecureLink: React.FC<{to: string, className?: string, children: React.ReactNode}> = ({ to, className, children }) => (
        <Link to={to} className={className} onClick={(e) => handleLinkClick(e, to)}>{children}</Link>
    );

    return (
        <div className="flex flex-col min-h-screen">
            <section className="flex flex-col items-center justify-center bg-gradient-to-r from-emerald-400 to-teal-500 text-white py-20 px-4">
                <h1 className="text-5xl md:text-5xl font-bold mb-10 p-3 rounded-lg border-4 border-white">Recipla.</h1>

                <div className="max-w-4xl mx-auto text-center">
                    <h1 className="text-4xl md:text-3xl font-bold mb-6">Personalised Meal Planning Made Simple</h1>
                    <p className="text-xl mb-8">Get tailored recipes based on your ingredients, preferences, and nutritional goals</p>

                    <div className="flex flex-wrap justify-center gap-4">
                        <SecureLink to="/account/recipes" className="px-6 py-3 bg-white text-emerald-500 font-bold rounded-lg hover:bg-gray-100 transition-colors">Generate Recipes</SecureLink>
                        <SecureLink to="/account" className="px-6 py-3 bg-emerald-600 text-white font-bold rounded-lg hover:bg-emerald-700 transition-colors">View Meal Plan</SecureLink>
                    </div>
                </div>
            </section>

            <section className="py-16 px-4 bg-gray-50">
                <div className="max-w-6xl mx-auto">
                    <div className="flex flex-row items-center justify-center gap-2 mb-12">
                        <h2 className="text-3xl font-bold">How It</h2>
                        <h2 className="text-3xl font-bold text-emerald-400">Works</h2>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        <div className="flex flex-col items-center p-6 bg-white rounded-lg shadow-[0_0_10px_rgba(0,0,0,0.1)]">
                            <div className="w-16 h-16 rounded-full bg-emerald-400 flex items-center justify-center text-white font-bold text-3xl mb-4">1</div>

                            <h3 className="text-xl font-bold mb-3">Add Your Ingredients</h3>
                            <p className="text-center text-gray-600">Enter ingredients you have available or want to use in your meals</p>
                        </div>
                        
                        <div className="flex flex-col items-center p-6 bg-white rounded-lg shadow-[0_0_10px_rgba(0,0,0,0.1)]">
                            <div className="w-16 h-16 rounded-full bg-emerald-400 flex items-center justify-center text-white font-bold text-3xl mb-4">2</div>

                            <h3 className="text-xl font-bold mb-3">Generate Recipes</h3>
                            <p className="text-center text-gray-600">Our system finds the perfect recipes based on your ingredients and preferences</p>
                        </div>
                        
                        <div className="flex flex-col items-center p-6 bg-white rounded-lg shadow-[0_0_10px_rgba(0,0,0,0.1)]">
                            <div className="w-16 h-16 rounded-full bg-emerald-400 flex items-center justify-center text-white font-bold text-3xl mb-4">3</div>

                            <h3 className="text-xl font-bold mb-3">Plan Your Meals</h3>
                            <p className="text-center text-gray-600">Organise your weekly meal plan and track nutritional information</p>
                        </div>
                    </div>
                </div>
            </section>

            <section className="py-16 px-4">
                <div className="max-w-6xl mx-auto">
                    <div className="flex flex-row items-center justify-center gap-2 mb-12">
                        <h2 className="text-3xl font-bold">Our</h2>
                        <h2 className="text-3xl font-bold text-emerald-400">Features</h2>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div className="flex flex-col p-6 rounded-lg shadow-[0_0_10px_rgba(0,0,0,0.2)] bg-slate-50">
                            <h3 className="text-xl font-bold mb-3 text-emerald-500">Smart Recipe Recommendations</h3>
                            <p className="text-gray-600 mb-4">Our hybrid recommendation system combines your ingredient list with your preferences to suggest recipes you'll love.</p>

                            <SecureLink to="/account/recipes" className="mt-auto text-emerald-500 font-bold hover:text-emerald-600">Try it now →</SecureLink>
                        </div>
                        
                        <div className="flex flex-col p-6 rounded-lg shadow-[0_0_10px_rgba(0,0,0,0.2)] bg-slate-50">
                            <h3 className="text-xl font-bold mb-3 text-emerald-500">Interactive Meal Calendar</h3>
                            <p className="text-gray-600 mb-4">Plan your meals for the week ahead and keep track of what you've enjoyed.</p>

                            <SecureLink to="/account" className="mt-auto text-emerald-500 font-bold hover:text-emerald-600">View calendar →</SecureLink>
                        </div>
                        
                        <div className="flex flex-col p-6 rounded-lg shadow-[0_0_10px_rgba(0,0,0,0.2)] bg-slate-50">
                            <h3 className="text-xl font-bold mb-3 text-emerald-500">Nutrition Tracking</h3>
                            <p className="text-gray-600 mb-4">Monitor your daily and weekly nutritional intake based on your meal plans.</p>

                            <SecureLink to="/account" className="mt-auto text-emerald-500 font-bold hover:text-emerald-600">View nutrition →</SecureLink>
                        </div>
                        
                        <div className="flex flex-col p-6 rounded-lg shadow-[0_0_10px_rgba(0,0,0,0.2)] bg-slate-50">
                            <h3 className="text-xl font-bold mb-3 text-emerald-500">Automated Shopping List</h3>
                            <p className="text-gray-600 mb-4">Generate shopping lists based on recipes you've selected and ingredients you need.</p>

                            <SecureLink to="/account/shopping" className="mt-auto text-emerald-500 font-bold hover:text-emerald-600">Manage shopping list →</SecureLink>
                        </div>
                    </div>
                </div>
            </section>

            <section className="py-16 px-4 bg-gradient-to-r from-teal-500 to-emerald-400 text-white">
                <div className="max-w-4xl mx-auto text-center">
                    <h2 className="text-3xl font-bold mb-6">Personalised For You</h2>
                    <p className="text-xl mb-8">Set your dietary preferences, exclude categories you don't enjoy, and get recommendations tailored to your taste.</p>

                    <SecureLink to="/profile" className="px-6 py-3 bg-white text-emerald-500 font-bold rounded-lg hover:bg-gray-100 transition-colors">Update Preferences</SecureLink>
                </div>
            </section>

            <footer className="bg-gray-800 text-white py-12 px-4 mt-auto">
                <div className="max-w-6xl mx-auto">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                        <div>
                            <h3 className="font-bold text-lg mb-4">Recipla</h3>
                            <p className="text-gray-300">Simplifying meal planning with personalised recipe recommendations.</p>
                        </div>
                        
                        <div>
                            <h4 className="font-bold mb-4">Features</h4>

                            <ul className="space-y-2">
                                <li><SecureLink to="/account/recipes" className="text-gray-300 hover:text-white">Recipe Recommendations</SecureLink></li>
                                <li><SecureLink to="/account" className="text-gray-300 hover:text-white">Meal Planning</SecureLink></li>
                                <li><SecureLink to="/account/ingredients" className="text-gray-300 hover:text-white">Ingredient Management</SecureLink></li>
                                <li><SecureLink to="/account/shopping" className="text-gray-300 hover:text-white">Shopping Lists</SecureLink></li>
                            </ul>
                        </div>
                        
                        <div>
                            <h4 className="font-bold mb-4">Account</h4>

                            <ul className="space-y-2">
                                <li><SecureLink to="/profile" className="text-gray-300 hover:text-white">Your Profile</SecureLink></li>
                                <li><SecureLink to="/profile" className="text-gray-300 hover:text-white">Preferences</SecureLink></li>
                            </ul>
                        </div>
                        
                        <div>
                            <h4 className="font-bold mb-4">About</h4>

                            <p className="text-gray-300">Digital Systems Project - UWE Bristol</p>
                            <p className="text-gray-300 mt-2">© {new Date().getFullYear()} Recipla</p>
                        </div>
                    </div>
                </div>
            </footer>

            <Auth isVisible={isAuthPopupVisible} onClose={() => setIsAuthPopupVisible(false)} onLoginSuccess={handleLoginSuccess} />
        </div>
    );
};

export default Home;