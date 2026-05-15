"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { fetchJson, postJson } from "@/lib/api";

function statusText(status: string) {
  const labels: Record<string, string> = {
    running: "В работе",
    pending: "В очереди",
    completed: "Завершено",
    failed: "Ошибка",
    cancelled: "Остановлено",
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

function formatElapsed(seconds: number): string {
  if (seconds < 60) return `${seconds} сек`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return s > 0 ? `${m} мин ${s} сек` : `${m} мин`;
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
  const [elapsed, setElapsed] = useState(0);
  const [isCancelling, setIsCancelling] = useState(false);
  const router = useRouter();
  const elapsedRef = useRef<NodeJS.Timeout | undefined>(undefined);

  const isActive = job?.status === "running" || job?.status === "pending";

  useEffect(() => {
    let intervalId: NodeJS.Timeout | undefined;

    const checkJobStatus = async () => {
      const nextJob = await fetchJson<PlanJob | null>(`/content-plans/${planId}/latest-job`, null);
      if (!nextJob) return;
      setJob(nextJob);
      if (nextJob.status === "completed" || nextJob.status === "failed" || nextJob.status === "cancelled") {
        if (intervalId) clearInterval(intervalId);
        router.refresh();
      }
    };

    if (isActive) {
      void checkJobStatus();
      intervalId = setInterval(() => void checkJobStatus(), 3000);
    }

    return () => { if (intervalId) clearInterval(intervalId); };
  }, [job?.status, planId, router, isActive]);

  // Elapsed timer
  useEffect(() => {
    if (isActive) {
      setElapsed(0);
      elapsedRef.current = setInterval(() => setElapsed((prev) => prev + 1), 1000);
    } else {
      if (elapsedRef.current) clearInterval(elapsedRef.current);
    }
    return () => { if (elapsedRef.current) clearInterval(elapsedRef.current); };
  }, [isActive]);

  async function handleCancel() {
    setIsCancelling(true);
    try {
      await postJson(`/content-plans/${planId}/cancel-pipeline`, {});
      router.refresh();
    } catch {
      setIsCancelling(false);
    }
  }

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
        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          {isActive && elapsed > 0 && (
            <span style={{ fontSize: "13px", color: "var(--muted)" }}>{formatElapsed(elapsed)}</span>
          )}
          <span className={isFailed ? "badge badge-danger" : "badge badge-warning"}>{statusText(job.status)}</span>
          {isActive && (
            <button
              type="button"
              className="btn btn-sm"
              style={{ borderColor: "var(--danger)", color: "var(--danger)" }}
              disabled={isCancelling}
              onClick={() => void handleCancel()}
            >
              {isCancelling ? "Останавливаем..." : "Остановить"}
            </button>
          )}
        </div>
      </div>
      <p className="form-hint" style={{ marginTop: "10px" }}>
        {isFailed
          ? job.error_message || "Сборка плана завершилась с ошибкой."
          : elapsed > 120
          ? "Генерация нескольких постов сразу занимает время — обычно 3–10 минут. Можно подождать или остановить и собрать материалы вручную."
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
          <style dangerouslySetInnerHTML={{ __html: `@keyframes indeterminate { 0% { transform: translateX(-100%) scaleX(0.2); } 50% { transform: translateX(0%) scaleX(0.5); } 100% { transform: translateX(200%) scaleX(0.2); } }` }} />
        </div>
      ) : null}
    </article>
  );
}
