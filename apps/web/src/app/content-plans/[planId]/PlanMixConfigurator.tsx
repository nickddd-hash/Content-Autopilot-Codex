"use client";

import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";

import HelpHint from "@/components/HelpHint";
import { patchJson } from "@/lib/api";

type MixKey = "practical" | "educational" | "news" | "opinion" | "critical";

type PlanMixConfiguratorProps = {
  planId: string;
  initialMix: Record<MixKey, number>;
};

const DIRECTION_META: Array<{ key: MixKey; label: string; description: string }> = [
  { key: "practical", label: "Practical", description: "Практика, применение, польза в работе и жизни." },
  { key: "educational", label: "Educational", description: "Объяснение AI простыми словами, база и разборы." },
  { key: "news", label: "News", description: "Важные новости и обновления AI понятным языком." },
  { key: "opinion", label: "Opinion", description: "Личная позиция, интерпретация, взгляд автора." },
  { key: "critical", label: "Critical", description: "Критический взгляд, ограничения, хайп и риски." },
];

function normalizeMix(input: Record<string, number> | undefined): Record<MixKey, number> {
  return {
    practical: Math.max(0, Math.min(100, Number(input?.practical || 0))),
    educational: Math.max(0, Math.min(100, Number(input?.educational || 0))),
    news: Math.max(0, Math.min(100, Number(input?.news || 0))),
    opinion: Math.max(0, Math.min(100, Number(input?.opinion || 0))),
    critical: Math.max(0, Math.min(100, Number(input?.critical || 0))),
  };
}

