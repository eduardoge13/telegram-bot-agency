export const ANNOUNCEMENT =
  "Envío consciente gratis desde $999 MXN · 10% en tu primera cosecha";

export const FREE_SHIPPING_THRESHOLD = 999;
export const SHIPPING_FLAT = 149;
export const TAX_RATE = 0.16;

export const PRODUCTS = [
  {
    id: "ashwagandha-vital",
    kind: "product",
    badge: "Más vendido",
    name: "Ashwagandha Vital",
    price: 349,
    image: "/yoga-verde/assets/shop/ashwagandha-vital.png",
    use: "energia",
    useLabel: "Energía y vitalidad",
    type: "raiz",
    typeLabel: "Raíz",
    origin: "andes",
    originLabel: "Andes Septentrionales",
    tags: ["adaptógeno", "ritual diario", "claridad", "raíces"],
    short: "Fortaleza botánica para días amplios y mente serena.",
    description:
      "Una raíz adaptógena pensada para rituales de enfoque estable, con una presencia cálida que acompaña mañanas largas y jornadas con intención.",
    benefits: [
      "Uso tradicional para sostener el ritmo diario con temple.",
      "Perfil botánico curado para rituales matinales o de media tarde.",
      "Origen de altura con cosecha ética y lotes pequeños.",
    ],
    instructions:
      "Mezcla 1 cucharadita en bebida tibia, leche vegetal o smoothie. Úsala en tu ritual diario de forma gradual.",
    rating: 4.9,
    reviewsCount: 182,
    featured: true,
  },
  {
    id: "curcuma-del-sol",
    kind: "product",
    badge: "Cosecha limitada",
    name: "Cúrcuma del Sol",
    price: 289,
    image: "/yoga-verde/assets/shop/curcuma-del-sol.png",
    use: "inmunidad",
    useLabel: "Inmunidad estacional",
    type: "raiz",
    typeLabel: "Raíz",
    origin: "selva",
    originLabel: "Selva Amazónica",
    tags: ["dorado", "bienestar consciente", "estacional", "cosecha ética"],
    short: "Un dorado terroso para rituales de temporada y cocina botánica.",
    description:
      "Cúrcuma seleccionada por su carácter cálido y terroso, ideal para acompañar temporadas de cambio y recetas vivas con origen botánico claro.",
    benefits: [
      "Uso tradicional en infusiones, caldos y bebidas doradas.",
      "Aporta calidez y profundidad al ritual culinario cotidiano.",
      "Curaduría enfocada en frescura y trazabilidad.",
    ],
    instructions:
      "Agrega 1 cucharadita a bebidas calientes, sopas o mezclas con miel. Combínala con grasa vegetal para un ritual más envolvente.",
    rating: 4.8,
    reviewsCount: 127,
    featured: true,
  },
  {
    id: "raiz-de-valeriana",
    kind: "product",
    badge: "Nuevo",
    name: "Raíz de Valeriana",
    price: 329,
    image: "/yoga-verde/assets/shop/raiz-de-valeriana.png",
    use: "relajacion",
    useLabel: "Relajación profunda",
    type: "raiz",
    typeLabel: "Raíz",
    origin: "altiplano",
    originLabel: "Altiplano Central",
    tags: ["noche", "ritual de descanso", "raíces", "calma"],
    short: "Raíz de noche lenta para bajar el ritmo con suavidad.",
    description:
      "Una raíz nocturna para rituales de cierre, pensada para quienes buscan bajar revoluciones y preparar una atmósfera de descanso consciente.",
    benefits: [
      "Uso tradicional en rituales nocturnos y pausas intencionales.",
      "Ideal para acompañar infusiones cálidas antes de dormir.",
      "Perfil aromático terroso y profundo.",
    ],
    instructions:
      "Infusiona media cucharadita en agua caliente durante 8 a 10 minutos. Disfrútala en un momento sin prisa al final del día.",
    rating: 4.7,
    reviewsCount: 96,
    featured: true,
  },
  {
    id: "maca-de-altura",
    kind: "product",
    badge: "Más vendido",
    name: "Maca de Altura",
    price: 379,
    image: "/yoga-verde/assets/shop/maca-de-altura.png",
    use: "energia",
    useLabel: "Energía y vitalidad",
    type: "extracto",
    typeLabel: "Extracto",
    origin: "andes",
    originLabel: "Andes Septentrionales",
    tags: ["ritual matinal", "vitalidad", "altiplano", "extracto"],
    short: "Extracto andino para una vitalidad constante y sin estridencias.",
    description:
      "Maca de altura en formato listo para mezclar, con textura fina y perfil terroso para rituales de impulso estable y bienestar consciente.",
    benefits: [
      "Uso tradicional para mañanas activas y procesos de exigencia prolongada.",
      "Textura amable para bebidas, bowls o mezclas vegetales.",
      "Curaduría de origen andino con comercio atento.",
    ],
    instructions:
      "Mezcla 1 cucharadita en leche vegetal, avena o batido. Empieza con una porción pequeña y ajusta a tu ritual diario.",
    rating: 4.9,
    reviewsCount: 204,
    featured: true,
  },
  {
    id: "diente-de-leon",
    kind: "product",
    badge: "Cosecha limitada",
    name: "Diente de León",
    price: 219,
    image: "/yoga-verde/assets/shop/diente-de-leon.png",
    use: "limpieza",
    useLabel: "Limpieza y renovación",
    type: "hoja",
    typeLabel: "Hoja",
    origin: "selva",
    originLabel: "Selva Amazónica",
    tags: ["limpieza", "renovación", "hoja", "bienestar consciente"],
    short: "Una hoja clara para rituales de renovación y cocina verde.",
    description:
      "Hoja seleccionada para acompañar cambios de ciclo, con un carácter fresco y un lugar natural dentro de rutinas ligeras y conscientes.",
    benefits: [
      "Uso tradicional en rituales de renovación suave.",
      "Se integra bien a infusiones y mezclas verdes ligeras.",
      "Cosecha ética con lectura estacional.",
    ],
    instructions:
      "Infusiona una cucharadita o úsala como mezcla suave en tisanas. Acompáñala con agua y un ritmo diario amable.",
    rating: 4.7,
    reviewsCount: 88,
    featured: false,
  },
];

