"""Agent data contracts — AgentTask, AgentResult, AgentStatus + travel domain models.

Imported by BaseAgent and all specialist agents. The TypeScript equivalents
live in shared/src/agents.ts (agent contracts) and shared/src/trip.ts (travel types).
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


class AgentTask(BaseModel):
    """Input contract for every specialist agent.

    The Orchestrator populates this from its Claude decomposition.
    ``context`` carries results from upstream agents (used by BudgetAgent fan-in).
    """

    task_id: str = Field(..., description="Shared ID for the entire trip-planning request")
    agent_name: str = Field(..., description="Which agent should handle this task")
    destination: str
    start_date: str = Field(..., description="ISO date string YYYY-MM-DD")
    end_date: str = Field(..., description="ISO date string YYYY-MM-DD")
    budget: float = Field(..., gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    raw_request: str = Field(
        default="", description="Original user prompt, for Orchestrator context"
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Results from upstream agents (e.g. flight cost passed to BudgetAgent)",
    )


class AgentResult(BaseModel):
    """Output contract for every specialist agent."""

    task_id: str
    agent_name: str
    status: AgentStatus
    summary: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    duration_ms: float | None = None


# ── Travel domain models ───────────────────────────────────────────────────────
# TS equivalents in shared/src/trip.ts


class FlightOption(BaseModel):
    airline: str
    flight_number: str
    origin: str           # IATA code, e.g. "JFK"
    destination: str      # IATA code, e.g. "NRT"
    departure_dt: str     # ISO datetime string
    arrival_dt: str       # ISO datetime string
    price: float = Field(..., gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    stops: int = Field(default=0, ge=0)
    duration_minutes: int = Field(..., gt=0)


class HotelOption(BaseModel):
    name: str
    address: str
    neighborhood: str
    price_per_night: float = Field(..., gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    rating: float = Field(default=0.0, ge=0.0, le=5.0)
    amenities: list[str] = Field(default_factory=list)


class Activity(BaseModel):
    name: str
    description: str
    location: str
    duration_minutes: int = Field(..., gt=0)
    estimated_cost: float = Field(default=0.0, ge=0.0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    category: str  # "museum" | "food" | "outdoor" | "shopping" | "transport" | etc.


class DayPlan(BaseModel):
    date: str              # ISO date string YYYY-MM-DD
    activities: list[Activity] = Field(default_factory=list)


class BudgetSummary(BaseModel):
    flight_total: float = Field(default=0.0, ge=0.0)
    hotel_total: float = Field(default=0.0, ge=0.0)
    activities_total: float = Field(default=0.0, ge=0.0)
    grand_total: float = Field(default=0.0, ge=0.0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    over_budget: bool = False
    remaining: float = 0.0
