"""
Response schemas for synth group statistics endpoint.

Provides pre-computed histogram data for demographics and sensitivities
to power the group detail page charts.

References:
    - Router: synth_lab.api.routers.synth_groups
    - Service: synth_lab.services.synth_group_service
"""

from pydantic import BaseModel, Field


class HistogramBucket(BaseModel):
    """A single bucket in a histogram."""

    label: str = Field(description="Bucket label (e.g., '15-29', '0.0-0.2').")
    count: int = Field(description="Number of items in this bucket.")
    percentage: float = Field(description="Percentage of total (0-100).")


class HistogramData(BaseModel):
    """Histogram with buckets and summary statistics."""

    buckets: list[HistogramBucket] = Field(default_factory=list)
    mean: float = Field(default=0.0, description="Mean value.")
    std_dev: float = Field(default=0.0, description="Standard deviation.")


class CategoryCount(BaseModel):
    """A category with count and percentage for pie charts."""

    label: str = Field(description="Category label.")
    count: int = Field(description="Number of items.")
    percentage: float = Field(description="Percentage of total (0-100).")


class DisabilityStats(BaseModel):
    """PcD vs non-PcD breakdown."""

    pcd_count: int = Field(default=0)
    pcd_percentage: float = Field(default=0.0)
    non_pcd_count: int = Field(default=0)
    non_pcd_percentage: float = Field(default=0.0)


class DemographicStats(BaseModel):
    """Aggregate demographic statistics for a synth group."""

    age: HistogramData = Field(default_factory=HistogramData)
    income: HistogramData = Field(default_factory=HistogramData)
    education: list[CategoryCount] = Field(default_factory=list)
    family_composition: list[CategoryCount] = Field(default_factory=list)
    disability: DisabilityStats = Field(default_factory=DisabilityStats)


class SensitivityStats(BaseModel):
    """Aggregate sensitivity distributions for a synth group."""

    distributions: dict[str, HistogramData] = Field(
        default_factory=dict,
        description="Sensitivity name -> histogram data.",
    )


class SynthGroupStatistics(BaseModel):
    """Full statistics response for a synth group."""

    group_id: str = Field(description="Synth group ID.")
    total_synths: int = Field(default=0, description="Total synths in group.")
    demographics: DemographicStats = Field(default_factory=DemographicStats)
    sensitivities: SensitivityStats = Field(default_factory=SensitivityStats)
