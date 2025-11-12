import { useEffect, useMemo, useState } from "react";
import { fetchUploads, uploadImage } from "./api";

const tabs = [
  { id: "dashboard", label: "Dashboard", icon: "🏠" },
  { id: "recent", label: "Recent", icon: "🗂" },
  { id: "chat", label: "Chat", icon: "💬" },
  { id: "profile", label: "Profile", icon: "👤" }
];

const gradient = "from-[#5f5afc] via-[#fc5fae] to-[#ffb86c]";

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [files, setFiles] = useState([]);
  const [previews, setPreviews] = useState([]);
  const [profileUrl, setProfileUrl] = useState("");
  const [profileBio, setProfileBio] = useState("");
  const [conversationText, setConversationText] = useState("");
  const [notes, setNotes] = useState("");
  const [uploads, setUploads] = useState([]);
  const [error, setError] = useState(null);
  const [isSubmitting, setSubmitting] = useState(false);

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    const urls = files.map((file) => URL.createObjectURL(file));
    setPreviews(urls);
    return () => urls.forEach((url) => URL.revokeObjectURL(url));
  }, [files]);

  async function refresh() {
    try {
      const data = await fetchUploads();
      setUploads(data);
    } catch (err) {
      setError(err.message);
    }
  }

  function handleFileChange(event) {
    const selected = Array.from(event.target.files ?? []);
    setFiles(selected.slice(0, 5));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (files.length === 0) {
      setError("Add at least one image");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await uploadImage(files, profileUrl, notes, profileBio, conversationText);
      setFiles([]);
      setProfileUrl("");
      setProfileBio("");
      setConversationText("");
      setNotes("");
      event.target.reset();
      await refresh();
      setActiveTab("recent");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#f8fbff] py-6 px-4 flex justify-center">
      <div className="w-full max-w-sm rounded-3xl shadow-2xl flex flex-col min-h-[720px] overflow-hidden border border-white/20 bg-gradient-to-br from-[#1f1fff] via-[#7b2ff7] to-[#ff6cab] text-white">
        <div className="flex-1 overflow-y-auto">
          {activeTab === "dashboard" && (
            <DashboardView
              previews={previews}
              filesCount={files.length}
              setFiles={setFiles}
              profileUrl={profileUrl}
              setProfileUrl={setProfileUrl}
              profileBio={profileBio}
              setProfileBio={setProfileBio}
              conversationText={conversationText}
              setConversationText={setConversationText}
              notes={notes}
              setNotes={setNotes}
              handleFileChange={handleFileChange}
              handleSubmit={handleSubmit}
              isSubmitting={isSubmitting}
              error={error}
            />
          )}
          {activeTab === "recent" && <RecentView uploads={uploads} />}
          {activeTab === "chat" && <PlaceholderView title="Chat" message="Secure messaging coming soon." />}
          {activeTab === "profile" && <PlaceholderView title="Profile" message="Magic-link login + billing will live here." />}
        </div>
        <BottomNav activeTab={activeTab} setActiveTab={setActiveTab} />
      </div>
    </div>
  );
}

