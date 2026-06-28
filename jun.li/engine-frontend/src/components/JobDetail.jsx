import { useEffect, useState } from "react";
import { useJobPoller } from "../hooks/useJobPoller";
import { api } from "../services/api";
import { StatusBadge } from "./StatusBadge";
import { StageProgress } from "./StageProgress";
import { ApprovePanel } from "./ApprovePanel";
import { SolveForm } from "./SolveForm";
import { VerifyForm } from "./VerifyForm";

function ArtifactView({ jobId, stage }) {
  const [artifact, setArtifact] = useState(null);

  useEffect(() => {
    if (!jobId || !stage) return;
    api
      .getArtifact(jobId, stage)
      .then(setArtifact)
      .catch(() => {});
  }, [jobId, stage]);

  if (!artifact) return null;

  return (
    <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
      <p className="text-xs font-semibold text-gray-500 uppercase mb-2">
        {stage} Artifact
      </p>
      <pre className="text-xs text-gray-700 whitespace-pre-wrap break-words">
        {JSON.stringify(artifact.payload, null, 2)}
      </pre>
    </div>
  );
}

export function JobDetail({ jobId }) {
  const { job, error } = useJobPoller(jobId);
  const [refreshKey, setRefreshKey] = useState(0);

  if (!jobId) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
        Select a job to view details
      </div>
    );
  }

  if (error) {
    return <p className="text-sm text-red-600 p-4">Error: {error}</p>;
  }

  if (!job) {
    return <p className="text-sm text-gray-400 p-4 animate-pulse">Loading…</p>;
  }

  const STAGES_DONE = ["UNDERSTAND", "ORIENT", "SOLVE", "VERIFY"].filter(
    (s) => {
      const idx = ["UNDERSTAND", "ORIENT", "SOLVE", "VERIFY"].indexOf(s);
      const curIdx = ["UNDERSTAND", "ORIENT", "SOLVE", "VERIFY"].indexOf(
        job.current_stage,
      );
      return idx < curIdx || job.status === "done";
    },
  );

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-gray-800">{job.problem}</p>
          <p className="text-xs text-gray-400 mt-1 font-mono">{job.job_id}</p>
        </div>
        <StatusBadge status={job.status} />
      </div>

      <StageProgress currentStage={job.current_stage} status={job.status} />

      {job.status === "waiting_approval" && job.current_stage === "ORIENT" && (
        <ApprovePanel
          key={refreshKey}
          jobId={job.job_id}
          artifact={null}
          onDecision={() => setRefreshKey((k) => k + 1)}
        />
      )}

      {job.status === "running" && job.current_stage === "SOLVE" && (
        <SolveForm
          key={refreshKey}
          jobId={job.job_id}
          onDone={() => setRefreshKey((k) => k + 1)}
        />
      )}

      {job.status === "running" && job.current_stage === "VERIFY" && (
        <VerifyForm
          key={refreshKey}
          jobId={job.job_id}
          onDone={() => setRefreshKey((k) => k + 1)}
        />
      )}

      {job.gate_failure && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm font-medium text-red-700">
            Gate Failed: {job.gate_failure.gate}
          </p>
          <p className="text-xs text-red-600 mt-1">{job.gate_failure.reason}</p>
        </div>
      )}

      {job.gate_history && job.gate_history.length > 0 && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-2">
          <p className="text-xs font-semibold text-gray-500 uppercase">
            Gate History
          </p>
          {job.gate_history.map((g, i) => (
            <div key={i} className="flex items-center gap-3 text-xs">
              <span className="font-mono font-bold text-gray-700 w-6">
                {g.gate}
              </span>
              <span
                className={`px-2 py-0.5 rounded-full font-medium ${g.result === "passed" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}
              >
                {g.result}
              </span>
              <span className="text-gray-400">{g.type}</span>
              {g.comment && (
                <span className="text-gray-500 italic">"{g.comment}"</span>
              )}
              <span className="text-gray-300 ml-auto">
                {g.checked_at?.slice(11, 19)}
              </span>
            </div>
          ))}
        </div>
      )}

      <div className="space-y-3">
        {STAGES_DONE.map((stage) => (
          <ArtifactView key={stage} jobId={job.job_id} stage={stage} />
        ))}
      </div>
    </div>
  );
}
