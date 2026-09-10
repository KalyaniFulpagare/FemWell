import { useMemo, useState } from "react";
import { createAssessment } from "../services/api";
import { useAuth } from "../context/AuthContext";
import "./Screening.css";

const F = {
  age: "Age (yrs)",
  weight: "Weight (Kg)",
  height: "Height(Cm)",
  bmi: "BMI",
  bloodGroup: "Blood Group",
  cycle: "Cycle(R/I)",
  cycleLength: "Cycle length(days)",
  pregnant: "Pregnant(Y/N)",
  abortions: "No. of aborptions",
  weightGain: "Weight gain(Y/N)",
  hairGrowth: "hair growth(Y/N)",
  skinDarkening: "Skin darkening (Y/N)",
  hairLoss: "Hair loss(Y/N)",
  pimples: "Pimples(Y/N)",
  fastFood: "Fast food (Y/N)",
  exercise: "Reg.Exercise(Y/N)",
  waist: "Waist(inch)",
  hip: "Hip(inch)",
  waistHip: "Waist:Hip Ratio",
  pulse: "Pulse rate(bpm)",
  rr: "RR (breaths/min)",
  hb: "Hb(g/dl)",
  systolic: "BP _Systolic (mmHg)",
  diastolic: "BP _Diastolic (mmHg)",
  rbs: "RBS(mg/dl)",
  beta1: "I   beta-HCG(mIU/mL)",
  beta2: "II    beta-HCG(mIU/mL)",
  fsh: "FSH(mIU/mL)",
  lh: "LH(mIU/mL)",
  fshLh: "FSH/LH",
  tsh: "TSH (mIU/L)",
  amh: "AMH(ng/mL)",
  prolactin: "PRL(ng/mL)",
  vitaminD: "Vit D3 (ng/mL)",
  progesterone: "PRG(ng/mL)",
  follicleL: "Follicle No. (L)",
  follicleR: "Follicle No. (R)",
  follicleSizeL: "Avg. F size (L) (mm)",
  follicleSizeR: "Avg. F size (R) (mm)",
  endometrium: "Endometrium (mm)",
};

const yn = (v) => (v === "yes" ? 1 : v === "no" ? 0 : undefined);

function Input({ number, label, unit, value, onChange, placeholder = "" }) {
  return (
    <div className="input-card">
      <div className="input-number">{number}</div>

      <div className="field">
        <span>{label}</span>

        <div className="input-wrap">
          <input
            type="number"
            value={value ?? ""}
            placeholder={placeholder}
            onChange={(e) => onChange(e.target.value)}
          />
          {unit && <small>{unit}</small>}
        </div>
      </div>
    </div>
  );
}

function Select({ number, label, value, onChange, children }) {
  return (
    <div className="input-card">
      <div className="input-number">{number}</div>

      <div className="field">
        <span>{label}</span>
        <select value={value ?? ""} onChange={(e) => onChange(e.target.value)}>
          <option value="">Select</option>
          {children}
        </select>
      </div>
    </div>
  );
}

