import { useState } from "react";
import { api } from "../services/api";

export function SubmitForm({ onJobCreated }) {
  const [problem, setProblem] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    if (!problem.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const job = await api.createJob(problem.trim());
      setProblem("");
      onJobCreated(job);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      onSubmit={submit}
      className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm"
    >
      <h2 className="text-lg font-semibold text-gray-800 mb-4">
        Submit Math Problem
      </h2>
      <textarea
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none
          focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
        rows={4}
        placeholder="Enter a math problem, e.g. Prove that √2 is irrational..."
        value={problem}
        onChange={(e) => setProblem(e.target.value)}
        disabled={loading}
      />
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      <button
        type="submit"
        disabled={loading || !problem.trim()}
        className="mt-3 px-5 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg
          hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? "Submitting…" : "Submit"}
      </button>
    </form>
  );
}
