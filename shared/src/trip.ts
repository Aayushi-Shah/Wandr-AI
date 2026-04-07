// Travel domain types — TypeScript equivalents of backend/app/agents/models.py
// Keep in sync with the Python models.

export interface FlightOption {
  airline: string
  flight_number: string
  origin: string        // IATA code, e.g. "JFK"
  destination: string   // IATA code, e.g. "NRT"
  departure_dt: string  // ISO datetime
  arrival_dt: string    // ISO datetime
  price: number
  currency: string
  stops: number
  duration_minutes: number
}

export interface HotelOption {
  name: string
  address: string
  neighborhood: string
  price_per_night: number
  currency: string
  rating: number        // 0.0–5.0
  amenities: string[]
}

export interface Activity {
  name: string
  description: string
  location: string
  duration_minutes: number
  estimated_cost: number
  currency: string
  category: string
}

export interface DayPlan {
  date: string          // ISO date YYYY-MM-DD
  activities: Activity[]
}

export interface BudgetSummary {
  flight_total: number
  hotel_total: number
  activities_total: number
  grand_total: number
  currency: string
  over_budget: boolean
  remaining: number
}

export interface TripPlan {
  trip_id: string
  destination: string
  start_date: string
  end_date: string
  flights: FlightOption[]
  hotels: HotelOption[]
  days: DayPlan[]
  budget: BudgetSummary
}
