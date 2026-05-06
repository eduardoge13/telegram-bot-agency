const MONEY = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
});

const PRODUCTS = [
  {
    id: "ashwagandha-vital",
    name: "Ashwagandha Vital",
    price: 24,
    badge: "Edición limitada",
    benefit: "energia",
    benefitLabel: "Energía y vitalidad",
    element: "raiz",
    elementLabel: "Raíz",
    origin: "andes",
    originLabel: "Andes Septentrionales",
    image: "/yoga-verde/assets/shop/ashwagandha-vital.png",
    short: "Fortaleza para el espíritu y calma para la mente inquieta.",
    lore:
      "Una raíz adaptógena recolectada en altura para sostener ciclos intensos sin perder claridad. Se usa cuando el cuerpo necesita vigor, pero la mente todavía exige calma.",
  },
  {
    id: "curcuma-del-sol",
    name: "Cúrcuma del Sol",
    price: 18.5,
    badge: "Inmunidad",
    benefit: "inmunidad",
    benefitLabel: "Inmunidad estacional",
    element: "raiz",
    elementLabel: "Raíz",
    origin: "selva",
    originLabel: "Selva Amazónica",
    image: "/yoga-verde/assets/shop/curcuma-del-sol.png",
    short: "El fuego de la tierra capturado para proteger tu linaje biológico.",
    lore:
      "De tono dorado profundo y carácter cálido, esta cúrcuma se selecciona por su potencia concentrada. Es una pieza de defensa y recuperación en épocas de desgaste.",
  },
  {
    id: "raiz-de-valeriana",
    name: "Raíz de Valeriana",
    price: 21,
    badge: "Sueño",
    benefit: "sueno",
    benefitLabel: "Relajación profunda",
    element: "raiz",
    elementLabel: "Raíz",
    origin: "altiplano",
    originLabel: "Altiplano Central",
    image: "/yoga-verde/assets/shop/raiz-de-valeriana.png",
    short: "Un puente hacia el descanso profundo, cosechada al atardecer.",
    lore:
      "La valeriana trabaja en la frontera entre tensión y reposo. Su perfil se reserva para rituales nocturnos y procesos de desaceleración consciente.",
  },
  {
    id: "maca-de-altura",
    name: "Maca de Altura",
    price: 26,
    badge: "Resistencia",
    benefit: "energia",
    benefitLabel: "Energía y vitalidad",
    element: "raiz",
    elementLabel: "Raíz",
    origin: "andes",
    originLabel: "Andes Septentrionales",
    image: "/yoga-verde/assets/shop/maca-de-altura.png",
    short: "Energía ancestral de los picos andinos. Adaptógeno puro.",
    lore:
      "La maca se integra al catálogo como una raíz de resistencia. Aporta sostén en temporadas de exigencia prolongada, especialmente cuando el cuerpo pide profundidad y no velocidad.",
  },
  {
    id: "diente-de-leon",
    name: "Diente de León",
    price: 15,
    badge: "Depurativo",
    benefit: "depurativo",
    benefitLabel: "Limpieza y renovación",
    element: "hoja",
    elementLabel: "Hoja",
    origin: "selva",
    originLabel: "Selva Amazónica",
    image: "/yoga-verde/assets/shop/diente-de-leon.png",
    short: "Limpieza y renovación desde la raíz. El aliado perfecto para los cambios de ciclo.",
    lore:
      "El diente de león aparece en este herbolario como una pieza de limpieza suave y sostenida. Su energía es clara: abrir espacio y ayudar a que el cuerpo recircule.",
  },
];

const STORAGE_KEY = "yogaVerdeCartV2";

const state = {
  search: "",
  benefitFilters: new Set(),
  elementFilters: new Set(),
  originFilters: new Set(),
  cart: loadCart(),
  detailProductId: null,
};

