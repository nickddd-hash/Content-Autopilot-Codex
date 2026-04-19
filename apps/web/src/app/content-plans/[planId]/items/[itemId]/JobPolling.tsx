"use client";

import { useEffect, useState } from "react";
import { fetchJson } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function JobPolling({ planId, itemId, initialStatus }: { planId: string, itemId: string, initialStatus: string }) {
  const [jobStatus, setJobStatus] = useState<string | null>(initialStatus);
  const router = useRouter();

  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    const checkJobStatus = async () => {
      const job = await fetchJson<any>(`/job-runs/content-plans/${planId}/items/${itemId}/latest`, null);
      if (job) {
        setJobStatus(job.status);
        if (job.status === "completed" || job.status === "failed") {
          clearInterval(intervalId);
          router.refresh(); // Reload page to get new content
        }
      }
    };

    if (jobStatus === "running" || jobStatus === "pending") {
      intervalId = setInterval(checkJobStatus, 3000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [jobStatus, planId, itemId, router]);

  if (jobStatus !== "running" && jobStatus !== "pending") {
    return null;
  }

  return (
    <div style={{ marginTop: "16px", padding: "16px", background: "var(--surface)", border: "1px solid var(--accent)", borderRadius: "12px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
        <strong>Generation in progress...</strong>
        <span className="badge badge-warning">{jobStatus}</span>
      </div>
      <div style={{ width: "100%", height: "8px", background: "rgba(255,255,255,0.1)", borderRadius: "4px", overflow: "hidden" }}>
        <div style={{ 
          width: "50%", 
          height: "100%", 
          background: "var(--accent)",
          animation: "indeterminate 1.5s infinite linear",
          transformOrigin: "0% 50%"
        }}></div>
      </div>
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes indeterminate {
          0% { transform: translateX(-100%) scaleX(0.2); }
          50% { transform: translateX(0%) scaleX(0.5); }
          100% { transform: translateX(200%) scaleX(0.2); }
        }
      `}} />
    </div>
  );
}
