const BASE = import.meta.env.VITE_API_URL ?? "/api";

async function request(method, path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw Object.assign(new Error(err.detail ?? "Request failed"), {
      status: res.status,
      body: err,
    });
  }
  return res.json();
}

export const api = {
  listJobs: () => request("GET", "/jobs"),
  createJob: (problem) => request("POST", "/jobs", { problem }),
  getJob: (jobId) => request("GET", `/jobs/${jobId}`),
  advance: (jobId, stage, payload) =>
    request("POST", `/jobs/${jobId}/advance`, { stage, payload }),
  approve: (jobId, approved, reason) =>
    request("POST", `/jobs/${jobId}/approve`, { approved, comment: reason }),
  getArtifact: (jobId, stage) =>
    request("GET", `/jobs/${jobId}/artifacts/${stage}`),
};
