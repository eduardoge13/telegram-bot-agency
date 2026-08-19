# Yoga Verde — handoff de rediseño visual

Fecha: 2026-08-09
Rama: `codex/yoga-verde-webflow-redesign`
Base: `5306b9e feat(yoga-verde): refine premium identity layer`

## Estado actual

- `origin/main` avanzó por fast-forward al release aprobado; el checkout local
  sucio de `main` no se tocó. El sitio se desplegó desde esta rama mediante el
  flujo canónico por tarball; el commit activo es `ee5ea3b` (`fix(yoga-verde):
  show complete kit galleries in detail`).
- La primera capa visual ya está implementada en el commit
  `4e3ea78 feat(yoga-verde): add editorial commerce visual layer`.
- La segunda capa de motion y campaña está implementada localmente: fondo
  editorial original, barrido de luz, header compacto al hacer scroll, parallax
  del hero y bloque de ritual por capas. El manifiesto está en
  `docs/YOGA_VERDE_MOTION_ASSETS.md`.
- El sitio conserva la lógica actual de Astro: catálogo, búsqueda, filtros,
  carrito, detalle responsive, scrollspy y slider.
- Se descartó la primera dirección de bodegón botánico generado porque no
  coincidió con la referencia visual buscada. Las dos imágenes rechazadas se
  movieron fuera del repositorio a `/tmp/yoga-verde-rejected-campaign/`.
- No quedan cambios de esas escenas en `index.astro` ni un manifiesto de assets
  rechazados dentro del proyecto.
- La validación local pasó `npm run check` con 0 errores/0 warnings propios y
  `npm run build` correctamente. Se revisaron capturas a 390×844 y 1280×900;
  el detalle móvil abre/cierra, el producto permanece centrado y no se observó
  overflow horizontal.
- Webflow sigue siendo un laboratorio visual/exportable, no la fuente de datos
  ni de checkout. La sesión de Webflow requiere que el usuario introduzca sus
  propias credenciales; el agente no debe escribirlas.

## Dirección aprobada para retomar

Cambiar a una referencia de e-commerce premium más limpia, cercana a
`https://www.skims-mexico.com/` y a tiendas editoriales de belleza:

- barra de anuncio fina y header compacto;
- navegación horizontal clara, logotipo centrado y acciones mínimas;
- hero editorial de producto real, sin escenas artificiales ni slogan genérico;
- producto grande, bien encuadrado y al ras de la composición, con caption corto
  y una sola acción;
- superficies blanco cálido y crema, con verde solo para tipografía, botones y
  estados activos; terracota únicamente como acento;
- cards de producto planas y más modernas, con bordes sutilmente curvos o
  biselados, sin grandes bloques verdes ni cambios abruptos de color;
- catálogo de tres/cuatro columnas en escritorio y una tarjeta completa en
  móvil, sin segunda tarjeta cortada;
- motion preciso y lento en scroll, hero slider ágil pero sin alterar su lógica;
- Webflow-ready mediante hooks y tokens, pero sin reemplazar `shop.js`, los
  datos, el modal de detalle ni `deploy.sh`.

## Investigación realizada

- Se inspeccionó visualmente SKIMS México en Chrome: anuncio compacto, wordmark
  negro, navegación densa, hero editorial a pantalla amplia, texto en overlay,
  CTA discreta, franja de beneficios y footer ligero.
- También se revisaron como referencias de jerarquía y e-commerce premium
  Retrouvé, Aesop, The Ordinary, Caudalie y ejemplos de beauty commerce de
  Shopify/Webflow.
- Webflow GSAP es la opción de motion preferida; Rive/WebGL solo debe quedar
  como experimento de escritorio con fallback estático en móvil y
  `prefers-reduced-motion`.
- Claude CLI está disponible en `/Users/eduardogaitan/.local/bin/claude`, versión
  `2.1.224`; debe usarse después de la implementación para auditoría de solo
  lectura, sin `git add .` ni modificaciones fuera de la rama.

## Siguiente bloque de trabajo

1. Mantener `origin/main` como fuente de verdad; el checkout local de `main`
   sigue sucio y debe alinearse únicamente después de preservar esos cambios.
2. Actualizar las dependencias de Astro en un commit separado para resolver el
   reporte de `npm audit`, con regresión funcional y visual antes de publicar.
