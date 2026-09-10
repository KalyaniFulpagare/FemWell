import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Auth from "./pages/Auth";
import Screening from "./pages/Screening";
import Results from "./pages/Results";
import "./App.css";

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) return null;

  return isAuthenticated ? children : <Navigate to="/auth" replace />;
}

function App() {
  const { isAuthenticated } = useAuth();

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <Navigate
              to={isAuthenticated ? "/screening" : "/auth"}
              replace
            />
          }
        />

        <Route path="/auth" element={<Auth />} />

        <Route
          path="/screening"
          element={
            <ProtectedRoute>
              <Screening />
            </ProtectedRoute>
          }
        />

        <Route
          path="/results/:id"
          element={
            <ProtectedRoute>
              <Results />
            </ProtectedRoute>
          }
        />

        <Route
          path="*"
          element={
            <Navigate
              to={isAuthenticated ? "/screening" : "/auth"}
              replace
            />
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
