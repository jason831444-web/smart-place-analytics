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