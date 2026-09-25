# syntax=docker/dockerfile:1
# Hermes for the captain's k3s cluster: the upstream image (the repo-root
# Dockerfile, built by docker-bake.hcl as the `hermes-upstream` context) plus
# the host tools the VPS install relied on. Entrypoint, user and volume layout
# stay upstream's.
FROM hermes-upstream

USER root

# GitHub CLI: the github skill and the nightly forex job (gh repo clone,
# gh pr create). Auth comes from $HOME/.config/gh/hosts.yml on the data volume.
ARG GH_VERSION=2.100.0
ARG GH_SHA256=e4d4bb4498e8d007abe545b6568926793ace1b6447da598294a610018cb164be
RUN set -eu; \
    curl -fsSL --retry 3 -o /tmp/gh.tar.gz \
        "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_amd64.tar.gz"; \
    printf '%s  %s\n' "${GH_SHA256}" /tmp/gh.tar.gz | sha256sum -c -; \
    tar -xzf /tmp/gh.tar.gz -C /tmp; \
    install -m 0755 "/tmp/gh_${GH_VERSION}_linux_amd64/bin/gh" /usr/local/bin/gh; \
    rm -rf /tmp/gh.tar.gz "/tmp/gh_${GH_VERSION}_linux_amd64"

# Kyutai Pocket TTS (CPU torch) for the `pocket` command TTS provider, at the
# versions the VPS ran. Models load from $HOME/.cache/huggingface.
COPY pocket-tts-requirements.txt /tmp/pocket-tts-requirements.txt
RUN uv venv --python /usr/bin/python3 /opt/pocket-tts && \
    uv pip install --no-cache --python /opt/pocket-tts/bin/python \
        --index-url https://pypi.org/simple \
        --extra-index-url https://download.pytorch.org/whl/cpu \
        --index-strategy unsafe-best-match \
        -r /tmp/pocket-tts-requirements.txt && \
    rm /tmp/pocket-tts-requirements.txt && \
    /opt/pocket-tts/bin/pocket-tts --help >/dev/null
COPY --chmod=0755 pocket-tts-hermes.sh /usr/local/bin/pocket-tts-hermes.sh

# Scripts that look for hermes at a fixed path (the forex nightly job checks
# ~/.local/bin/hermes, then /usr/local/bin/hermes).
RUN ln -s /opt/hermes/bin/hermes /usr/local/bin/hermes
