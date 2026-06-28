import { useState } from "react";
import { api } from "../services/api";

export function ApprovePanel({ jobId, artifact, onDecision }) {
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const decide = async (approved) => {
    setLoading(true);
    setError(null);
    try {
      await api.approve(jobId, approved, reason || undefined);
      onDecision();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-5">
      <h3 className="font-semibold text-yellow-800 mb-3">
        G2 — Intuition Check (Human Gate)
      </h3>
      {artifact?.payload?.candidate_paths && (
        <div className="mb-4 space-y-2">
          {artifact.payload.candidate_paths.map((p, i) => (
            <div
              key={i}
              className="bg-white border border-yellow-100 rounded-lg p-3"
            >
              <p className="text-sm font-medium text-gray-700">{p.name}</p>
              <p className="text-xs text-gray-500 mt-1">{p.intuition_basis}</p>
            </div>
          ))}
        </div>
      )}
      <label className="block text-xs text-gray-600 mb-1">
        Reason (optional)
      </label>
      <textarea
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none
          focus:outline-none focus:ring-2 focus:ring-yellow-400"
        rows={2}
        placeholder="Why approve or reject?"
        value={reason}
        onChange={(e) => setReason(e.target.value)}
        disabled={loading}
      />
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      <div className="mt-3 flex gap-3">
        <button
          onClick={() => decide(true)}
          disabled={loading}
          className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg
            hover:bg-green-700 disabled:opacity-40 transition-colors"
        >
          Approve
        </button>
        <button
          onClick={() => decide(false)}
          disabled={loading}
          className="px-4 py-2 bg-red-500 text-white text-sm font-medium rounded-lg
            hover:bg-red-600 disabled:opacity-40 transition-colors"
        >
          Reject
        </button>
      </div>
    </div>
  );
}
