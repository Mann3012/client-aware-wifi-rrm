"""
Quality of Experience (QoE) Engine for the Client-Aware WiFi RRM Simulator.

Maps raw network metrics (Throughput, Latency, Jitter, Loss) into a human-
understandable 0-100 score based on specific application requirements.

Sources:
    - Arista Networks client-centric health scoring philosophy.
    - ITU-T G.107 (E-model for voice quality).
"""

from src.realistic_simulator.constants import ApplicationType, QOE_APP_WEIGHTS
from src.realistic_simulator.models import QoE


class QoEEngine:
    """Computes Application-Specific Quality of Experience."""

    def __init__(self):
        # Thresholds defining discrete QoE categories
        self.excellent_threshold = 85.0
        self.good_threshold = 65.0
        self.fair_threshold = 40.0

    def normalize_metric(self, value: float, best: float, worst: float) -> float:
        """
        Normalizes a metric to a 0.0 - 1.0 scale.
        
        Args:
            value: The measured value.
            best: The value considered perfect (yields 1.0).
            worst: The value considered completely failed (yields 0.0).
            
        Returns:
            Score from 0.0 to 1.0.
        """
        if best < worst:
            # E.g., Latency: lower is better
            if value <= best: return 1.0
            if value >= worst: return 0.0
            return 1.0 - ((value - best) / (worst - best))
        else:
            # E.g., Throughput: higher is better
            if value >= best: return 1.0
            if value <= worst: return 0.0
            return (value - worst) / (best - worst)

    def get_category(self, score: float) -> str:
        """Maps a 0-100 score to a category string."""
        if score >= self.excellent_threshold: return "Excellent"
        if score >= self.good_threshold: return "Good"
        if score >= self.fair_threshold: return "Fair"
        return "Poor"

    def compute_qoe(
        self,
        app_type_str: str,
        throughput_mbps: float,
        demand_mbps: float,
        latency_ms: float,
        jitter_ms: float,
        packet_loss_rate: float,
        retry_rate: float = 0.0
    ) -> QoE:
        """
        Computes the final QoE score using application-specific weights.

        Args:
            app_type_str: String matching ApplicationType enum.
            throughput_mbps: Actual achieved throughput.
            demand_mbps: Requested application throughput.
            latency_ms: End-to-end latency.
            jitter_ms: End-to-end jitter.
            packet_loss_rate: Packet loss (0.0 to 1.0).
            retry_rate: MAC layer retry rate (0.0 to 1.0).

        Returns:
            QoE object with score and category.
        """
        try:
            app_type = ApplicationType(app_type_str.lower())
        except ValueError:
            app_type = ApplicationType.BROWSING

        # Get specific weights for this application
        w_lat, w_tpt, w_loss, w_jit, w_retry = QOE_APP_WEIGHTS[app_type]

        # 1. Normalize Throughput (Demand satisfaction)
        score_tpt = self.normalize_metric(throughput_mbps, best=demand_mbps, worst=0.0)

        # 2. Normalize Latency
        if app_type == ApplicationType.VOICE or app_type == ApplicationType.GAMING:
            score_lat = self.normalize_metric(latency_ms, best=20.0, worst=150.0)
        elif app_type == ApplicationType.VIDEO:
            score_lat = self.normalize_metric(latency_ms, best=50.0, worst=300.0)
        else:
            score_lat = self.normalize_metric(latency_ms, best=100.0, worst=1000.0)

        # 3. Normalize Jitter
        if app_type == ApplicationType.VOICE:
            score_jit = self.normalize_metric(jitter_ms, best=5.0, worst=30.0)
        else:
            score_jit = self.normalize_metric(jitter_ms, best=10.0, worst=100.0)

        # 4. Normalize Packet Loss
        if app_type == ApplicationType.BULK_DOWNLOAD:
            # TCP handles loss via retransmission, less strict requirement
            score_loss = self.normalize_metric(packet_loss_rate, best=0.001, worst=0.10)
        else:
            # Real-time traffic suffers heavily from loss
            score_loss = self.normalize_metric(packet_loss_rate, best=0.001, worst=0.03)

        # 5. Normalize Retry Rate
        score_retry = self.normalize_metric(retry_rate, best=0.05, worst=0.50)

        # 6. Weighted Sum
        final_score = (
            (w_tpt * score_tpt) +
            (w_lat * score_lat) +
            (w_jit * score_jit) +
            (w_loss * score_loss) +
            (w_retry * score_retry)
        )
        
        # Scale to 0-100
        final_score_100 = max(0.0, min(100.0, final_score * 100.0))
        
        return QoE(
            score=final_score_100,
            category=self.get_category(final_score_100)
        )
