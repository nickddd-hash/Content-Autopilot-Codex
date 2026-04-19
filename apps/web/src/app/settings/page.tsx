import { fetchJson } from "@/lib/api";
import SettingsForm from "./SettingsForm";

export default async function SettingsPage() {
  const settingsArray = await fetchJson<Array<{key: string, value: string}>>("/settings/", []);
  const initialSettings = settingsArray.reduce((acc, curr) => {
    acc[curr.key] = curr.value || "";
    return acc;
  }, {} as Record<string, string>);

  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">System</p>
          <h1>Global Settings</h1>
          <p className="lead">Manage your API keys and global system configuration.</p>
        </div>
      </header>

      <section className="panel-grid">
        <article className="panel panel-wide">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">Integrations</span>
              <h2 className="panel-title">API Keys</h2>
            </div>
          </div>
          <SettingsForm initialSettings={initialSettings} />
        </article>
      </section>
    </>
  );
}
