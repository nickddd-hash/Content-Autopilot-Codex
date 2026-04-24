"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { fetchJson } from "@/lib/api";

function statusText(status: string) {
  const labels: Record<string, string> = {
    running: "В работе",
    pending: "В очереди",
    completed: "Завершено",
    failed: "Ошибка",
  };

  return labels[status] || status;
}

export default function JobPolling({
  planId,
  itemId,
  initialStatus,
}: {
  planId: string;
  itemId: string;
  initialStatus: string;
}) {
  const [jobStatus, setJobStatus] = useState<string | null>(initialStatus);
  const router = useRouter();

  useEffect(() => {
    let intervalId: NodeJS.Timeout | undefined;

    const checkJobStatus = async () => {
      const job = await fetchJson<any>(`/content-plans/${planId}/items/${itemId}/latest-job`, null);
      if (!job) return;

      setJobStatus(job.status);
      if (job.status === "completed" || job.status === "failed") {
        if (intervalId) clearInterval(intervalId);
        router.refresh();
      }
    };

    if (jobStatus === "running" || jobStatus === "pending") {
      void checkJobStatus();
      intervalId = setInterval(() => {
        void checkJobStatus();
      }, 3000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [jobStatus, planId, itemId, router]);

  if (jobStatus !== "running" && jobStatus !== "pending") {
    return null;
  }

  return (
    <div
      style={{
        marginTop: "16px",
        padding: "16px",
        background: "var(--surface)",
        border: "1px solid var(--accent)",
        borderRadius: "12px",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px", gap: "12px", flexWrap: "wrap" }}>
        <strong>Генерация в процессе</strong>
        <span className="badge badge-warning">{statusText(jobStatus)}</span>
      </div>
      <p style={{ margin: "0 0 12px", color: "var(--muted)", fontSize: "0.95rem" }}>
        Страница обновится автоматически, когда задача завершится.
      </p>
      <div style={{ width: "100%", height: "8px", background: "rgba(255,255,255,0.1)", borderRadius: "4px", overflow: "hidden" }}>
        <div
          style={{
            width: "50%",
            height: "100%",
            background: "var(--accent)",
            animation: "indeterminate 1.5s infinite linear",
            transformOrigin: "0% 50%",
          }}
        />
      </div>
      <style
        dangerouslySetInnerHTML={{
          __html: `
            @keyframes indeterminate {
              0% { transform: translateX(-100%) scaleX(0.2); }
              50% { transform: translateX(0%) scaleX(0.5); }
              100% { transform: translateX(200%) scaleX(0.2); }
            }
          `,
        }}
      />
    </div>
  );
}
