from typing import Optional

from opentelemetry.metrics import Meter, MeterProvider
from opentelemetry.trace import TracerProvider

from faststream.opentelemetry.middleware import TelemetryMiddleware
from faststream.rabbit.opentelemetry.provider import RabbitTelemetrySettingsProvider


class RabbitTelemetryMiddleware(TelemetryMiddleware):
    def __init__(
        self,
        *,
        tracer_provider: Optional[TracerProvider] = None,
        meter_provider: Optional[MeterProvider] = None,
        meter: Optional[Meter] = None,
    ) -> None:
        super().__init__(
            settings_provider_factory=lambda _: RabbitTelemetrySettingsProvider(),
            tracer_provider=tracer_provider,
            meter_provider=meter_provider,
            meter=meter,
            include_messages_counters=False,
        )
