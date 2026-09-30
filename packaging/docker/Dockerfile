# Card-level ClaimBound CLI in a small image, built from a locally built wheel:
#   python -m build --wheel && docker build -f packaging/docker/Dockerfile -t claimbound-evidence .
# Run:  docker run --rm -v "$PWD:/work" claimbound-evidence validate-card card.json
FROM python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f

LABEL org.opencontainers.image.title="claimbound-evidence" \
      org.opencontainers.image.description="Evidence cards for narrow public AI, ML and data claims" \
      org.opencontainers.image.source="https://github.com/ClaimBound/claimbound-evidence" \
      org.opencontainers.image.licenses="Apache-2.0"

COPY dist/*.whl /tmp/wheel/
RUN pip install --no-cache-dir /tmp/wheel/*.whl && rm -rf /tmp/wheel \
    && useradd --create-home --shell /usr/sbin/nologin claimbound

USER claimbound
WORKDIR /work
ENTRYPOINT ["claimbound"]
CMD ["--help"]