export default function PlanMixConfigurator({ planId, initialMix }: PlanMixConfiguratorProps) {
  const [mounted, setMounted] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const [mix, setMix] = useState<Record<MixKey, number>>(() => normalizeMix(initialMix));

  useEffect(() => {
    setMounted(true);
  }, []);

  const total = useMemo(() => Object.values(mix).reduce((sum, value) => sum + value, 0), [mix]);
  const hasAny = useMemo(() => Object.values(mix).some((value) => value > 0), [mix]);
  const canSave = total === 100 && hasAny && !isSaving;

  function toggleDirection(key: MixKey, checked: boolean) {
    setMix((current) => {
      const next = { ...current };
      if (!checked) {
        next[key] = 0;
        return next;
      }

      const remaining = Math.max(0, 100 - Object.values(current).reduce((sum, value) => sum + value, 0));
      next[key] = current[key] > 0 ? current[key] : Math.min(20, remaining);
      return next;
    });
  }

  function updateDirection(key: MixKey, requestedValue: number) {
    setMix((current) => {
      const otherTotal = Object.entries(current)
        .filter(([entryKey]) => entryKey !== key)
        .reduce((sum, [, value]) => sum + value, 0);
      const maxAllowed = Math.max(0, 100 - otherTotal);
      const safeValue = Math.max(0, Math.min(requestedValue, maxAllowed));

      return {
        ...current,
        [key]: safeValue,
      };
    });
  }

  async function handleSave() {
    if (!canSave) return;

    setIsSaving(true);
    setError("");

    try {
      await patchJson(`/content-plans/${planId}`, {
        settings_json: {
          content_mix: mix,
        },
      });
      window.location.reload();
    } catch {
      setError("Не удалось сохранить настройку плана.");
      setIsSaving(false);
    }
  }

  const modal = isOpen ? (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(4, 6, 12, 0.82)",
        backdropFilter: "blur(8px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
        zIndex: 10000,
      }}
    >
      <div
        style={{
          width: "min(860px, 100%)",
          height: "min(90vh, 860px)",
          background: "#101114",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "20px",
          boxShadow: "0 30px 80px rgba(0,0,0,0.45)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        <div style={{ padding: "24px 24px 0", display: "flex", justifyContent: "space-between", gap: "12px" }}>
          <div>
            <div className="panel-kicker">Стратегия плана</div>
            <h2 style={{ margin: "8px 0 0", fontSize: "1.4rem", color: "#f5f7f1", display: "inline-flex", alignItems: "center", gap: "8px" }}>
              Настроить план
              <HelpHint text="Выберите направления и задайте долю каждого. Сумма должна быть ровно 100%." />
            </h2>
          </div>
          <button type="button" className="btn" onClick={() => setIsOpen(false)}>
            Закрыть
          </button>
        </div>

        <div style={{ padding: "20px 24px 0", overflowY: "auto", display: "grid", gap: "12px", flex: 1, minHeight: 0 }}>
          {DIRECTION_META.map((direction) => {
            const enabled = mix[direction.key] > 0;
            const otherTotal = Object.entries(mix)
              .filter(([entryKey]) => entryKey !== direction.key)
              .reduce((sum, [, value]) => sum + value, 0);
            const maxAllowed = Math.max(mix[direction.key], 100 - otherTotal);

            return (
              <div
                key={direction.key}
                style={{
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                  borderRadius: "14px",
                  padding: "14px 16px",
                  background: enabled ? "rgba(255,255,255,0.035)" : "rgba(255,255,255,0.02)",
                }}
              >
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "minmax(0, 1fr) minmax(260px, 360px)",
                    gap: "16px",
                    alignItems: "center",
                  }}
                >
                  <label style={{ display: "flex", gap: "12px", alignItems: "flex-start", cursor: "pointer", minWidth: 0 }}>
                    <input
                      type="checkbox"
                      checked={enabled}
                      onChange={(event) => toggleDirection(direction.key, event.target.checked)}
                      style={{ marginTop: "3px", flexShrink: 0 }}
                    />
                    <div style={{ minWidth: 0 }}>
                      <div style={{ color: "#f5f7f1", fontWeight: 600 }}>{direction.label}</div>
                      <div
                        style={{
                          color: "rgba(245, 247, 241, 0.7)",
                          fontSize: "0.92rem",
                          lineHeight: 1.45,
                          display: "-webkit-box",
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: "vertical",
                          overflow: "hidden",
                        }}
                      >
                        {direction.description}
                      </div>
                    </div>
                  </label>

                  <div style={{ display: "grid", gap: "8px", opacity: enabled ? 1 : 0.45 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", color: "#f5f7f1", fontSize: "0.95rem" }}>
                      <span>Доля</span>
                      <strong>{mix[direction.key]}%</strong>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={maxAllowed}
                      step={5}
                      value={mix[direction.key]}
                      disabled={!enabled}
                      onChange={(event) => updateDirection(direction.key, Number(event.target.value))}
                    />
                  </div>
                </div>
              </div>
            );
          })}

          <div
            style={{
              padding: "14px 16px",
              borderRadius: "14px",
              border: `1px solid ${total === 100 ? "rgba(198, 255, 72, 0.25)" : "rgba(255, 166, 0, 0.25)"}`,
              background: total === 100 ? "rgba(198, 255, 72, 0.06)" : "rgba(255, 166, 0, 0.08)",
              color: "#f5f7f1",
            }}
          >
            <div style={{ fontWeight: 600, display: "inline-flex", alignItems: "center", gap: "8px" }}>
              <span>Сумма: {total}%</span>
              <HelpHint text="Слайдеры ограничены автоматически: больше 100% поставить нельзя." />
            </div>
          </div>

          {error ? <div style={{ color: "#ff8e8e" }}>{error}</div> : null}
        </div>

        <div
          style={{
            flexShrink: 0,
            display: "flex",
            justifyContent: "flex-end",
            gap: "12px",
            flexWrap: "wrap",
            padding: "16px 24px 24px",
            borderTop: "1px solid rgba(255, 255, 255, 0.08)",
            background: "#101114",
          }}
        >
          <button type="button" className="btn" onClick={() => setIsOpen(false)} disabled={isSaving}>
            Отмена
          </button>
          <button type="button" className="btn btn-primary" onClick={() => void handleSave()} disabled={!canSave}>
            {isSaving ? "Сохраняем..." : "Сохранить"}
          </button>
        </div>
      </div>
    </div>
  ) : null;

  return (
    <>
      <button type="button" className="btn" onClick={() => setIsOpen(true)}>
        Настроить план
      </button>
      {mounted && modal ? createPortal(modal, document.body) : null}
    </>
  );
}
