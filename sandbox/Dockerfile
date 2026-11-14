# QuestForge Isolated Code Execution Sandbox
# Hardened, zero-network, unprivileged execution environment
FROM python:3.12-slim-bookworm

# Install minimal compiler toolchains for multi-language execution
RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ \
    gcc \
    default-jdk-headless \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged runner user
RUN groupadd -g 10001 sandboxgroup && \
    useradd -u 10001 -g sandboxgroup -m -s /bin/bash sandboxuser

# Setup isolated workspace
WORKDIR /sandbox
RUN chown -R sandboxuser:sandboxgroup /sandbox

USER sandboxuser

# Keep container idle awaiting isolated 'docker exec' invocations
ENTRYPOINT ["tail", "-f", "/dev/null"]
