const dataNode = document.getElementById("yoga-verde-data");

if (!dataNode) {
  throw new Error("Yoga Verde data payload not found.");
}

const store = JSON.parse(dataNode.textContent || "{}");

const PRODUCTS = Array.isArray(store.products) ? store.products : [];
const KITS = Array.isArray(store.kits) ? store.kits : [];
const ALL_ITEMS = [...PRODUCTS, ...KITS];
const ITEM_INDEX = new Map(ALL_ITEMS.map((item) => [item.id, item]));
const ACCENT_COLORS = store.accentColors && typeof store.accentColors === "object" ? store.accentColors : {};

function accentOf(item) {
  return (item && ACCENT_COLORS[item.use]) || ACCENT_COLORS.terracota || "#C06145";
}

const FREE_SHIPPING_THRESHOLD = Number(store.freeShippingThreshold) || 999;
const SHIPPING_FLAT = Number(store.shippingFlat) || 149;
const TAX_RATE = Number(store.taxRate) || 0.16;

const STORAGE_KEY = "yogaVerdeCartV3";
const MONEY = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
  maximumFractionDigits: 0,
});

const useLabelMap = new Map(PRODUCTS.map((product) => [product.use, product.useLabel]));
const typeLabelMap = new Map(PRODUCTS.map((product) => [product.type, product.typeLabel]));

let lastDetailTrigger = null;

const state = {
  search: "",
  useFilters: new Set(),
  typeFilters: new Set(),
  cart: loadCart(),
  detailItemId: null,
  cartOpen: false,
  detailOpen: false,
  filtersOpen: false,
};

const els = {
  grid: document.querySelector("[data-products-grid]"),
  empty: document.querySelector("[data-empty-state]"),
  counts: document.querySelectorAll("[data-product-count], [data-product-count-filtered]"),
  activeFilters: document.querySelector("[data-active-filters]"),
  search: document.querySelector("[data-search-input]"),
  filtersDrawer: document.querySelector("[data-filters-drawer]"),
  filtersOverlay: document.querySelector("[data-filters-overlay]"),
  cartDrawer: document.querySelector("[data-cart-drawer]"),
  cartOverlay: document.querySelector("[data-cart-overlay]"),
  cartItems: document.querySelector("[data-cart-items]"),
  cartEmpty: document.querySelector("[data-cart-empty]"),
  cartCounts: document.querySelectorAll("[data-cart-count]"),
  subtotal: document.querySelector("[data-subtotal]"),
  shipping: document.querySelector("[data-shipping]"),
  tax: document.querySelector("[data-tax]"),
  total: document.querySelector("[data-total]"),
  checkout: document.querySelector("[data-checkout]"),
  shippingMessage: document.querySelector("[data-shipping-message]"),
  shippingProgress: document.querySelector("[data-shipping-progress]"),
  cartUpsell: document.querySelector("[data-cart-upsell]"),
  modal: document.querySelector("[data-detail-modal]"),
  modalOverlay: document.querySelector("[data-modal-overlay]"),
  pageContent: document.querySelector("[data-page-content]"),
  detailBadge: document.querySelector("[data-detail-badge]"),
  detailTitle: document.querySelector("[data-detail-title]"),
  detailDescription: document.querySelector("[data-detail-description]"),
  detailTags: document.querySelector("[data-detail-tags]"),
  detailBenefits: document.querySelector("[data-detail-benefits]"),
  detailInstructions: document.querySelector("[data-detail-instructions]"),
  detailScent: document.querySelector("[data-detail-scent]"),
  detailBody: document.querySelector(".detail-body"),
  detailBenefitsBlock: document.querySelector("[data-detail-benefits-block]"),
  detailInstructionsBlock: document.querySelector("[data-detail-instructions-block]"),
  detailPrice: document.querySelector("[data-detail-price]"),
  detailImage: document.querySelector("[data-detail-image]"),
  detailAdd: document.querySelector("[data-detail-add]"),
};