function YesNo({ number, label, value, onChange }) {
  return (
    <div className="input-card">
      <div className="input-number">{number}</div>

      <div className="field">
        <span>{label}</span>

        <div className="choice-row">
          <button
            type="button"
            className={`choice ${value === "yes" ? "active" : ""}`}
            onClick={() => onChange("yes")}
          >
            Yes
          </button>

          <button
            type="button"
            className={`choice ${value === "no" ? "active" : ""}`}
            onClick={() => onChange("no")}
          >
            No
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Screening() {
  const { token } = useAuth();

  const [step, setStep] = useState(1);
  const [result, setResult] = useState(null);
  const [hasReport, setHasReport] = useState(null);
  const [form, setForm] = useState({});
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const set = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const bmi = useMemo(() => {
    const weight = Number(form.weight);
    const height = Number(form.height);

    if (!weight || !height) return null;

    return Number((weight / ((height / 100) ** 2)).toFixed(2));
  }, [form.weight, form.height]);

  const waistHip = useMemo(() => {
    const waist = Number(form.waist);
    const hip = Number(form.hip);

    if (!waist || !hip) return null;

    return Number((waist / hip).toFixed(2));
  }, [form.waist, form.hip]);

  const fshLh = useMemo(() => {
    const fsh = Number(form.fsh);
    const lh = Number(form.lh);

    if (!fsh || !lh) return null;

    return Number((fsh / lh).toFixed(2));
  }, [form.fsh, form.lh]);

  const add = (obj, key, value) => {
    if (value !== undefined && value !== null && value !== "") {
      obj[F[key]] = Number(value);
    }
  };

  const buildInputs = () => {
    const inputs = {};

    add(inputs, "age", form.age);
    add(inputs, "weight", form.weight);
    add(inputs, "height", form.height);
    add(inputs, "bmi", bmi);

    add(inputs, "bloodGroup", form.bloodGroup);
    add(inputs, "cycle", form.cycle);
    add(inputs, "cycleLength", form.cycleLength);
    add(inputs, "pregnant", yn(form.pregnant));
    add(inputs, "abortions", form.abortions);

    add(inputs, "weightGain", yn(form.weightGain));
    add(inputs, "hairGrowth", yn(form.hairGrowth));
    add(inputs, "skinDarkening", yn(form.skinDarkening));
    add(inputs, "hairLoss", yn(form.hairLoss));
    add(inputs, "pimples", yn(form.pimples));

    add(inputs, "fastFood", yn(form.fastFood));
    add(inputs, "exercise", yn(form.exercise));

    add(inputs, "waist", form.waist);
    add(inputs, "hip", form.hip);
    add(inputs, "waistHip", waistHip);

    add(inputs, "pulse", form.pulse);
    add(inputs, "rr", form.rr);
    add(inputs, "hb", form.hb);
    add(inputs, "systolic", form.systolic);
    add(inputs, "diastolic", form.diastolic);
    add(inputs, "rbs", form.rbs);

    if (hasReport) {
      add(inputs, "beta1", form.beta1);
      add(inputs, "beta2", form.beta2);
      add(inputs, "fsh", form.fsh);
      add(inputs, "lh", form.lh);
      add(inputs, "fshLh", fshLh);
      add(inputs, "tsh", form.tsh);
      add(inputs, "amh", form.amh);
      add(inputs, "prolactin", form.prolactin);
      add(inputs, "vitaminD", form.vitaminD);
      add(inputs, "progesterone", form.progesterone);
      add(inputs, "follicleL", form.follicleL);
      add(inputs, "follicleR", form.follicleR);
      add(inputs, "follicleSizeL", form.follicleSizeL);
      add(inputs, "follicleSizeR", form.follicleSizeR);
      add(inputs, "endometrium", form.endometrium);
    }

    return inputs;
  };

  const next = () => {
    setError("");
    setStep((s) => Math.min(5, s + 1));
  };

  const back = () => {
    setError("");
    setStep((s) => Math.max(1, s - 1));
  };

  const submit = async () => {
    setSubmitting(true);
    setError("");

    try {
      const result = await createAssessment(buildInputs(), token);
      setResult(result);
      setStep(6);
      window.location.href = `/results/${result.assessment_id}`;
    } catch (err) {
      setError(err.message || "Unable to create assessment.");
    } finally {
      setSubmitting(false);
    }
  };

  const stepTitles = [
    "About you",
    "Periods & symptoms",
    "Lifestyle & measurements",
    "Your reports",
    "Review",
  ];

  return (
    <div className="screening-page">

      <div className="topbar">
        <div className="brand">
          <img src="/femwell-logo.png" alt="FemWell" />
          FemWell
        </div>

        <div className="form-count">
          {stepTitles[step - 1]} · {step}/5
        </div>
      </div>

      <main className="screening-shell">

        <div className="screening-heading">
          <span className="eyebrow">PCOS RISK SCREENING</span>

          <h1>
            Let's understand <em>your health.</em>
          </h1>

          <p>
            A simple screening based on your periods, symptoms and health
            information. You only need to provide measurements you actually know.
          </p>
        </div>

        <div className="assessment-form">

          {step === 1 && (
            <>
              <Input
                number="01"
                label="How old are you?"
                value={form.age}
                onChange={(v) => set("age", v)}
                placeholder="Your age"
                unit="years"
              />

              <Input
                number="02"
                label="How tall are you?"
                value={form.height}
                onChange={(v) => set("height", v)}
                placeholder="e.g. 160"
                unit="cm"
              />

              <Input
                number="03"
                label="How much do you weigh?"
                value={form.weight}
                onChange={(v) => set("weight", v)}
                placeholder="e.g. 55"
                unit="kg"
              />

              <Select
                number="04"
                label="Do you know your blood group?"
                value={form.bloodGroup}
                onChange={(v) => set("bloodGroup", v)}
              >
                <option value="11">A+</option>
                <option value="12">A−</option>
                <option value="13">B+</option>
                <option value="14">B−</option>
                <option value="15">AB+</option>
                <option value="16">AB−</option>
                <option value="17">O+</option>
                <option value="18">O−</option>
              </Select>

              {bmi !== null && (
                <div className="input-card">
                  <div className="input-number">✓</div>
                  <div className="field">
                    <span>Your BMI</span>
                    <small>
                      Calculated automatically from your height and weight.
                    </small>
                    <strong>{bmi}</strong>
                  </div>
                </div>
              )}

              <div className="form-footer">
                <p>
                  No medical report is needed for this step.
                </p>

                <button className="primary-btn" onClick={next}>
                  Continue
                </button>
              </div>
            </>
          )}

          {step === 2 && (
            <>
              <Select
                number="01"
                label="How would you describe your periods?"
                value={form.cycle}
                onChange={(v) => set("cycle", v)}
              >
                <option value="2">Usually regular</option>
                <option value="4">Often irregular</option>
              </Select>

              <Input
                number="02"
                label="What is your usual cycle length?"
                value={form.cycleLength}
                onChange={(v) => set("cycleLength", v)}
                placeholder="e.g. 28"
                unit="days"
              />

              <YesNo
                number="03"
                label="Are you currently pregnant?"
                value={form.pregnant}
                onChange={(v) => set("pregnant", v)}
              />

              <YesNo
                number="04"
                label="Have you noticed unusual weight gain?"
                value={form.weightGain}
                onChange={(v) => set("weightGain", v)}
              />

              <YesNo
                number="05"
                label="Have you noticed increased facial or body hair?"
                value={form.hairGrowth}
                onChange={(v) => set("hairGrowth", v)}
              />

              <YesNo
                number="06"
                label="Have you noticed unusual hair loss?"
                value={form.hairLoss}
                onChange={(v) => set("hairLoss", v)}
              />

              <YesNo
                number="07"
                label="Have you noticed darker patches of skin?"
                value={form.skinDarkening}
                onChange={(v) => set("skinDarkening", v)}
              />

              <YesNo
                number="08"
                label="Have you been experiencing frequent pimples?"
                value={form.pimples}
                onChange={(v) => set("pimples", v)}
              />

              <div className="form-footer">
                <p>Answer based on what you have personally noticed.</p>

                <div>
                  <button className="primary-btn" onClick={next}>
                    Continue
                  </button>
                </div>
              </div>
            </>
          )}

          {step === 3 && (
            <>
              <YesNo
                number="01"
                label="Do you frequently eat fast food?"
                value={form.fastFood}
                onChange={(v) => set("fastFood", v)}
              />

              <YesNo
                number="02"
                label="Do you exercise regularly?"
                value={form.exercise}
                onChange={(v) => set("exercise", v)}
              />

              <Input
                number="03"
                label="Do you know your waist measurement?"
                value={form.waist}
                onChange={(v) => set("waist", v)}
                placeholder="Optional"
                unit="inch"
              />

              <Input
                number="04"
                label="Do you know your hip measurement?"
                value={form.hip}
                onChange={(v) => set("hip", v)}
                placeholder="Optional"
                unit="inch"
              />

              {waistHip !== null && (
                <div className="input-card">
                  <div className="input-number">✓</div>
                  <div className="field">
                    <span>Waist-to-hip ratio</span>
                    <small>Calculated automatically.</small>
                    <strong>{waistHip}</strong>
                  </div>
                </div>
              )}

              <Input
                number="05"
                label="Do you know your pulse rate?"
                value={form.pulse}
                onChange={(v) => set("pulse", v)}
                placeholder="Optional"
                unit="bpm"
              />

              <Input
                number="06"
                label="Do you know your blood pressure?"
                value={form.systolic}
                onChange={(v) => set("systolic", v)}
                placeholder="Upper number"
                unit="mmHg"
              />

              <Input
                number="07"
                label="And the lower blood-pressure number?"
                value={form.diastolic}
                onChange={(v) => set("diastolic", v)}
                placeholder="Lower number"
                unit="mmHg"
              />

              <div className="form-footer">
                <p>
                  These measurements are optional. Skip anything you don't know.
                </p>

                <button className="primary-btn" onClick={next}>
                  Continue
                </button>
              </div>
            </>
          )}

          {step === 4 && (
            <>
              <div className="input-card">
                <div className="input-number">01</div>

                <div className="field">
                  <span>Do you have a recent blood or ultrasound report?</span>

                  <small>
                    If you do, you can enter values from it. If not, simply skip
                    this section.
                  </small>

                  <div className="choice-row">
                    <button
                      type="button"
                      className={`choice ${hasReport === true ? "active" : ""}`}
                      onClick={() => setHasReport(true)}
                    >
                      Yes, I have one
                    </button>

                    <button
                      type="button"
                      className={`choice ${hasReport === false ? "active" : ""}`}
                      onClick={() => setHasReport(false)}
                    >
                      No, skip
                    </button>
                  </div>
                </div>
              </div>

              {hasReport === true && (
                <>
                  <Input number="02" label="FSH" unit="mIU/mL" value={form.fsh} onChange={(v) => set("fsh", v)} placeholder="From your report" />
                  <Input number="03" label="LH" unit="mIU/mL" value={form.lh} onChange={(v) => set("lh", v)} placeholder="From your report" />

                  {fshLh !== null && (
                    <div className="input-card">
                      <div className="input-number">✓</div>
                      <div className="field">
                        <span>FSH/LH ratio</span>
                        <small>Calculated automatically.</small>
                        <strong>{fshLh}</strong>
                      </div>
                    </div>
                  )}

                  <Input number="04" label="AMH" unit="ng/mL" value={form.amh} onChange={(v) => set("amh", v)} placeholder="From your report" />
                  <Input number="05" label="TSH" unit="mIU/L" value={form.tsh} onChange={(v) => set("tsh", v)} placeholder="From your report" />
                  <Input number="06" label="Prolactin" unit="ng/mL" value={form.prolactin} onChange={(v) => set("prolactin", v)} placeholder="From your report" />
                  <Input number="07" label="Vitamin D3" unit="ng/mL" value={form.vitaminD} onChange={(v) => set("vitaminD", v)} placeholder="From your report" />
                  <Input number="08" label="Progesterone" unit="ng/mL" value={form.progesterone} onChange={(v) => set("progesterone", v)} placeholder="From your report" />

                  <Input number="09" label="Follicle count — left ovary" value={form.follicleL} onChange={(v) => set("follicleL", v)} placeholder="From your report" />
                  <Input number="10" label="Follicle count — right ovary" value={form.follicleR} onChange={(v) => set("follicleR", v)} placeholder="From your report" />
                  <Input number="11" label="Average follicle size — left" unit="mm" value={form.follicleSizeL} onChange={(v) => set("follicleSizeL", v)} placeholder="From your report" />
                  <Input number="12" label="Average follicle size — right" unit="mm" value={form.follicleSizeR} onChange={(v) => set("follicleSizeR", v)} placeholder="From your report" />
                  <Input number="13" label="Endometrium thickness" unit="mm" value={form.endometrium} onChange={(v) => set("endometrium", v)} placeholder="Only if reported" />
                </>
              )}

              {hasReport === false && (
                <div className="input-card">
                  <div className="input-number">✓</div>
                  <div className="field">
                    <span>That's completely fine.</span>
                    <small>
                      FemWell can still perform the screening without report
                      values.
                    </small>
                  </div>
                </div>
              )}

              <div className="form-footer">
                <p>
                  Report values are optional and are never guessed.
                </p>

                <button
                  className="primary-btn"
                  disabled={hasReport === null}
                  onClick={next}
                >
                  Review
                </button>
              </div>
            </>
          )}

          {step === 5 && (
            <>
              <div className="input-card">
                <div className="input-number">✓</div>

                <div className="field">
                  <span>Basic information</span>
                  <small>
                    Age, height, weight, cycle information and symptoms you've
                    provided.
                  </small>
                </div>
              </div>

              <div className="input-card">
                <div className="input-number">✓</div>

                <div className="field">
                  <span>Health measurements</span>
                  <small>
                    Only measurements you actually entered will be used.
                  </small>
                </div>
              </div>

              <div className="input-card">
                <div className="input-number">✓</div>

                <div className="field">
                  <span>Medical reports</span>
                  <small>
                    {hasReport
                      ? "The report values you entered will be included."
                      : "No report values will be included."}
                  </small>
                </div>
              </div>

              <div className="form-footer">
                <p>
                  FemWell is a screening prototype, not a medical diagnosis.
                </p>

                <button
                  className="primary-btn"
                  disabled={submitting}
                  onClick={submit}
                >
                  {submitting ? "Screening..." : "Get my result"}
                </button>
              </div>

              {error && <div className="form-error">{error}</div>}
            </>
          )}

        </div>
      </main>
    </div>
  );
}



