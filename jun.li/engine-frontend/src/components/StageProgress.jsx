const STAGES = ["UNDERSTAND", "ORIENT", "SOLVE", "VERIFY"];

export function StageProgress({ currentStage, status }) {
  const currentIdx = STAGES.indexOf(currentStage);

  return (
    <div className="flex items-center gap-2">
      {STAGES.map((stage, idx) => {
        const done = idx < currentIdx || status === "done";
        const active = idx === currentIdx && status !== "done";
        return (
          <div key={stage} className="flex items-center gap-2">
            <div
              className={`flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium
                ${done ? "bg-green-100 text-green-700" : ""}
                ${active ? "bg-blue-100 text-blue-700 ring-1 ring-blue-400" : ""}
                ${!done && !active ? "bg-gray-100 text-gray-400" : ""}`}
            >
              <span
                className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px]
                  ${done ? "bg-green-500 text-white" : ""}
                  ${active ? "bg-blue-500 text-white" : ""}
                  ${!done && !active ? "bg-gray-300 text-white" : ""}`}
              >
                {done ? "✓" : idx + 1}
              </span>
              {stage}
            </div>
            {idx < STAGES.length - 1 && (
              <div
                className={`h-px w-4 ${idx < currentIdx ? "bg-green-400" : "bg-gray-200"}`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
