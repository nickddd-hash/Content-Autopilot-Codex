"use client";

import { useState } from "react";
import { patchJson } from "@/lib/api";

type ProductContextFormProps = {
  productId: string;
  initialFullDescription: string;
  initialToneOfVoice: string;
  initialTargetAudience: string;
};

export default function ProductContextForm({
  productId,
  initialFullDescription,
  initialToneOfVoice,
  initialTargetAudience,
}: ProductContextFormProps) {
  const [fullDescription, setFullDescription] = useState(initialFullDescription);
  const [toneOfVoice, setToneOfVoice] = useState(initialToneOfVoice);
  const [targetAudience, setTargetAudience] = useState(initialTargetAudience);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setMessage("");

    try {
      await patchJson(`/products/${productId}`, {
        full_description: fullDescription,
        tone_of_voice: toneOfVoice,
        target_audience: targetAudience,
      });
      setMessage("Контекст сохранен.");
    } catch {
      setMessage("Не удалось сохранить контекст.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      <div className="form-group">
        <label className="form-label" style={{ display: "flex", justifyContent: "space-between" }}>
          <span>Глубокий контекст (Резюме от Gemini)</span>
          <span className="badge badge-info" style={{ fontWeight: "normal" }}>
            full_description
          </span>
        </label>
        <p className="form-hint" style={{ marginBottom: "8px", fontSize: "13px", color: "var(--text-secondary)" }}>
          Вставьте сюда результаты анализа ваших навыков, проектов и экспертизы. AI-агент будет читать это перед каждой генерацией текста.
        </p>
        <textarea
          name="fullDescription"
          className="form-input"
          rows={8}
          placeholder="Вставьте глубокий контекст о проекте или вашем личном бренде..."
          value={fullDescription}
          onChange={(event) => setFullDescription(event.target.value)}
        />
      </div>

      <div className="form-group" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
        <div>
          <label className="form-label">Голос и тон (Tone of Voice)</label>
          <p className="form-hint" style={{ marginBottom: "8px", fontSize: "13px", color: "var(--text-secondary)" }}>
            Как общаться с аудиторией? Например: "Пиши дерзко, без воды, обращайся на ты".
          </p>
          <textarea
            name="toneOfVoice"
            className="form-input"
            rows={4}
            placeholder="Опишите стиль..."
            value={toneOfVoice}
            onChange={(event) => setToneOfVoice(event.target.value)}
          />
        </div>

        <div>
          <label className="form-label">Целевая аудитория</label>
          <p className="form-hint" style={{ marginBottom: "8px", fontSize: "13px", color: "var(--text-secondary)" }}>
            Для кого мы пишем этот контент?
          </p>
          <textarea
            name="targetAudience"
            className="form-input"
            rows={4}
            placeholder="Опишите портрет аудитории..."
            value={targetAudience}
            onChange={(event) => setTargetAudience(event.target.value)}
          />
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "flex-end", alignItems: "center", gap: "12px", marginTop: "12px" }}>
        {message && (
          <span style={{ color: message.includes("сохранен") ? "var(--success)" : "var(--danger)" }}>
            {message}
          </span>
        )}
        <button type="submit" className="btn btn-primary" style={{ padding: "0 32px" }} disabled={isSaving}>
          {isSaving ? "Сохраняем..." : "Сохранить контекст"}
        </button>
      </div>
    </form>
  );
}
