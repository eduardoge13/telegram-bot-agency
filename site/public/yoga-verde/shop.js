const dataNode = document.getElementById("yoga-verde-data");

if (!dataNode) {
  throw new Error("Yoga Verde data payload not found.");
}

const store = JSON.parse(dataNode.textContent || "{}");

const PRODUCTS = Array.isArray(store.products) ? store.products : [];
const KITS = Array.isArray(store.kits) ? store.kits : [];
const ALL_ITEMS = [...PRODUCTS, ...KITS];
const ITEM_INDEX = new Map(ALL_ITEMS.map((item) => [item.id, item]));

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
const originLabelMap = new Map(PRODUCTS.map((product) => [product.origin, product.originLabel]));

const state = {
  search: "",
  useFilters: new Set(),
  typeFilters: new Set(),
  originFilters: new Set(),
  cart: loadCart(),
  detailItemId: null,
  cartOpen: false,
  detailOpen: false,
  filtersOpen: false,
  menuOpen: false,
};

const els = {
  grid: document.querySelector("[data-products-grid]"),
  empty: document.querySelector("[data-empty-state]"),
  count: document.querySelector("[data-product-count]"),
  activeFilters: document.querySelector("[data-active-filters]"),
  search: document.querySelector("[data-search-input]"),
  filtersDrawer: document.querySelector("[data-filters-drawer]"),
  filtersOverlay: document.querySelector("[data-filters-overlay]"),
  menuDrawer: document.querySelector("[data-menu-drawer]"),
  menuOverlay: document.querySelector("[data-menu-overlay]"),
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
  mobileCta: document.querySelector("[data-mobile-cart-cta]"),
  mobileCount: document.querySelector("[data-mobile-count]"),
  mobileTotal: document.querySelector("[data-mobile-total]"),
  modal: document.querySelector("[data-detail-modal]"),
  modalOverlay: document.querySelector("[data-modal-overlay]"),
  detailBadge: document.querySelector("[data-detail-badge]"),
  detailTitle: document.querySelector("[data-detail-title]"),
  detailDescription: document.querySelector("[data-detail-description]"),
  detailTags: document.querySelector("[data-detail-tags]"),
  detailBenefits: document.querySelector("[data-detail-benefits]"),
  detailInstructions: document.querySelector("[data-detail-instructions]"),
  detailPrice: document.querySelector("[data-detail-price]"),
  detailImage: document.querySelector("[data-detail-image]"),
  detailAdd: document.querySelector("[data-detail-add]"),
  detailRatingStars: document.querySelector("[data-detail-rating-stars]"),
  detailRatingCopy: document.querySelector("[data-detail-rating-copy]"),
};

const PILL_ACTIVE_CLASS =
  "rounded-full bg-tertiary-container px-4 py-2 text-sm font-medium text-on-tertiary-container transition hover:bg-tertiary hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-secondary/35";
const PILL_INACTIVE_CLASS =
  "rounded-full bg-surface-container-highest px-4 py-2 text-sm font-medium text-on-surface-variant transition hover:bg-tertiary-container hover:text-on-tertiary-container focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-secondary/35";
const LINK_ACTIVE_CLASS =
  "block text-left text-sm text-secondary underline decoration-secondary/30 underline-offset-4 focus-visible:outline-none";
const LINK_INACTIVE_CLASS =
  "block text-left text-sm text-on-surface-variant transition hover:text-secondary focus-visible:outline-none focus-visible:text-secondary";

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

function starMarkup(rating) {
  return Array.from({ length: 5 }, (_, index) =>
    `<span aria-hidden="true">${index < Math.round(rating) ? "★" : "☆"}</span>`,
  ).join("");
}

