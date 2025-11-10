import React from "react";
import { BrowserRouter as Router, Routes, Route, useLocation } from "react-router-dom";
import Navbar from "./Components/Navbar/Navbar";
import Home from "./pages/Home";
import Signup from "./pages/Signup";
import Login from "./pages/Login";
import Profile from "./pages/Profile";


import LawyerProfile from "./pages/LawyerProfile";
import Lawyers from "./pages/Lawyers";
import DocumentAnalyzer from "./pages/DocumentAnalyzer";
import LawyerConnect from "./pages/LawyerConnect";
import MyDocuments from "./pages/MyDocuments";
import DocumentCreation from "./pages/DocumentCreation";
import SharedDocument from "./pages/SharedDocument";

function AppContent() {
  const location = useLocation();
  const hideNavbarRoutes = ['/login', '/signup'];
  const shouldShowNavbar = !hideNavbarRoutes.includes(location.pathname);

  return (
      <>
        {/* Conditionally render navbar */}
        {shouldShowNavbar && <Navbar />}
        
        {/* Page routes with conditional top padding for fixed navbar */}
        <main className={shouldShowNavbar ? "pt-20 bg-gray-50" : "bg-gray-50"}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/document-analyzer/:id" element={<DocumentAnalyzer />} />
          <Route path="/document-creation" element={<DocumentCreation />} />
          <Route path="/document-creation/:id" element={<DocumentCreation />} />
          <Route path="/shared/:id" element={<SharedDocument />} />
          <Route path="/lawyer-connect" element={<LawyerConnect />} />
          <Route path="/my-documents" element={<MyDocuments />} />


          <Route path="/lawyer-profile/:id" element={<LawyerProfile />} />
          <Route path="/lawyers" element={<Lawyers />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/profile" element={<Profile />} />
        </Routes>
      </main>
    </>
  );
}

import { Toaster } from 'react-hot-toast';

function App() {
  return (
    <Router>
      <Toaster position="bottom-right" />
      <AppContent />
    </Router>
  );
}

export default App;
