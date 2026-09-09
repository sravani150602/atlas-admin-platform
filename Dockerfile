FROM node:22-bookworm-slim AS web
WORKDIR /app
COPY package.json package-lock.json ./
COPY apps/admin/package.json apps/admin/package.json
COPY packages/ux/package.json packages/ux/package.json
RUN npm ci --no-audit --no-fund
COPY packages packages
COPY apps apps
RUN npm run build

FROM python:3.12-slim-bookworm AS native
RUN apt-get update && apt-get install -y --no-install-recommends gcc make libc6-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.lock.txt ./
RUN python -m venv /venv && /venv/bin/pip install --no-cache-dir -r requirements.lock.txt
COPY Makefile ./
COPY engine engine
COPY proto proto
RUN make all && mkdir -p services/policy && /venv/bin/python -m grpc_tools.protoc -I proto --python_out=services/policy --grpc_python_out=services/policy proto/policy.proto

FROM python:3.12-slim-bookworm AS runtime
RUN useradd --uid 10001 --create-home atlas
WORKDIR /app
COPY --from=native /venv /venv
COPY --from=native /app/build/libatlas.so build/libatlas.so
COPY services services
COPY --from=native /app/services/policy/policy_pb2.py /app/services/policy/policy_pb2_grpc.py services/policy/
COPY --from=web /app/apps/admin/dist apps/admin/dist
RUN mkdir -p /app/data && chown -R atlas:atlas /app/data
ENV PATH="/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
USER atlas
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "services.gateway.app:app", "--host", "0.0.0.0", "--port", "8000"]
