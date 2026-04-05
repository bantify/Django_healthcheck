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


## Installing Bootstrap in a Django Project

Bootstrap can be added to Django in **two recommended ways**:
1. Using **CDN** (simplest and most common)
2. Using **static files** (offline / production‑controlled)

---

## Option 1: Install Bootstrap Using CDN (Recommended)

This method does **not require downloading Bootstrap**.

### Step 1: Create / Update Base Template

Download bootstrap from internet:

project/
├── static/
│   └── bootstrap/
│       ├── css/
│       └── js/
├── templates/
│   └── base.html


Create a base template (if not already created):

```bash
templates/base.html
