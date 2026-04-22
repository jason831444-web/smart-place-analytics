import type { HistoryPoint } from "@/types/api";

export type TrendPoint = HistoryPoint & {
  bucket_start: number;
  bucket_end: number;
  label: string;
  occupancy_percent: number;
  average_people_count: number;
  samples: number;
};

export type TrendSeries = {
  points: TrendPoint[];
  grain: "5-minute" | "hourly" | "daily";
};

const hourFormatter = new Intl.DateTimeFormat("en", {
  month: "short",
  day: "numeric",
  hour: "numeric",
  minute: "2-digit"
});

const dayFormatter = new Intl.DateTimeFormat("en", {
  month: "short",
  day: "numeric"
});

function bucketSizeForRange(rangeMs: number): { grain: TrendSeries["grain"]; sizeMs: number } {
  const hour = 60 * 60 * 1000;
  const day = 24 * hour;
  if (rangeMs <= 6 * hour) {
    return { grain: "5-minute", sizeMs: 5 * 60 * 1000 };
  }
  if (rangeMs <= 3 * day) {
    return { grain: "hourly", sizeMs: hour };
  }
  return { grain: "daily", sizeMs: day };
}

function labelForBucket(timestamp: number, grain: TrendSeries["grain"]): string {
  const date = new Date(timestamp);
  if (grain === "daily") {
    return dayFormatter.format(date);
  }
  return hourFormatter.format(date);
}

export function toTrendSeries(data: HistoryPoint[]): TrendSeries {
  const validPoints = [...data]
    .filter((point) => Number.isFinite(point.occupancy_rate) && !Number.isNaN(Date.parse(point.timestamp)))
    .sort((a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp));

  if (!validPoints.length) {
    return { points: [], grain: "hourly" };
  }

  const first = Date.parse(validPoints[0].timestamp);
  const last = Date.parse(validPoints[validPoints.length - 1].timestamp);
  const { grain, sizeMs } = bucketSizeForRange(last - first);
  const buckets = new Map<number, HistoryPoint[]>();

  for (const point of validPoints) {
    const timestamp = Date.parse(point.timestamp);
    const bucketStart = Math.floor(timestamp / sizeMs) * sizeMs;
    const bucket = buckets.get(bucketStart) ?? [];
    bucket.push(point);
    buckets.set(bucketStart, bucket);
  }

  return {
    grain,
    points: [...buckets.entries()]
      .sort(([a], [b]) => a - b)
      .map(([bucketStart, points]) => {
        const occupancyRate = points.reduce((sum, point) => sum + point.occupancy_rate, 0) / points.length;
        const peopleCount = points.reduce((sum, point) => sum + point.people_count, 0) / points.length;
        const latest = points[points.length - 1];

        return {
          ...latest,
          bucket_start: bucketStart,
          bucket_end: bucketStart + sizeMs,
          label: labelForBucket(bucketStart, grain),
          occupancy_percent: Math.round(occupancyRate * 100),
          average_people_count: Math.round(peopleCount * 10) / 10,
          samples: points.length
        };
      })
  };
}
