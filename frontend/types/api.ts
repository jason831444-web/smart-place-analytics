export type CongestionLevel = "Low" | "Medium" | "High";

export type Facility = {
  id: number;
  name: string;
  type: string;
  location: string;
  description?: string | null;
  total_seats: number;
  seat_usage_factor: number;
  image_url?: string | null;
  created_at: string;
  updated_at: string;
};

export type FacilityStatus = {
  facility: Facility;
  people_count: number;
  occupied_seats: number;
  available_seats: number;
  occupancy_rate: number;
  congestion_level: CongestionLevel;
  congestion_score: number;
  latest_analysis_id?: number | null;
  latest_analysis_at?: string | null;
};

export type HistoryPoint = {
  timestamp: string;
  people_count: number;
  occupied_seats: number;
  available_seats: number;
  occupancy_rate: number;
  congestion_score: number;
  congestion_level: CongestionLevel;
};

export type OccupancyLog = HistoryPoint & {
  id: number;
  facility_id: number;
  analysis_id?: number | null;
  confidence?: number | null;
  source_type: string;
  image_path?: string | null;
  annotated_image_path?: string | null;
  image_url?: string | null;
  annotated_image_url?: string | null;
  created_at: string;
};

export type LatestStatus = {
  facility_id: number;
  timestamp?: string | null;
  people_count: number;
  occupied_seats: number;
  available_seats: number;
  occupancy_rate: number;
  congestion_score: number;
  congestion_level: CongestionLevel;
  confidence?: number | null;
  source_type?: string | null;
  analysis_id?: number | null;
  image_url?: string | null;
  annotated_image_url?: string | null;
};

export type FacilitySummary = {
  facility_id: number;
  latest_occupancy_rate: number;
  average_occupancy_rate: number;
  peak_occupancy_rate: number;
  high_congestion_events: number;
  most_recent_timestamp?: string | null;
  latest_people_count: number;
  samples: number;
};

export type Analysis = {
  id: number;
  facility_id: number;
  upload_id: number;
  people_count: number;
  occupied_seats: number;
  available_seats: number;
  occupancy_rate: number;
  congestion_level: CongestionLevel;
  congestion_score: number;
  annotated_image_path?: string | null;
  created_at: string;
  image_url?: string | null;
  annotated_image_url?: string | null;
};

export type LiveAnalysis = {
  facility_id: number;
  people_count: number;
  occupied_seats: number;
  available_seats: number;
  occupancy_rate: number;
  congestion_level: CongestionLevel;
  congestion_score: number;
  detector_backend: string;
  detector_model: string;
  persisted: boolean;
  persistence_requested: boolean;
  next_persist_after_seconds: number;
  analysis_id?: number | null;
  image_url?: string | null;
  annotated_image_url?: string | null;
  fallback_reason?: string | null;
  created_at: string;
};

export type SensorLog = {
  id: number;
  facility_id: number;
  timestamp: string;
  temperature: number;
  humidity: number;
  power_kw: number;
  door_count: number;
  noise_level: number;
  source_type: string;
  created_at: string;
};

export type SensorSummary = {
  facility_id: number;
  latest_temperature?: number | null;
  latest_humidity?: number | null;
  latest_power_kw?: number | null;
  latest_door_count?: number | null;
  latest_noise_level?: number | null;
  average_temperature: number;
  average_humidity: number;
  average_power_kw: number;
  total_door_count: number;
  average_noise_level: number;
  most_recent_timestamp?: string | null;
  samples: number;
};

export type Forecast = {
  facility_id: number;
  window_minutes: number;
  predicted_occupancy_rate: number;
  predicted_congestion_level: CongestionLevel;
  confidence: number;
  method: string;
  explanation: string;
  generated_at: string;
};

export type Recommendation = {
  recommendation_type: string;
  severity: "low" | "medium" | "high";
  title: string;
  message: string;
  evidence: string[];
  created_at: string;
};

export type FacilityMetric = {
  facility_id: number;
  facility_name: string;
  average_occupancy_rate: number;
  average_congestion_score: number;
  latest_congestion_level?: CongestionLevel | null;
  analyses_count: number;
};

export type PeakHourMetric = {
  hour: number;
  average_occupancy_rate: number;
  average_congestion_score: number;
  samples: number;
};

export type RecentActivity = {
  analysis_id: number;
  facility_id: number;
  facility_name: string;
  people_count: number;
  occupancy_rate: number;
  congestion_level: CongestionLevel;
  created_at: string;
};

export type AnalyticsOverview = {
  facilities_count: number;
  analyses_count: number;
  uploads_count: number;
  average_occupancy_rate: number;
  average_congestion_score: number;
  busiest_facilities: FacilityMetric[];
  peak_hours: PeakHourMetric[];
  recent_activity: RecentActivity[];
};
