export interface User {
  id: number;
  email: string;
  nickname: string;
  avatar: string | null;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Place {
  id: number;
  amap_id: string | null;
  name: string;
  address: string | null;
  city: string | null;
  category: string | null;
  latitude: number;
  longitude: number;
  rating: number | null;
  image_url: string | null;
}

export interface ScheduleItem {
  id: number;
  day: number;
  order_index: number;
  place: Place;
  recommended_time: string | null;
  duration_minutes: number;
  cost_estimate: number;
  transport: string | null;
  reason: string | null;
}

export interface Trip {
  id: number;
  title: string;
  destination: string;
  start_date: string;
  end_date: string;
  travelers: number;
  budget: number;
  pace: string;
  interests: string[];
  travel_style?: string;
  traveler_group?: string;
  traveler_profile: string | null;
  consumption_level: string | null;
  budget_min: number | null;
  budget_max: number | null;
  budget_breakdown: Record<string, number>;
  alternatives: TripAlternative[];
  city_level: string | null;
  city_factor: number | null;
  daily_budget: number | null;
  weather: string | null;
  score_total: number | null;
  score_detail: {
    total?: number;
    budget_match?: number;
    interest_match?: number;
    route_reason?: number;
    quality_match?: number;
  };
  llm_seconds: number | null;
  status: string;
  created_at: string;
  updated_at: string;
  schedules: ScheduleItem[];
}

export interface TripAlternative {
  name: string;
  description: string | null;
  cost_estimate: number;
  day: number | null;
  replaces: string | null;
  reason: string | null;
}

export interface TripCreate {
  destination: string;
  title?: string;
  start_date: string;
  end_date: string;
  travelers: number;
  budget: number;
  pace: string;
  interests: string[];
  travel_style?: string;
  traveler_group?: string;
}

export interface AIGenerateResponse {
  trip: Trip;
  mock: boolean;
  message: string;
}
