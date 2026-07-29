// Checkout de Yoga Verde — crea sesiones de Stripe Checkout.
//
// Los precios se leen SIEMPRE del catálogo del servidor, nunca del cuerpo de
// la petición: el navegador solo manda ids y cantidades. Si el precio viniera
// del cliente, cualquiera podría editarlo y pagar de menos.
//
// Variables requeridas (ver README.md):
//   STRIPE_SECRET_KEY   sk_test_… / sk_live_…
//   PUBLIC_SITE_URL     https://yoga-verde.srv1175749.hstgr.cloud
//   PORT                (opcional, default 8095)

import http from "node:http";
import Stripe from "stripe";
import { PRODUCTS, KITS, FREE_SHIPPING_THRESHOLD, SHIPPING_FLAT } from "./catalog.mjs";

const SECRET = process.env.STRIPE_SECRET_KEY;
const SITE_URL = process.env.PUBLIC_SITE_URL || "https://yoga-verde.srv1175749.hstgr.cloud";
const PORT = Number(process.env.PORT) || 8095;

const stripe = SECRET ? new Stripe(SECRET) : null;
const CATALOG = new Map([...PRODUCTS, ...KITS].map((item) => [item.id, item]));

const json = (res, status, body) => {
  res.writeHead(status, { "Content-Type": "application/json" });
  res.end(JSON.stringify(body));
};

const server = http.createServer(async (req, res) => {
  if (req.method !== "POST" || !req.url.endsWith("/checkout")) {
    return json(res, 404, { error: "Not found" });
  }

  if (!stripe) {
    // Sin llaves configuradas todavía: lo decimos claro en el log del server
    // en vez de fallar con un error genérico de Stripe.
    console.error("[yoga-verde] STRIPE_SECRET_KEY no está configurada.");
    return json(res, 503, { error: "Checkout no configurado." });
  }

  let payload = "";
  req.on("data", (chunk) => {
    payload += chunk;
    if (payload.length > 1e5) req.destroy();
  });

  req.on("end", async () => {
    try {
      const { items } = JSON.parse(payload || "{}");
      if (!Array.isArray(items) || !items.length) {
        return json(res, 400, { error: "Carrito vacío." });
      }

      const lineItems = [];
      let subtotal = 0;

      for (const entry of items) {
        const item = CATALOG.get(entry.id);
        const quantity = Math.max(1, Math.min(99, Number(entry.quantity) || 1));
        if (!item) return json(res, 400, { error: `Producto desconocido: ${entry.id}` });

        subtotal += item.price * quantity;
        lineItems.push({
          quantity,
          price_data: {
            currency: "mxn",
            unit_amount: Math.round(item.price * 100),
            product_data: {
              name: item.scent ? `${item.name} · ${item.scent}` : item.name,
              images: item.image ? [`${SITE_URL}${item.image}`] : undefined,
            },
          },
        });
      }

      const shipping = subtotal >= FREE_SHIPPING_THRESHOLD ? 0 : SHIPPING_FLAT;

      const session = await stripe.checkout.sessions.create({
        mode: "payment",
        line_items: lineItems,
        success_url: `${SITE_URL}/yoga-verde/?pedido=confirmado`,
        cancel_url: `${SITE_URL}/yoga-verde/?pedido=cancelado`,
        shipping_address_collection: { allowed_countries: ["MX"] },
        shipping_options: [
          {
            shipping_rate_data: {
              type: "fixed_amount",
              display_name: shipping === 0 ? "Envío gratis" : "Envío nacional",
              fixed_amount: { amount: Math.round(shipping * 100), currency: "mxn" },
            },
          },
        ],
      });

      return json(res, 200, { url: session.url });
    } catch (error) {
      console.error("[yoga-verde] checkout:", error);
      return json(res, 500, { error: "No se pudo crear la sesión de pago." });
    }
  });
});

server.listen(PORT, () => {
  console.log(`[yoga-verde] checkout escuchando en :${PORT}`);
  if (!stripe) console.warn("[yoga-verde] Sin STRIPE_SECRET_KEY — el endpoint responderá 503.");
});
