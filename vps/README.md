# vps-patches

This branch is upstream `NousResearch/hermes-agent` plus the patches the
captain's VPS ran, and the image the k3s cluster deploys
(`corygforsythe/homelab-gitops`, `workloads/hermes`).

- The commits on top of the upstream base are the local patches (auto-TTS under
  the routed profile's scope, and no Opus conversion for command TTS providers
  outside Opus platforms), plus this directory and
  `.github/workflows/vps-image.yml`.
- `.github/workflows/vps-image.yml` builds on every push to `vps-patches`:
  the repo-root `Dockerfile` unchanged, then `vps/Dockerfile` on top (the GitHub
  CLI, Pocket TTS on CPU torch at the VPS's versions from
  `pocket-tts-requirements.txt`, and `pocket-tts-hermes.sh`). It pushes
  `ghcr.io/corygforsythe/hermes-agent:<full commit SHA>` and `:vps-patches`.
  Argo CD Image Updater picks up the SHA tag.
- To move to a newer upstream: rebase this branch onto it, drop any patch that
  upstream has absorbed, and push.
