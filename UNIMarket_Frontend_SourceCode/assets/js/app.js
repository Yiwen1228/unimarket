'use strict';

const Store = {
  users: 'um_users',
  current: 'um_current_user',
  products: 'um_products',
  orders: 'um_orders'
};

function read(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function write(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function bootstrapData() {
  if (!read(Store.users, null)) {
    write(Store.users, [
      { userId: 'STAFF001', email: 'staff@unimarket.test', password: 'Staff123!', role: 'staff' },
      { userId: 'CUS001', email: 'customer@unimarket.test', password: 'Customer123!', role: 'customer' }
    ]);
  }

  if (!read(Store.products, null)) {
    write(Store.products, [
      { id: 1, name: 'Milk 1L', category: 'Dairy', price: 1.2, stock: 32 },
      { id: 2, name: 'Eggs 6-Pack', category: 'Dairy', price: 2.1, stock: 14 },
      { id: 3, name: 'Wholemeal Bread', category: 'Bakery', price: 1.5, stock: 18 },
      { id: 4, name: 'Apple', category: 'Fruit', price: 0.8, stock: 20 },
      { id: 5, name: 'Orange Juice', category: 'Drinks', price: 2.9, stock: 11 },
      { id: 6, name: 'Pasta 500g', category: 'Grocery', price: 1.1, stock: 26 }
    ]);
  }

  if (!read(Store.orders, null)) {
    write(Store.orders, []);
  }

  migrateLegacyUsers();
}

function migrateLegacyUsers() {
  const users = read(Store.users, []);
  let changed = false;

  const upgraded = users.map((u, idx) => {
    const role = (u.role === 'staff' || u.role === 'customer') ? u.role : 'customer';
    let userId = typeof u.userId === 'string' ? u.userId.trim() : '';
    if (!userId) {
      userId = `${role === 'staff' ? 'STAFF' : 'CUS'}${String(idx + 1).padStart(3, '0')}`;
      changed = true;
    }

    if (!u.email || !u.password) {
      changed = true;
    }

    return {
      userId,
      email: (u.email || '').toLowerCase(),
      password: u.password || '',
      role
    };
  }).filter(u => u.email && u.password);

  if (changed) {
    write(Store.users, upgraded);
  }
}

function currentUser() {
  return read(Store.current, null);
}

function setCurrentUser(user) {
  write(Store.current, user);
}

function clearCurrentUser() {
  localStorage.removeItem(Store.current);
}

function findUser(email, password, role) {
  const users = read(Store.users, []);
  return users.find(u => u.email === email && u.password === password && u.role === role) || null;
}

function showFeedback(message, isError = false) {
  const el = document.getElementById('feedback');
  if (!el) return;
  el.textContent = message;
  el.classList.toggle('error', isError);
}

function formatMoney(amount) {
  return `GBP ${amount.toFixed(2)}`;
}

function statusBadge(status) {
  const map = {
    pending: 'status-pending',
    processing: 'status-processing',
    completed: 'status-completed',
    cancelled: 'status-cancelled'
  };
  return `<span class="status-badge ${map[status] || 'status-pending'}">${status}</span>`;
}

function requireRole(role) {
  const user = currentUser();
  if (!user || user.role !== role) {
    const target = role === 'staff' ? 'staff-login.html' : 'customer-login.html';
    window.location.href = target;
    return false;
  }
  return true;
}

function renderUserId() {
  const user = currentUser();
  document.querySelectorAll('[data-user-id]').forEach(el => {
    el.textContent = user ? user.userId : 'Guest';
  });
}

function bindLogout() {
  document.querySelectorAll('.js-logout').forEach(btn => {
    btn.addEventListener('click', () => {
      clearCurrentUser();
      window.location.href = '../index.html';
    });
  });
}

function registerAccount(formId, role) {
  const form = document.getElementById(formId);
  if (!form) return;

  form.addEventListener('submit', event => {
    event.preventDefault();
    const userId = form.userId.value.trim();
    const email = form.email.value.trim().toLowerCase();
    const password = form.password.value;

    if (!userId || !email || !password) {
      showFeedback('User ID, email, and password are required.', true);
      return;
    }

    const users = read(Store.users, []);
    const duplicate = users.find(u =>
      (String(u.userId || '').toLowerCase() === userId.toLowerCase()) ||
      (String(u.email || '').toLowerCase() === email)
    );
    if (duplicate) {
      showFeedback('User ID or email already exists.', true);
      return;
    }

    users.push({ userId, email, password, role });
    write(Store.users, users);
    showFeedback(`${role} account created successfully.`);
    form.reset();
  });
}

function bindCustomerLogin() {
  const form = document.getElementById('customerLoginForm');
  if (!form) return;

  form.addEventListener('submit', event => {
    event.preventDefault();
    const email = form.email.value.trim().toLowerCase();
    const password = form.password.value;
    const user = findUser(email, password, 'customer');

    if (!user) {
      showFeedback('Invalid customer credentials.', true);
      return;
    }

    setCurrentUser({ userId: user.userId, email: user.email, role: user.role });
    window.location.href = 'products.html';
  });
}

function bindStaffLogin() {
  const form = document.getElementById('staffLoginForm');
  if (!form) return;

  form.addEventListener('submit', event => {
    event.preventDefault();
    const email = form.email.value.trim().toLowerCase();
    const password = form.password.value;
    const user = findUser(email, password, 'staff');

    if (!user) {
      showFeedback('Invalid staff credentials.', true);
      return;
    }

    setCurrentUser({ userId: user.userId, email: user.email, role: user.role });
    window.location.href = 'staff-dashboard.html';
  });
}

const cart = [];

function renderProductsTable(rows) {
  const tbody = document.getElementById('productTableBody');
  if (!tbody) return;

  tbody.innerHTML = rows.map(product => `
    <tr>
      <td>${product.name}</td>
      <td>${product.category}</td>
      <td>${formatMoney(product.price)}</td>
      <td>${product.stock}</td>
      <td>
        <label class="visually-hidden" for="qty-${product.id}">Quantity for ${product.name}</label>
        <input id="qty-${product.id}" type="number" min="1" max="${product.stock}" value="1" class="form-control form-control-sm qty-input">
      </td>
      <td><button type="button" class="btn-soft js-add" data-id="${product.id}">Add to order</button></td>
    </tr>
  `).join('');
}

function renderCart() {
  const list = document.getElementById('cartList');
  const total = document.getElementById('cartTotal');
  if (!list || !total) return;

  if (!cart.length) {
    list.innerHTML = '<li class="text-muted">No items selected yet.</li>';
    total.textContent = formatMoney(0);
    return;
  }

  let sum = 0;
  list.innerHTML = cart.map(item => {
    const subtotal = item.qty * item.price;
    sum += subtotal;
    return `<li>${item.name} x ${item.qty} <strong class="ms-1">${formatMoney(subtotal)}</strong></li>`;
  }).join('');
  total.textContent = formatMoney(sum);
}

function bindProductSearchAndAdd() {
  const search = document.getElementById('productSearch');
  const placeBtn = document.getElementById('placeOrderBtn');
  const products = read(Store.products, []);

  renderProductsTable(products);
  renderCart();

  if (search) {
    search.addEventListener('input', () => {
      const q = search.value.trim().toLowerCase();
      const filtered = products.filter(p => p.name.toLowerCase().includes(q) || p.category.toLowerCase().includes(q));
      renderProductsTable(filtered);
    });
  }

  document.addEventListener('click', event => {
    const btn = event.target.closest('.js-add');
    if (!btn) return;

    const id = Number(btn.dataset.id);
    const product = read(Store.products, []).find(p => p.id === id);
    const qtyInput = document.getElementById(`qty-${id}`);
    const qty = Number(qtyInput ? qtyInput.value : 1);

    if (!product || qty < 1) {
      showFeedback('Invalid quantity.', true);
      return;
    }

    if (qty > product.stock) {
      showFeedback('Quantity exceeds available stock.', true);
      return;
    }

    const existing = cart.find(c => c.productId === id);
    if (existing) {
      existing.qty += qty;
    } else {
      cart.push({ productId: id, name: product.name, qty, price: product.price });
    }

    renderCart();
    showFeedback(`${product.name} added to order basket.`);
  });

  if (placeBtn) {
    placeBtn.addEventListener('click', () => {
      const user = currentUser();
      if (!user || user.role !== 'customer') {
        showFeedback('Please sign in as customer before placing an order.', true);
        return;
      }

      if (!cart.length) {
        showFeedback('Your order basket is empty.', true);
        return;
      }

      const productsCurrent = read(Store.products, []);
      for (const item of cart) {
        const p = productsCurrent.find(x => x.id === item.productId);
        if (!p || p.stock < item.qty) {
          showFeedback(`Stock not available for ${item.name}.`, true);
          return;
        }
      }

      cart.forEach(item => {
        const p = productsCurrent.find(x => x.id === item.productId);
        p.stock -= item.qty;
      });
      write(Store.products, productsCurrent);

      const orders = read(Store.orders, []);
      const total = cart.reduce((sum, i) => sum + i.qty * i.price, 0);
      const newOrder = {
        id: Date.now(),
        customerEmail: user.email,
        customerId: user.userId,
        items: cart.map(i => ({ ...i })),
        total,
        status: 'pending',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      orders.unshift(newOrder);
      write(Store.orders, orders);
      cart.length = 0;
      renderCart();
      renderProductsTable(read(Store.products, []));
      showFeedback('Order submitted successfully. Payment is handled offline.', false);
    });
  }
}

function renderCustomerOrders() {
  const tbody = document.getElementById('customerOrdersBody');
  if (!tbody) return;
  if (!requireRole('customer')) return;

  const user = currentUser();
  const orders = read(Store.orders, []).filter(o => o.customerEmail === user.email);

  if (!orders.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-muted">No orders yet.</td></tr>';
    return;
  }

  tbody.innerHTML = orders.map(order => {
    const items = order.items.map(i => `${i.name} x ${i.qty}`).join(', ');
    return `
      <tr>
        <td>#${order.id}</td>
        <td>${items}</td>
        <td>${formatMoney(order.total)}</td>
        <td>${statusBadge(order.status)}</td>
        <td>${new Date(order.updatedAt).toLocaleString()}</td>
      </tr>
    `;
  }).join('');
}

function renderStaffDashboard() {
  const pendingBody = document.getElementById('pendingOrdersBody');
  if (!pendingBody) return;
  if (!requireRole('staff')) return;

  const orders = read(Store.orders, []);
  const products = read(Store.products, []);
  const pending = orders.filter(o => o.status === 'pending').length;
  const processing = orders.filter(o => o.status === 'processing').length;
  const completed = orders.filter(o => o.status === 'completed').length;
  const lowStock = products.filter(p => p.stock < 10).length;

  const map = {
    kpiPending: pending,
    kpiProcessing: processing,
    kpiCompleted: completed,
    kpiLowStock: lowStock
  };

  Object.entries(map).forEach(([id, value]) => {
    const el = document.getElementById(id);
    if (el) el.textContent = String(value);
  });

  const pendingOrders = orders.filter(o => o.status === 'pending').slice(0, 6);
  if (!pendingOrders.length) {
    pendingBody.innerHTML = '<tr><td colspan="4" class="text-muted">No pending orders.</td></tr>';
    return;
  }

  pendingBody.innerHTML = pendingOrders.map(order => `
    <tr>
      <td>#${order.id}</td>
      <td>${order.customerId}</td>
      <td>${formatMoney(order.total)}</td>
      <td>${new Date(order.createdAt).toLocaleString()}</td>
    </tr>
  `).join('');
}

function renderStaffOrders() {
  const tbody = document.getElementById('staffOrdersBody');
  if (!tbody) return;
  if (!requireRole('staff')) return;

  const orders = read(Store.orders, []);
  const filter = document.querySelector('.filter-btn.active')?.dataset.filter || 'all';
  const shown = filter === 'all' ? orders : orders.filter(o => o.status === filter);

  if (!shown.length) {
    tbody.innerHTML = '<tr><td colspan="8" class="text-muted">No orders for this filter.</td></tr>';
    return;
  }

  tbody.innerHTML = shown.map(order => {
    const itemsHtml = order.items.map(item => {
      const subtotal = item.qty * item.price;
      return `
        <li>
          <span>${item.name}</span>
          <span>${item.qty} x ${formatMoney(item.price)} = <strong>${formatMoney(subtotal)}</strong></span>
        </li>
      `;
    }).join('');

    return `
    <tr class="order-row-main">
      <td>#${order.id}</td>
      <td>${order.customerId}</td>
      <td>${order.items.length}</td>
      <td>${formatMoney(order.total)}</td>
      <td>${statusBadge(order.status)}</td>
      <td>
        <button
          type="button"
          class="btn-soft js-toggle-details"
          data-order-id="${order.id}"
          aria-expanded="false"
          aria-controls="details-${order.id}">
          View
        </button>
      </td>
      <td>
        <label class="visually-hidden" for="status-${order.id}">Update status for order ${order.id}</label>
        <select id="status-${order.id}" class="form-select form-select-sm" data-order-id="${order.id}">
          <option value="pending" ${order.status === 'pending' ? 'selected' : ''}>pending</option>
          <option value="processing" ${order.status === 'processing' ? 'selected' : ''}>processing</option>
          <option value="completed" ${order.status === 'completed' ? 'selected' : ''}>completed</option>
          <option value="cancelled" ${order.status === 'cancelled' ? 'selected' : ''}>cancelled</option>
        </select>
      </td>
      <td><button type="button" class="btn-soft js-update-order" data-order-id="${order.id}">Update</button></td>
    </tr>
    <tr id="details-${order.id}" class="order-details-row" hidden>
      <td colspan="8">
        <div class="order-details">
          <p class="mb-2"><strong>Purchased Items</strong></p>
          <ul class="order-items-list mb-0">
            ${itemsHtml}
          </ul>
        </div>
      </td>
    </tr>
  `;
  }).join('');
}

function bindStaffOrders() {
  const wrap = document.getElementById('staffOrdersArea');
  if (!wrap) return;

  wrap.addEventListener('click', event => {
    const filterBtn = event.target.closest('.filter-btn');
    if (filterBtn) {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      filterBtn.classList.add('active');
      renderStaffOrders();
      return;
    }

    const detailsBtn = event.target.closest('.js-toggle-details');
    if (detailsBtn) {
      const id = detailsBtn.dataset.orderId;
      const row = document.getElementById(`details-${id}`);
      if (!row) return;
      const isOpen = !row.hidden;
      row.hidden = isOpen;
      detailsBtn.setAttribute('aria-expanded', String(!isOpen));
      detailsBtn.textContent = isOpen ? 'View' : 'Hide';
      return;
    }

    const updateBtn = event.target.closest('.js-update-order');
    if (!updateBtn) return;

    const id = Number(updateBtn.dataset.orderId);
    const select = document.getElementById(`status-${id}`);
    if (!select) return;

    const orders = read(Store.orders, []);
    const target = orders.find(o => o.id === id);
    if (!target) return;

    target.status = select.value;
    target.updatedAt = new Date().toISOString();
    write(Store.orders, orders);
    renderStaffOrders();
    showFeedback(`Order #${id} updated to ${target.status}.`);
  });
}

function renderInventory() {
  const tbody = document.getElementById('inventoryBody');
  if (!tbody) return;
  if (!requireRole('staff')) return;

  const products = read(Store.products, []);
  tbody.innerHTML = products.map(p => {
    let status = 'In Stock';
    let badge = 'status-completed';
    if (p.stock === 0) {
      status = 'Out of Stock';
      badge = 'status-cancelled';
    } else if (p.stock < 10) {
      status = 'Low Stock';
      badge = 'status-pending';
    }

    return `
      <tr>
        <td>${p.name}</td>
        <td>${p.category}</td>
        <td>${formatMoney(p.price)}</td>
        <td>${p.stock}</td>
        <td><span class="status-badge ${badge}">${status}</span></td>
        <td>
          <div class="d-flex gap-1">
            <label class="visually-hidden" for="delta-${p.id}">Adjust stock for ${p.name}</label>
            <input id="delta-${p.id}" type="number" value="1" min="1" class="form-control form-control-sm stock-delta">
            <button type="button" class="btn-soft js-stock" data-id="${p.id}" data-mode="in">+In</button>
            <button type="button" class="btn-soft js-stock" data-id="${p.id}" data-mode="out">-Out</button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function bindInventory() {
  const area = document.getElementById('inventoryArea');
  const search = document.getElementById('inventorySearch');
  if (!area) return;

  area.addEventListener('click', event => {
    const btn = event.target.closest('.js-stock');
    if (!btn) return;

    const id = Number(btn.dataset.id);
    const mode = btn.dataset.mode;
    const deltaInput = document.getElementById(`delta-${id}`);
    const delta = Number(deltaInput ? deltaInput.value : 1);

    if (!delta || delta < 1) {
      showFeedback('Adjustment value must be greater than zero.', true);
      return;
    }

    const products = read(Store.products, []);
    const target = products.find(p => p.id === id);
    if (!target) return;

    if (mode === 'in') {
      target.stock += delta;
    } else {
      target.stock = Math.max(0, target.stock - delta);
    }

    write(Store.products, products);
    renderInventory();
    showFeedback(`Stock updated for ${target.name}.`);
  });

  if (search) {
    search.addEventListener('input', () => {
      const q = search.value.trim().toLowerCase();
      document.querySelectorAll('#inventoryBody tr').forEach(row => {
        const name = row.children[0].textContent.toLowerCase();
        row.hidden = q ? !name.includes(q) : false;
      });
    });
  }
}

function init() {
  bootstrapData();
  renderUserId();
  bindLogout();
  registerAccount('registerForm', 'customer');
  registerAccount('staffRegisterForm', 'staff');
  bindCustomerLogin();
  bindStaffLogin();
  bindProductSearchAndAdd();
  renderCustomerOrders();
  renderStaffDashboard();
  renderStaffOrders();
  bindStaffOrders();
  renderInventory();
  bindInventory();
}

document.addEventListener('DOMContentLoaded', init);
