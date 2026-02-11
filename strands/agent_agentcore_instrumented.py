#!/usr/bin/env python3
from opentelemetry.instrumentation.auto_instrumentation import _load_distro, _load_instrumentors
from agent_agentcore import app


def start_telemetry():
    # 1. Initialize the Distro (sets up default configuration)
    distro = _load_distro()
    distro.configure()

    # 2. Initialize the Instrumentors (this is the "magic" part)
    # This scans your installed packages and patches them.
    _load_instrumentors(distro)

start_telemetry()

if __name__ == "__main__":
    app.run()
