"""Run the CLUTCH-X API using the port assigned by the hosting platform."""

import os

import uvicorn


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    if not 1 <= port <= 65535:
        raise ValueError(f"PORT must be between 1 and 65535, received {port}")
    uvicorn.run(
        "clutch_x.api.main:app",
        host="0.0.0.0",
        port=port,
    )


if __name__ == "__main__":
    main()