const PILL_ACTIVE_CLASS = "filter-option is-active";
const PILL_INACTIVE_CLASS = "filter-option";

function loadCart() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") return {};

    return Object.fromEntries(
      Object.entries(parsed)
        .filter(([id]) => ITEM_INDEX.has(id))
        .map(([id, quantity]) => [id, Math.max(0, Number(quantity) || 0)])
        .filter(([, quantity]) => quantity > 0),
    );
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

function normalizeText(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function productSearchHaystack(product) {
  return normalizeText([
    product.name,
    product.short,
    product.description,
    product.useLabel,
    product.typeLabel,
    ...(product.tags || []),
    ...(product.benefits || []),
    product.instructions,
  ].join(" "));
}

function getFilteredProducts() {
  const term = normalizeText(state.search.trim());

  return PRODUCTS.filter((product) => {
    const matchesSearch = !term || productSearchHaystack(product).includes(term);
    const matchesUse =
      state.useFilters.size === 0 || state.useFilters.has(product.use);
    const matchesType =
      state.typeFilters.size === 0 || state.typeFilters.has(product.type);
    return matchesSearch && matchesUse && matchesType;
  });
}

function cartEntries() {
  return Object.entries(state.cart)
    .map(([id, quantity]) => {
      const item = ITEM_INDEX.get(id);
      return item ? { item, quantity } : null;
    })
    .filter(Boolean);
}

function cartTotals() {
  const subtotal = cartEntries().reduce(
    (sum, entry) => sum + entry.item.price * entry.quantity,
    0,
  );
  const shipping =
    subtotal === 0 ? 0 : subtotal >= FREE_SHIPPING_THRESHOLD ? 0 : SHIPPING_FLAT;
  const tax = Math.round(subtotal * TAX_RATE);
  const total = subtotal + shipping + tax;
  const count = cartEntries().reduce((sum, entry) => sum + entry.quantity, 0);
  return { subtotal, shipping, tax, total, count };
}

// Un solo lugar decide si un valor es pintable. Evita que un campo vacío se
// convierta en "undefined", en un separador suelto (" · Cuidado facial") o en
// una pill en blanco.
function clean(value) {
  if (value === undefined || value === null) return "";
  const text = String(value).trim();
  return text === "undefined" || text === "null" ? "" : text;
}

// Muestra el elemento solo si su contenido existe; si no, lo oculta entero
// para no dejar un encabezado sin cuerpo.
function setText(el, value) {
  if (!el) return "";
  const text = clean(value);
  el.textContent = text;
  return text;
}

function toggleBlock(el, hasContent) {
  if (el) el.hidden = !hasContent;
}

function detailTagMarkup(label) {
  return `<span class="detail-tag">${escapeHtml(label)}</span>`;
}

function catalogCardMarkup(product) {
  const accent = accentOf(product);
  return `
    <article class="product-card group" style="--accent: ${escapeHtml(accent)}">
      <div class="product-image-frame relative">
        ${product.badge ? `<span class="product-badge absolute left-4 top-4 z-10">${escapeHtml(product.badge)}</span>` : ""}
        <img alt="${escapeHtml(product.name)} ${escapeHtml(product.scent || "")}" class="product-media aspect-square w-full transition duration-500 group-hover:scale-[1.02]" src="${escapeHtml(product.image)}" />
      </div>
      <div class="product-card__body">
        <div class="flex items-start justify-between gap-4">
          <div class="min-w-0">
            <p class="product-eyebrow">${escapeHtml(product.typeLabel)}</p>
            <h3 class="product-name product-card__title">${escapeHtml(product.name)}</h3>
            <p class="product-card__scent">${escapeHtml(product.scent || "")}</p>
          </div>
          <span class="price shrink-0 text-lg">${formatMoney(product.price)}</span>
        </div>
        <p class="product-card__description">${escapeHtml(product.short)}</p>
        <div class="product-card__meta">
          <span>${escapeHtml(product.useLabel)}</span>
          ${product.size ? `<span>${escapeHtml(product.size)}</span>` : ""}
        </div>
        <div class="product-card__actions">
          <button aria-controls="detail-title" aria-haspopup="dialog" class="text-link" data-open-detail="${escapeHtml(product.id)}" type="button">Ver detalle</button>
          <button aria-label="Añadir ${escapeHtml(product.name)} al carrito" class="primary-action" data-add-item="${escapeHtml(product.id)}" type="button">
            Añadir
          </button>
        </div>
      </div>
    </article>
  `;
}

function cartItemMarkup(entry) {
  const { item, quantity } = entry;
  return `
    <article class="border border-outline-variant/50 bg-surface-container-low p-5">
      <div class="flex gap-4">
        <img alt="${escapeHtml(item.name)}" class="h-28 w-28 bg-surface-container-lowest object-contain p-0.5" src="${escapeHtml(item.image)}" />
        <div class="flex flex-1 flex-col">
          <div class="flex items-start justify-between gap-4">
            <div class="min-w-0">
              <p class="text-[11px] uppercase tracking-[0.22em] text-on-surface-variant">${escapeHtml(item.badge)}</p>
              <h3 class="product-name mt-1 font-headline text-base leading-snug text-primary">${escapeHtml(item.name)}</h3>
              <p class="mt-2 text-sm text-on-surface-variant">${escapeHtml(item.scent || item.useLabel)}</p>
            </div>
            <span class="price shrink-0 text-lg">${formatMoney(item.price * quantity)}</span>
          </div>
          <div class="mt-4 flex items-center justify-between gap-3">
            <div class="inline-flex items-center gap-4 border border-outline-variant/50 bg-surface-container-highest px-4 py-2">
              <button aria-label="Disminuir cantidad de ${escapeHtml(item.name)}" class="text-primary transition hover:text-secondary" data-qty="${escapeHtml(item.id)}" data-delta="-1" type="button">
                <span class="material-symbols-outlined text-base">remove</span>
              </button>
              <span class="min-w-4 text-center font-semibold text-primary">${quantity}</span>
              <button aria-label="Aumentar cantidad de ${escapeHtml(item.name)}" class="text-primary transition hover:text-secondary" data-qty="${escapeHtml(item.id)}" data-delta="1" type="button">
                <span class="material-symbols-outlined text-base">add</span>
              </button>
            </div>
            <button class="inline-flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.22em] text-on-surface-variant transition hover:text-secondary" data-remove="${escapeHtml(item.id)}" type="button">
              <span class="material-symbols-outlined text-base">delete</span>
              Eliminar
            </button>
          </div>
        </div>
      </div>
    </article>
  `;
}

function upsellMarkup(item) {
  return `
    <div class="flex items-start gap-4">
      <img alt="${escapeHtml(item.name)}" class="h-24 w-24 rounded-[22px] bg-surface-container-lowest object-contain p-0.5" src="${escapeHtml(item.image)}" />
      <div class="flex-1">
        <p class="text-xs uppercase tracking-[0.22em] text-secondary">También te puede interesar</p>
        <h3 class="product-name mt-1.5 font-headline text-xl leading-snug text-primary">${escapeHtml(item.name)}</h3>
        <p class="mt-2 text-sm leading-7 text-on-surface-variant">${escapeHtml(item.short)}</p>
        <div class="mt-4 flex items-center justify-between gap-4">
          <span class="price text-2xl">${formatMoney(item.price)}</span>
          <button class="inline-flex items-center gap-2 rounded-2xl bg-primary px-4 py-3 text-sm font-semibold text-on-primary transition hover:bg-primary-container focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-secondary/35" data-add-item="${escapeHtml(item.id)}" type="button">
            Añadir
          </button>
        </div>
      </div>
    </div>
  `;
}

function getActiveFilterBadges() {
  const active = [];

  if (state.search.trim()) {
      active.push({
      group: "search",
      value: "",
      label: `Búsqueda: ${state.search.trim()}`,
    });
  }

  for (const value of state.useFilters) {
    active.push({ group: "use", value, label: useLabelMap.get(value) || value });
  }
  for (const value of state.typeFilters) {
    active.push({ group: "type", value, label: typeLabelMap.get(value) || value });
  }

  return active;
}

function renderActiveFilters() {
  const active = getActiveFilterBadges();

  if (!els.activeFilters) return;

  if (!active.length) {
    els.activeFilters.innerHTML =
        '<span class="filter-status">Sin filtros activos</span>';
    return;
  }

  els.activeFilters.innerHTML = active
    .map(
      (filter) => `
        <button class="filter-status is-active inline-flex items-center gap-2" data-remove-filter="${escapeHtml(filter.group)}:${escapeHtml(filter.value)}" type="button">
          ${escapeHtml(filter.label)}
          <span class="material-symbols-outlined text-sm">close</span>
        </button>
      `,
    )
    .join("");
}

function syncFilterControls() {
  document.querySelectorAll("[data-filter-use]").forEach((button) => {
    const active = state.useFilters.has(button.dataset.filterUse);
    button.className = active ? PILL_ACTIVE_CLASS : PILL_INACTIVE_CLASS;
    button.setAttribute("aria-pressed", String(active));
  });

  document.querySelectorAll("[data-filter-type]").forEach((button) => {
    const active = state.typeFilters.has(button.dataset.filterType);
    button.className = active ? PILL_ACTIVE_CLASS : PILL_INACTIVE_CLASS;
    button.setAttribute("aria-pressed", String(active));
  });
}

function renderProducts() {
  const filtered = getFilteredProducts();

  if (els.counts) {
    els.counts.forEach((el) => {
      el.textContent = String(filtered.length);
    });
  }

  if (els.grid) {
    els.grid.innerHTML = filtered.map(catalogCardMarkup).join("");
  }

  if (els.empty) {
    els.empty.classList.toggle("hidden", filtered.length !== 0);
  }

  renderActiveFilters();
}

function getUpsellItem() {
  const idsInCart = new Set(cartEntries().map((entry) => entry.item.id));
  const firstEntry = cartEntries()[0];

  if (firstEntry) {
    const matchingKit = KITS.find(
      (kit) => kit.use === firstEntry.item.use && !idsInCart.has(kit.id),
    );
    if (matchingKit) return matchingKit;
  }

  return (
    KITS.find((kit) => !idsInCart.has(kit.id)) ||
    PRODUCTS.find((product) => product.featured && !idsInCart.has(product.id)) ||
    null
  );
}

function renderCart() {
  const entries = cartEntries();
  const totals = cartTotals();
  const upsellItem = getUpsellItem();

  els.cartCounts.forEach((node) => {
    node.textContent = String(totals.count);
  });

  if (els.subtotal) {
    els.subtotal.textContent = formatMoney(totals.subtotal);
  }
  if (els.shipping) {
    els.shipping.textContent = formatMoney(totals.shipping);
  }
  if (els.tax) {
    els.tax.textContent = formatMoney(totals.tax);
  }
  if (els.total) {
    els.total.textContent = formatMoney(totals.total);
  }
  if (els.checkout) {
    els.checkout.disabled = totals.count === 0;
  }

  if (els.shippingProgress) {
    const progress = Math.min(100, Math.round((totals.subtotal / FREE_SHIPPING_THRESHOLD) * 100));
    els.shippingProgress.style.width = `${Number.isFinite(progress) ? progress : 0}%`;
  }

  if (els.shippingMessage) {
    if (totals.subtotal === 0) {
      els.shippingMessage.textContent = `Te faltan ${formatMoney(FREE_SHIPPING_THRESHOLD)} para envío gratis.`;
    } else if (totals.subtotal >= FREE_SHIPPING_THRESHOLD) {
      els.shippingMessage.textContent = "Tu envío ya es gratis.";
    } else {
      els.shippingMessage.textContent = `Te faltan ${formatMoney(FREE_SHIPPING_THRESHOLD - totals.subtotal)} para envío gratis.`;
    }
  }


  if (els.cartItems) {
    els.cartItems.innerHTML = entries.map(cartItemMarkup).join("");
  }

  if (els.cartEmpty) {
    els.cartEmpty.classList.toggle("hidden", entries.length !== 0);
  }

  if (els.cartUpsell) {
    els.cartUpsell.innerHTML = upsellItem
      ? upsellMarkup(upsellItem)
      : '<p class="text-sm leading-7 text-on-surface-variant">Tu carrito ya contiene toda la curaduría sugerida por ahora.</p>';
  }
}

function syncBodyLock() {
  document.body.classList.toggle(
    "ui-locked",
    state.cartOpen || state.detailOpen || state.filtersOpen,
  );
}

function openFilters() {
  state.filtersOpen = true;
  els.filtersDrawer?.classList.remove("-translate-x-full");
  els.filtersOverlay?.classList.remove("pointer-events-none", "opacity-0");
  els.filtersOverlay?.classList.add("opacity-100");
  syncBodyLock();
}

function closeFilters() {
  state.filtersOpen = false;
  els.filtersDrawer?.classList.add("-translate-x-full");
  els.filtersOverlay?.classList.add("pointer-events-none", "opacity-0");
  els.filtersOverlay?.classList.remove("opacity-100");
  syncBodyLock();
}

function openCart() {
  state.cartOpen = true;
  closeFilters();
  els.cartDrawer?.classList.remove("translate-x-full");
  els.cartOverlay?.classList.remove("pointer-events-none", "opacity-0");
  els.cartOverlay?.classList.add("opacity-100");
  syncBodyLock();
}

function closeCart() {
  state.cartOpen = false;
  els.cartDrawer?.classList.add("translate-x-full");
  els.cartOverlay?.classList.add("pointer-events-none", "opacity-0");
  els.cartOverlay?.classList.remove("opacity-100");
  syncBodyLock();
}

function detailFocusableElements() {
  if (!els.modal) return [];

  return [...els.modal.querySelectorAll(
    'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
  )].filter((element) => {
    const styles = window.getComputedStyle(element);
    return styles.visibility !== "hidden" && styles.display !== "none";
  });
}

function openDetail(itemId) {
  const item = ITEM_INDEX.get(itemId);
  if (!item) return;

  state.detailItemId = itemId;
  state.detailOpen = true;
  // Se recuerda quién abrió para devolverle el foco al cerrar.
  lastDetailTrigger = document.activeElement;

  if (els.modal) els.modal.style.setProperty("--accent", accentOf(item));

  // El badge se arma solo con las partes que existen: así no queda " · algo".
  setText(els.detailBadge, [clean(item.badge), clean(item.typeLabel)].filter(Boolean).join(" · "));
  setText(els.detailTitle, item.name);
  setText(els.detailScent, item.scent);
  setText(els.detailPrice, formatMoney(item.price));
  setText(els.detailDescription, item.description);

  if (els.detailImage) {
    els.detailImage.src = clean(item.image);
    els.detailImage.alt = clean(item.name);
  }

  if (els.detailTags) {
    const tags = [clean(item.useLabel), clean(item.size)].filter(Boolean);
    els.detailTags.innerHTML = tags.map(detailTagMarkup).join("");
    els.detailTags.hidden = tags.length === 0;
  }

  if (els.detailBenefits) {
    const benefits = (item.benefits || []).map(clean).filter(Boolean);
    els.detailBenefits.innerHTML = benefits
      .map(
        (benefit) =>
          `<li class="flex gap-3"><span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--accent)]"></span><span>${escapeHtml(benefit)}</span></li>`,
      )
      .join("");
    toggleBlock(els.detailBenefitsBlock, benefits.length > 0);
  }

  toggleBlock(els.detailInstructionsBlock, setText(els.detailInstructions, item.instructions) !== "");

  els.modal?.classList.add("is-open");
  els.modalOverlay?.classList.add("is-open");
  els.modal?.setAttribute("aria-hidden", "false");
  els.pageContent?.setAttribute("aria-hidden", "true");
  if (els.pageContent) els.pageContent.inert = true;
  document.body.classList.add("detail-open");
  syncBodyLock();

  // El panel arranca arriba y recibe el foco, para que lector de pantalla y
  // teclado entren al diálogo en vez de quedarse en la página de fondo.
  if (els.detailBody) els.detailBody.scrollTop = 0;
  els.modal?.focus({ preventScroll: true });
}

function closeDetail() {
  state.detailItemId = null;
  state.detailOpen = false;
  els.modal?.classList.remove("is-open");
  els.modalOverlay?.classList.remove("is-open");
  els.modal?.setAttribute("aria-hidden", "true");
  els.pageContent?.removeAttribute("aria-hidden");
  if (els.pageContent) els.pageContent.inert = false;
  document.body.classList.remove("detail-open");
  syncBodyLock();

  // Devolver el foco a "Ver detalle" para no perder el lugar en la página.
  if (lastDetailTrigger && document.contains(lastDetailTrigger)) {
    lastDetailTrigger.focus({ preventScroll: true });
  }
  lastDetailTrigger = null;
}

function addToCart(itemId, quantity = 1, openDrawer = true) {
  if (!ITEM_INDEX.has(itemId)) return;

  state.cart[itemId] = (state.cart[itemId] || 0) + quantity;
  saveCart();
  renderCart();

  if (openDrawer) {
    openCart();
  }
}

function updateQuantity(itemId, delta) {
  if (!ITEM_INDEX.has(itemId)) return;

  const next = (state.cart[itemId] || 0) + delta;
  if (next <= 0) {
    delete state.cart[itemId];
  } else {
    state.cart[itemId] = next;
  }

  saveCart();
  renderCart();
}

function removeFromCart(itemId) {
  delete state.cart[itemId];
  saveCart();
  renderCart();
}

function clearFilters() {
  state.search = "";
  state.useFilters.clear();
  state.typeFilters.clear();

  if (els.search) {
    els.search.value = "";
  }

  syncFilterControls();
  renderProducts();
}

function removeFilter(group, value) {
  if (group === "search") {
    state.search = "";
    if (els.search) {
      els.search.value = "";
    }
  }
  if (group === "use") {
    state.useFilters.delete(value);
  }
  if (group === "type") {
    state.typeFilters.delete(value);
  }

  syncFilterControls();
  renderProducts();
}

function toggleFilter(group, value) {
  const targetSet = group === "use" ? state.useFilters : state.typeFilters;

  if (targetSet.has(value)) {
    targetSet.delete(value);
  } else {
    targetSet.add(value);
  }

  syncFilterControls();
  renderProducts();
}

function scrollToSection(id) {
  const section = document.getElementById(id);
  if (section) {
    section.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function focusSearch() {
  scrollToSection("catalogo");
  window.setTimeout(() => {
    els.search?.focus();
  }, 220);
}

function applyNeedFilter(slug) {
  state.search = "";
  state.useFilters = new Set([slug]);
  state.typeFilters.clear();

  if (els.search) {
    els.search.value = "";
  }

  syncFilterControls();
  renderProducts();
  scrollToSection("catalogo");
}

// Stripe Checkout. The browser never sees a secret key: it POSTs the cart to
// the site's checkout endpoint, which creates the Stripe session server-side
// and returns its hosted URL. Until that endpoint is deployed with real keys,
// the button reports it plainly instead of failing silently.
const CHECKOUT_ENDPOINT = "/api/yoga-verde/checkout";

async function startCheckout() {
  const entries = cartEntries();
  if (!entries.length) return;

  const button = document.querySelector("[data-checkout]");
  const originalLabel = button ? button.innerHTML : "";
  if (button) {
    button.disabled = true;
    button.innerHTML = "Conectando con el pago seguro...";
  }

  try {
    const response = await fetch(CHECKOUT_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        items: entries.map((entry) => ({
          id: entry.item.id,
          quantity: entry.quantity,
        })),
      }),
    });

    if (!response.ok) throw new Error(`Checkout respondió ${response.status}`);

    const data = await response.json();
    if (!data || !data.url) throw new Error("Checkout no devolvió una URL de pago.");

    window.location.href = data.url;
  } catch (error) {
    console.error("[yoga-verde] checkout:", error);
    if (button) {
      button.disabled = false;
      button.innerHTML = originalLabel;
    }
    window.alert(
      "No pudimos abrir el pago en este momento. Vuelve a intentarlo en unos minutos o escríbenos para completar tu pedido.",
    );
  }
}

