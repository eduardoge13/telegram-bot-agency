# Yoga Verde — handoff de rediseño visual

Fecha: 2026-08-08
Rama: `codex/yoga-verde-webflow-redesign`
Base: `5306b9e feat(yoga-verde): refine premium identity layer`

## Estado actual

- No se tocó `main`, no se hizo push, merge ni despliegue.
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

1. Revisar la vista local con el usuario y ajustar únicamente lo que no apruebe.
2. Auditar funcionalidad completa: navegación, búsqueda, filtros, carrito y
   detalle en 320, 390, 414, 1280 y 1440 px.
3. Volver a intentar la auditoría con Claude CLI cuando haya sesión iniciada;
   en esta ejecución respondió `Not logged in`.
4. Revisar acceso a Webflow; el usuario debe introducir sus credenciales.
5. Solo después de aprobación visual se considerará
   commit final, push, merge y despliegue mediante `site/scripts/deploy.sh`.

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
No se hizo push, merge ni despliegue.

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
