# Card-level Protocolith CLI in a small image, built from a locally built wheel:
#   python -m build --wheel && docker build -f packaging/docker/Dockerfile -t protocolith .
# Run:  docker run --rm -v "$PWD:/work" protocolith validate-card card.json
FROM python:3.15-slim@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928

LABEL org.opencontainers.image.title="protocolith" \
      org.opencontainers.image.description="Evidence cards for narrow public AI, ML and data claims" \
      org.opencontainers.image.source="https://github.com/protocolith/protocolith" \
      org.opencontainers.image.licenses="Apache-2.0"

COPY dist/*.whl /tmp/wheel/
RUN pip install --no-cache-dir /tmp/wheel/*.whl && rm -rf /tmp/wheel \
    && useradd --create-home --shell /usr/sbin/nologin protocolith

USER protocolith
WORKDIR /work
ENTRYPOINT ["protocolith"]
CMD ["--help"]
