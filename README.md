"# Django_healthcheck" 
## Infra health check

### Project created

#### Podman command:

docker pull ghcr.io/bantify/django_healthcheck:latest
podman run  -d -p 8000:8000   -v healthcheck:/var/log/healthcheck:ro   ghcr.io/bantify/django_healthcheck:latest

Image delete
podman image rm 7b3e3ddc24c1
Container delete
podman rm 282bf9182790

