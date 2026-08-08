# Yoga Verde — handoff de rediseño visual

Fecha: 2026-08-08
Rama: `codex/yoga-verde-webflow-redesign`
Base: `5306b9e feat(yoga-verde): refine premium identity layer`

## Estado al pausar

- No se tocó `main`, no se hizo push, merge ni despliegue.
- El sitio conserva la lógica actual de Astro: catálogo, búsqueda, filtros,
  carrito, detalle responsive, scrollspy y slider.
- Se descartó la primera dirección de bodegón botánico generado porque no
  coincidió con la referencia visual buscada. Las dos imágenes rechazadas se
  movieron fuera del repositorio a `/tmp/yoga-verde-rejected-campaign/`.
- No quedan cambios de esas escenas en `index.astro` ni un manifiesto de assets
  rechazados dentro del proyecto.
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

1. Aplicar el sistema visual SKIMS/editorial sobre `index.astro` y
   `yoga-verde.css` usando los derivados reales `products/display/*.webp`.
2. Convertir el hero actual en una composición editorial limpia: logo visible,
   slider de producto real, caption corto y frame sin tarjeta pesada.
3. Rehacer header, cards, búsqueda, catálogo, kit, filosofía, newsletter y
   footer para eliminar rigidez cuadrada y verde dominante.
4. Añadir únicamente hooks `data-wf-*` útiles para un futuro export de Webflow.
5. Ejecutar `npm run check`, `npm run build`, revisión visual responsive y
   auditoría read-only con Claude CLI.
6. Presentar una vista local para aprobación. Solo después se considerará
   commit final, push, merge y despliegue mediante `site/scripts/deploy.sh`.

## Restricciones que siguen vigentes

- No cambiar precios, textos de producto, assets reales ni comportamiento de
  compra sin necesidad.
- No usar `object-fit: cover` para fotografías de producto; mantener
  `contain`, centrado y derivados normalizados.
- No usar `rsync`, overlays de tarball ni deploy desde el worktree antiguo.
- No desplegar antes de aprobación visual explícita.
