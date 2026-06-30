export type TimeBand = {
  clock: string;
  mood: string;
  vibe: string;
  label: string;
};

function formatClock(d: Date): string {
  const h = d.getHours() % 12 || 12;
  const m = d.getMinutes().toString().padStart(2, "0");
  const ap = d.getHours() < 12 ? "am" : "pm";
  return `${h}:${m} ${ap}`;
}

export function getTimeBand(now = new Date()): TimeBand {
  const h = now.getHours();
  let mood: string;
  let vibe: string;
  let label: string;

  if (h >= 5 && h < 9) {
    mood = "Early morning — ease in, calm and spiritual.";
    vibe = "calm, peaceful, spiritual early-morning music";
    label = "morning calm";
  } else if (h >= 9 && h < 12) {
    mood = "Morning — easy, feel-good momentum to start the day.";
    vibe = "easy, uplifting, feel-good morning music";
    label = "feel-good morning";
  } else if (h >= 12 && h < 17) {
    mood = "Afternoon break — want something light and fun?";
    vibe = "light, fun, upbeat afternoon pick-me-up";
    label = "afternoon fun";
  } else if (h >= 17 && h < 21) {
    mood = "Evening — keep the energy up, maybe a drive?";
    vibe = "upbeat, high-energy evening drive music";
    label = "evening energy";
  } else {
    mood = "Night — time to slow down and relax.";
    vibe = "relaxing, mellow, soothing late-night music";
    label = "late-night relax";
  }

  return { clock: formatClock(now).toUpperCase(), mood, vibe, label };
}
