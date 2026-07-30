# Despliegue del sitio (blueskytravelmx.com + Yoga Verde)

**Regla única: el despliegue se hace con `site/scripts/deploy.sh`. Nada más.**

```bash
cd site
./scripts/deploy.sh
```

Este documento existe porque el sitio se desplegó mal varias veces y siempre por
la misma razón. Si vas a tocar el despliegue, lee las dos trampas antes.

---

## Prohibido: `rsync` y `scp -r`

No es una preferencia de estilo. Ambos **fallaron en silencio** en este
proyecto: terminaban con código de salida 0 y el árbol copiado a medias.
El resultado fue `src/` vacío en el servidor y `scripts/run-astro.mjs` borrado,
lo que rompía el build. Como el contenedor seguía sirviendo la imagen anterior,
el sitio parecía sano mientras el código fuente en el servidor estaba destruido.

La ruta correcta es **un solo tarball con checksum verificado**: es atómica y se
puede comprobar antes de tocar producción.

---

## Trampa 1: hay dos copias del sitio en el servidor

```
/docker/blueskytravel-site/          ← ESTA es la real. Docker construye aquí.
/docker/blueskytravel-site/site/     ← copia huérfana de un despliegue viejo
```

Ambas tienen `docker-compose.yml` y `Dockerfile`, así que desplegar en `site/`
**parece funcionar**: el build corre limpio y no cambia nada. Costó cerca de una
hora de depuración la primera vez. El script excluye `site/` a propósito.

Comprobación rápida de que el contenido llegó de verdad:

```bash
ssh -p 2222 vps-n8n "sudo docker exec blueskytravel-site-bluesky-site-1 \
  ls /usr/share/nginx/html/yoga-verde/"
```

## Trampa 2: `ufw` limita el puerto SSH

- El puerto SSH real es **2222** (el 22 hace timeout).
- Hay una regla `LIMIT` en 2222: más de ~6 conexiones en 30s y el servidor
  empieza a rechazar. **No hagas reintentos en bucle cerrado**; espera 30-60s.
- No es fail2ban. Verificable con `sudo ufw status verbose`.

---

## Qué hace el script, y por qué cada paso

| Paso | Por qué |
|---|---|
| `npm run check` + `npm run build` | No se despliega algo que no compila. |
| Empaqueta un `.tar.gz` | Excluye `node_modules`, `.git`, `.astro`, `dist`, `.env*`, `*.pem`, `*.key`, credenciales. **Aborta** si algo sensible se coló. |
| Transfiere **un** archivo y compara md5 | Detecta la transferencia incompleta que rsync ocultaba. |
| Extrae a staging y valida el paquete | Comprueba que existen `run-astro.mjs`, `package.json`, la página y los datos **antes** de tocar producción. Este es el paso que faltaba. |
| Publica y reconstruye `--no-cache` | El contexto de build es la raíz, no `site/`. |
| Verifica en vivo con reintentos | Espera a que nginx acepte tráfico y luego **grepea el HTML servido** para confirmar que es este build: un 200 puede venir de una imagen vieja. |

---

## CI/CD

**No existe todavía.** No hay `.github/workflows/` ni ningún otro pipeline en
este repositorio.

Si se agrega, debe **invocar este mismo script** (o reproducir sus pasos
exactamente) para que la ruta de despliegue siga siendo una sola. Requeriría:

- una llave SSH con acceso a `vps-n8n:2222` como secreto del repositorio;
- ejecutar únicamente cuando cambie `site/`;
- conservar la validación de staging y la verificación de contenido en vivo.

No se creó un workflow ahora porque sin el secreto configurado quedaría un
pipeline que falla en cada ejecución, lo cual es peor que no tenerlo.

---

## Contexto del servidor

- Host SSH: `vps-n8n` (Hostinger, `72.60.228.135`), usuario `deploy` con sudo.
- Traefik (`n8n-traefik-1`) enruta 80/443, red externa `n8n_default`,
  certresolver `mytlschallenge`.
- Contenedor: `blueskytravel-site-bluesky-site-1` (nginx sirviendo el build
  estático de Astro).
- Dominios servidos por el mismo contenedor:
  - `https://blueskytravelmx.com` → sitio Blue Sky Travel
  - `https://yoga-verde.srv1175749.hstgr.cloud` → tienda Yoga Verde
  - `https://blueskytravelmx.com/yoga-verde` → la misma tienda

Al desplegar **se publican los dos sitios a la vez**. Verifica ambos.
