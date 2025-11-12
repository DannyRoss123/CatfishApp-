const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

export async function fetchUploads() {
  const res = await fetch(`${API_BASE}/api/uploads`);
  if (!res.ok) throw new Error("Failed to load uploads");
  return res.json();
}

export async function uploadImage(files, profileUrl, notes, profileBio, conversationText) {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  if (profileUrl) formData.append("profile_url", profileUrl);
  if (notes) formData.append("notes", notes);
  if (profileBio) formData.append("profile_bio", profileBio);
  if (conversationText) formData.append("conversation_text", conversationText);
  const res = await fetch(`${API_BASE}/api/uploads`, {
    method: "POST",
    body: formData
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Upload failed");
  }
  return res.json();
}
