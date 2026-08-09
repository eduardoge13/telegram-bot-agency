# Despliegue del sitio (blueskytravelmx.com + Yoga Verde)

**Regla única: el despliegue se hace con `site/scripts/deploy.sh`. Nada más.**

```bash
cd site
./scripts/deploy.sh
```

Este documento existe porque el sitio se desplegó mal varias veces y siempre por
la misma razón. Si vas a tocar el despliegue, lee las dos trampas antes.

## Fuente de una release

Publica únicamente desde el checkout que contiene el commit aprobado para esa
release. Antes de ejecutar el script confirma `git rev-parse --show-toplevel`,
`git branch --show-current`, `git log -1 --oneline` y `git status`; el worktree
`yoga-verde-redesign` quedó obsoleto y no es una fuente válida. La release de
Yoga Verde del 2026-08-05 incluye el pase premium de identidad: superficies
claras, verde solo como acento, paneles con bisel/radio suave, derivados de
producto normalizados y el detalle móvil con scroll y cierre accesibles.

---

## Prohibido: `rsync` y `scp -r`

No es una preferencia de estilo. Ambos **fallaron en silencio** en este
proyecto: terminaban con código de salida 0 y el árbol copiado a medias.
El resultado fue `src/` vacío en el servidor y `scripts/run-astro.mjs` borrado,
lo que rompía el build. Como el contenedor seguía sirviendo la imagen anterior,
el sitio parecía sano mientras el código fuente en el servidor estaba destruido.

La ruta correcta es **un solo tarball con SHA-256 verificado**. Se extrae y se
valida en un release staging en el mismo volumen; la publicación reemplaza el
directorio completo, no aplica el tarball como un overlay aditivo. El script
aborta antes del intercambio si detecta secretos, bases de datos o archivos
operativos dentro del root activo.

---

## Trampa 1: hay dos copias del sitio en el servidor

```
/docker/blueskytravel-site/          ← ESTA es la real. Docker construye aquí.
/docker/blueskytravel-site/site/     ← copia huérfana de un despliegue viejo
```

Ambas tienen `docker-compose.yml` y `Dockerfile`, así que desplegar en `site/`
**parece funcionar**: el build corre limpio y no cambia nada. Costó cerca de una
hora de depuración la primera vez. El script publica la raíz completa; al
completar correctamente el intercambio, la copia huérfana deja de formar parte
del release activo.

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
| Empaqueta un `.tar.gz` | Excluye `node_modules`, `.git`, `.astro`, `dist`, `.env*`, `*.pem`, `*.key`, credenciales y tokens. **Aborta** si algo sensible se coló. |
| Transfiere **un** archivo y compara SHA-256 | Detecta la transferencia incompleta que rsync ocultaba. |
| Extrae a staging y valida el paquete | Comprueba que existen el runtime, la página, los datos y `deploy-manifest.json` **antes** de tocar producción. |
| Protege el root activo | Aborta si encuentra `.env`, llaves, bases de datos, overrides de Compose u otros archivos operativos que serían eliminados por el reemplazo completo. |
| Intercambia el release completo | Mueve el release activo a un respaldo y coloca el staging en su lugar. Así también desaparecen archivos borrados del repositorio; no se usa un overlay aditivo. |
| Reconstruye `--no-cache` y escanea | El contexto de build es la raíz, no `site/`. Antes de recrear, Trivy debe reportar cero vulnerabilidades `HIGH`/`CRITICAL` con corrección disponible; si falla el build o la compuerta, restaura directorios sin reconstruir innecesariamente el contenedor viejo. |
| Verifica en vivo con reintentos | Espera a que nginx acepte tráfico y confirma ambos dominios. Después valida el manifest con el ID exacto de esta ejecución. |

## Rollback y limpieza

Durante el deploy el script mantiene una máquina de estados: `none`, `swapping`,
`swapped`, `running` y `done`. Un `trap` para `EXIT`, `INT` y `TERM` limpia el
staging y el tarball; si el proceso se interrumpe después del intercambio,
restaura el release anterior moviendo el release fallido a cuarentena. Si la
interrupción ocurre después de `up -d`, también reconstruye y recrea el release
anterior. Un fallo de `build` no reconstruye el contenedor viejo porque este
seguía sirviendo la imagen anterior.

El identificador servido en
`/yoga-verde/deploy-manifest.json` combina el commit y la ejecución actual. Solo
después de verificarlo se elimina el respaldo. Un recolector posterior elimina
directorios temporales antiguos con el prefijo exacto del sitio; nunca toca el
release activo.

## Checklist visual antes de publicar

- Confirmar que el hero no muestra “Piel, cabello y bienestar” como titular.
- Confirmar que el header usa el YG compacto en móvil y que el logo completo no
  domina la barra superior.
- Confirmar que catálogo, selección, kits, filosofía, newsletter y footer no
  usan verde como superficie dominante.
- Confirmar `object-fit: contain`, `object-position: center` y los derivados
  `public/yoga-verde/assets/products/display/*.webp`; no volver a `cover`.
- Confirmar en móvil que cada tarjeta se ve completa, que “Ver detalle” abre,
  permite scroll y cierra, y que no existe overflow horizontal.

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