const els = {
  grid: document.querySelector("[data-products-grid]"),
  empty: document.querySelector("[data-empty-state]"),
  count: document.querySelector("[data-product-count]"),
  search: document.querySelector("[data-search-input]"),
  cartDrawer: document.querySelector("[data-cart-drawer]"),
  cartOverlay: document.querySelector("[data-cart-overlay]"),
  cartItems: document.querySelector("[data-cart-items]"),
  cartEmpty: document.querySelector("[data-cart-empty]"),
  cartCount: document.querySelector("[data-cart-count]"),
  subtotal: document.querySelector("[data-subtotal]"),
  shipping: document.querySelector("[data-shipping]"),
  tax: document.querySelector("[data-tax]"),
  total: document.querySelector("[data-total]"),
  checkout: document.querySelector("[data-checkout]"),
  mobileCta: document.querySelector("[data-mobile-cart-cta]"),
  mobileCount: document.querySelector("[data-mobile-count]"),
  mobileTotal: document.querySelector("[data-mobile-total]"),
  modal: document.querySelector("[data-detail-modal]"),
  modalOverlay: document.querySelector("[data-modal-overlay]"),
  detailBadge: document.querySelector("[data-detail-badge]"),
  detailTitle: document.querySelector("[data-detail-title]"),
  detailDescription: document.querySelector("[data-detail-description]"),
  detailTags: document.querySelector("[data-detail-tags]"),
  detailPrice: document.querySelector("[data-detail-price]"),
  detailImage: document.querySelector("[data-detail-image]"),
  detailAdd: document.querySelector("[data-detail-add]"),
};

function loadCart() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveCart() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state.cart));
}

function formatMoney(value) {
  return MONEY.format(value);
}

function getFilteredProducts() {
  return PRODUCTS.filter((product) => {
    const term = state.search.trim().toLowerCase();
    const matchesSearch =
      !term ||
      [product.name, product.short, product.lore, product.benefitLabel, product.originLabel]
        .join(" ")
        .toLowerCase()
        .includes(term);

    const matchesBenefit =
      state.benefitFilters.size === 0 || state.benefitFilters.has(product.benefit);
    const matchesElement =
      state.elementFilters.size === 0 || state.elementFilters.has(product.element);
    const matchesOrigin =
      state.originFilters.size === 0 || state.originFilters.has(product.origin);

    return matchesSearch && matchesBenefit && matchesElement && matchesOrigin;
  });
}

function cartEntries() {
  return Object.entries(state.cart)
    .map(([id, quantity]) => {
      const product = PRODUCTS.find((item) => item.id === id);
      return product ? { product, quantity } : null;
    })
    .filter(Boolean);
}

function cartTotals() {
  const subtotal = cartEntries().reduce((sum, item) => sum + item.product.price * item.quantity, 0);
  const shipping = subtotal > 0 ? 5 : 0;
  const tax = subtotal * 0.08;
  const total = subtotal + shipping + tax;
  const count = cartEntries().reduce((sum, item) => sum + item.quantity, 0);
  return { subtotal, shipping, tax, total, count };
}

function renderProducts() {
  const filtered = getFilteredProducts();
  els.count.textContent = String(filtered.length);
  els.grid.innerHTML = filtered
    .map(
      (product) => `
      <article class="group overflow-hidden rounded-[28px] bg-surface-container-lowest shadow-parchment transition-transform hover:-translate-y-1">
        <div class="relative overflow-hidden bg-surface-container-low p-4">
          <span class="absolute left-4 top-4 z-10 rounded-full bg-surface px-3 py-1 text-[10px] font-bold uppercase tracking-[0.22em] text-primary">${product.badge}</span>
          <img alt="${product.name}" class="aspect-[5/4] w-full rounded-[22px] object-cover transition-transform duration-500 group-hover:scale-105" src="${product.image}" />
        </div>
        <div class="p-6">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-[11px] uppercase tracking-[0.22em] text-on-surface-variant">${product.elementLabel} • ${product.originLabel}</p>
              <h3 class="mt-2 font-headline text-4xl leading-none text-primary">${product.name}</h3>
            </div>
            <span class="font-headline text-3xl text-secondary">${formatMoney(product.price)}</span>
          </div>
          <p class="mt-4 min-h-[72px] text-sm italic leading-7 text-on-surface-variant">${product.short}</p>
          <div class="mt-6 flex items-center justify-between border-t border-outline-variant/40 pt-5">
            <button class="inline-flex items-center gap-2 text-sm font-semibold text-primary transition-colors hover:text-secondary" data-open-detail="${product.id}" type="button">
              <span class="material-symbols-outlined text-base">auto_stories</span>
              Ver sabiduría
            </button>
            <button class="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-primary text-on-primary transition-colors hover:bg-secondary" data-add="${product.id}" type="button">
              <span class="material-symbols-outlined">add</span>
            </button>
          </div>
        </div>
      </article>
    `
    )
    .join("");

  els.empty.classList.toggle("hidden", filtered.length !== 0);
}

