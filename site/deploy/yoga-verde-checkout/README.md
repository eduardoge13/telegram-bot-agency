# Checkout de Yoga Verde (Stripe) — pendiente de llaves

El sitio de Yoga Verde es estático (Astro `output: "static"`, servido por nginx
dentro del contenedor `blueskytravel-site`). Stripe Checkout necesita crear la
sesión de pago **del lado del servidor**, porque la llave secreta nunca puede
viajar al navegador.

El frontend ya está listo: `public/yoga-verde/shop.js` → `startCheckout()` hace
`POST /api/yoga-verde/checkout` con el carrito y redirige a la URL que le
regrese. Falta únicamente levantar ese endpoint.

## Lo que falta (cuando haya llaves)

1. Crear la cuenta de Stripe de Yoga Verde y obtener:
   - `STRIPE_SECRET_KEY` (empieza con `sk_test_…` para pruebas, `sk_live_…` real)
   - `STRIPE_WEBHOOK_SECRET` (para confirmar pagos)
2. Desplegar `server.js` (en esta carpeta) como un servicio chico en el VPS,
   igual que los otros de `/docker/`, con esas variables en su `.env`.
3. Añadir en `deploy/nginx.conf` el proxy para que `/api/yoga-verde/` apunte a
   ese servicio, de modo que el sitio estático y el checkout compartan dominio
   (evita CORS y cookies de terceros).

## Decisión pendiente

El precio se toma **del servidor**, no del navegador: el endpoint vuelve a leer
`yoga-verde-store.js` y calcula el total él mismo. Esto es a propósito — si el
precio viniera del cliente, cualquiera podría editar el carrito en el navegador
y pagar $1. No cambiar ese comportamiento.