3. Revisar acceso a Webflow si se abre una nueva fase visual; el usuario debe
   introducir sus credenciales.

## Restricciones que siguen vigentes

- No cambiar precios, textos de producto, assets reales ni comportamiento de
  compra sin necesidad.
- No usar `object-fit: cover` para fotografías de producto; mantener
  `contain`, centrado y derivados normalizados.
- No usar `rsync`, overlays de tarball ni deploy desde el worktree antiguo.
- No desplegar antes de aprobación visual explícita.

## Iteración móvil bold — 2026-08-09

Se añadió una capa específica para celular, no una simple reducción del
desktop:

- hero con swipe táctil y CTA de producto conservada;
- selección esencial como deck horizontal de una tarjeta completa, con
  `scroll-snap`, contador y navegación por dots;
- escena editorial con productos tocables, estado 01/03 y cambio de producto
  según el avance del scroll;
- quick view visible sobre la imagen en móvil y también en las tarjetas que
  `shop.js` genera dinámicamente;
- progreso de lectura, headings por palabras, entrada por clip y respuesta
  magnética en desktop como capa complementaria;
- `prefers-reduced-motion` mantiene estados estáticos y no bloquea compra,
  detalle, carrito ni navegación.

Validación de esta iteración: `npm run check` 0 errores/0 warnings, `npm run
build` exitoso, 320×692 y 390×844 sin overflow horizontal, 27 quick views
dinámicos, detalle abre/cierra con body lock y carrito abre desde el header.
Ese estado visual quedó incluido en el despliegue seguro descrito abajo. No se
hizo push ni merge.

## Despliegue seguro — 2026-08-09

- Claude CLI realizó una auditoría de solo lectura del checkout, del script de
  despliegue y de los requisitos del VPS; emitió `GO` sin bloqueadores P0.
- La primera verificación posterior al release visual detectó seis hallazgos
  `HIGH` corregibles y cero `CRITICAL` en paquetes Alpine de la imagen final de
  nginx. No se aceptaron como estado final.
- El commit `80b6746` añade `apk upgrade --no-cache` al stage final y convierte
  Trivy en una compuerta obligatoria antes de `docker compose up -d`.
- El despliegue final usó exclusivamente `site/scripts/deploy.sh`: tarball,
  SHA-256 verificado, staging en `/docker`, intercambio completo, rollback por
  estado y manifest vivo. No se usó `rsync` ni `scp -r`.
- Trivy del release final: `0 HIGH`, `0 CRITICAL` con `--ignore-unfixed`.
- Manifest activo: `80b674614c93-20260809-153413-22556`.
- `yoga-verde.srv1175749.hstgr.cloud`, `blueskytravelmx.com` y
  `www.blueskytravelmx.com` respondieron `200`; Traefik conservó su contenedor
  y siguen activos 20 contenedores en total.
- No quedaron releases `stage`, `old` o `failed` del sitio en `/docker`.
- `npm audit` todavía reporta vulnerabilidades en dependencias usadas durante
  la compilación de Astro. No viajan en la imagen nginx multi-stage, pero deben
  resolverse en una actualización separada de `package-lock.json`, con build y
  regresión visual completos; no ejecutar `npm audit fix` a ciegas.

## Revisión crítica de hero y campaña — 2026-08-09

La mezcla entre el fondo de estudio generado y los productos reales se
descartó. Los derivados tienen un canvas `#faf8f4` horneado; sobre el antiguo
degradado aparecían rectángulos claros y la campaña perdía coherencia.

Cambios definitivos:

- hero reconstruido como una sola escena móvil: logo, nombre/beneficio y un
  producto protagonista sobre el mismo `#faf8f4` del asset;
- fondo generado eliminado del CSS y del paquete;
- captions salientes ocultos de inmediato para evitar texto fantasma durante
  la transición;
- “Tres esenciales. Una pausa para ti.” reemplazado por “Tu ritual, un paso a
  la vez.”;
- collage de tres productos sustituido por un solo producto activo con tres
  pasos táctiles;
- eliminadas la línea terracota móvil y las marcas técnicas que cruzaban la
  composición;
- referencia visual principal: la jerarquía móvil de Sustain Yourself —una
  escena, un producto, un mensaje— adaptada a los assets reales de Yoga Verde.