function renderCart() {
  const items = cartEntries();
  const totals = cartTotals();

  els.cartCount.textContent = String(totals.count);
  els.mobileCount.textContent = `${totals.count} ${totals.count === 1 ? "pieza" : "piezas"}`;
  els.mobileTotal.textContent = formatMoney(totals.total);
  els.subtotal.textContent = formatMoney(totals.subtotal);
  els.shipping.textContent = formatMoney(totals.shipping);
  els.tax.textContent = formatMoney(totals.tax);
  els.total.textContent = formatMoney(totals.total);
  els.checkout.disabled = totals.count === 0;

  els.mobileCta.classList.toggle("pointer-events-none", totals.count === 0);
  els.mobileCta.classList.toggle("translate-y-24", totals.count === 0);
  els.mobileCta.classList.toggle("opacity-0", totals.count === 0);
  els.mobileCta.classList.toggle("translate-y-0", totals.count > 0);
  els.mobileCta.classList.toggle("opacity-100", totals.count > 0);

  if (!items.length) {
    els.cartItems.innerHTML = "";
    els.cartEmpty.classList.remove("hidden");
    return;
  }

  els.cartEmpty.classList.add("hidden");
  els.cartItems.innerHTML = items
    .map(
      ({ product, quantity }) => `
      <article class="overflow-hidden rounded-[28px] bg-surface-container-low p-5 shadow-parchment">
        <div class="flex gap-4">
          <img alt="${product.name}" class="h-28 w-28 rounded-[22px] object-cover" src="${product.image}" />
          <div class="flex flex-1 flex-col">
            <div class="flex items-start justify-between gap-4">
              <div>
                <p class="text-[11px] uppercase tracking-[0.22em] text-on-surface-variant">${product.badge}</p>
                <h3 class="mt-2 font-headline text-3xl leading-none text-primary">${product.name}</h3>
                <p class="mt-2 text-sm text-on-surface-variant">${product.originLabel}</p>
              </div>
              <span class="font-headline text-3xl text-primary">${formatMoney(product.price * quantity)}</span>
            </div>
            <div class="mt-4 flex items-center justify-between">
              <div class="inline-flex items-center gap-4 rounded-full bg-surface-container-highest px-4 py-2">
                <button class="text-primary transition-colors hover:text-secondary" data-qty="${product.id}" data-delta="-1" type="button">
                  <span class="material-symbols-outlined text-base">remove</span>
                </button>
                <span class="min-w-4 text-center font-semibold text-primary">${quantity}</span>
                <button class="text-primary transition-colors hover:text-secondary" data-qty="${product.id}" data-delta="1" type="button">
                  <span class="material-symbols-outlined text-base">add</span>
                </button>
              </div>
              <button class="inline-flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.22em] text-on-surface-variant transition-colors hover:text-secondary" data-remove="${product.id}" type="button">
                <span class="material-symbols-outlined text-base">delete</span>
                Eliminar
              </button>
            </div>
          </div>
        </div>
      </article>
    `
    )
    .join("");
}

function syncFilterButtons() {
  document.querySelectorAll("[data-filter-element]").forEach((button) => {
    const active = state.elementFilters.has(button.dataset.filterElement);
    button.className = active
      ? "rounded-full bg-tertiary-container px-4 py-2 text-sm font-medium text-on-tertiary-container transition-colors hover:bg-tertiary hover:text-white"
      : "rounded-full bg-surface-container-highest px-4 py-2 text-sm font-medium text-on-surface-variant transition-colors hover:bg-tertiary-container hover:text-on-tertiary-container";
  });

  document.querySelectorAll("[data-filter-origin]").forEach((button) => {
    const active = state.originFilters.has(button.dataset.filterOrigin);
    button.className = active
      ? "block text-left text-sm text-secondary underline decoration-secondary/30 underline-offset-4"
      : "block text-left text-sm text-on-surface-variant transition-colors hover:text-secondary";
  });
}

function openCart() {
  document.body.classList.add("cart-open");
  els.cartDrawer.classList.remove("translate-x-full");
  els.cartOverlay.classList.remove("pointer-events-none", "opacity-0");
  els.cartOverlay.classList.add("opacity-100");
}

function closeCart() {
  document.body.classList.remove("cart-open");
  els.cartDrawer.classList.add("translate-x-full");
  els.cartOverlay.classList.add("pointer-events-none", "opacity-0");
  els.cartOverlay.classList.remove("opacity-100");
}

