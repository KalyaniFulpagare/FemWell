import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { Activity, ArrowRight, ShieldCheck } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { loginUser, registerUser } from "../services/api";
import "./Auth.css";

export default function Auth() {
  const { login, isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();

  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (loading) return null;
  if (isAuthenticated) return <Navigate to="/screening" replace />;

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    if (!email.trim() || !password) {
      setError("Please enter your email and password.");
      return;
    }

    if (password.length < 8) {
      setError("Password must contain at least 8 characters.");
      return;
    }

    setSubmitting(true);

    try {
      if (mode === "register") {
        const result = await registerUser(email.trim(), password);
        login(result.token, { user_id: result.user_id });
      } else {
        const result = await loginUser(email.trim(), password);
        login(result.token, result.user);
      }

      navigate("/screening", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-visual">
        <div className="auth-brand">
          <img className="auth-logo-image" src="/femwell-logo.png" alt="FemWell" />
          <span>FemWell</span>
        </div>

        <div className="auth-message">
          <p className="eyebrow">PERSONAL HEALTH INSIGHT</p>
          <h1>
            Understand your
            <em> health patterns.</em>
          </h1>
          <p>
            A private screening space designed to help you explore
            patterns associated with PCOS using machine learning.
          </p>
        </div>

        <div className="auth-note">
          <ShieldCheck size={17} />
          <span>Your assessment history stays linked to your account.</span>
        </div>
      </section>

      <section className="auth-panel">
        <div className="auth-card">
          <div className="auth-icon">
            <Activity size={21} />
          </div>

          <p className="auth-kicker">
            {mode === "login" ? "WELCOME BACK" : "GET STARTED"}
          </p>

          <h2>
            {mode === "login"
              ? "Continue your journey."
              : "Create your FemWell space."}
          </h2>

          <p className="auth-description">
            {mode === "login"
              ? "Sign in to access your screening history and insights."
              : "Create an account to save assessments and explore your results."}
          </p>

          <form onSubmit={handleSubmit}>
            <label>
              Email
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
              />
            </label>

            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimum 8 characters"
                autoComplete={
                  mode === "login" ? "current-password" : "new-password"
                }
              />
            </label>

            {error && <div className="auth-error">{error}</div>}

            <button className="auth-submit" disabled={submitting}>
              {submitting
                ? "Please wait..."
                : mode === "login"
                  ? "Sign in"
                  : "Create account"}
              {!submitting && <ArrowRight size={18} />}
            </button>
          </form>

          <div className="auth-switch">
            <span>
              {mode === "login"
                ? "Don't have an account?"
                : "Already have an account?"}
            </span>

            <button
              type="button"
              onClick={() => {
                setMode(mode === "login" ? "register" : "login");
                setError("");
              }}
            >
              {mode === "login" ? "Create one" : "Sign in"}
            </button>
          </div>

          <p className="auth-disclaimer">
            FemWell is an educational/screening prototype. It does not
            diagnose PCOS or replace professional healthcare advice.
          </p>
        </div>
      </section>
    </main>
  );
}

