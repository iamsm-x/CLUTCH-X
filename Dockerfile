FROM python:3.13-slim AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml README.md ./
COPY engine ./engine
RUN python -m pip install --no-cache-dir .

COPY ["Data Pack/", "/app/Data Pack/"]
RUN python -m clutch_x.etl.validate_sources --data-dir "Data Pack" \
    && python -m clutch_x.etl.reconstruct_state --data-dir "Data Pack" --output-dir data/processed \
    && python -m clutch_x.etl.score_pressure \
    && python -m clutch_x.etl.validate_pressure \
    && python -m clutch_x.etl.normalizer \
    && python -m clutch_x.etl.score_batting \
    && python -m clutch_x.etl.score_bowling \
    && python -m clutch_x.etl.reliability_filter \
    && python -m clutch_x.etl.rank_players \
    && python -m clutch_x.etl.ranking_audit --allow-stability-failure \
    && python -m clutch_x.etl.build_store --data-dir "Data Pack"

FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CLUTCH_X_DB=/data/clutch_x.duckdb
WORKDIR /app
RUN mkdir -p /data
COPY --from=build /usr/local /usr/local
COPY --from=build /app/data/processed/clutch_x.duckdb /data/clutch_x.duckdb

EXPOSE 8000
CMD ["python", "-m", "clutch_x.api.run"]