function openDetail(productId) {
  const product = PRODUCTS.find((item) => item.id === productId);
  if (!product) return;

  state.detailProductId = productId;
  els.detailBadge.textContent = `${product.badge} • ${product.elementLabel}`;
  els.detailTitle.textContent = product.name;
  els.detailDescription.textContent = product.lore;
  els.detailImage.src = product.image;
  els.detailImage.alt = product.name;
  els.detailPrice.textContent = formatMoney(product.price);
  els.detailTags.innerHTML = [product.benefitLabel, product.originLabel, product.elementLabel]
    .map(
      (tag) =>
        `<span class="rounded-full bg-surface-container-low px-4 py-2 text-sm font-medium text-on-surface-variant">${tag}</span>`
    )
    .join("");

  els.modal.classList.remove("pointer-events-none", "scale-95", "opacity-0");
  els.modalOverlay.classList.remove("pointer-events-none", "opacity-0");
  els.modalOverlay.classList.add("opacity-100");
}

function closeDetail() {
  state.detailProductId = null;
  els.modal.classList.add("pointer-events-none", "scale-95", "opacity-0");
  els.modalOverlay.classList.add("pointer-events-none", "opacity-0");
  els.modalOverlay.classList.remove("opacity-100");
}

function addToCart(productId, quantity = 1) {
  state.cart[productId] = (state.cart[productId] || 0) + quantity;
  saveCart();
  renderCart();
  openCart();
}

function updateQuantity(productId, delta) {
  const next = (state.cart[productId] || 0) + delta;
  if (next <= 0) {
    delete state.cart[productId];
  } else {
    state.cart[productId] = next;
  }
  saveCart();
  renderCart();
}

function clearFilters() {
  state.search = "";
  state.benefitFilters.clear();
  state.elementFilters = new Set();
  state.originFilters.clear();
  els.search.value = "";
  document.querySelectorAll("[data-filter-benefit]").forEach((input) => {
    input.checked = false;
  });
  syncFilterButtons();
  renderProducts();
}

function checkoutDemo() {
  const totals = cartTotals();
  const summary = cartEntries()
    .map(({ product, quantity }) => `${quantity}x ${product.name}`)
    .join(", ");

  window.alert(
    `Pedido preparado: ${summary}\n\nTotal estimado: ${formatMoney(
      totals.total
    )}\n\nSiguiente paso: conectar checkout real o WhatsApp de ventas.`
  );
}

document.addEventListener("click", (event) => {
  const target = event.target.closest("button, a");
  if (!target) return;

  if (target.matches("[data-add]")) {
    addToCart(target.dataset.add);
  }

  if (target.matches("[data-open-cart]")) {
    openCart();
  }

  if (target.matches("[data-close-cart]") || target.matches("[data-cart-overlay]")) {
    closeCart();
  }

  if (target.matches("[data-open-detail]")) {
    openDetail(target.dataset.openDetail);
  }

  if (target.matches("[data-close-detail]") || target.matches("[data-modal-overlay]")) {
    closeDetail();
  }

  if (target.matches("[data-detail-add]") && state.detailProductId) {
    addToCart(state.detailProductId);
    closeDetail();
  }

  if (target.matches("[data-qty]")) {
    updateQuantity(target.dataset.qty, Number(target.dataset.delta));
  }

  if (target.matches("[data-remove]")) {
    delete state.cart[target.dataset.remove];
    saveCart();
    renderCart();
  }

  if (target.matches("[data-filter-element]")) {
    const value = target.dataset.filterElement;
    if (state.elementFilters.has(value)) {
      state.elementFilters.delete(value);
    } else {
      state.elementFilters.add(value);
    }
    syncFilterButtons();
    renderProducts();
  }

  if (target.matches("[data-filter-origin]")) {
    const value = target.dataset.filterOrigin;
    if (state.originFilters.has(value)) {
      state.originFilters.delete(value);
    } else {
      state.originFilters.add(value);
    }
    syncFilterButtons();
    renderProducts();
  }

  if (target.matches("[data-clear-filters]")) {
    clearFilters();
  }

  if (target.matches("[data-checkout]")) {
    checkoutDemo();
  }

  if (target.matches("[data-scroll-to]")) {
    const section = document.getElementById(target.dataset.scrollTo);
    if (section) {
      section.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }
});

document.querySelectorAll("[data-filter-benefit]").forEach((input) => {
  input.addEventListener("change", () => {
    if (input.checked) {
      state.benefitFilters.add(input.dataset.filterBenefit);
    } else {
      state.benefitFilters.delete(input.dataset.filterBenefit);
    }
    renderProducts();
  });
});

els.search.addEventListener("input", () => {
  state.search = els.search.value;
  renderProducts();
});

els.cartOverlay.addEventListener("click", closeCart);
els.modalOverlay.addEventListener("click", closeDetail);

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeCart();
    closeDetail();
  }
});

syncFilterButtons();
renderProducts();
renderCart();
