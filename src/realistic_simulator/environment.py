"""
Wireless Environment Model for the Client-Aware WiFi RRM Simulator.

Models the physical layout of an indoor wireless environment including:
- Room dimensions (2D coordinate space)
- Wall segments with material-specific attenuation
- Obstacle regions
- Interference source placements
- AP and client coordinate positions

The environment provides geometric queries (e.g., ray-casting to determine
which walls lie between two points) consumed by the Propagation and
Interference engines.

Sources:
    - ITU-R P.1238-10 (Indoor propagation modeling)
    - Rappaport, "Wireless Communications", Chapter 4
"""

import logging
import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from src.realistic_simulator.constants import (
    WallMaterial,
    WALL_ATTENUATION_DB,
    EnvironmentType,
    InterferenceType,
)

logger = logging.getLogger("RRM.Environment")


# ─────────────────────────────────────────────────────────────────────────────
# Data Structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Point:
    """A 2D coordinate in meters."""
    x: float
    y: float

    def distance_to(self, other: "Point") -> float:
        """Euclidean distance between two points.
        Formula: d = √((x₂ − x₁)² + (y₂ − y₁)²)
        """
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


@dataclass
class Wall:
    """A wall segment defined by two endpoints, a material type, and attenuation.

    The attenuation is looked up from the material's typical value in
    constants.WALL_ATTENUATION_DB unless explicitly overridden.
    """
    start: Point
    end: Point
    material: WallMaterial
    attenuation_db: Optional[float] = None

    def __post_init__(self) -> None:
        if self.attenuation_db is None:
            _min, typical, _max = WALL_ATTENUATION_DB[self.material]
            self.attenuation_db = typical

    def length(self) -> float:
        """Length of the wall segment in meters."""
        return self.start.distance_to(self.end)


@dataclass
class Obstacle:
    """A rectangular obstacle (e.g., filing cabinet, bookshelf) with a material type."""
    center: Point
    width: float   # meters (along x-axis)
    height: float  # meters (along y-axis)
    material: WallMaterial

    @property
    def attenuation_db(self) -> float:
        """Typical attenuation for this obstacle's material."""
        _min, typical, _max = WALL_ATTENUATION_DB[self.material]
        return typical

    def corners(self) -> Tuple[Point, Point, Point, Point]:
        """Returns four corner points (top-left, top-right, bottom-right, bottom-left)."""
        hw = self.width / 2.0
        hh = self.height / 2.0
        return (
            Point(self.center.x - hw, self.center.y + hh),  # top-left
            Point(self.center.x + hw, self.center.y + hh),  # top-right
            Point(self.center.x + hw, self.center.y - hh),  # bottom-right
            Point(self.center.x - hw, self.center.y - hh),  # bottom-left
        )

    def edges(self) -> List[Tuple[Point, Point]]:
        """Returns the four edges of the obstacle as (start, end) point pairs."""
        tl, tr, br, bl = self.corners()
        return [(tl, tr), (tr, br), (br, bl), (bl, tl)]


@dataclass
class InterferenceSource:
    """An external interference source with physical RF characteristics.

    Each source has a location, frequency/bandwidth, duty cycle, and transmit
    power. The InterferenceEngine uses these parameters to compute per-type
    interference contributions.
    """
    source_id: str
    interference_type: InterferenceType
    location: Point
    frequency_mhz: float
    bandwidth_mhz: float
    tx_power_dbm: float
    duty_cycle: float           # 0.0 to 1.0 (fraction of time active)
    active: bool = True
    active_start_s: float = 0.0   # Simulation time when source activates
    active_end_s: float = float("inf")  # Simulation time when source deactivates


