import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getAssessment } from "../services/api";
import { useAuth } from "../context/AuthContext";
import "./Screening.css";

const featureInfo = {
  "hair growth": {
    label: "Hair growth",
    key: "hair growth(Y/N)",
    explanation: "Increased facial or body hair can be one of the patterns considered when screening for PCOS-related features. FemWell considers this alongside your other responses."
  },
  "weight gain": {
    label: "Recent weight gain",
    key: "Weight gain(Y/N)",
    explanation: "Recent weight gain can occur alongside several hormonal or metabolic patterns. FemWell considers it as one input among many."
  },
  "skin darkening": {
    label: "Skin darkening",
    key: "Skin darkening (Y/N)",
    explanation: "Certain types of skin darkening can occur alongside metabolic or hormonal changes. FemWell considers this pattern together with other information."
  },
  "pimples": {
    label: "Acne / pimples",
    key: "Pimples(Y/N)",
    explanation: "Acne or increased pimples can occur with hormonal changes, but they are also common for many other reasons. FemWell treats this as one contributing pattern."
  },
  "weight": {
    label: "Weight",
    key: "Weight (Kg)",
    explanation: "Body weight is one of the measurements included in the model. Its contribution is interpreted alongside height, BMI, cycle information and symptoms."
  },
  "height": {
    label: "Height",
    key: "Height(Cm)",
    explanation: "Height is one of the measurements included in the model and is considered alongside weight and BMI."
  },
  "bmi": {
    label: "BMI",
    key: "BMI",
    explanation: "BMI is one of the measurements considered by the model. It is interpreted alongside your other responses rather than as a standalone indicator."
  },
  "systolic": {
    label: "Systolic blood pressure",
    key: "BP _Systolic (mmHg)",
    explanation: "Systolic blood pressure is one of the health measurements included in the model. FemWell considers it alongside the other information provided."
  },
  "diastolic": {
    label: "Diastolic blood pressure",
    key: "BP _Diastolic (mmHg)",
    explanation: "Diastolic blood pressure is one of the health measurements included in the model. FemWell considers it alongside the other information provided."
  },
  "follicle no. (r)": {
    label: "Right ovary follicle count",
    key: "Follicle No. (R)",
    explanation: "The model uses the reported follicle count as one of several clinical measurements. This value should be interpreted by a healthcare professional in its proper clinical context."
  },
  "follicle no. (l)": {
    label: "Left ovary follicle count",
    key: "Follicle No. (L)",
    explanation: "The model uses the reported follicle count as one of several clinical measurements. This value should be interpreted by a healthcare professional in its proper clinical context."
  },
  "amh(ng/ml)": {
    label: "AMH level",
    key: "AMH(ng/mL)",
    explanation: "AMH is a hormone measurement that can be included in assessments involving ovarian function. FemWell uses the reported value as one model input rather than as a standalone diagnostic indicator."
  },
  "lh(miu/ml)": {
    label: "LH level",
    key: "LH(mIU/mL)",
    explanation: "LH is one of the hormone measurements included in the model. FemWell considers it together with other measurements rather than as a standalone indicator."
  },
  "cycle length(days)": {
    label: "Menstrual cycle length",
    key: "Cycle length(days)",
    explanation: "Cycle length is one of the menstrual-cycle measurements considered by the model. FemWell interprets it together with the other information provided."
  },
  "fast food": {
    label: "Fast-food intake",
    key: "Fast food (Y/N)",
    explanation: "Diet-related information is one of the lifestyle patterns included in the model. A single dietary response does not determine PCOS risk or cause."
  },
  "cycle(r/i)": {
    label: "Menstrual cycle pattern",
    key: "Cycle(R/I)",
    explanation: "Menstrual cycle regularity is an important piece of information in many PCOS-related assessments. FemWell considers it together with your other responses."
  }
};

function normalizeFeature(feature) {
  const cleaned = feature
    .replace(/^bin__/, "")
    .replace(/^num__/, "")
    .replace(/^cat__/, "")
    .replace(/_\d+$/, "")
    .replace(/\s*\(Y\/N\)\s*/gi, "")
    .trim()
    .toLowerCase();

  if (cleaned.includes("bp _systolic")) return "systolic";
  if (cleaned.includes("bp _diastolic")) return "diastolic";
  if (cleaned.includes("height")) return "height";
  if (cleaned === "weight (kg)") return "weight";

  return cleaned;
}

function getFeatureInfo(feature) {
  const normalized = normalizeFeature(feature);

  return (
    featureInfo[normalized] || {
      label: feature
        .replace(/^bin__/, "")
        .replace(/^num__/, "")
        .replace(/^cat__/, "")
        .replace(/_\d+$/, "")
        .replace(/\s*\(Y\/N\)\s*/gi, "")
        .trim(),
      key: null,
      explanation:
        "This feature contributed to the model's estimate based on the pattern found in your responses. Its contribution does not mean that this feature causes PCOS or confirms a diagnosis."
    }
  );
}