Validación adicional: 320×692, 390×844, 414×896 y 1280×900 sin overflow;
un solo caption activo durante el slider; detalle móvil abre con cierre visible;
preview del build estático en puerto limpio con 0 errores, 0 warnings y ninguna
petición al asset retirado.

## Menú móvil editorial — 2026-08-09

> Esta versión quedó reemplazada por la corrección móvil integral documentada
> abajo. Se conserva aquí únicamente como historial de la iteración.

El menú superior izquierdo dejó de ser un drawer genérico y ahora funciona
como una interacción móvil completa:

- el icono de dos líneas se transforma en “X” al abrir;
- el panel entra con máscara curva, desplazamiento y fondo desenfocado;
- encabezado y seis destinos aparecen con stagger, numeración y estado activo;
- el cierre conserva `<details open>` durante 740 ms para que la animación de
  salida sí sea visible antes de desmontar el panel;
- el fondo permanece bloqueado durante toda la transición y se libera al final;
- Escape, backdrop y el mismo toggle cierran el menú y devuelven el foco;
- el foco queda atrapado dentro de la interacción mientras está abierta;
- elegir una sección espera el cierre y después navega, manteniendo scrollspy;
- `prefers-reduced-motion` elimina las demoras sin romper la navegación.

Validación: `npm run check` con 0 errores/0 warnings y `npm run build` exitoso;
320×692, 390×844 y 414×896 sin overflow horizontal ni enlaces recortados; 0
errores de consola; cierre animado, Escape, bloqueo de fondo, retorno de foco,
Catálogo activo y detalle móvil verificados. No se hizo push, merge ni deploy.

## Corrección móvil integral + auditoría Claude — 2026-08-09

La iteración final reemplaza el drawer decorativo por una navegación sobria y
full-screen, y armoniza el resto del home móvil sin cambiar datos ni precios:

- panel crema de `100vw × 100dvh`, sin blur, sombra, máscara, números, flechas
  ni radios; cinco destinos principales, búsqueda separada y pie con envío,
  origen y contador real del carrito;
- monograma móvil de 30 px, header estable y controles de 44 px sin colisiones;
- animación real de apertura de 320 ms, cierre de 240 ms y stagger de enlaces;
  el `<details>` permanece abierto durante la salida;
- foco inicial, trampa de foco, Escape, retorno de foco, `inert`, scroll lock y
  variante `prefers-reduced-motion` de solo fade a 120 ms;
- cierre inmediato y liberación del fondo si una rotación o resize cruza el
  breakpoint desktop de 768 px;
- catálogo y selección con medios 4:5, `object-fit: contain`, radio de 16 px,
  sin sombras permanentes ni quick-view superpuesto; ninguna segunda tarjeta
  asoma en el carril móvil;
- hero sin guiones automáticos en el nombre y composición corregida a 320 px;
- terracota de texto oscurecida a `#b4563c` para 4.64:1 sobre papel cálido;
- los botones de imagen anuncian nombre, aroma y badge, incluidos los tres
  productos con “Formato mini”;
- navegación calculada con `offsetTop` para ignorar transforms de entrada y
  dejar los títulos debajo del header sticky.

Validación desde el build estático en un contexto nuevo:

- `npm run check`: 0 errores, 0 warnings, 0 hints;
- `npm run build`: exitoso; `git diff --check`: limpio;
- 320×692, 375×812, 390×844, 414×896 y 1280×900: cero overflow y cero
  colisiones en el header;
- menú completo sin scroll interno, apertura 351–361 ms medida con overhead de
  navegador, cierre 250–253 ms, foco y scroll lock correctos;
- rotación simulada 390→844 libera `inert`, `aria-hidden` y scroll;
- búsqueda, carrito, navegación, scrollspy y foco atrapado verificados;
- detalle de kit visible, desplazable y cerrable en móvil y escritorio;
- consola: 0 errores y 0 warnings.

Claude Opus realizó la segunda auditoría de solo lectura. Encontró el bloqueo
de breakpoint y el badge accesible; ambos se corrigieron. La comprobación final
reportó `P0: ninguno`, `P1: ninguno` y `APROBADO`. Sus P2 visuales aplicables
también quedaron resueltos (blend normal, hover solo en puntero fino, tokens de
menú, cobertura 375 y limpieza de quick-view muerto). Queda únicamente CSS
histórico de `.ritual-mobile-hint`, sin marcado ni impacto runtime.