document.addEventListener("click", (event) => {
  const target = event.target instanceof Element ? event.target.closest("button, a") : null;
  if (!target) return;

  if (target.matches("[data-open-filters]")) openFilters();
  if (target.matches("[data-close-filters]")) closeFilters();

  if (target.matches("[data-open-cart]")) openCart();
  if (target.matches("[data-close-cart]")) closeCart();

  if (target.matches("[data-add-item]")) {
    addToCart(target.dataset.addItem);
  }

  if (target.matches("[data-open-detail]")) {
    event.preventDefault();
    openDetail(target.getAttribute("data-open-detail"));
  }

  if (target.matches("[data-close-detail]")) {
    closeDetail();
  }

  if (target.matches("[data-detail-add]") && state.detailItemId) {
    addToCart(state.detailItemId);
    closeDetail();
  }

  if (target.matches("[data-qty]")) {
    updateQuantity(target.dataset.qty, Number(target.dataset.delta));
  }

  if (target.matches("[data-remove]")) {
    removeFromCart(target.dataset.remove);
  }

  if (target.matches("[data-filter-use]")) {
    toggleFilter("use", target.dataset.filterUse);
  }

  if (target.matches("[data-filter-type]")) {
    toggleFilter("type", target.dataset.filterType);
  }

  if (target.matches("[data-clear-filters]")) {
    clearFilters();
  }

  if (target.matches("[data-remove-filter]")) {
    const [group, value] = target.dataset.removeFilter.split(":");
    removeFilter(group, value);
  }

  if (target.matches("[data-apply-use]")) {
    applyNeedFilter(target.dataset.applyUse);
  }

  if (target.matches("[data-scroll-to]")) {
    closeFilters();
    target.closest("[data-mobile-menu]")?.removeAttribute("open");
    scrollToSection(target.dataset.scrollTo);
  }

  if (target.matches("[data-focus-search]")) {
    closeFilters();
    focusSearch();
  }

  if (target.matches("[data-checkout]")) {
    startCheckout();
  }
});

els.search?.addEventListener("input", () => {
  state.search = els.search.value;
  renderProducts();
});

els.filtersOverlay?.addEventListener("click", closeFilters);
els.cartOverlay?.addEventListener("click", closeCart);
els.modalOverlay?.addEventListener("click", closeDetail);

document.addEventListener("keydown", (event) => {
  if (state.detailOpen && event.key === "Tab") {
    const focusable = detailFocusableElements();
    if (focusable.length === 0) {
      event.preventDefault();
      els.modal?.focus({ preventScroll: true });
      return;
    }

    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && (document.activeElement === first || document.activeElement === els.modal)) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && (document.activeElement === last || document.activeElement === els.modal)) {
      event.preventDefault();
      first.focus();
    }
    return;
  }

  if (event.key !== "Escape") return;

  if (state.detailOpen) {
    closeDetail();
    return;
  }
  if (state.cartOpen) {
    closeCart();
    return;
  }
  if (state.filtersOpen) {
    closeFilters();
    return;
  }
});

syncFilterControls();
renderProducts();
renderCart();
closeFilters();
closeCart();
closeDetail();
