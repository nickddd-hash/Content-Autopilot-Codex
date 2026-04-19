"use client";

import { useState } from "react";
import { postJson } from "@/lib/api";

export default function SettingsForm({ initialSettings }: { initialSettings: Record<string, string> }) {
  const [settings, setSettings] = useState(initialSettings);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState("");

  const handleChange = (key: string, value: string) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    setMessage("");
    try {
      await postJson("/settings/", { settings });
      setMessage("Settings saved successfully!");
    } catch (e) {
      setMessage("Failed to save settings.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="key-value-stack">
      <div className="kv-pair">
        <label className="kv-label">OpenRouter API Key</label>
        <input 
          type="password" 
          value={settings["OPENROUTER_API_KEY"] || ""} 
          onChange={(e) => handleChange("OPENROUTER_API_KEY", e.target.value)}
          className="form-input"
          style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "var(--surface)", border: "1px solid var(--border)", color: "#fff" }}
        />
      </div>
      <div className="kv-pair">
        <label className="kv-label">Apify API Key</label>
        <input 
          type="password" 
          value={settings["APIFY_API_KEY"] || ""} 
          onChange={(e) => handleChange("APIFY_API_KEY", e.target.value)}
          className="form-input"
          style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "var(--surface)", border: "1px solid var(--border)", color: "#fff" }}
        />
      </div>
      <div className="kv-pair">
        <label className="kv-label">Kie.ai API Key</label>
        <input 
          type="password" 
          value={settings["KIE_AI_API_KEY"] || ""} 
          onChange={(e) => handleChange("KIE_AI_API_KEY", e.target.value)}
          className="form-input"
          style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "var(--surface)", border: "1px solid var(--border)", color: "#fff" }}
        />
      </div>
      
      <div style={{ marginTop: "20px", display: "flex", alignItems: "center", gap: "16px" }}>
        <button className="btn btn-primary" onClick={handleSave} disabled={isSaving}>
          {isSaving ? "Saving..." : "Save Settings"}
        </button>
        {message && <span style={{ color: message.includes("success") ? "var(--success)" : "var(--danger)" }}>{message}</span>}
      </div>
    </div>
  );
}