Este estado visual forma parte del release desplegado en `ee5ea3b`; el código
quedó incorporado a `origin/main` por fast-forward.

## Detalle completo de kits — 2026-08-09

- `Kit Ritual Facial` muestra sus tres fórmulas reales dentro del detalle, con
  imágenes normalizadas, captions y separadores `+` animados.
- Los demás kits muestran todos sus componentes reales; los kits dúo conservan
  dos productos y no duplican fotografías para simular un tercero.
- Los controles `+` de Beneficios y Cómo usarlo tienen transición de estado y
  respetan `prefers-reduced-motion`.
- Se verificaron 320×692, 390×844, 414×896 y 1280×900: detalle desplazable y
  cerrable, CTA visible, producto individual con una sola imagen, cero overflow
  horizontal y consola limpia.
- Release activo: `ee5ea3b`; manifest
  `ee5ea3baee64-20260809-162903-26112`; Yoga Verde y Blue Sky respondieron
  `200`; Trivy de la imagen final reportó `0` HIGH/CRITICAL y no quedaron
  releases temporales bajo `/docker`.

## Catálogo vigente y campaña editorial — 2026-08-18

- El PDF vigente proporcionado por el cliente se cruzó con los 27 productos de
  la tienda. Se actualizaron 17 variantes existentes con sus precios oficiales
  y se conservaron sin cambios los artículos ausentes del PDF; no se
  inventaron tarifas para productos ni kits.
- Beneficios y descripciones se adaptaron del catálogo con formulaciones
  prudentes de “ayuda a” y “apariencia”. El bálsamo coco y menta existente se
  identificó como la presentación grande de 50 g a `$210`; la presentación de
  10 g no se creó sin fotografía y registro propios.
- El hero móvil quedó dividido en tres regiones físicas —marca, fotografía y
  ficha—. Las mediciones en 320, 390 y 414 px reportaron cero intersección entre
  imagen y texto y cero overflow del documento.

## Portada-catálogo y assets retina — 2026-08-18

- “El color nace del ingrediente” y el hero se fusionaron en una sola portada
  inspirada en el catálogo oficial: fondo crema continuo, jerarquía editorial,
  logo real, acentos terracota y selección aleatoria de seis productos.
- El conjunto disponible creció a 13 productos reales. La selección permanece
  estable por navegador mediante una semilla local anónima; no se recopila PII
  ni comportamiento del visitante.
- Las imágenes se extrajeron de los originales embebidos en el PDF a 300 ppi,
  no de screenshots. Los masters miden 1400–1624 px de ancho y hasta 2351 px
  de alto; cada uno cuenta con un derivado de 800 px y entrega responsiva por
  `srcset`/`sizes`.
- En escritorio la fotografía vertical y la ficha viven en columnas separadas,
  evitando que `cover` corte la etiqueta. En móvil la ficha empieza después de
  la fotografía y el primer visual ya asoma dentro del viewport inicial.
- QA desde build estático: `npm run check` sin diagnósticos, `npm run build`
  exitoso, consola limpia y cero overflow horizontal en 320×692, 390×844,
  414×896 y 1280×900. No se hizo merge ni despliegue en esta iteración.

## Controles desktop y dirección de color — 2026-08-18

- Los controles del hero ahora muestran explícitamente `01–06`, se numeran de
  nuevo después del shuffle y exponen `aria-current` para la pieza activa.
- En desktop el bloque se desplazó fuera del bisel orgánico: los seis objetivos
  quedan completos, miden 44×44 y pasan hit-testing real en su centro.
- Se añadió una gradación moderada por fotografía. Agua micelar usa mayor
  saturación/contraste; cera y crema de manos, que ya eran referencias fuertes,
  reciben el ajuste mínimo.
- La manteca mango/coco usa `manteca-campana-v2.webp`, edición no destructiva
  creada con la herramienta integrada de generación de imágenes. El original
  sigue en el repositorio. La nueva escena corrige la percepción comprimida y
  alinea mango, coco, tarro y fondo dentro de una composición vertical.
- Verificación visual dirigida con semilla `22`: agua micelar, cera, manteca,
  desmaquillante, desodorante y crema de manos; los seis controles fueron
  accionables. En 390×844 la manteca no se superpone con la ficha y el documento
  conserva cero overflow. Consola: cero errores y cero warnings.