function productSearchHaystack(product) {
  return normalizeText([
    product.name,
    product.short,
    product.description,
    product.useLabel,
    product.originLabel,
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
    const matchesOrigin =
      state.originFilters.size === 0 || state.originFilters.has(product.origin);

    return matchesSearch && matchesUse && matchesType && matchesOrigin;
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

function detailTagMarkup(label) {
  return `<span class="rounded-full bg-surface-container-low px-4 py-2 text-sm font-medium text-on-surface-variant">${escapeHtml(label)}</span>`;
}

function catalogCardMarkup(product) {
  return `
    <article class="group overflow-hidden rounded-[30px] bg-surface-container-lowest shadow-parchment transition-transform hover:-translate-y-1">
      <div class="relative overflow-hidden bg-surface-container-low p-4">
        <span class="absolute left-4 top-4 z-10 rounded-full bg-surface px-3 py-1 text-[10px] font-bold uppercase tracking-[0.22em] text-primary">${escapeHtml(product.badge)}</span>
        <img alt="${escapeHtml(product.name)}" class="aspect-[5/4] w-full rounded-[24px] object-cover transition duration-500 group-hover:scale-105" src="${escapeHtml(product.image)}" />
      </div>
      <div class="p-6">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-[11px] uppercase tracking-[0.22em] text-on-surface-variant">${escapeHtml(product.typeLabel)} · ${escapeHtml(product.originLabel)}</p>
            <h3 class="mt-2 font-headline text-4xl leading-none text-primary">${escapeHtml(product.name)}</h3>
          </div>
          <span class="font-headline text-3xl text-secondary">${formatMoney(product.price)}</span>
        </div>
        <div class="mt-4 flex items-center gap-3 text-sm text-on-surface-variant">
          <div class="flex items-center gap-1 text-secondary">${starMarkup(product.rating)}</div>
          <span>${product.rating.toFixed(1)} · ${product.reviewsCount} reseñas</span>
        </div>
        <p class="mt-4 min-h-[84px] text-sm italic leading-7 text-on-surface-variant">${escapeHtml(product.short)}</p>
        <div class="mt-4 flex flex-wrap gap-2">
          <span class="rounded-full bg-surface-container-low px-3 py-2 text-xs font-semibold text-primary">${escapeHtml(product.useLabel)}</span>
          <span class="rounded-full bg-surface-container-low px-3 py-2 text-xs font-semibold text-on-surface-variant">${escapeHtml(product.originLabel)}</span>
        </div>
        <div class="mt-6 flex items-center justify-between gap-3 border-t border-outline-variant/40 pt-5">
          <button class="inline-flex items-center gap-2 text-sm font-semibold text-primary transition hover:text-secondary focus-visible:outline-none" data-open-detail="${escapeHtml(product.id)}" type="button">
            <span class="material-symbols-outlined text-base">auto_stories</span>
            Ver detalle
          </button>
          <button aria-label="Añadir ${escapeHtml(product.name)} al carrito" class="inline-flex items-center gap-2 rounded-2xl bg-primary px-4 py-3 text-sm font-semibold text-on-primary transition hover:bg-primary-container focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-secondary/35" data-add-item="${escapeHtml(product.id)}" type="button">
            Añadir al carrito
          </button>
        </div>
      </div>
    </article>
  `;
}

function cartItemMarkup(entry) {
  const { item, quantity } = entry;
  return `
    <article class="overflow-hidden rounded-[28px] bg-surface-container-low p-5 shadow-parchment">
      <div class="flex gap-4">
        <img alt="${escapeHtml(item.name)}" class="h-28 w-28 rounded-[22px] object-cover" src="${escapeHtml(item.image)}" />
        <div class="flex flex-1 flex-col">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-[11px] uppercase tracking-[0.22em] text-on-surface-variant">${escapeHtml(item.badge)}</p>
              <h3 class="mt-2 font-headline text-3xl leading-none text-primary">${escapeHtml(item.name)}</h3>
              <p class="mt-2 text-sm text-on-surface-variant">${escapeHtml(item.useLabel)} · ${escapeHtml(item.originLabel)}</p>
            </div>
            <span class="font-headline text-3xl text-primary">${formatMoney(item.price * quantity)}</span>
          </div>
          <div class="mt-4 flex items-center justify-between gap-3">
            <div class="inline-flex items-center gap-4 rounded-full bg-surface-container-highest px-4 py-2">
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
      <img alt="${escapeHtml(item.name)}" class="h-24 w-24 rounded-[22px] object-cover" src="${escapeHtml(item.image)}" />
      <div class="flex-1">
        <p class="text-xs uppercase tracking-[0.22em] text-secondary">Upsell sugerido</p>
        <h3 class="mt-2 font-headline text-3xl text-primary">${escapeHtml(item.name)}</h3>
        <p class="mt-2 text-sm leading-7 text-on-surface-variant">${escapeHtml(item.short)}</p>
        <div class="mt-4 flex items-center justify-between gap-4">
          <span class="font-headline text-3xl text-secondary">${formatMoney(item.price)}</span>
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
  for (const value of state.originFilters) {
    active.push({
      group: "origin",
      value,
      label: originLabelMap.get(value) || value,
    });
  }

  return active;
}

function renderActiveFilters() {
  const active = getActiveFilterBadges();

  if (!els.activeFilters) return;

  if (!active.length) {
    els.activeFilters.innerHTML =
      '<span class="rounded-full bg-surface-container-lowest px-3 py-2 text-xs font-semibold text-on-surface-variant">Sin filtros activos</span>';
    return;
  }

  els.activeFilters.innerHTML = active
    .map(
      (filter) => `
        <button class="inline-flex items-center gap-2 rounded-full bg-surface-container-lowest px-3 py-2 text-xs font-semibold text-primary shadow-parchment transition hover:text-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-secondary/35" data-remove-filter="${escapeHtml(filter.group)}:${escapeHtml(filter.value)}" type="button">
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

  document.querySelectorAll("[data-filter-origin]").forEach((button) => {
    const active = state.originFilters.has(button.dataset.filterOrigin);
    button.className = active ? LINK_ACTIVE_CLASS : LINK_INACTIVE_CLASS;
    button.setAttribute("aria-pressed", String(active));
  });
}

function renderProducts() {
  const filtered = getFilteredProducts();

  if (els.count) {
    els.count.textContent = String(filtered.length);
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

  if (els.mobileCount) {
    els.mobileCount.textContent = `${totals.count} ${totals.count === 1 ? "pieza" : "piezas"}`;
  }
  if (els.mobileTotal) {
    els.mobileTotal.textContent = formatMoney(totals.total);
  }
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
      els.shippingMessage.textContent = "Tu envío consciente ya es gratis.";
    } else {
      els.shippingMessage.textContent = `Te faltan ${formatMoney(FREE_SHIPPING_THRESHOLD - totals.subtotal)} para envío gratis.`;
    }
  }

  if (els.mobileCta) {
    const hasItems = totals.count > 0;
    els.mobileCta.classList.toggle("pointer-events-none", !hasItems);
    els.mobileCta.classList.toggle("translate-y-24", !hasItems);
    els.mobileCta.classList.toggle("opacity-0", !hasItems);
    els.mobileCta.classList.toggle("translate-y-0", hasItems);
    els.mobileCta.classList.toggle("opacity-100", hasItems);
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
    state.cartOpen || state.detailOpen || state.filtersOpen || state.menuOpen,
  );
}

function openMenu() {
  state.menuOpen = true;
  state.filtersOpen = false;
  els.menuDrawer?.classList.remove("-translate-x-full");
  els.menuOverlay?.classList.remove("pointer-events-none", "opacity-0");
  els.menuOverlay?.classList.add("opacity-100");
  els.filtersDrawer?.classList.add("-translate-x-full");
  els.filtersOverlay?.classList.add("pointer-events-none", "opacity-0");
  syncBodyLock();
}

function closeMenu() {
  state.menuOpen = false;
  els.menuDrawer?.classList.add("-translate-x-full");
  els.menuOverlay?.classList.add("pointer-events-none", "opacity-0");
  els.menuOverlay?.classList.remove("opacity-100");
  syncBodyLock();
}

function openFilters() {
  state.filtersOpen = true;
  state.menuOpen = false;
  els.filtersDrawer?.classList.remove("-translate-x-full");
  els.filtersOverlay?.classList.remove("pointer-events-none", "opacity-0");
  els.filtersOverlay?.classList.add("opacity-100");
  els.menuDrawer?.classList.add("-translate-x-full");
  els.menuOverlay?.classList.add("pointer-events-none", "opacity-0");
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
  closeMenu();
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

function openDetail(itemId) {
  const item = ITEM_INDEX.get(itemId);
  if (!item) return;

  state.detailItemId = itemId;
  state.detailOpen = true;

  if (els.detailBadge) {
    els.detailBadge.textContent = `${item.badge} · ${item.typeLabel}`;
  }
  if (els.detailTitle) {
    els.detailTitle.textContent = item.name;
  }
  if (els.detailDescription) {
    els.detailDescription.textContent = item.description;
  }
  if (els.detailImage) {
    els.detailImage.src = item.image;
    els.detailImage.alt = item.name;
  }
  if (els.detailPrice) {
    els.detailPrice.textContent = formatMoney(item.price);
  }
  if (els.detailTags) {
    els.detailTags.innerHTML = [
      item.useLabel,
      item.originLabel,
      item.typeLabel,
      ...(item.tags || []).slice(0, 2),
    ]
      .map(detailTagMarkup)
      .join("");
  }
  if (els.detailBenefits) {
    els.detailBenefits.innerHTML = (item.benefits || [])
      .map(
        (benefit) =>
          `<li class="flex gap-3"><span class="mt-2 h-2.5 w-2.5 rounded-full bg-secondary"></span><span>${escapeHtml(benefit)}</span></li>`,
      )
      .join("");
  }
  if (els.detailInstructions) {
    els.detailInstructions.textContent = item.instructions;
  }
  if (els.detailRatingStars) {
    els.detailRatingStars.innerHTML = starMarkup(item.rating);
  }
  if (els.detailRatingCopy) {
    els.detailRatingCopy.textContent = `${item.rating.toFixed(1)} · ${item.reviewsCount} reseñas`;
  }

  els.modal?.classList.remove("pointer-events-none", "scale-95", "opacity-0");
  els.modalOverlay?.classList.remove("pointer-events-none", "opacity-0");
  els.modalOverlay?.classList.add("opacity-100");
  syncBodyLock();
}

function closeDetail() {
  state.detailItemId = null;
  state.detailOpen = false;
  els.modal?.classList.add("pointer-events-none", "scale-95", "opacity-0");
  els.modalOverlay?.classList.add("pointer-events-none", "opacity-0");
  els.modalOverlay?.classList.remove("opacity-100");
  syncBodyLock();
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
  state.originFilters.clear();

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
  if (group === "origin") {
    state.originFilters.delete(value);
  }

  syncFilterControls();
  renderProducts();
}

function toggleFilter(group, value) {
  const targetSet =
    group === "use"
      ? state.useFilters
      : group === "type"
        ? state.typeFilters
        : state.originFilters;

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
  state.originFilters.clear();

  if (els.search) {
    els.search.value = "";
  }

  syncFilterControls();
  renderProducts();
  scrollToSection("catalogo");
}

function checkoutDemo() {
  const totals = cartTotals();
  const summary = cartEntries()
    .map((entry) => `${entry.quantity}x ${entry.item.name}`)
    .join(", ");

  window.alert(
    `Pedido preparado: ${summary}\n\nTotal estimado: ${formatMoney(
      totals.total,
    )}\n\nSiguiente paso sugerido: conectar checkout real o handoff de ventas por WhatsApp.`,
  );
}

document.addEventListener("click", (event) => {
  const target = event.target.closest("button, a");
  if (!target) return;

  if (target.matches("[data-open-menu]")) openMenu();
  if (target.matches("[data-close-menu]")) closeMenu();
  if (target.matches("[data-open-filters]")) openFilters();
  if (target.matches("[data-close-filters]")) closeFilters();

  if (target.matches("[data-open-cart]")) openCart();
  if (target.matches("[data-close-cart]")) closeCart();

  if (target.matches("[data-add-item]")) {
    addToCart(target.dataset.addItem);
  }

  if (target.matches("[data-open-detail]")) {
    openDetail(target.dataset.openDetail);
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

  if (target.matches("[data-filter-origin]")) {
    toggleFilter("origin", target.dataset.filterOrigin);
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
    closeMenu();
    closeFilters();
    scrollToSection(target.dataset.scrollTo);
  }

  if (target.matches("[data-focus-search]")) {
    closeMenu();
    closeFilters();
    focusSearch();
  }

  if (target.matches("[data-checkout]")) {
    checkoutDemo();
  }
});

els.search?.addEventListener("input", () => {
  state.search = els.search.value;
  renderProducts();
});

els.menuOverlay?.addEventListener("click", closeMenu);
els.filtersOverlay?.addEventListener("click", closeFilters);
els.cartOverlay?.addEventListener("click", closeCart);
els.modalOverlay?.addEventListener("click", closeDetail);

document.addEventListener("keydown", (event) => {
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
  if (state.menuOpen) {
    closeMenu();
  }
});

syncFilterControls();
renderProducts();
renderCart();
closeMenu();
closeFilters();
closeCart();
closeDetail();
