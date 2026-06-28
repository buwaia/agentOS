import { useState } from "react";
import { api } from "../services/api";

const emptyCase = () => ({
  method: "",
  input: "",
  expected: "",
  actual: "",
  passed: true,
});

export function VerifyForm({ jobId, onDone }) {
  const [cases, setCases] = useState([emptyCase()]);
  const [hasIntuition, setHasIntuition] = useState(true);
  const [hasStory, setHasStory] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const updateCase = (i, field, val) => {
    setCases((prev) =>
      prev.map((c, idx) => (idx === i ? { ...c, [field]: val } : c)),
    );
  };

  const addCase = () => setCases((prev) => [...prev, emptyCase()]);
  const removeCase = (i) =>
    setCases((prev) => prev.filter((_, idx) => idx !== i));

  const allPassed = cases.every((c) => c.passed);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.advance(jobId, "VERIFY", {
        stage: "VERIFY",
        verification_cases: cases,
        quality_check: {
          has_intuition: hasIntuition,
          has_story: hasStory,
          all_verifications_passed: allPassed,
        },
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
      className="bg-purple-50 border border-purple-200 rounded-xl p-5 space-y-4"
    >
      <h3 className="font-semibold text-purple-800">VERIFY — 提交验证结果</h3>

      <div className="space-y-3">
        {cases.map((c, i) => (
          <div
            key={i}
            className="bg-white border border-purple-100 rounded-lg p-3 space-y-2"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-gray-500">
                Case {i + 1}
              </span>
              {cases.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeCase(i)}
                  className="text-xs text-red-400 hover:text-red-600"
                >
                  删除
                </button>
              )}
            </div>
            <input
              className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
              placeholder="Method（验证方法）"
              value={c.method}
              onChange={(e) => updateCase(i, "method", e.target.value)}
              required
            />
            <input
              className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
              placeholder="Input（输入）"
              value={c.input}
              onChange={(e) => updateCase(i, "input", e.target.value)}
              required
            />
            <input
              className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
              placeholder="Expected（期望结果）"
              value={c.expected}
              onChange={(e) => updateCase(i, "expected", e.target.value)}
              required
            />
            <input
              className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
              placeholder="Actual（实际结果）"
              value={c.actual}
              onChange={(e) => updateCase(i, "actual", e.target.value)}
              required
            />
            <label className="flex items-center gap-2 text-sm text-gray-600">
              <input
                type="checkbox"
                checked={c.passed}
                onChange={(e) => updateCase(i, "passed", e.target.checked)}
                className="rounded"
              />
              验证通过
            </label>
          </div>
        ))}
      </div>

      <button
        type="button"
        onClick={addCase}
        className="text-sm text-purple-600 hover:text-purple-800 font-medium"
      >
        + 添加验证用例
      </button>

      <div className="bg-white border border-purple-100 rounded-lg p-3 space-y-2">
        <p className="text-xs font-semibold text-gray-500">Quality Check</p>
        <label className="flex items-center gap-2 text-sm text-gray-600">
          <input
            type="checkbox"
            checked={hasIntuition}
            onChange={(e) => setHasIntuition(e.target.checked)}
            className="rounded"
          />
          Has Intuition（解法包含洞见）
        </label>
        <label className="flex items-center gap-2 text-sm text-gray-600">
          <input
            type="checkbox"
            checked={hasStory}
            onChange={(e) => setHasStory(e.target.checked)}
            className="rounded"
          />
          Has Story（解法有完整叙述）
        </label>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        type="submit"
        disabled={loading}
        className="px-5 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg
          hover:bg-purple-700 disabled:opacity-40 transition-colors"
      >
        {loading ? "提交中…" : "提交 VERIFY"}
      </button>
    </form>
  );
}
