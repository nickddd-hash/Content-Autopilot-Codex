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

function jobTitle(jobType: string | null) {
  if (jobType === "plan_generation_pipeline") {
    return "Контент-план собирается: темы, посты, иллюстрации и расписание";
  }
  if (jobType === "plan_material_build") {
    return "Материалы пересобираются для текущего плана";
  }
  return "Контент-завод работает над планом";
}

type PlanJob = {
  id: string;
  job_type: string;
  status: string;
  error_message?: string | null;
};

export default function PlanJobPolling({
  planId,
  initialJob,
}: {
  planId: string;
  initialJob: PlanJob | null;
}) {
  const [job, setJob] = useState<PlanJob | null>(initialJob);
  const router = useRouter();

  useEffect(() => {
    let intervalId: NodeJS.Timeout | undefined;

    const checkJobStatus = async () => {
      const nextJob = await fetchJson<PlanJob | null>(`/content-plans/${planId}/latest-job`, null);
      if (!nextJob) return;

      setJob(nextJob);
      if (nextJob.status === "completed" || nextJob.status === "failed") {
        if (intervalId) clearInterval(intervalId);
        router.refresh();
      }
    };

    if (job?.status === "running" || job?.status === "pending") {
      void checkJobStatus();
      intervalId = setInterval(() => {
        void checkJobStatus();
      }, 3000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [job?.status, planId, router]);

  if (!job || (job.status !== "running" && job.status !== "pending" && job.status !== "failed")) {
    return null;
  }

  const isFailed = job.status === "failed";

  return (
    <article
      className="panel"
      style={{
        borderColor: isFailed ? "rgba(214, 86, 86, 0.35)" : "rgba(255, 196, 107, 0.35)",
        background: isFailed ? "rgba(214, 86, 86, 0.06)" : "rgba(255, 196, 107, 0.08)",
      }}
    >
      <div className="panel-header">
        <div>
          <span className="panel-kicker">Контент-завод</span>
          <h2 className="panel-title">{jobTitle(job.job_type)}</h2>
        </div>
        <span className={isFailed ? "badge badge-danger" : "badge badge-warning"}>{statusText(job.status)}</span>
      </div>
      <p className="form-hint" style={{ marginTop: "10px" }}>
        {isFailed
          ? job.error_message || "Сборка плана завершилась с ошибкой."
          : "Страница обновится автоматически, когда сборка плана закончится."}
      </p>
      {!isFailed ? (
        <div style={{ width: "100%", height: "8px", background: "rgba(255,255,255,0.1)", borderRadius: "4px", overflow: "hidden", marginTop: "12px" }}>
          <div
            style={{
              width: "50%",
              height: "100%",
              background: "var(--accent)",
              animation: "indeterminate 1.5s infinite linear",
              transformOrigin: "0% 50%",
            }}
          />
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
      ) : null}
    </article>
  );
}
