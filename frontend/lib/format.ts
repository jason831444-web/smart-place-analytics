export function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function score(value: number): string {
  return `${Math.round(value)}`;
}

export function shortDate(value?: string | null): string {
  if (!value) return "No analysis yet";
  return new Intl.DateTimeFormat("en", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }).format(new Date(value));
}

