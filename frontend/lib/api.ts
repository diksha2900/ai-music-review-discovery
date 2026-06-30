import { authHeaders } from "./session";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    credentials: "include",
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || res.statusText);
  }
  return res.json();
}

export type Track = {
  id: string;
  name: string;
  artist: string;
  album_art?: string;
  url?: string;
  why?: string;
};

export async function searchTracks(q: string) {
  return post<{ tracks: Track[] }>("/api/search", { q });
}

export async function findCousins(title: string, artist: string) {
  return post<{ anchor: Track; anchor_tag?: string; tracks: Track[] }>("/api/cousins", {
    title,
    artist,
  });
}

export async function getVibe(text: string, familiarity: number) {
  return post<{ label: string; tracks: Track[] }>("/api/vibe", { text, familiarity });
}

export async function breakLoop(tracks: Track[]) {
  return post<{ label: string; tracks: Track[] }>("/api/break-loop", { tracks });
}

export function loginUrl() {
  return `${API}/auth/login`;
}

export async function authMe() {
  const res = await fetch(`${API}/auth/me`, {
    credentials: "include",
    headers: authHeaders(),
  });
  if (!res.ok) return { logged_in: false };
  return res.json();
}
