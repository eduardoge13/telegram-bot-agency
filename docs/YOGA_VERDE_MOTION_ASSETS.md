# Yoga Verde — motion y assets editoriales

## Asset integrado

`site/public/yoga-verde/assets/campaign/editorial-studio-backdrop.webp`

- Origen: generado con ImageGen para Yoga Verde.
- Uso: fondo atmosférico del hero y del bloque editorial de ritual.
- Dimensión: 1672 × 941 px.
- Peso: aproximadamente 98 KB en WebP.
- Contenido: estudio cálido con tela crema, yeso mate y espacio negativo.
- No contiene productos, etiquetas, logotipos, texto ni marcas inventadas.
- Los envases que aparecen encima siguen siendo los derivados reales de
  `products/display/*.webp`.

## Prompt final

> Create a high-end editorial beauty campaign background that can sit behind
> real product cutouts added separately in HTML/CSS. A quiet warm-white studio
> with sculptural matte cream fabric, subtle folded forms, a soft plaster
> surface, generous negative space, diffused daylight, muted terracotta and
> cream, no products, packaging, labels, logos, letters, words, people, hands
> or watermark.

## Motion aplicado

- Hero con parallax de puntero en escritorio y desplazamiento de fondo reducido.
- Barrido de luz editorial durante el primer ciclo del hero.
- Slider real de productos con transición direccional existente.
- Header sticky que se compacta después del primer scroll.
- Reveals lentos con stagger de cards.
- Bloque editorial con profundidad por capas: backdrop, wash, copy y productos.
- Hover de tarjetas con desplazamiento, zoom mínimo y barrido de luz.
- Todos los efectos se desactivan con `prefers-reduced-motion`.

## Referencias externas

La dirección se estudió visualmente en [SKIMS México](https://www.skims-mexico.com/)
y [Sustain Yourself](https://www.sustainyourselfshop.com/). Se tomaron patrones
generales —hero editorial, navegación compacta, bloques de campaña, best-sellers
y franja de beneficios—, no código, assets ni animaciones propietarias.

Para una futura pieza de video se identificaron catálogos de stock con licencia
comercial, como [Pexels skincare videos](https://www.pexels.com/search/videos/skincare/)
y [Mixkit skincare videos](https://mixkit.co/free-stock-video/skincare/). No se
integró un video remoto todavía: un clip sin la identidad Yoga Verde puede
reducir autenticidad y un MP4 pesado puede perjudicar móvil. La siguiente pieza
debe descargarse, optimizarse, registrar su URL/licencia y usarse con poster,
`muted`, `playsinline`, `loop`, carga diferida y fallback estático.

## Sites/Webflow

No existe `.openai/hosting.json` ni un proyecto Sites existente para Yoga Verde,
por lo que no se creó un sitio paralelo que pudiera fragmentar la fuente de
verdad. El código actual sigue en Astro; los hooks `data-wf-*` quedan listos
para llevar la dirección visual a Webflow cuando el usuario complete el acceso.
