import { revalidatePath } from "next/cache";

import AutoSaveSettingsForm from "./AutoSaveSettingsForm";
import HelpHint from "@/components/HelpHint";
import { fetchJson, patchJson } from "@/lib/api";

export const dynamic = "force-dynamic";

type SystemSetting = {
  key: string;
  value: string | null;
  description?: string | null;
};

const MANAGED_SETTINGS: Array<{ key: string; description?: string }> = [
  { key: "LLM_PROVIDER", description: "Основной провайдер генерации." },
  { key: "OPENAI_API_KEY", description: "Ключ OpenAI." },
  { key: "OPENROUTER_API_KEY", description: "Ключ OpenRouter." },
  { key: "KIE_AI_API_KEY", description: "Ключ KIE." },
  { key: "HUBRIS_API_KEY", description: "Ключ Hubris (hubris.pw)." },
  { key: "TEXT_MODEL", description: "Общая текстовая модель." },
  { key: "IMAGE_MODEL", description: "Общая модель изображений." },
  { key: "VIDEO_MODEL", description: "Общая видеомодель." },
];

const PROVIDER_OPTIONS = [
  { value: "openai", label: "OpenAI" },
  { value: "openrouter", label: "OpenRouter" },
  { value: "hubris", label: "Hubris" },
  { value: "kie", label: "KIE" },
];

const TEXT_MODEL_OPTIONS = [
  { value: "gpt-5.4", label: "OpenAI · GPT-5.4" },
  { value: "gpt-5.4-mini", label: "OpenAI · GPT-5.4 Mini" },
  { value: "google/gemini-2.5-flash", label: "OpenRouter · Gemini 2.5 Flash" },
  { value: "google/gemini-2.5-flash-lite", label: "OpenRouter · Gemini 2.5 Flash Lite" },
  { value: "gpt-5-4", label: "KIE · GPT-5.4" },
  { value: "google/gemini-2.5-flash", label: "Hubris · Gemini 2.5 Flash" },
  { value: "google/gemini-2.5-pro", label: "Hubris · Gemini 2.5 Pro" },
  { value: "anthropic/claude-sonnet-4.6", label: "Hubris · Claude Sonnet 4.6" },
  { value: "anthropic/claude-haiku-4.5", label: "Hubris · Claude Haiku 4.5" },
  { value: "openai/gpt-4o", label: "Hubris · GPT-4o" },
  { value: "openai/gpt-4o-mini", label: "Hubris · GPT-4o Mini" },
];

const IMAGE_MODEL_OPTIONS = [
  { value: "gpt-image-1", label: "OpenAI · GPT Image 1" },
  { value: "google/gemini-2.5-flash-image", label: "OpenRouter · Nano Banana" },
  { value: "google/gemini-3.1-flash-image-preview", label: "OpenRouter · Nano Banana 2" },
  { value: "black-forest-labs/flux.2-klein", label: "OpenRouter · FLUX.2 Klein" },
  { value: "black-forest-labs/flux.2-pro", label: "OpenRouter · FLUX.2 Pro" },
  { value: "black-forest-labs/flux.2-max", label: "OpenRouter · FLUX.2 Max" },
];

const VIDEO_MODEL_OPTIONS = [
  { value: "", label: "Не выбрано" },
  { value: "google/veo-3.1", label: "OpenRouter · Veo 3.1" },
  { value: "google/veo-3.1-fast", label: "OpenRouter · Veo 3.1 Fast" },
];

function getSecretPlaceholder(value: string) {
  return value ? "Ключ сохранен. Введите новый, чтобы заменить." : "Введите ключ";
}

async function saveSettingsAction(formData: FormData) {
  "use server";

  const settings = MANAGED_SETTINGS.map((item) => ({
    key: item.key,
    value: String(formData.get(item.key) || "").trim() || null,
    description: item.description,
  }));

  await patchJson("/settings/system", { settings });
  revalidatePath("/settings");
}

