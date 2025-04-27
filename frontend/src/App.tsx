import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import Nav from "./components/nav/Nav";

import Home from "./pages/home/Home";

import ProtectedRoute from "./components/protected/ProtectedRoute";
import ErrorPage from "./pages/error/ErrorPage";

import Profile from "./pages/profile/Profile";
import Account from "./pages/account/Account";
import Ingredients from "./pages/ingredients/Ingredients";
import Shopping from "./pages/shopping/Shopping";
import Recipes from "./pages/recipes/Recipes";
import CategorySelection from "./components/auth/CategorySelection";

const App: React.FC = () => {
  return (
    <Router>
      <Nav />
      
      <Routes>
        <Route path="/" element={<Home />} />

        <Route path="/error" element={<ErrorPage />} />

        <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
        <Route path="/account" element={<ProtectedRoute><Account /></ProtectedRoute>} />
        <Route path="/account/ingredients" element={<ProtectedRoute><Ingredients /></ProtectedRoute>} />
        <Route path="/account/shopping" element={<ProtectedRoute><Shopping /></ProtectedRoute>} />
        <Route path="/account/recipes" element={<ProtectedRoute><Recipes /></ProtectedRoute>} />
        <Route path="/select-categories" element={<CategorySelection />} />
        <Route path="/update-categories" element={<CategorySelection isUpdating={true} />} />
      </Routes>
    </Router>
  );
};

export default App;