export const KITS = [
  {
    id: "kit-energia",
    kind: "kit",
    badge: "Kit",
    name: "Kit Energía",
    price: 799,
    image: "/yoga-verde/assets/image-01.png",
    use: "energia",
    useLabel: "Energía y vitalidad",
    type: "kit",
    typeLabel: "Kit curado",
    origin: "curaduria",
    originLabel: "Curaduría Yoga Verde",
    tags: ["kit", "ritual matinal", "energía", "best seller"],
    short: "Ashwagandha Vital + Maca de Altura para un arranque con centro.",
    description:
      "Una dupla pensada para rituales matinales con raíz y extracto: impulso estable, textura amable y un inicio de día más intencional.",
    benefits: [
      "Incluye Ashwagandha Vital y Maca de Altura.",
      "Pensado para rituales de enfoque y constancia.",
      "Precio de kit con ahorro frente a piezas individuales.",
    ],
    instructions:
      "Alterna ambas piezas durante la semana o combínalas en mañanas clave. Empieza por porciones pequeñas.",
    rating: 4.8,
    reviewsCount: 54,
    featured: true,
  },
  {
    id: "kit-relajacion",
    kind: "kit",
    badge: "Kit",
    name: "Kit Relajación",
    price: 759,
    image: "/yoga-verde/assets/image-02.png",
    use: "relajacion",
    useLabel: "Relajación profunda",
    type: "kit",
    typeLabel: "Kit curado",
    origin: "curaduria",
    originLabel: "Curaduría Yoga Verde",
    tags: ["kit", "noche", "descanso", "ritual lento"],
    short: "Valeriana, lavanda visual y una pausa diseñada para bajar el día.",
    description:
      "Una curaduría para noches de ritual lento, con raíz terrosa y una narrativa visual más suave para acompañar el cierre del día.",
    benefits: [
      "Incluye Raíz de Valeriana y una guía breve de ritual nocturno.",
      "Ideal para una rutina de desconexión consciente.",
      "Curaduría cálida para regalar o empezar un nuevo hábito.",
    ],
    instructions:
      "Prepáralo por la noche, acompáñalo con luz tenue y deja que el ritual marque el cierre de la jornada.",
    rating: 4.8,
    reviewsCount: 41,
    featured: false,
  },
  {
    id: "kit-inmunidad",
    kind: "kit",
    badge: "Kit",
    name: "Kit Inmunidad",
    price: 739,
    image: "/yoga-verde/assets/image-03.png",
    use: "inmunidad",
    useLabel: "Inmunidad estacional",
    type: "kit",
    typeLabel: "Kit curado",
    origin: "curaduria",
    originLabel: "Curaduría Yoga Verde",
    tags: ["kit", "temporada", "inmunidad", "cosecha"],
    short: "Una selección botánica de temporada para acompañar cambios de clima.",
    description:
      "Ritual pensado para semanas de transición, con una raíz cálida, cocina botánica y una experiencia de compra más simple.",
    benefits: [
      "Incluye Cúrcuma del Sol y sugerencias de uso estacional.",
      "Pensado para acompañar recetas y bebidas tibias.",
      "Formato de regalo listo para sumar al carrito.",
    ],
    instructions:
      "Úsalo en bebidas doradas, caldos o mezclas con miel. Mantén una rutina suave durante la temporada.",
    rating: 4.7,
    reviewsCount: 38,
    featured: false,
  },
  {
    id: "kit-limpieza",
    kind: "kit",
    badge: "Kit",
    name: "Kit Limpieza",
    price: 699,
    image: "/yoga-verde/assets/image-04.png",
    use: "limpieza",
    useLabel: "Limpieza y renovación",
    type: "kit",
    typeLabel: "Kit curado",
    origin: "curaduria",
    originLabel: "Curaduría Yoga Verde",
    tags: ["kit", "renovación", "hojas", "ritual verde"],
    short: "Una entrada amable para cambios de ciclo y bienestar consciente.",
    description:
      "Kit para semanas de ajuste y renovación, con una hoja clara y un relato amable para quienes quieren comprar fácil y empezar suave.",
    benefits: [
      "Incluye Diente de León y una secuencia breve para el ritual de mañana.",
      "Ideal para semanas ligeras o reinicios estacionales.",
      "Precio especial para primeras compras.",
    ],
    instructions:
      "Integra la hoja a una tisana ligera por la mañana o en la tarde. Acompaña con hidratación y una rutina simple.",
    rating: 4.7,
    reviewsCount: 33,
    featured: false,
  },
];

