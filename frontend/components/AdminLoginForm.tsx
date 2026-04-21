"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { api, setToken } from "@/lib/api";

export function AdminLoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("admin12345");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await api.login(email, password);
      setToken(response.access_token);
      router.push("/admin");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={submit} className="mx-auto max-w-md rounded-lg border border-line bg-white p-6 shadow-soft">
      <h1 className="text-2xl font-semibold text-ink">Admin Login</h1>
      <div className="mt-6 space-y-4">
        <label className="block text-sm font-medium text-slate-700">
          Email
          <input className="focus-ring mt-2 w-full rounded-lg border border-line px-3 py-2" value={email} onChange={(event) => setEmail(event.target.value)} />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Password
          <input className="focus-ring mt-2 w-full rounded-lg border border-line px-3 py-2" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
        </label>
      </div>
      {error ? <p className="mt-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}
      <button className="focus-ring mt-6 w-full rounded-lg bg-ink px-4 py-3 text-sm font-semibold text-white" disabled={loading}>
        {loading ? "Signing in..." : "Sign in"}
      </button>
    </form>
  );
}

