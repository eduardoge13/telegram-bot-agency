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

## Capa móvil interactiva

- El hero admite swipe horizontal en pantallas táctiles; un tap conserva el CTA
  de detalle del producto.
- La selección esencial se convierte en un deck de una tarjeta completa por
  pantalla con `scroll-snap`, dots táctiles, contador 01/03 y la indicación
  “Desliza para explorar”. No se muestra una segunda tarjeta cortada.
- La escena editorial responde al avance del scroll: activa el producto de la
  etapa correspondiente, actualiza el contador y permite tocar cada producto
  para abrir el detalle real.
- El catálogo dinámico de `shop.js` conserva la misma quick view sobre la foto,
  de modo que la interacción no desaparece después del primer render.
- Un indicador terracota de progreso acompaña el scroll global; no bloquea la
  navegación ni altera el layout horizontal.
- Las pruebas móviles confirmaron ancho de documento igual al viewport en
  320×692 y 390×844, detalle abrible/cerrable, carrito accesible y consola sin
  errores.

La implementación usa APIs nativas, `IntersectionObserver`, `requestAnimationFrame`
y CSS `scroll-snap` como equivalente ligero de SplitText/Staggers/ScrollTrigger.
Esto conserva la sensación Webflow sin cargar GSAP en cada visita ni convertir el
flujo de compra en una escena WebGL.

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

La investigación de Webflow también confirmó que su capa actual de Interactions
powered by GSAP ofrece SplitText, Staggers y ScrollTrigger, pero los triggers
específicos de sliders, tabs y navbars requieren JavaScript propio. Yoga Verde
mantiene ese límite deliberadamente: motion editorial en CSS/DOM y lógica de
commerce en JavaScript existente. Referencias: [Webflow GSAP](https://webflow.com/updates/introducing-webflow-interactions-powered-by-gsap),
[triggers y targets](https://help.webflow.com/hc/en-us/articles/42832349989395-Triggers-targets-in-Interactions-with-GSAP)
y [Made in Webflow](https://webflow.com/made-in-webflow).

## Sites/Webflow

No existe `.openai/hosting.json` ni un proyecto Sites existente para Yoga Verde,
por lo que no se creó un sitio paralelo que pudiera fragmentar la fuente de
verdad. El código actual sigue en Astro; los hooks `data-wf-*` quedan listos
para llevar la dirección visual a Webflow cuando el usuario complete el acceso.
