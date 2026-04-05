# Django_healthcheck

## Infra Health Check

### Project Created

#### Podman / Docker Commands


```bash
podman pull ghcr.io/bantify/django_healthcheck:latest

podman run -d -p 8000:8000 -v healthcheck:/var/log/healthcheck:ro ghcr.io/bantify/django_healthcheck:latest -name healthcheck

podman exec -it healthcheck /bin/bash
podman image rm 7b3e3ddc24c1
Container delete
podman rm 282bf9182790