- Se incorporaron fotografías oficiales optimizadas bajo
  `site/public/yoga-verde/assets/catalog/` y una composición editorial sobre
  superficies crema. El PDF fuente no se versionó ni se despliega.
- El detalle móvil fue verificado con scroll interno, cierre de 44 px, Escape,
  retorno de foco y el precio actualizado; la consola quedó sin errores.
- Se creó `.github/workflows/site-ci.yml`: instalación bloqueada, check y build
  para PRs y `main`, permisos de solo lectura, acciones fijadas por SHA,
  timeout y concurrencia cancelable. El primer run pasó en 38 segundos.
- PR `#2` integrado a `main` mediante merge commit `0472a2f`. El release se
  desplegó desde ese commit con `site/scripts/deploy.sh`; tarball de 8.2 MB,
  SHA-256 verificado, staging completo, Trivy `0` y rollback disponible.
- Manifest activo:
  `0472a2f0204f-20260818-130157-1488`. Yoga Verde y Blue Sky respondieron `200`,
  el asset editorial respondió `200` y los precios oficiales se confirmaron en
  el HTML servido.
- `npm audit` sigue señalando vulnerabilidades de la cadena de compilación. Una
  actualización dentro de rango redujo el conteo, pero rompió la compatibilidad
  Astro/Vite/Tailwind; se revirtió por completo. El runtime publicado es nginx
  estático y la imagen final sí pasó la compuerta Trivy. La migración de
  dependencias debe hacerse en una iteración separada con regresión visual.
- El tarball ahora usa `--no-xattrs` además de `COPYFILE_DISABLE=1` para omitir
  `com.apple.provenance` y evitar ruido de libarchive en despliegues futuros.

## Selección anónima del hero — 2026-08-18

- El hero dispone de 13 productos con fotografía real y presenta seis por
  navegador, en un orden aleatorio estable. Esto amplía la variedad sin llenar
  el hero móvil con controles que provocarían saturación u overflow.
- La única persistencia es una semilla aleatoria de 32 bits en
  `localStorage`, bajo `yoga-verde:hero-seed:v1`. No identifica a la persona,
  no registra navegación y no se transmite al servidor.
- Cada slide expone internamente categoría y familia de aroma como contrato
  para un ranking futuro. No existe todavía perfilado, analítica ni uso de
  información pública.
- Una fase futura de recomendaciones deberá definir consentimiento, aviso de
  privacidad, retención, borrado y explicación de por qué se recomienda cada
  producto antes de registrar un perfil de consumo.
- QA local: dos contextos aislados recibieron selecciones distintas; un mismo
  contexto conservó su orden al recargar; seis slides y seis controles quedaron
  visibles, sin errores de consola ni overflow en 320, 390, 414 y 1280 px.

## Release de portada aleatoria y campaña refinada — 2026-08-18

- PR `#4` pasó Site CI y se integró a `main` mediante merge commit `71d9103`.
  El checkout local sucio de `main` permaneció intacto; el despliegue salió de
  un worktree limpio creado desde `origin/main`.
- El release se publicó únicamente con `site/scripts/deploy.sh`: tarball de
  14 MB y 186 entradas, SHA-256
  `0144f00aa676daaa1f240114e6f851c79aad8620c5cbe3839c480ff623c3be05`,
  staging en el mismo volumen, intercambio completo, rollback por estado y
  compuerta Trivy antes de recrear el contenedor. No se usó `rsync` ni copia
  recursiva.
- Manifest activo:
  `71d9103d2024-20260818-143523-26030`. Yoga Verde, Blue Sky y `www` devolvieron
  `200`; “El color nace del ingrediente”, los controles numerados y la nueva
  escena de manteca se confirmaron desde contenido público. El asset de manteca
  respondió `200` con 194,914 bytes.
- La imagen final `alpine 3.23.5` reportó `0` HIGH/CRITICAL. El contenedor del
  sitio quedó `running`, Traefik conservó su ID, continuaron 20 contenedores en
  ejecución y no quedaron releases temporales bajo `/docker`.
- `npm audit` reporta nueve avisos HIGH en la cadena de compilación de
  Astro/Vite y dependencias transitivas. Esos paquetes no forman parte del
  runtime Nginx estático, pero deben migrarse en una iteración separada con
  regresión funcional y visual; no ejecutar `npm audit fix` a ciegas.
