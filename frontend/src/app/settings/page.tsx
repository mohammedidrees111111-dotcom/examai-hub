"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import Footer from "@/components/Footer";

const API_BASE = typeof window !== "undefined"
  ? (window.location.hostname === "localhost" ? "http://127.0.0.1:8000" : "https://examai-hub-api.onrender.com")
  : "https://examai-hub-api.onrender.com";

interface Provider {
  name: string;
  label: string;
  has_key: boolean;
  url: string;
  free_tier: string;
}

export default function SettingsPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [providers, setProviders] = useState<Provider[]>([]);
  const [keys, setKeys] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<Record<string, boolean>>({});
  const [testing, setTesting] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    if (!authLoading && !user) { router.push("/login"); return; }
    if (!user) return;
    fetchProviders();
  }, [user, authLoading, router]);

  const token = typeof window !== "undefined" ? localStorage.getItem("token") : "";

  const fetchProviders = async () => {
    try {
      const res = await fetch(`${API_BASE}/settings/api-keys`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setProviders(data.providers);
      }
    } catch {}
  };

  const saveKey = async (provider: string) => {
    const key = keys[provider];
    if (!key) return;
    setSaving((p) => ({ ...p, [provider]: true }));
    setError(""); setSuccess("");
    try {
      const res = await fetch(`${API_BASE}/settings/api-keys/set`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ provider, key }),
      });
      if (res.ok) {
        setSuccess(`Key saved for ${provider}`);
        setKeys((p) => ({ ...p, [provider]: "" }));
        fetchProviders();
      } else {
        const d = await res.json();
        setError(d.detail || "Failed to save");
      }
    } catch {
      setError("Network error");
    } finally {
      setSaving((p) => ({ ...p, [provider]: false }));
    }
  };

  const deleteKey = async (provider: string) => {
    setSaving((p) => ({ ...p, [provider]: true }));
    try {
      await fetch(`${API_BASE}/settings/api-keys/delete`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ provider, key: "" }),
      });
      fetchProviders();
      setSuccess(`Key deleted for ${provider}`);
    } catch {
      setError("Failed to delete");
    } finally {
      setSaving((p) => ({ ...p, [provider]: false }));
    }
  };

  const testKey = async (provider: string) => {
    setTesting((p) => ({ ...p, [provider]: "Testing..." }));
    try {
      const res = await fetch(`${API_BASE}/settings/api-keys/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ provider }),
      });
      const d = await res.json();
      setTesting((p) => ({ ...p, [provider]: d.status === "valid" ? "Valid!" : "Invalid" }));
    } catch {
      setTesting((p) => ({ ...p, [provider]: "Error" }));
    }
  };

  if (authLoading || !user) return <div className="p-8 text-center">Loading...</div>;

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-2">Settings</h1>
      <p className="text-gray-600 mb-8">Manage your API keys and preferences.</p>

      {error && <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-4 text-sm">{error}</div>}
      {success && <div className="bg-green-50 text-green-600 p-3 rounded-lg mb-4 text-sm">{success}</div>}

      <div className="bg-white rounded-2xl border shadow-sm p-6 mb-8">
        <h2 className="text-xl font-semibold mb-1">AI Providers</h2>
        <p className="text-gray-500 text-sm mb-6">
          Bring your own API keys. You pay the provider directly — we never charge you for API usage.
        </p>

        <div className="space-y-5">
          {providers.map((prov) => (
            <div key={prov.name} className="border border-gray-200 rounded-xl p-4">
              <div className="flex justify-between items-center mb-2">
                <div>
                  <span className="font-semibold text-gray-800">{prov.label}</span>
                  <span className="ml-2 text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded">{prov.free_tier}</span>
                </div>
                <div className="flex gap-2">
                  {prov.has_key && (
                    <>
                      <button
                        onClick={() => testKey(prov.name)}
                        className="text-xs text-indigo-600 hover:underline"
                      >
                        {testing[prov.name] || "Test"}
                      </button>
                      <button
                        onClick={() => deleteKey(prov.name)}
                        disabled={saving[prov.name]}
                        className="text-xs text-red-500 hover:underline"
                      >
                        Remove
                      </button>
                    </>
                  )}
                </div>
              </div>

              <div className="flex gap-2">
                <input
                  type="password"
                  value={keys[prov.name] || ""}
                  onChange={(e) => setKeys((p) => ({ ...p, [prov.name]: e.target.value }))}
                  placeholder={prov.has_key ? "•••••••• (saved)" : `Paste your ${prov.label} API key...`}
                  className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm"
                />
                <button
                  onClick={() => saveKey(prov.name)}
                  disabled={saving[prov.name] || !keys[prov.name]}
                  className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-40"
                >
                  {saving[prov.name] ? "Saving..." : prov.has_key ? "Update" : "Save"}
                </button>
              </div>

              <a href={prov.url} target="_blank" rel="noopener noreferrer" className="text-xs text-gray-400 hover:text-indigo-500 mt-1 inline-block">
                Get a key →
              </a>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 text-sm text-amber-700">
        <p className="font-semibold mb-1">How it works</p>
        <ul className="list-disc pl-4 space-y-1">
          <li>Your API keys are encrypted and stored securely</li>
          <li>You pay the AI provider directly — we take <strong>0% commission</strong></li>
          <li>Each request uses <strong>your key first</strong>, platform key as backup</li>
          <li>Free tiers available on all providers — sign up in 1 minute</li>
        </ul>
      </div>

      <Footer />
    </div>
  );
}