export default async function SettingsPage() {
  const storedSettings = await fetchJson<SystemSetting[]>("/settings/system", []);
  const settingsMap = new Map(storedSettings.map((item) => [item.key, item]));
  const getValue = (key: string, fallback = "") => settingsMap.get(key)?.value || fallback;

  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">Система</p>
          <h1>Настройки API</h1>
        </div>
      </header>

      <section className="panel">
        <AutoSaveSettingsForm action={saveSettingsAction}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label form-label-inline" htmlFor="LLM_PROVIDER">
              Провайдер
              <HelpHint text="Определяет, куда система отправляет запросы на текст, изображения и видео." />
            </label>
            <select key={getValue("LLM_PROVIDER", "openai")} id="LLM_PROVIDER" name="LLM_PROVIDER" className="form-input" defaultValue={getValue("LLM_PROVIDER", "openai")}>
              {PROVIDER_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div
            style={{
              display: "grid",
              gap: "14px",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            }}
          >
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label form-label-inline" htmlFor="OPENAI_API_KEY">
                OpenAI key
                <HelpHint text="Нужен только если используете OpenAI как основной или резервный контур." />
              </label>
              <input
                id="OPENAI_API_KEY"
                name="OPENAI_API_KEY"
                type="password"
                className="form-input"
                defaultValue=""
                placeholder={getSecretPlaceholder(getValue("OPENAI_API_KEY"))}
              />
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label form-label-inline" htmlFor="OPENROUTER_API_KEY">
                OpenRouter key
                <HelpHint text="Ключ для Gemini, Nano Banana, FLUX и других моделей через OpenRouter." />
              </label>
              <input
                id="OPENROUTER_API_KEY"
                name="OPENROUTER_API_KEY"
                type="password"
                className="form-input"
                defaultValue=""
                placeholder={getSecretPlaceholder(getValue("OPENROUTER_API_KEY"))}
              />
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label form-label-inline" htmlFor="KIE_AI_API_KEY">
                KIE key
                <HelpHint text="Резервный путь для медиа и будущих video-сценариев." />
              </label>
              <input
                id="KIE_AI_API_KEY"
                name="KIE_AI_API_KEY"
                type="password"
                className="form-input"
                defaultValue=""
                placeholder={getSecretPlaceholder(getValue("KIE_AI_API_KEY"))}
              />
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label form-label-inline" htmlFor="HUBRIS_API_KEY">
                Hubris key
                <HelpHint text="Ключ hubris.pw — OpenAI-совместимый агрегатор, дешевле за счёт рублёвого тарифа." />
              </label>
              <input
                id="HUBRIS_API_KEY"
                name="HUBRIS_API_KEY"
                type="password"
                className="form-input"
                defaultValue=""
                placeholder={getSecretPlaceholder(getValue("HUBRIS_API_KEY"))}
              />
            </div>
          </div>

          <div
            style={{
              display: "grid",
              gap: "14px",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            }}
          >
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label form-label-inline" htmlFor="TEXT_MODEL">
                Текст
                <HelpHint text="Модель для контент-планов, постов и перегенерации текста." />
              </label>
              <select key={getValue("TEXT_MODEL", "google/gemini-2.5-flash")} id="TEXT_MODEL" name="TEXT_MODEL" className="form-input" defaultValue={getValue("TEXT_MODEL", "google/gemini-2.5-flash")}>
                {TEXT_MODEL_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label form-label-inline" htmlFor="IMAGE_MODEL">
                Изображение
                <HelpHint text="Модель для генерации и перегенерации иллюстраций." />
              </label>
              <select
                id="IMAGE_MODEL"
                name="IMAGE_MODEL"
                className="form-input"
                key={getValue("IMAGE_MODEL", "google/gemini-3.1-flash-image-preview")}
                defaultValue={getValue("IMAGE_MODEL", "google/gemini-3.1-flash-image-preview")}
              >
                {IMAGE_MODEL_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label form-label-inline" htmlFor="VIDEO_MODEL">
                Видео
                <HelpHint text="Заготовка на будущее: здесь будет модель для видео." />
              </label>
              <select key={getValue("VIDEO_MODEL")} id="VIDEO_MODEL" name="VIDEO_MODEL" className="form-input" defaultValue={getValue("VIDEO_MODEL")}>
                {VIDEO_MODEL_OPTIONS.map((option) => (
                  <option key={option.value || "empty"} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </AutoSaveSettingsForm>
      </section>
    </>
  );
}
