# Builds ghcr.io/corygforsythe/hermes-agent: the unmodified upstream
# Dockerfile, then vps/Dockerfile on top of it.
#   GIT_SHA=$(git rev-parse HEAD) docker buildx bake -f vps/docker-bake.hcl
variable "IMAGE" {
  default = "ghcr.io/corygforsythe/hermes-agent"
}

variable "GIT_SHA" {
  default = ""
}

group "default" {
  targets = ["vps"]
}

target "upstream" {
  context    = "."
  dockerfile = "Dockerfile"
  platforms  = ["linux/amd64"]
  args = {
    HERMES_GIT_SHA = GIT_SHA
  }
}

target "vps" {
  context    = "vps"
  dockerfile = "Dockerfile"
  platforms  = ["linux/amd64"]
  contexts = {
    hermes-upstream = "target:upstream"
  }
  tags = compact([
    GIT_SHA != "" ? "${IMAGE}:${GIT_SHA}" : "",
    "${IMAGE}:vps-patches",
  ])
  labels = {
    "org.opencontainers.image.source"   = "https://github.com/corygforsythe/hermes-agent"
    "org.opencontainers.image.revision" = GIT_SHA
  }
}
