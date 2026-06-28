import { StatusBadge } from "./StatusBadge";

export function JobList({ jobs, selectedId, onSelect }) {
  if (jobs.length === 0) {
    return (
      <p className="text-sm text-gray-400 italic">
        No jobs yet. Submit a problem above.
      </p>
    );
  }

  return (
    <ul className="space-y-2">
      {jobs.map((job) => (
        <li
          key={job.job_id}
          onClick={() => onSelect(job.job_id)}
          className={`cursor-pointer rounded-lg border px-4 py-3 transition-colors
            ${selectedId === job.job_id ? "border-blue-400 bg-blue-50" : "border-gray-200 bg-white hover:bg-gray-50"}`}
        >
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm text-gray-800 truncate flex-1">
              {job.problem}
            </p>
            <StatusBadge status={job.status} />
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Stage: <span className="font-medium">{job.current_stage}</span>
          </p>
        </li>
      ))}
    </ul>
  );
}
