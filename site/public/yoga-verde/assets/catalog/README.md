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

`hero/` contiene fotografías extraídas de los originales embebidos en el
catálogo, no capturas de sus páginas. Los masters WebP conservan entre 1400 y
1624 px de ancho (hasta 2351 px de alto) y se codificaron a calidad alta. Cada
producto mantiene su etiqueta y fotografía reales; no se usó IA para
reconstruir envases, logotipos ni texto de empaque.

Cada master tiene un derivado `*-800.webp`. El hero publica ambos mediante
`srcset`/`sizes`: pantallas pequeñas descargan 800 px cuando es suficiente y
pantallas de alta densidad reciben el master. Esto evita ampliar previews
borrosos sin obligar a todos los teléfonos a descargar el archivo más pesado.

En escritorio, la fotografía y la ficha ocupan columnas independientes para
preservar completa la silueta vertical del envase. En móvil, fotografía y texto
son bloques consecutivos sin superposición. Los archivos históricos en la raíz
de esta carpeta se conservan como derivados de la campaña anterior, pero la
portada vigente consume exclusivamente `hero/`.
