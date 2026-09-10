const API_BASE = "https://femwell-api.onrender.com/api/v1";

async function request(url, options = {}) {
  const response = await fetch(`${API_BASE}${url}`, options);

  if (!response.ok) {
    const text = await response.text();

    let message = "Something went wrong.";
    try {
      const data = JSON.parse(text);
      message = data.detail || message;
    } catch {
      if (text) message = text;
    }

    throw new Error(message);
  }

  return response.json();
}

export async function registerUser(email, password) {
  return request("/auth/register", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email,
      password,
    }),
  });
}

export async function loginUser(email, password) {
  return request("/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email,
      password,
    }),
  });
}

export async function getCurrentUser(token) {
  return request("/auth/me", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function getFeatureSchema() {
  return request("/assessments/feature-schema");
}

export async function createAssessment(inputs, token) {
  return request("/assessments", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      inputs,
    }),
  });
}

export async function getAssessmentHistory(token) {
  return request("/assessments/history", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function getAssessment(id, token) {
  return request(`/assessments/${id}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function runWhatIf(baselineAssessmentId, modifiedFeatures, token) {
  return request("/assessments/whatif", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      baseline_assessment_id: baselineAssessmentId,
      modified_features: modifiedFeatures,
    }),
  });
}

export async function compareAssessments(id1, id2, token) {
  return request(`/assessments/compare/${id1}/${id2}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}