- El preflight siguió mostrando dos unidades fallidas ajenas a este sitio:
  `site-advisor.service` y `telegram-bot-sync.service`. No se modificaron en
  este release.

## Rediseño multipágina para aprobación — 2026-08-18

- Se eliminó la dependencia de una portada larga como tienda completa. Yoga
  Verde ahora tiene home editorial, catálogo, cuatro colecciones, índice de
  kits, seis detalles de kit y 27 páginas de producto con URLs propias.
- La portada usa la campaña de cera con miel como protagonista y conserva los
  visuales aprobados de mango, manzanilla y mango/coco para dirigir a compras
  concretas. Los precios quedan visibles junto al nombre y antes de la CTA.
- El catálogo mantiene búsqueda, filtros y 27 productos, pero cada tarjeta
  conduce a una ficha completa. El carrito persiste entre páginas y su drawer
  se corrigió para no recortar precio, cantidad ni “Eliminar” en móvil.
- El Kit Ritual Facial muestra sus tres piezas en una composición responsive:
  agua micelar, crema facial y contorno de ojos. Los productos incluidos también
  conservan páginas y precios individuales.
- QA local: `npm run check` sin diagnósticos, `npm run build` exitoso con 49
  páginas, 42 rutas internas y 43 assets Yoga Verde respondiendo `200`; cero
  overflow horizontal en 320, 390, 414 y 1440 px. Menú, búsqueda, filtros,
  carrito persistente y CTA de producto verificados en navegador real.
- Rama de trabajo: `codex/yoga-verde-multipage-redesign`. Esta iteración queda
  solo para aprobación local; no se desplegó ni se modificó producción.

## Release multipágina y ruta canónica — 2026-08-18

- El rediseño se integró mediante PR `#6` y merge commit `e3708b0`; los hotfixes
  de URL canónica pasaron por PR `#7` y `#8`. El release final corresponde al
  merge commit `e8f9fbe` de `origin/main`.
- La auditoría previa cubrió 48 rutas publicables y 97 recursos enlazados. En
  navegador real se validaron 320, 390, 414 y 1280 px sin overflow, consola
  limpia, 27 productos, seis kits, búsqueda/filtros, menú, detalle, imágenes y
  carrito. El carrito añade, incrementa, reduce, elimina y conserva estado al
  cambiar de página; sus controles y el logo cumplen 44 px en móvil.
- Ritual Facial sirve sus tres imágenes reales: agua micelar, crema facial y
  contorno de ojos. La ficha de contorno confirma `$350` y `10 mL`; el kit
  confirma `$749`.
- La verificación independiente del primer release detectó un `404` exclusivo
  de `/yoga-verde` sin slash. El siguiente deploy rechazó correctamente un
  `Location: http://...` generado detrás de Traefik y ejecutó rollback completo.
  El hotfix final usa redirección relativa `308 /yoga-verde/` y el script
  canónico ahora la exige en cada despliegue.
- El release final se publicó solo mediante `site/scripts/deploy.sh`: tarball de
  14 MB y 201 entradas, SHA-256
  `891702e116a4d19b13f3887420693761825cf7c62482fdf17a0ae215cd29c759`,
  staging en el mismo volumen, swap completo, rollback por estado y compuerta
  Trivy antes de recrear el contenedor. No se usó `rsync` ni copia recursiva.
- Manifest vivo:
  `e8f9fbec3741-20260818-160413-40220`. Yoga Verde, Blue Sky y `www`
  respondieron `200`; el contenedor quedó `running`, con `RestartCount=0`, y la
  imagen final Alpine 3.23.5 reportó `0` HIGH/CRITICAL en Trivy.
- Límite comercial vigente: el carrito funciona, pero
  `/api/yoga-verde/checkout` responde `404` porque el shell de Stripe no está
  conectado al Compose productivo. No presentar el sitio como capaz de cobrar
  hasta desplegar la API con cuenta, secretos y pruebas propias de Yoga Verde.
- `npm ci` continúa reportando 14 avisos en dependencias de compilación, nueve
  HIGH. No forman parte del runtime Nginx estático; migrarlos en una iteración
  separada con regresión funcional/visual, sin ejecutar `npm audit fix` a
  ciegas. GitHub Actions también avisa que los SHA actuales de checkout/setup
  usan runtime Node 20 forzado a Node 24; actualizar esas actions por separado.