function getResponse(inputs, feature) {
  const info = getFeatureInfo(feature);

  if (
    info.key &&
    inputs?.[info.key] !== undefined &&
    inputs?.[info.key] !== null
  ) {
    return inputs[info.key];
  }

  return "Not provided";
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") {
    return "Not provided";
  }

  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(1);
  }

  return String(value);
}

export default function Results() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();

  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [openFeature, setOpenFeature] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await getAssessment(id, token);
        setResult(data);
      } catch (err) {
        setError(err.message || "Could not load your result.");
      }
    }

    if (token && id) {
      load();
    }
  }, [id, token]);

  if (error) {
    return (
      <div className="result-page">
        <div className="result-shell">
          <h1>Something went wrong.</h1>
          <p>{error}</p>
          <button
            className="primary-btn"
            onClick={() => navigate("/screening")}
          >
            Back to screening
          </button>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="loading-screen">
        <p>Preparing your result...</p>
      </div>
    );
  }

  const probability = Math.round(result.probability * 100);

  const increasing = result.top_features_increasing || [];
  const decreasing = result.top_features_decreasing || [];

  const features = [
    ...increasing.map((item) => ({ ...item, direction: "up" })),
    ...decreasing.map((item) => ({ ...item, direction: "down" }))
  ];

  const maxContribution = Math.max(
    ...features.map((item) => Math.abs(item.contribution)),
    0.01
  );

  return (
    <div className="result-page">

      <header className="topbar">
        <div className="brand">
          <img src="/femwell-logo.png" alt="FemWell" />
          <span>FemWell</span>
        </div>
      </header>

      <main className="result-shell">

        <section className="result-main">

          <div className="risk-ring">
            <span>{probability}%</span>
          </div>

          <div className="result-copy">
            <p className="eyebrow">YOUR SCREENING RESULT</p>

            <h1>
              Your estimated risk is {result.risk_category}.
            </h1>

            <p>
              FemWell found patterns in your answers that correspond
              to this estimated level of PCOS risk.
            </p>
          </div>

        </section>

        {features.length > 0 && (
          <section className="insight-section">

            <p className="eyebrow">WHAT INFLUENCED YOUR RESULT</p>

            <p className="insight-intro">
              These are the features that had the strongest influence
              on this particular model estimate.
            </p>

            <div className="insight-list">

              {features.map((item) => {

                const info = getFeatureInfo(item.feature);
                const isOpen = openFeature === item.feature;

                const percentage =
                  (Math.abs(item.contribution) / maxContribution) * 100;

                return (
                  <div className="insight-card" key={item.feature}>

                    <button
                      className="insight-header"
                      onClick={() =>
                        setOpenFeature(isOpen ? null : item.feature)
                      }
                    >

                      <div className="insight-title">

                        <span>{info.label}</span>

                        <span
                          className={`insight-direction ${item.direction}`}
                        >
                          {item.direction === "up" ? "Higher" : "Lower"}
                        </span>

                        <span className="insight-expand">
                          {isOpen ? "-" : "+"}
                        </span>

                      </div>

                      <div className="contribution-bar">
                        <div
                          className={`contribution-fill ${item.direction}`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>

                    </button>

                    {isOpen && (
                      <div className="insight-details">

                        <p>{info.explanation}</p>

                        <div className="your-response">

                          <span>Your response</span>

                          <strong>
                            {formatValue(
                              getResponse(result.inputs, item.feature)
                            )}
                          </strong>

                        </div>

                        <small>
                          {item.direction === "up"
                            ? "This feature pushed the model estimate higher."
                            : "This feature pushed the model estimate lower."}{" "}
                          This does not mean it causes or rules out PCOS.
                        </small>

                      </div>
                    )}

                  </div>
                );
              })}

            </div>

          </section>
        )}

        <section className="result-meaning">

          <p className="eyebrow">WHAT THIS MEANS</p>

          <p>
            Your result is a machine-learning screening estimate based
            on patterns in the information you provided. It is not a
            diagnosis, and a higher or lower estimate does not by itself
            confirm or rule out PCOS.
          </p>

        </section>

        <div className="result-note">
          <strong>Important:</strong> This is a screening estimate,
          not a diagnosis. FemWell does not replace professional
          medical advice.
        </div>

        <button
          className="primary-btn"
          onClick={() => navigate("/screening")}
        >
          Take another screening
        </button>

      </main>

    </div>
  );
}