export const BENEFIT_ITEMS = [
  {
    icon: "eco",
    title: "Cosecha ética",
    copy: "Trabajamos con lotes pequeños y ritmos que respetan el origen botánico.",
  },
  {
    icon: "package_2",
    title: "Empaque reciclado",
    copy: "Cada pedido viaja en materiales conscientes y listos para proteger la cosecha.",
  },
  {
    icon: "local_florist",
    title: "Plantas seleccionadas",
    copy: "Curaduría enfocada en uso tradicional, trazabilidad y bienestar consciente.",
  },
  {
    icon: "local_shipping",
    title: "Envío seguro",
    copy: "Despachos cuidados para que tu pedido llegue claro, limpio y bien resguardado.",
  },
  {
    icon: "verified_user",
    title: "Compra protegida",
    copy: "Carrito simple, checkout demo transparente y una experiencia fácil de comprar.",
  },
];

export const SHOP_NEEDS = [
  {
    slug: "energia",
    title: "Energía y vitalidad",
    copy: "Raíces y extractos para mañanas con intención, foco y ritmo constante.",
    icon: "bolt",
    image: "/yoga-verde/assets/shop/maca-de-altura.png",
  },
  {
    slug: "relajacion",
    title: "Relajación profunda",
    copy: "Rituales de noche lenta para bajar el día con una narrativa más suave.",
    icon: "bedtime",
    image: "/yoga-verde/assets/shop/raiz-de-valeriana.png",
  },
  {
    slug: "inmunidad",
    title: "Inmunidad estacional",
    copy: "Piezas cálidas de temporada para cocina botánica y bienestar consciente.",
    icon: "health_and_safety",
    image: "/yoga-verde/assets/shop/curcuma-del-sol.png",
  },
  {
    slug: "limpieza",
    title: "Limpieza y renovación",
    copy: "Hojas y rituales verdes para cambios de ciclo ligeros y bien acompañados.",
    icon: "water_drop",
    image: "/yoga-verde/assets/shop/diente-de-leon.png",
  },
];

export const TESTIMONIALS = [
  {
    quote:
      "La tienda se siente clara y confiable. Pude armar mi ritual de mañana en menos de cinco minutos y todo llegó muy cuidado.",
    name: "María P.",
    location: "Monterrey",
  },
  {
    quote:
      "Me gustó que cada pieza explicara su uso tradicional sin exagerar. Compré el kit de relajación y la experiencia fue muy amable.",
    name: "Sofía R.",
    location: "Querétaro",
  },
  {
    quote:
      "Yoga Verde conserva una narrativa editorial hermosa, pero ahora comprar es mucho más fácil. El carrito y los kits hacen sentido.",
    name: "Daniela C.",
    location: "CDMX",
  },
];
