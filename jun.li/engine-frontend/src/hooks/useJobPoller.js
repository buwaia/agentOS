import { useState, useEffect, useRef } from "react";
import { api } from "../services/api";

export function useJobPoller(jobId) {
  const [job, setJob] = useState(null);
  const [error, setError] = useState(null);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (!jobId) return;

    const TERMINAL = ["DONE", "FAILED"];

    const poll = async () => {
      try {
        const data = await api.getJob(jobId);
        setJob(data);
        if (TERMINAL.includes(data.status)) {
          clearInterval(intervalRef.current);
        }
      } catch (e) {
        setError(e.message);
      }
    };

    poll();
    intervalRef.current = setInterval(poll, 3000);
    return () => clearInterval(intervalRef.current);
  }, [jobId]);

  return { job, error };
}
