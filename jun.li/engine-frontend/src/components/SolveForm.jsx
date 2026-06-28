import { useState } from "react";
import { api } from "../services/api";

const emptyStep = () => ({ expression: "", reason: "" });

export function SolveForm({ jobId, onDone }) {
  const [steps, setSteps] = useState([emptyStep()]);
  const [finalResult, setFinalResult] = useState("");
  const [intuition, setIntuition] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const updateStep = (i, field, val) => {
    setSteps((prev) =>
      prev.map((s, idx) => (idx === i ? { ...s, [field]: val } : s)),
    );
  };

  const addStep = () => setSteps((prev) => [...prev, emptyStep()]);
  const removeStep = (i) =>
    setSteps((prev) => prev.filter((_, idx) => idx !== i));

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.advance(jobId, "SOLVE", {
        stage: "SOLVE",
        steps: steps.map((s, i) => ({
          step: i + 1,
          expression: s.expression,
          reason: s.reason,
        })),
        final_result: finalResult,
        intuition_explanation: intuition,
      });
      onDone();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      onSubmit={submit}
      className="bg-blue-50 border border-blue-200 rounded-xl p-5 space-y-4"
    >
      <h3 className="font-semibold text-blue-800">SOLVE — 提交解题步骤</h3>

      <div className="space-y-3">
        {steps.map((s, i) => (
          <div
            key={i}
            className="bg-white border border-blue-100 rounded-lg p-3 space-y-2"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-gray-500">
                Step {i + 1}
              </span>
              {steps.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeStep(i)}
                  className="text-xs text-red-400 hover:text-red-600"
                >
                  删除
                </button>
              )}
            </div>
            <input
              className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="Expression（表达式）"
              value={s.expression}
              onChange={(e) => updateStep(i, "expression", e.target.value)}
              required
            />
            <input
              className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="Reason（这步的理由，不能为空）"
              value={s.reason}
              onChange={(e) => updateStep(i, "reason", e.target.value)}
              required
            />
          </div>
        ))}
      </div>

      <button
        type="button"
        onClick={addStep}
        className="text-sm text-blue-600 hover:text-blue-800 font-medium"
      >
        + 添加步骤
      </button>

      <div className="space-y-2">
        <input
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          placeholder="Final Result（最终结论）"
          value={finalResult}
          onChange={(e) => setFinalResult(e.target.value)}
          required
        />
        <textarea
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-400"
          rows={3}
          placeholder="Intuition Explanation（洞见说明，解释为什么这条路径有效）"
          value={intuition}
          onChange={(e) => setIntuition(e.target.value)}
          required
        />
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        type="submit"
        disabled={loading}
        className="px-5 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg
          hover:bg-blue-700 disabled:opacity-40 transition-colors"
      >
        {loading ? "提交中…" : "提交 SOLVE"}
      </button>
    </form>
  );
}