@dataclass
class WirelessEnvironment:
    """Models the physical indoor wireless environment.

    Provides geometric queries consumed by the Propagation, Channel, and
    Interference engines. All coordinates are in meters.

    Attributes:
        width_m: Room width (x-axis extent).
        height_m: Room height (y-axis extent).
        environment_type: Classification affecting path loss exponent and fading.
        walls: List of wall segments.
        obstacles: List of rectangular obstacles.
        interference_sources: List of external interference emitters.
    """
    width_m: float = 50.0
    height_m: float = 50.0
    environment_type: EnvironmentType = EnvironmentType.INDOOR_OFFICE
    walls: List[Wall] = field(default_factory=list)
    obstacles: List[Obstacle] = field(default_factory=list)
    interference_sources: List[InterferenceSource] = field(default_factory=list)

    def walls_between(self, point_a: Point, point_b: Point) -> List[Wall]:
        """Determines which walls are intersected by the line segment from
        point_a to point_b using a ray-casting (line-segment intersection)
        algorithm.

        Args:
            point_a: Start point (e.g., AP location).
            point_b: End point (e.g., client location).

        Returns:
            List of Wall objects whose segments are crossed by the direct
            path between the two points.

        Algorithm:
            For each wall, test whether the line segment (point_a → point_b)
            intersects the wall segment (wall.start → wall.end) using the
            parametric intersection method.
        """
        intersected: List[Wall] = []

        for wall in self.walls:
            if _segments_intersect(
                point_a.x, point_a.y, point_b.x, point_b.y,
                wall.start.x, wall.start.y, wall.end.x, wall.end.y,
            ):
                intersected.append(wall)

        return intersected

    def obstacle_attenuation(self, point_a: Point, point_b: Point) -> float:
        """Computes total attenuation from obstacles intersected by the
        direct path between two points.

        Args:
            point_a: Start point.
            point_b: End point.

        Returns:
            Total obstacle attenuation in dB.
        """
        total_db = 0.0
        for obstacle in self.obstacles:
            for edge_start, edge_end in obstacle.edges():
                if _segments_intersect(
                    point_a.x, point_a.y, point_b.x, point_b.y,
                    edge_start.x, edge_start.y, edge_end.x, edge_end.y,
                ):
                    total_db += obstacle.attenuation_db
                    break  # Count each obstacle only once
        return total_db

    def total_wall_attenuation(self, point_a: Point, point_b: Point) -> float:
        """Computes total wall attenuation along the direct path between
        two points. Includes both wall segments and obstacle edges.

        Formula: L_walls = Σ Attenuation(wall_i) + Σ Attenuation(obstacle_j)

        Args:
            point_a: Start point (typically AP).
            point_b: End point (typically client).

        Returns:
            Total attenuation in dB from all intersected walls and obstacles.
        """
        wall_loss = sum(
            w.attenuation_db for w in self.walls_between(point_a, point_b)
        )
        obstacle_loss = self.obstacle_attenuation(point_a, point_b)
        total = wall_loss + obstacle_loss
        if total > 0:
            logger.debug(
                "Path (%.1f,%.1f)→(%.1f,%.1f): wall_loss=%.1f dB, "
                "obstacle_loss=%.1f dB, total=%.1f dB",
                point_a.x, point_a.y, point_b.x, point_b.y,
                wall_loss, obstacle_loss, total,
            )
        return total

    def active_interference_sources(
        self, sim_time_s: float = 0.0
    ) -> List[InterferenceSource]:
        """Returns interference sources that are currently active at the
        given simulation timestamp.

        Args:
            sim_time_s: Current simulation time in seconds.

        Returns:
            List of active InterferenceSource objects.
        """
        return [
            src for src in self.interference_sources
            if src.active
            and src.active_start_s <= sim_time_s <= src.active_end_s
        ]

    def clamp_position(self, point: Point) -> Point:
        """Clamps a point to stay within the environment boundaries.

        Args:
            point: The point to clamp.

        Returns:
            New Point with coordinates clamped to [0, width] × [0, height].
        """
        return Point(
            x=max(0.0, min(self.width_m, point.x)),
            y=max(0.0, min(self.height_m, point.y)),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Geometry Utilities
# ─────────────────────────────────────────────────────────────────────────────

def _segments_intersect(
    ax1: float, ay1: float, ax2: float, ay2: float,
    bx1: float, by1: float, bx2: float, by2: float,
) -> bool:
    """Tests whether two line segments intersect using the parametric method.

    Segment A: (ax1, ay1) → (ax2, ay2)
    Segment B: (bx1, by1) → (bx2, by2)

    Uses the parametric form:
        P = A1 + t·(A2 − A1)
        Q = B1 + u·(B2 − B1)

    Segments intersect if both t ∈ (0, 1) and u ∈ (0, 1).
    We use open intervals to avoid counting shared endpoints.

    Returns:
        True if the segments cross each other.
    """
    dx_a = ax2 - ax1
    dy_a = ay2 - ay1
    dx_b = bx2 - bx1
    dy_b = by2 - by1

    denom = dx_a * dy_b - dy_a * dx_b

    if abs(denom) < 1e-12:
        # Parallel or collinear segments — treat as non-intersecting
        return False

    dx_ab = bx1 - ax1
    dy_ab = by1 - ay1

    t = (dx_ab * dy_b - dy_ab * dx_b) / denom
    u = (dx_ab * dy_a - dy_ab * dx_a) / denom

    # Open interval (0, 1) to avoid counting shared endpoints
    return 0.0 < t < 1.0 and 0.0 < u < 1.0


def create_rectangular_room(
    width_m: float,
    height_m: float,
    wall_material: WallMaterial = WallMaterial.DRYWALL,
    environment_type: EnvironmentType = EnvironmentType.INDOOR_OFFICE,
) -> WirelessEnvironment:
    """Factory function to create a simple rectangular room with four walls.

    Args:
        width_m: Room width in meters.
        height_m: Room height in meters.
        wall_material: Material for all four walls.
        environment_type: Environment classification.

    Returns:
        A WirelessEnvironment with four perimeter walls.
    """
    walls = [
        Wall(Point(0, 0), Point(width_m, 0), wall_material),          # bottom
        Wall(Point(width_m, 0), Point(width_m, height_m), wall_material),  # right
        Wall(Point(width_m, height_m), Point(0, height_m), wall_material), # top
        Wall(Point(0, height_m), Point(0, 0), wall_material),              # left
    ]
    env = WirelessEnvironment(
        width_m=width_m,
        height_m=height_m,
        environment_type=environment_type,
        walls=walls,
    )
    logger.info(
        "Created rectangular room: %.0f×%.0f m, material=%s, type=%s",
        width_m, height_m, wall_material.value, environment_type.value,
    )
    return env


def create_office_environment(
    width_m: float = 40.0,
    height_m: float = 30.0,
) -> WirelessEnvironment:
    """Factory function to create a typical office layout with interior walls.

    Creates a room with:
    - Perimeter walls (concrete)
    - Two interior partition walls (drywall) dividing the space
    - A glass conference room wall

    Args:
        width_m: Office width in meters.
        height_m: Office height in meters.

    Returns:
        A WirelessEnvironment modelling a simple office floor plan.
    """
    env = create_rectangular_room(
        width_m, height_m,
        wall_material=WallMaterial.CONCRETE,
        environment_type=EnvironmentType.INDOOR_OFFICE,
    )

    # Add interior partition walls (drywall)
    interior_walls = [
        # Horizontal partition at 1/3 height
        Wall(Point(0, height_m / 3), Point(width_m * 0.7, height_m / 3),
             WallMaterial.DRYWALL),
        # Horizontal partition at 2/3 height
        Wall(Point(width_m * 0.3, 2 * height_m / 3),
             Point(width_m, 2 * height_m / 3), WallMaterial.DRYWALL),
        # Conference room glass wall
        Wall(Point(width_m * 0.7, height_m / 3),
             Point(width_m * 0.7, 2 * height_m / 3), WallMaterial.GLASS),
    ]
    env.walls.extend(interior_walls)

    logger.info(
        "Created office environment: %.0f×%.0f m with %d walls",
        width_m, height_m, len(env.walls),
    )
    return env
