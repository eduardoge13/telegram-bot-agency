# Fotografías del catálogo Yoga Verde

Derivados WebP optimizados a partir de `Catalogo_YogaVerde_NP.pdf`, material
proporcionado por el cliente el 18 de agosto de 2026. Se utilizan únicamente
como fotografía editorial de la marca. El PDF original no se publica ni se
incluye en el paquete de despliegue.

- `ritual-botanico.webp`: composición de colección sobre fondo botánico.
- `agua-micelar-manzanilla.webp`: agua micelar entre manzanilla.
- `contorno-lavanda.webp`: contorno de ojos en escena floral cálida.
- `manos-mango.webp`: crema de manos con mango.
- `mousse-uva.webp`: mousse corporal en escena crema.

## Portada editorial de alta resolución — 2026-08-18

`hero/` contiene principalmente fotografías extraídas de los originales
embebidos en el catálogo, no capturas de sus páginas. Los masters originales
WebP conservan entre 1400 y 1624 px de ancho (hasta 2351 px de alto) y se
codificaron a calidad alta. Cada producto mantiene su etiqueta y fotografía
reales.

Cada master tiene un derivado `*-800.webp`. El hero publica ambos mediante
`srcset`/`sizes`: pantallas pequeñas descargan 800 px cuando es suficiente y
pantallas de alta densidad reciben el master. Esto evita ampliar previews
borrosos sin obligar a todos los teléfonos a descargar el archivo más pesado.

En escritorio, la fotografía y la ficha ocupan columnas independientes para
preservar completa la silueta vertical del envase. En móvil, fotografía y texto
son bloques consecutivos sin superposición. Los archivos históricos en la raíz
de esta carpeta se conservan como derivados de la campaña anterior, pero la
portada vigente consume exclusivamente `hero/`.

### Manteca mango y coco — campaña v2

`manteca-campana-v2.webp` es una edición no destructiva creada con la
herramienta integrada de generación de imágenes a partir de la fotografía real
de la manteca y usando cera/cabello y crema/manos únicamente como referencias
de dirección de arte. La edición cambia la escena por mango, coco y fondo
amarillo; conserva el tarro, la etiqueta y el logotipo. El master generado mide
1138×1382 y su derivado responsive 800×972. Los archivos `manteca.webp` y
`manteca-800.webp` originales permanecen como respaldo y no se sobrescribieron.

La portada aplica una gradación CSS moderada por fotografía (saturación
1.02–1.14 y contraste 1.02–1.04). No se recomprime el master para producir el
color y la animación termina exactamente en la misma gradación, sin el estado
lavado que aparecía durante la transición.
