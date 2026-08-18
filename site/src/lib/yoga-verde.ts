import {
  ACCENT_COLORS,
  ANNOUNCEMENT,
  FREE_SHIPPING_THRESHOLD,
  KITS,
  PRODUCTS,
  SHIPPING_FLAT,
  TAX_RATE,
} from "../data/yoga-verde-store";

export const money = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
  maximumFractionDigits: 0,
});

export const formatMoney = (value: number) => money.format(value);

export const displayImage = (path: string) =>
  path.replace("/products/", "/products/display/").replace(/\.jpg$/i, ".webp");

export const products = PRODUCTS.map((product) => ({
  ...product,
  image: displayImage(product.image),
}));

export const kits = KITS.map((kit) => ({
  ...kit,
  image: displayImage(kit.image),
}));

export type YogaProduct = (typeof products)[number];
export type YogaKit = (typeof kits)[number];

export const productById = new Map(products.map((product) => [product.id, product]));
export const kitById = new Map(kits.map((kit) => [kit.id, kit]));

export const productUrl = (product: { id: string }) => `/yoga-verde/productos/${product.id}`;
export const kitUrl = (kit: { id: string }) => `/yoga-verde/kits/${kit.id}`;

export const kitProducts = (kit: { items?: string[] }) =>
  (kit.items || []).map((id) => productById.get(id)).filter(Boolean) as YogaProduct[];

export const campaignMedia: Record<
  string,
  { src: string; width: number; height: number; position?: string }
> = {
  "desmaquillante-almendra-dulce": { src: "/yoga-verde/assets/catalog/hero/desmaquillante.webp", width: 1568, height: 2351, position: "center 68%" },
  "agua-micelar-manzanilla": { src: "/yoga-verde/assets/catalog/hero/agua-micelar.webp", width: 1624, height: 2166, position: "center 58%" },
  "contorno-de-ojos-lavanda": { src: "/yoga-verde/assets/catalog/hero/contorno.webp", width: 1400, height: 1700 },
  "mousse-corporal-uva": { src: "/yoga-verde/assets/catalog/hero/mousse.webp", width: 1400, height: 1700 },
  "crema-manos-mango": { src: "/yoga-verde/assets/catalog/hero/crema-manos.webp", width: 1400, height: 1700 },
  "manteca-mango-coco": { src: "/yoga-verde/assets/catalog/hero/manteca-campana-v2.webp", width: 1138, height: 1382 },
  "desodorante-lavanda-toronja": { src: "/yoga-verde/assets/catalog/hero/desodorante-lavanda.webp", width: 1400, height: 1700 },
  "aceite-cabello-seco-coco-argan": { src: "/yoga-verde/assets/catalog/hero/aceite-cabello-seco.webp", width: 1400, height: 1700 },
  "aceite-cabello-graso-uva": { src: "/yoga-verde/assets/catalog/hero/aceite-cabello-graso.webp", width: 1400, height: 1700 },
  "cera-cabello-ceja": { src: "/yoga-verde/assets/catalog/hero/cera-cabello.webp", width: 1400, height: 1700 },
  "vela-soya-vainilla": { src: "/yoga-verde/assets/catalog/hero/vela-vainilla.webp", width: 1400, height: 1700 },
  "vela-soya-coco": { src: "/yoga-verde/assets/catalog/hero/vela-coco.webp", width: 1400, height: 1700 },
  "vela-soya-bergamota": { src: "/yoga-verde/assets/catalog/hero/vela-bergamota.webp", width: 1400, height: 1700 },
};

export const collections = [
  {
    slug: "rostro",
    label: "Rostro",
    title: "Rituales para el rostro",
    copy: "Limpieza, hidratación y cuidado diario con manzanilla, lavanda, almendra y chabacano.",
    types: ["facial", "labial"],
    imageId: "agua-micelar-manzanilla",
    accent: "terracotta",
  },
  {
    slug: "cuerpo",
    label: "Cuerpo",
    title: "Texturas para el cuerpo",
    copy: "Mango, coco y uva en fórmulas de hidratación profunda y absorción confortable.",
    types: ["corporal"],
    imageId: "crema-manos-mango",
    accent: "mango",
  },
  {
    slug: "cabello",
    label: "Cabello",
    title: "Cuidado para cabello y cejas",
    copy: "Aceites nutritivos y cera de abeja con romero para nutrir, controlar y dar forma.",
    types: ["cabello"],
    imageId: "cera-cabello-ceja",
    accent: "honey",
  },
  {
    slug: "hogar",
    label: "Hogar",
    title: "Aromas para el hogar",
    copy: "Velas de soya con vainilla, coco y bergamota para acompañar cada momento del día.",
    types: ["aromaterapia"],
    imageId: "vela-soya-bergamota",
    accent: "sage",
  },
] as const;

export type YogaCollection = (typeof collections)[number];

export const productsForCollection = (collection: YogaCollection) =>
  products.filter((product) => collection.types.includes(product.type as never));

export const featuredProducts = [
  "cera-cabello-ceja",
  "crema-manos-mango",
  "agua-micelar-manzanilla",
  "manteca-mango-coco",
].map((id) => productById.get(id)).filter(Boolean) as YogaProduct[];

export const storeData = {
  announcement: ANNOUNCEMENT,
  freeShippingThreshold: FREE_SHIPPING_THRESHOLD,
  shippingFlat: SHIPPING_FLAT,
  taxRate: TAX_RATE,
  products,
  kits,
  accentColors: ACCENT_COLORS,
};

export {
  ACCENT_COLORS,
  ANNOUNCEMENT,
  FREE_SHIPPING_THRESHOLD,
  SHIPPING_FLAT,
  TAX_RATE,
};