function DashboardView({
  previews,
  filesCount,
  profileUrl,
  setProfileUrl,
  profileBio,
  setProfileBio,
  conversationText,
  setConversationText,
  notes,
  setNotes,
  handleFileChange,
  handleSubmit,
  isSubmitting,
  error
}) {
  return (
    <div className="p-5 space-y-5">
      <div className="rounded-3xl bg-white/10 text-white p-6 shadow-xl">
        <p className="uppercase text-xs tracking-[0.4em]">Catfish</p>
        <h1 className="text-3xl font-semibold mt-3">Fake or not?</h1>
        <p className="text-sm mt-2 text-white/90">Run a deep authenticity check without leaving your browser.</p>
      </div>

      <form className="space-y-4" onSubmit={handleSubmit}>
        <div className="rounded-3xl bg-white/5 border border-white/20 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-400">Evidence</p>
          <label className="mt-3 block rounded-2xl border border-dashed border-slate-700 bg-slate-900/60 p-4 text-center cursor-pointer">
            <input type="file" multiple accept="image/*" className="hidden" onChange={handleFileChange} />
            <p className="text-sm text-slate-200">Tap to select up to 5 images</p>
            <p className="text-xs text-slate-500">{filesCount === 0 ? "No files" : `${filesCount} selected`}</p>
          </label>
          {previews.length > 0 && (
            <div className="mt-3 grid grid-cols-3 gap-2">
              {previews.map((src, idx) => (
                <img key={src} src={src} alt={`preview-${idx}`} className="h-20 w-full rounded-xl object-cover" />
              ))}
            </div>
          )}
        </div>

        <div className="rounded-3xl bg-white/5 border border-white/20 p-4 space-y-3">
          <Field label="Profile link">
            <input
              type="url"
              value={profileUrl}
              onChange={(e) => setProfileUrl(e.target.value)}
              placeholder="https://tinder.com/@username"
              className="w-full bg-transparent focus:outline-none"
            />
          </Field>
          <Field label="Profile bio">
            <textarea
              value={profileBio}
              onChange={(e) => setProfileBio(e.target.value)}
              rows={3}
              placeholder="Paste the bio or summary"
              className="w-full bg-transparent focus:outline-none resize-none"
            />
          </Field>
          <Field label="Conversation text">
            <textarea
              value={conversationText}
              onChange={(e) => setConversationText(e.target.value)}
              rows={4}
              placeholder="Paste key parts of your chat"
              className="w-full bg-transparent focus:outline-none resize-none"
            />
          </Field>
          <Field label="Notes / red flags">
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              placeholder="Anything else we should know"
              className="w-full bg-transparent focus:outline-none resize-none"
            />
          </Field>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className={`w-full rounded-2xl py-3 font-semibold text-slate-900 bg-gradient-to-r ${gradient} disabled:opacity-60`}
        >
          {isSubmitting ? "Generating..." : "Generate prediction"}
        </button>
        {error && <p className="text-xs text-rose-300">{error}</p>}
      </form>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label className="block rounded-2xl border border-slate-800 bg-slate-900/50 px-3 py-2 text-sm text-slate-200">
      <span className="block text-[11px] uppercase tracking-wide text-slate-500 mb-1">{label}</span>
      {children}
    </label>
  );
}

function RecentView({ uploads }) {
  return (
    <div className="p-5 space-y-4">
      <h2 className="text-lg font-semibold text-slate-100">Recent checks</h2>
      {uploads.length === 0 && <p className="text-sm text-slate-500">No reports yet.</p>}
      <div className="space-y-3">
        {uploads.map((upload) => (
          <article key={upload.id} className="rounded-2xl bg-slate-950/70 border border-slate-800 p-4 space-y-3">
            <div className="flex justify-between items-center">
              <div>
                <p className="font-semibold text-slate-100 truncate max-w-[180px]">{upload.filename}</p>
                <p className="text-xs text-slate-500">{new Date(upload.created_at).toLocaleString()}</p>
              </div>
              <div className="text-right">
                <p className="text-[11px] uppercase text-slate-500">Risk</p>
                <p className="text-2xl font-bold text-white">{upload.risk_score ?? 0}</p>
              </div>
            </div>
            {upload.signals?.length ? (
              <ul className="text-xs text-slate-400 space-y-1">
                {upload.signals.slice(0, 3).map((signal, idx) => (
                  <li key={`${signal.type}-${idx}`}>
                    <span className="text-slate-200">{signal.type}</span> · {signal.severity}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-slate-500">No strong signals.</p>
            )}
            {upload.advice?.length && (
              <div className="text-xs text-slate-500">
                <p className="text-[11px] uppercase tracking-wide text-slate-500 mb-1">Advice</p>
                <ul className="list-disc pl-4 space-y-1">
                  {upload.advice.slice(0, 2).map((tip) => (
                    <li key={tip}>{tip}</li>
                  ))}
                </ul>
              </div>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}

function PlaceholderView({ title, message }) {
  return (
    <div className="p-5 h-full flex flex-col items-center justify-center text-center space-y-2 text-slate-400">
      <div className="text-4xl">✨</div>
      <h2 className="text-lg font-semibold text-slate-100">{title}</h2>
      <p className="text-sm text-slate-400">{message}</p>
    </div>
  );
}

function BottomNav({ activeTab, setActiveTab }) {
  return (
    <nav className="grid grid-cols-4 border-t border-slate-800 bg-slate-950/80">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => setActiveTab(tab.id)}
          className={`py-3 text-sm flex flex-col items-center ${activeTab === tab.id ? "text-white" : "text-slate-500"}`}
        >
          <span className="text-lg">{tab.icon}</span>
          <span className="text-[11px]">{tab.label}</span>
        </button>
      ))}
    </nav>
  );
}
