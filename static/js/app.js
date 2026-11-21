/**
 * PageVault - Main Application Entrypoint
 * Handles Cart Drawer, Transactional Checkout, Wishlist, and Book Details
 */

/**
 * PaymentGateway Simulator
 * Provides authentic, interactive demo transaction screens for bKash, Nagad, and Debit/Credit Card.
 */
const PaymentGateway = {
  activeMethod: null,
  orderPayload: null,
  totalAmount: 0,
  currentStep: 1,
  timerInterval: null,
  timerSeconds: 45,

  open(method, orderPayload, totalAmount) {
    this.activeMethod = method;
    this.orderPayload = orderPayload;
    this.totalAmount = totalAmount;
    this.currentStep = 1;

    const modal = document.getElementById('payment-gateway-modal');
    if (!modal) return;

    // Set top bar styling & branding
    const topBar = document.getElementById('pg-top-bar');
    const brandLogoArea = document.getElementById('pg-brand-logo-area');
    const amountVal = document.getElementById('pg-display-amount');
    const invoiceRef = document.getElementById('pg-invoice-ref');

    if (topBar) {
      topBar.className = 'pg-top-bar';
      if (method === 'bKash') topBar.classList.add('bkash-theme');
      else if (method === 'Nagad') topBar.classList.add('nagad-theme');
      else topBar.classList.add('card-theme');
    }

    if (amountVal) amountVal.textContent = `৳${totalAmount.toFixed(2)}`;
    if (invoiceRef) invoiceRef.textContent = `PV-${Math.floor(100000 + Math.random() * 900000)}`;

    if (brandLogoArea) {
      if (method === 'bKash') {
        brandLogoArea.innerHTML = `<span class="pg-brand-badge" style="color: #FFFFFF;">bKash</span>`;
      } else if (method === 'Nagad') {
        brandLogoArea.innerHTML = `<span class="pg-brand-badge" style="color: #FFFFFF;">নগদ Nagad</span>`;
      } else {
        brandLogoArea.innerHTML = `<span class="pg-brand-badge" style="color: #FFFFFF;">VISA / MasterCard</span>`;
      }
    }

    this.renderStep();
    modal.classList.add('active');
  },

  cancel() {
    this.clearTimer();
    const modal = document.getElementById('payment-gateway-modal');
    if (modal) modal.classList.remove('active');
    showToast('Payment process cancelled. Cart items retained.', 'info');
  },

  clearTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  },

  startTimer(resendElId) {
    this.clearTimer();
    this.timerSeconds = 45;
    const el = document.getElementById(resendElId);
    if (!el) return;
    el.textContent = `(0:${this.timerSeconds < 10 ? '0' : ''}${this.timerSeconds})`;

    this.timerInterval = setInterval(() => {
      this.timerSeconds--;
      if (this.timerSeconds <= 0) {
        this.clearTimer();
        const curEl = document.getElementById(resendElId);
        if (curEl) curEl.innerHTML = `<a href="javascript:void(0)" class="pg-resend-link" onclick="PaymentGateway.resendOtp('${resendElId}')">Resend Code</a>`;
      } else {
        const curEl = document.getElementById(resendElId);
        if (curEl) curEl.textContent = `(0:${this.timerSeconds < 10 ? '0' : ''}${this.timerSeconds})`;
      }
    }, 1000);
  },

  resendOtp(resendElId) {
    showToast('New verification code sent: 123456', 'info');
    this.startTimer(resendElId);
  },

  renderStep() {
    const container = document.getElementById('pg-view-container');
    if (!container) return;

    if (this.activeMethod === 'bKash') {
      this.renderBkash(container);
    } else if (this.activeMethod === 'Nagad') {
      this.renderNagad(container);
    } else {
      this.renderCard(container);
    }
  },

  // ---------------------------------------------------------------------------
  // bKash Flow
  // ---------------------------------------------------------------------------
  renderBkash(container) {
    if (this.currentStep === 1) {
      const defaultPhone = this.orderPayload.customer_phone || '01712345678';
      container.innerHTML = `
        <div class="pg-view-title">bKash Account Number</div>
        <div class="pg-view-subtitle">Enter your personal bKash wallet account number to initiate checkout.</div>
        <div class="pg-form-group">
          <label class="pg-label">bKash Mobile Number</label>
          <input type="tel" id="bkash-phone" class="pg-input" value="${defaultPhone}" placeholder="01XXXXXXXXX" maxlength="11">
          <span class="pg-demo-hint">&#128276; Demo Mode: Any 11-digit mobile number works</span>
        </div>
        <div style="font-size: 0.74rem; color: #64748B; margin-top: 10px; line-height: 1.4;">
          By clicking <strong>Confirm</strong>, you agree to the Terms &amp; Conditions of bKash payment gateway.
        </div>
        <div class="pg-btn-row">
          <button type="button" class="pg-btn pg-btn-cancel" onclick="PaymentGateway.cancel()">Close</button>
          <button type="button" class="pg-btn pg-btn-bkash" onclick="PaymentGateway.onBkashStep1()">Confirm</button>
        </div>
      `;
    } else if (this.currentStep === 2) {
      container.innerHTML = `
        <div class="pg-view-title">bKash Verification Code</div>
        <div class="pg-view-subtitle">A 6-digit verification code has been sent to your bKash mobile number.</div>
        <div class="pg-form-group">
          <label class="pg-label">Verification Code (OTP)</label>
          <input type="text" id="bkash-otp" class="pg-input pg-input-otp" placeholder="1 2 3 4 5 6" maxlength="6" value="123456">
          <div class="pg-timer-row">
            <span>Demo OTP: <strong>123456</strong></span>
            <span id="bkash-timer-span">(0:45)</span>
          </div>
        </div>
        <div class="pg-btn-row">
          <button type="button" class="pg-btn pg-btn-cancel" onclick="PaymentGateway.goToStep(1)">Back</button>
          <button type="button" class="pg-btn pg-btn-bkash" onclick="PaymentGateway.onBkashStep2()">Verify OTP</button>
        </div>
      `;
      this.startTimer('bkash-timer-span');
    } else if (this.currentStep === 3) {
      container.innerHTML = `
        <div class="pg-view-title">Enter bKash PIN</div>
        <div class="pg-view-subtitle">Enter your 5-digit bKash PIN to confirm payment authorization.</div>
        <div class="pg-form-group">
          <label class="pg-label">bKash PIN</label>
          <input type="password" id="bkash-pin" class="pg-input pg-input-otp" placeholder="• • • • •" maxlength="5" value="12345">
          <span class="pg-demo-hint">&#128274; Demo PIN: <strong>12345</strong> (bKash never discloses your PIN)</span>
        </div>
        <div class="pg-btn-row">
          <button type="button" class="pg-btn pg-btn-cancel" onclick="PaymentGateway.goToStep(2)">Back</button>
          <button type="button" class="pg-btn pg-btn-bkash" onclick="PaymentGateway.onBkashStep3()">Confirm Payment</button>
        </div>
      `;
    } else if (this.currentStep === 4) {
      container.innerHTML = `
        <div class="pg-spinner-wrapper">
          <div class="pg-spinner"></div>
          <div style="font-weight: 800; font-size: 1.1rem; color: #0F172A; margin-bottom: 6px;">Processing Payment...</div>
          <div style="font-size: 0.85rem; color: #64748B;">Connecting to bKash Secure Gateway &amp; Verifying Transaction...</div>
        </div>
      `;
    }
  },

  onBkashStep1() {
    const phone = document.getElementById('bkash-phone').value.trim();
    if (!phone || phone.length < 11) {
      alert('Please enter a valid 11-digit bKash mobile number.');
      return;
    }
    this.goToStep(2);
  },

  onBkashStep2() {
    const otp = document.getElementById('bkash-otp').value.trim();
    if (!otp || otp.length < 4) {
      alert('Please enter the 6-digit OTP code (Demo: 123456).');
      return;
    }
    this.clearTimer();
    this.goToStep(3);
  },

  onBkashStep3() {
    const pin = document.getElementById('bkash-pin').value.trim();
    if (!pin || pin.length < 4) {
      alert('Please enter your bKash PIN (Demo: 12345).');
      return;
    }
    this.goToStep(4);
    setTimeout(() => {
      this.completeTransaction('BKSH');
    }, 1200);
  },

  // ---------------------------------------------------------------------------
  // Nagad Flow
  // ---------------------------------------------------------------------------
  renderNagad(container) {
    if (this.currentStep === 1) {
      const defaultPhone = this.orderPayload.customer_phone || '01812345678';
      container.innerHTML = `
        <div class="pg-view-title">Nagad Account Number</div>
        <div class="pg-view-subtitle">Enter your Nagad digital wallet number to proceed with transaction.</div>
        <div class="pg-form-group">
          <label class="pg-label">Nagad Mobile Number</label>
          <input type="tel" id="nagad-phone" class="pg-input" value="${defaultPhone}" placeholder="01XXXXXXXXX" maxlength="11">
          <span class="pg-demo-hint">&#128276; Demo Mode: Any 11-digit mobile number works</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px; margin-top: 10px; font-size: 0.78rem; color: #475569;">
          <input type="checkbox" id="nagad-terms" checked>
          <label for="nagad-terms">I agree to Nagad Merchant Payment Terms &amp; Policies</label>
        </div>
        <div class="pg-btn-row">
          <button type="button" class="pg-btn pg-btn-cancel" onclick="PaymentGateway.cancel()">Cancel</button>
          <button type="button" class="pg-btn pg-btn-nagad" onclick="PaymentGateway.onNagadStep1()">Proceed</button>
        </div>
      `;
    } else if (this.currentStep === 2) {
      container.innerHTML = `
        <div class="pg-view-title">Nagad One-Time Password (OTP)</div>
        <div class="pg-view-subtitle">Enter the 6-digit verification code sent to your registered Nagad number.</div>
        <div class="pg-form-group">
          <label class="pg-label">Nagad OTP</label>
          <input type="text" id="nagad-otp" class="pg-input pg-input-otp" placeholder="1 2 3 4 5 6" maxlength="6" value="123456">
          <div class="pg-timer-row">
            <span>Demo OTP: <strong>123456</strong></span>
            <span id="nagad-timer-span">(0:45)</span>
          </div>
        </div>
        <div class="pg-btn-row">
          <button type="button" class="pg-btn pg-btn-cancel" onclick="PaymentGateway.goToStep(1)">Back</button>
          <button type="button" class="pg-btn pg-btn-nagad" onclick="PaymentGateway.onNagadStep2()">Proceed</button>
        </div>
      `;
      this.startTimer('nagad-timer-span');
    } else if (this.currentStep === 3) {
      container.innerHTML = `
        <div class="pg-view-title">Enter Nagad PIN</div>
        <div class="pg-view-subtitle">Enter your 4-digit secret PIN to authorize the payment.</div>
        <div class="pg-form-group">
          <label class="pg-label">4-Digit PIN</label>
          <input type="password" id="nagad-pin" class="pg-input pg-input-otp" placeholder="• • • •" maxlength="4" value="1234">
          <span class="pg-demo-hint">&#128274; Demo PIN: <strong>1234</strong></span>
        </div>
        <div class="pg-btn-row">
          <button type="button" class="pg-btn pg-btn-cancel" onclick="PaymentGateway.goToStep(2)">Back</button>
          <button type="button" class="pg-btn pg-btn-nagad" onclick="PaymentGateway.onNagadStep3()">Complete Payment</button>
        </div>
      `;
    } else if (this.currentStep === 4) {
      container.innerHTML = `
        <div class="pg-spinner-wrapper">
          <div class="pg-spinner nagad-spinner"></div>
          <div style="font-weight: 800; font-size: 1.1rem; color: #0F172A; margin-bottom: 6px;">Authenticating with Nagad...</div>
          <div style="font-size: 0.85rem; color: #64748B;">Executing instant digital clearing via Bangladesh Post Office network...</div>
        </div>
      `;
    }
  },

  onNagadStep1() {
    const phone = document.getElementById('nagad-phone').value.trim();
    if (!phone || phone.length < 11) {
      alert('Please enter a valid 11-digit Nagad phone number.');
      return;
    }
    const terms = document.getElementById('nagad-terms');
    if (terms && !terms.checked) {
      alert('Please accept terms and conditions to proceed.');
      return;
    }
    this.goToStep(2);
  },

  onNagadStep2() {
    const otp = document.getElementById('nagad-otp').value.trim();
    if (!otp || otp.length < 4) {
      alert('Please enter OTP (Demo: 123456).');
      return;
    }
    this.clearTimer();
    this.goToStep(3);
  },

  onNagadStep3() {
    const pin = document.getElementById('nagad-pin').value.trim();
    if (!pin || pin.length < 4) {
      alert('Please enter your 4-digit PIN (Demo: 1234).');
      return;
    }
    this.goToStep(4);
    setTimeout(() => {
      this.completeTransaction('NAG');
    }, 1200);
  },

  // ---------------------------------------------------------------------------
  // Card Flow (Visa / Mastercard)
  // ---------------------------------------------------------------------------
  renderCard(container) {
    if (this.currentStep === 1) {
      const cardName = this.orderPayload.customer_name || 'Cardholder Name';
      container.innerHTML = `
        <div class="pg-view-title">Cardholder &amp; Payment Details</div>
        <div class="pg-view-subtitle">Enter your Visa or MasterCard debit/credit card details.</div>
        <div class="pg-form-group">
          <label class="pg-label">Cardholder Name</label>
          <input type="text" id="card-holder" class="pg-input" value="${cardName}" placeholder="Name as printed on card">
        </div>
        <div class="pg-form-group">
          <label class="pg-label">Card Number</label>
          <input type="text" id="card-number" class="pg-input" value="4532 8920 1827 9012" placeholder="XXXX XXXX XXXX XXXX" maxlength="19">
          <span class="pg-demo-hint">&#128179; Demo Visa Card: 4532 8920 1827 9012</span>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div class="pg-form-group">
            <label class="pg-label">Expiry (MM/YY)</label>
            <input type="text" id="card-exp" class="pg-input" value="12/28" placeholder="MM/YY" maxlength="5">
          </div>
          <div class="pg-form-group">
            <label class="pg-label">CVV / CVC</label>
            <input type="password" id="card-cvv" class="pg-input" value="789" placeholder="3 digits" maxlength="4">
          </div>
        </div>
        <div class="pg-btn-row">
          <button type="button" class="pg-btn pg-btn-cancel" onclick="PaymentGateway.cancel()">Cancel</button>
          <button type="button" class="pg-btn pg-btn-card" onclick="PaymentGateway.onCardStep1()">Pay ৳${this.totalAmount.toFixed(2)}</button>
        </div>
      `;
    } else if (this.currentStep === 2) {
      container.innerHTML = `
        <div class="pg-view-title">3D Secure Bank Authentication</div>
        <div class="pg-view-subtitle">Verified by Visa / MasterCard Identity Check. Enter the authentication code sent to your registered mobile.</div>
        <div class="pg-form-group">
          <label class="pg-label">One-Time Passcode (OTP)</label>
          <input type="text" id="card-otp" class="pg-input pg-input-otp" placeholder="1 2 3 4 5 6" maxlength="6" value="123456">
          <span class="pg-demo-hint">&#128274; Demo Bank OTP: <strong>123456</strong></span>
        </div>
        <div class="pg-btn-row">
          <button type="button" class="pg-btn pg-btn-cancel" onclick="PaymentGateway.goToStep(1)">Back</button>
          <button type="button" class="pg-btn pg-btn-card" onclick="PaymentGateway.onCardStep2()">Submit OTP</button>
        </div>
      `;
    } else if (this.currentStep === 3) {
      container.innerHTML = `
        <div class="pg-spinner-wrapper">
          <div class="pg-spinner card-spinner"></div>
          <div style="font-weight: 800; font-size: 1.1rem; color: #0F172A; margin-bottom: 6px;">Authorizing Payment...</div>
          <div style="font-size: 0.85rem; color: #64748B;">Processing 256-bit encrypted clearance through card network...</div>
        </div>
      `;
    }
  },

  onCardStep1() {
    const cardNum = document.getElementById('card-number').value.trim();
    if (!cardNum || cardNum.length < 12) {
      alert('Please enter a valid card number.');
      return;
    }
    this.goToStep(2);
  },

  onCardStep2() {
    const otp = document.getElementById('card-otp').value.trim();
    if (!otp || otp.length < 4) {
      alert('Please enter the OTP (Demo: 123456).');
      return;
    }
    this.goToStep(3);
    setTimeout(() => {
      this.completeTransaction('CARD');
    }, 1200);
  },

  // ---------------------------------------------------------------------------
  // Transition & Completion
  // ---------------------------------------------------------------------------
  goToStep(step) {
    this.currentStep = step;
    this.renderStep();
  },

  completeTransaction(prefix) {
    this.clearTimer();
    const modal = document.getElementById('payment-gateway-modal');
    if (modal) modal.classList.remove('active');

    // Generate realistic transaction ID (e.g. BKSH-9A82B310)
    const randomHex = Math.random().toString(36).substring(2, 10).toUpperCase();
    const trxId = `${prefix}-${randomHex}`;

    // Attach transaction ID to order payload and complete order placement
    const payload = Object.assign({}, this.orderPayload, { transaction_id: trxId });
    App.executeOrderPlacement(payload);
  }
};

const App = {
  cart: [],
  wishlist: [],
  deliveryFee: 60.0,
  deliveryZoneName: 'Dhaka',

  init() {
    this.loadState();
    this.bindGlobalEvents();
    this.loadCategories();
    Auth.init();
    SearchEngine.init();
    this.updateCartBadge();
    this.updateWishlistBadge();
  },

  loadState() {
    try {
      const storedCart = localStorage.getItem('pagevault_cart');
      if (storedCart) this.cart = JSON.parse(storedCart);
    } catch (e) {
      this.cart = [];
    }

    try {
      const storedWishlist = localStorage.getItem('pagevault_wishlist');
      if (storedWishlist) this.wishlist = JSON.parse(storedWishlist);
    } catch (e) {
      this.wishlist = [];
    }
  },

  saveCart() {
    localStorage.setItem('pagevault_cart', JSON.stringify(this.cart));
    this.updateCartBadge();
    this.renderCartDrawer();
  },

  saveWishlist() {
    localStorage.setItem('pagevault_wishlist', JSON.stringify(this.wishlist));
    this.updateWishlistBadge();
  },

  updateCartBadge() {
    const totalCount = this.cart.reduce((sum, item) => sum + item.quantity, 0);
    const badge = document.getElementById('cart-count');
    const drawerCount = document.getElementById('drawer-items-count');
    if (badge) badge.textContent = totalCount;
    if (drawerCount) drawerCount.textContent = totalCount;
  },

  updateWishlistBadge() {
    const badge = document.getElementById('wishlist-count');
    const modalCount = document.getElementById('wishlist-modal-count');
    if (badge) badge.textContent = this.wishlist.length;
    if (modalCount) modalCount.textContent = this.wishlist.length;
  },

  // -------------------------------------------------------------------------
  // Sidebar Navigation (Desktop Collapse & Mobile Responsive Drawer)
  // -------------------------------------------------------------------------
  toggleSidebar(e) {
    if (e && typeof e.stopPropagation === 'function') {
      e.stopPropagation();
    }
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const toggleBtn = document.getElementById('sidebar-toggle-btn');
    if (!sidebar) return;

    if (window.innerWidth <= 900) {
      const isOpen = sidebar.classList.contains('mobile-open');
      if (isOpen) {
        this.closeMobileSidebar(e);
      } else {
        sidebar.classList.add('mobile-open');
        if (overlay) overlay.classList.add('active');
        if (toggleBtn) toggleBtn.classList.add('active');
        document.body.classList.add('sidebar-open-locked');
      }
    } else {
      sidebar.classList.toggle('collapsed');
    }
  },

  closeMobileSidebar(e) {
    if (e && typeof e.stopPropagation === 'function') {
      e.stopPropagation();
    }
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const toggleBtn = document.getElementById('sidebar-toggle-btn');
    if (sidebar) sidebar.classList.remove('mobile-open');
    if (overlay) overlay.classList.remove('active');
    if (toggleBtn) toggleBtn.classList.remove('active');
    document.body.classList.remove('sidebar-open-locked');
  },

  bindGlobalEvents() {
    // Sidebar toggle (desktop collapse + mobile toggle)
    const toggleBtn = document.getElementById('sidebar-toggle-btn');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', (e) => this.toggleSidebar(e));
    }

    // Mobile sidebar overlay touch / click dismissal
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    if (sidebarOverlay) {
      sidebarOverlay.addEventListener('click', (e) => this.closeMobileSidebar(e));
      sidebarOverlay.addEventListener('touchstart', (e) => this.closeMobileSidebar(e), { passive: true });
    }

    // Mobile sidebar header 3-bar and close buttons
    const mobileCloseBtn = document.getElementById('sidebar-close-btn');
    if (mobileCloseBtn) {
      mobileCloseBtn.addEventListener('click', (e) => this.closeMobileSidebar(e));
    }

    const mobileToggleBtn = document.getElementById('sidebar-mobile-toggle-btn');
    if (mobileToggleBtn) {
      mobileToggleBtn.addEventListener('click', (e) => this.closeMobileSidebar(e));
    }

    // Tap/click randomly anywhere outside sidebar on phone to dismiss immediately
    const handleOutsideSidebarClick = (e) => {
      if (window.innerWidth > 900) return;
      const sidebar = document.getElementById('sidebar');
      if (!sidebar || !sidebar.classList.contains('mobile-open')) return;
      const tBtn = document.getElementById('sidebar-toggle-btn');
      if (sidebar.contains(e.target)) return;
      if (tBtn && (tBtn === e.target || tBtn.contains(e.target))) return;
      this.closeMobileSidebar(e);
    };

    document.addEventListener('click', handleOutsideSidebarClick);
    document.addEventListener('touchstart', handleOutsideSidebarClick, { passive: true });

    // Escape key closes mobile sidebar
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        const sidebar = document.getElementById('sidebar');
        if (sidebar && sidebar.classList.contains('mobile-open')) {
          this.closeMobileSidebar(e);
        }
      }
    });

    // Modal background click to close
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
          overlay.classList.remove('active');
        }
      });
    });

    // Close buttons on all modals
    document.querySelectorAll('.modal-close-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const modal = btn.closest('.modal-overlay');
        if (modal) modal.classList.remove('active');
      });
    });

    // Cart button in top navbar
    const cartBtn = document.getElementById('open-cart-btn');
    if (cartBtn) {
      cartBtn.addEventListener('click', () => this.openCartDrawer());
    }

    // Wishlist button in top navbar
    const wishlistBtn = document.getElementById('open-wishlist-btn');
    if (wishlistBtn) {
      wishlistBtn.addEventListener('click', () => this.openWishlistModal());
    }

    // Admin button in top navbar
    const adminBtn = document.getElementById('open-admin-btn');
    if (adminBtn) {
      adminBtn.addEventListener('click', () => this.openAdminDashboard());
    }

    // Add Book Nav button
    const addBookNavBtn = document.getElementById('add-book-nav-btn');
    if (addBookNavBtn) {
      addBookNavBtn.addEventListener('click', () => this.openCreateBookModal());
    }

    // Book CRUD Form submit
    const crudForm = document.getElementById('book-crud-form');
    if (crudForm) {
      crudForm.addEventListener('submit', (e) => this.handleBookCrudSubmit(e));
    }

    // Checkout Form submit
    const checkoutForm = document.getElementById('checkout-form');
    if (checkoutForm) {
      checkoutForm.addEventListener('submit', (e) => this.handleCheckoutSubmit(e));
    }
  },

  async loadCategories() {
    const list = document.getElementById('categories-filter-list');
    if (!list) return;

    try {
      const res = await fetch('/api/categories');
      const data = await res.json();
      const categories = data.categories || [];

      let html = `
        <li>
          <button class="filter-item-btn category-filter-btn active" data-category-id="all" onclick="SearchEngine.selectCategory(null)">
            <span>All Disciplines</span>
            <span class="filter-badge">All</span>
          </button>
        </li>
      `;

      categories.forEach(c => {
        html += `
          <li>
            <button class="filter-item-btn category-filter-btn" data-category-id="${c.category_id}" onclick="SearchEngine.selectCategory(${c.category_id})">
              <span>${c.name}</span>
              <span class="filter-badge">${c.book_count}</span>
            </button>
          </li>
        `;
      });

      list.innerHTML = html;

      this.categories = categories;

      // Populate category dropdown in CRUD Book form
      const select = document.getElementById('crud-book-category');
      if (select) {
        select.innerHTML = categories.map(c => `<option value="${c.category_id}">${escapeHtml(c.name)}</option>`).join('');
      }
    } catch (err) {
      console.error('Error loading categories:', err);
    }
  },

  // -------------------------------------------------------------------------
  // Cart Drawer Logic
  // -------------------------------------------------------------------------
  openCartDrawer() {
    const drawer = document.getElementById('cart-drawer');
    const overlay = document.getElementById('cart-drawer-overlay');
    if (drawer && overlay) {
      this.renderCartDrawer();
      drawer.classList.add('active');
      overlay.classList.add('active');
    }
  },

  closeCartDrawer() {
    const drawer = document.getElementById('cart-drawer');
    const overlay = document.getElementById('cart-drawer-overlay');
    if (drawer && overlay) {
      drawer.classList.remove('active');
      overlay.classList.remove('active');
    }
  },

  addToCart(bookId, title, price, coverImage) {
    const existing = this.cart.find(item => item.bookId === bookId);
    if (existing) {
      existing.quantity += 1;
    } else {
      this.cart.push({
        bookId: bookId,
        title: title,
        price: parseFloat(price),
        coverImage: coverImage || '/static/img/book-placeholder.svg',
        quantity: 1
      });
    }
    this.saveCart();
    showToast(`Added "${title}" to your cart!`, 'success');
  },

  changeQuantity(bookId, delta) {
    const item = this.cart.find(i => i.bookId === bookId);
    if (!item) return;

    item.quantity += delta;
    if (item.quantity <= 0) {
      this.cart = this.cart.filter(i => i.bookId !== bookId);
    }
    this.saveCart();
  },

  removeFromCart(bookId) {
    this.cart = this.cart.filter(i => i.bookId !== bookId);
    this.saveCart();
    showToast('Item removed from cart.', 'info');
  },

  updateDeliveryZone(fee, zoneName) {
    this.deliveryFee = parseFloat(fee);
    this.deliveryZoneName = zoneName;
    this.renderCartDrawer();
  },

  renderCartDrawer() {
    const container = document.getElementById('cart-drawer-items');
    const subtotalEl = document.getElementById('drawer-subtotal');
    const deliveryEl = document.getElementById('drawer-delivery-fee');
    const totalEl = document.getElementById('drawer-total-amount');
    const checkoutBtn = document.getElementById('proceed-checkout-btn');

    if (!container) return;

    if (this.cart.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 60px 20px; color: #64748b;">
          <div style="font-size: 3rem; margin-bottom: 12px;">🛒</div>
          <h4 style="font-size: 1.1rem; color: #0f172a; margin-bottom: 6px;">Your Cart is Empty</h4>
          <p style="font-size: 0.85rem; margin-bottom: 16px;">Explore our catalog of 27 titles and add books to read!</p>
          <button class="auth-btn auth-btn-primary" onclick="App.closeCartDrawer()">Start Browsing</button>
        </div>
      `;
      if (subtotalEl) subtotalEl.textContent = '৳0.00';
      if (totalEl) totalEl.textContent = '৳0.00';
      if (checkoutBtn) checkoutBtn.disabled = true;
      return;
    }

    if (checkoutBtn) checkoutBtn.disabled = false;

    let subtotal = 0;

    container.innerHTML = this.cart.map(item => {
      const itemTotal = item.price * item.quantity;
      subtotal += itemTotal;

      return `
        <div class="cart-item-card">
          <img class="cart-item-img" src="${item.coverImage}" alt="${escapeHtml(item.title)}" onerror="this.onerror=null; this.src='/static/img/book-placeholder.svg';" />
          <div class="cart-item-details">
            <h4 class="cart-item-title">${escapeHtml(item.title)}</h4>
            <div class="cart-item-price">৳${item.price.toFixed(2)}</div>
            <div class="cart-item-qty-row">
              <div class="qty-control">
                <button class="qty-btn" onclick="App.changeQuantity(${item.bookId}, -1)">−</button>
                <span class="qty-val">${item.quantity}</span>
                <button class="qty-btn" onclick="App.changeQuantity(${item.bookId}, 1)">+</button>
              </div>
              <button class="item-delete-btn" title="Remove Item" onclick="App.removeFromCart(${item.bookId})">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
              </button>
            </div>
          </div>
        </div>
      `;
    }).join('');

    const grandTotal = subtotal + this.deliveryFee;

    if (subtotalEl) subtotalEl.textContent = `৳${subtotal.toFixed(2)}`;
    if (deliveryEl) deliveryEl.textContent = `৳${this.deliveryFee.toFixed(2)}`;
    if (totalEl) totalEl.textContent = `৳${grandTotal.toFixed(2)}`;
  },

  // -------------------------------------------------------------------------
  // Checkout & Order Placement (ACID Transactional Fulfillment)
  // -------------------------------------------------------------------------
  openCheckoutModal() {
    if (this.cart.length === 0) {
      showToast('Your cart is empty. Please add books before checkout.', 'error');
      return;
    }

    this.closeCartDrawer();
    const modal = document.getElementById('checkout-modal');
    if (!modal) return;

    // Auto-fill logged in user info if available
    if (Auth.currentUser) {
      const nameField = document.getElementById('checkout-name');
      if (nameField && !nameField.value) nameField.value = Auth.currentUser.full_name;
      const emailField = document.getElementById('checkout-email');
      if (emailField && !emailField.value) emailField.value = Auth.currentUser.email;
    }

    const subtotal = this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const total = subtotal + this.deliveryFee;
    const payableTotal = document.getElementById('checkout-payable-total');
    if (payableTotal) payableTotal.textContent = `৳${total.toFixed(2)}`;

    modal.classList.add('active');
  },

  closeCheckoutModal() {
    const modal = document.getElementById('checkout-modal');
    if (modal) modal.classList.remove('active');
  },

  onDistrictChange(district) {
    if (district === 'Dhaka') {
      this.deliveryFee = 60.0;
      this.deliveryZoneName = 'Dhaka';
    } else {
      this.deliveryFee = 120.0;
      this.deliveryZoneName = 'Outside Dhaka';
    }

    const subtotal = this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const total = subtotal + this.deliveryFee;
    const payableTotal = document.getElementById('checkout-payable-total');
    if (payableTotal) payableTotal.textContent = `৳${total.toFixed(2)}`;
  },

  async handleCheckoutSubmit(e) {
    e.preventDefault();

    if (this.cart.length === 0) {
      showToast('Your shopping cart is empty.', 'error');
      return;
    }

    const name = document.getElementById('checkout-name').value.trim();
    const phone = document.getElementById('checkout-phone').value.trim();
    const email = document.getElementById('checkout-email') ? document.getElementById('checkout-email').value.trim() : '';
    const address = document.getElementById('checkout-address').value.trim();
    const district = document.getElementById('checkout-district').value;
    const paymentRadio = document.querySelector('input[name="payment-method"]:checked');
    const paymentMethod = paymentRadio ? paymentRadio.value : 'Cash on Delivery';

    const subtotal = this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const totalAmount = subtotal + this.deliveryFee;

    const orderPayload = {
      customer_name: name,
      customer_phone: phone,
      customer_email: email,
      delivery_address: address,
      district: district,
      payment_method: paymentMethod,
      user_id: Auth.currentUser ? Auth.currentUser.user_id : null,
      items: this.cart.map(item => ({
        book_id: item.bookId,
        title: item.title,
        quantity: item.quantity,
        unit_price: item.price
      }))
    };

    if (paymentMethod === 'Cash on Delivery') {
      await this.executeOrderPlacement(orderPayload);
    } else {
      // Interactive simulated gateway for bKash, Nagad, or Debit/Credit Card
      this.closeCheckoutModal();
      PaymentGateway.open(paymentMethod, orderPayload, totalAmount);
    }
  },

  async executeOrderPlacement(orderPayload) {
    try {
      const res = await fetch('/api/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderPayload)
      });
      const data = await res.json();

      if (res.ok && data.success) {
        // Order successfully committed to database
        this.closeCheckoutModal();

        // Clear cart
        this.cart = [];
        this.saveCart();

        // Open Success Modal
        const successModal = document.getElementById('order-success-modal');
        if (successModal) {
          const codeEl = document.getElementById('success-order-code');
          if (codeEl) codeEl.textContent = data.order_code;

          const nameEl = document.getElementById('success-customer-name');
          if (nameEl) nameEl.textContent = orderPayload.customer_name;

          const amtEl = document.getElementById('success-total-amount');
          if (amtEl) amtEl.textContent = `৳${data.total_amount.toFixed(2)}`;

          const payEl = document.getElementById('success-payment-method');
          if (payEl) payEl.textContent = orderPayload.payment_method;

          const trxEl = document.getElementById('success-transaction-id');
          if (trxEl) {
            trxEl.textContent = data.transaction_id || orderPayload.transaction_id || 'N/A (Cash on Delivery)';
          }

          const statusEl = document.getElementById('success-payment-status');
          if (statusEl) {
            if (orderPayload.payment_method === 'Cash on Delivery') {
              statusEl.className = 'status-badge status-confirmed';
              statusEl.textContent = 'Pending (Pay on Delivery)';
            } else {
              statusEl.className = 'badge-status-paid';
              statusEl.innerHTML = '&#10003; Paid &amp; Verified';
            }
          }
          successModal.classList.add('active');
        }

        // Re-execute search to reflect freshly decremented stock quantities
        SearchEngine.executeSearch();
      } else {
        showToast(data.message || 'Error processing your order.', 'error');
      }
    } catch (err) {
      showToast('Network error processing checkout.', 'error');
    }
  },

  closeOrderSuccessModal() {
    const modal = document.getElementById('order-success-modal');
    if (modal) modal.classList.remove('active');
  },

  // -------------------------------------------------------------------------
  // Wishlist Logic
  // -------------------------------------------------------------------------
  toggleWishlist(bookId, e) {
    if (e) e.stopPropagation();

    const idx = this.wishlist.indexOf(bookId);
    if (idx > -1) {
      this.wishlist.splice(idx, 1);
      showToast('Removed from reading wishlist.', 'info');
    } else {
      this.wishlist.push(bookId);
      showToast('Saved to your reading wishlist! ♥', 'success');
    }
    this.saveWishlist();

    // Toggle heart icon state on active cards
    document.querySelectorAll(`.book-card[data-book-id="${bookId}"] .wishlist-toggle-btn`).forEach(btn => {
      const isNowWishlisted = this.wishlist.includes(bookId);
      btn.classList.toggle('active', isNowWishlisted);
      btn.innerHTML = isNowWishlisted ? '♥' : '♡';
    });
  },

  async openWishlistModal() {
    const modal = document.getElementById('wishlist-modal');
    const container = document.getElementById('wishlist-modal-body');
    if (!modal || !container) return;

    modal.classList.add('active');

    if (this.wishlist.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 50px 20px; color: #64748b;">
          <div style="font-size: 3rem; margin-bottom: 12px;">♡</div>
          <h4 style="font-size: 1.1rem; color: #0f172a; margin-bottom: 6px;">Your Wishlist is Empty</h4>
          <p style="font-size: 0.85rem;">Click the heart icon on any book to curate your favorite titles!</p>
        </div>
      `;
      return;
    }

    container.innerHTML = '<div style="padding: 30px; text-align: center;"><p>Loading wishlist titles...</p></div>';

    try {
      const itemsHtml = await Promise.all(this.wishlist.map(async id => {
        const res = await fetch(`/api/books/${id}`);
        const data = await res.json();
        const b = data.book;
        if (!b) return '';
        const effectivePrice = (b.price * (1 - (b.discount_pct / 100))).toFixed(2);

        return `
          <div style="display: flex; gap: 14px; align-items: center; padding: 12px 0; border-bottom: 1px solid var(--cream-border);">
            <img src="${b.cover_image || '/static/img/book-placeholder.svg'}" alt="${escapeHtml(b.title)}" style="width: 48px; height: 68px; object-fit: cover; border-radius: 6px;" onerror="this.onerror=null; this.src='/static/img/book-placeholder.svg';" />
            <div style="flex: 1; min-width: 0;">
              <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--ink-black); margin-bottom: 2px;">${escapeHtml(b.title)}</h4>
              <p style="font-size: 0.8rem; color: var(--ink-muted); margin-bottom: 4px;">by ${escapeHtml(b.author_names || 'Unknown')}</p>
              <span style="font-size: 0.95rem; font-weight: 800; font-family: var(--font-mono); color: var(--burnt-orange);">৳${effectivePrice}</span>
            </div>
            <div style="display: flex; gap: 8px;">
              <button class="btn-buy" style="font-size: 0.8rem; padding: 7px 14px;" onclick="App.addToCart(${b.book_id}, '${escapeQuote(b.title)}', ${effectivePrice}, '${escapeQuote(b.cover_image || '')}'); App.closeWishlistModal();">Add to Cart</button>
              <button class="auth-btn auth-btn-ghost" style="padding: 6px 12px; font-size: 0.8rem;" onclick="App.toggleWishlist(${b.book_id}); App.openWishlistModal();">Remove</button>
            </div>
          </div>
        `;
      }));

      container.innerHTML = `
        <div style="display: flex; flex-direction: column;">
          ${itemsHtml.join('')}
        </div>
      `;
    } catch (err) {
      container.innerHTML = '<p>Error loading wishlist items.</p>';
    }
  },

  closeWishlistModal() {
    const modal = document.getElementById('wishlist-modal');
    if (modal) modal.classList.remove('active');
  },

  // -------------------------------------------------------------------------
  // Book Specifications Modal
  // -------------------------------------------------------------------------
  async openBookModal(bookId) {
    const modal = document.getElementById('book-detail-modal');
    const container = document.getElementById('book-detail-body');
    if (!modal || !container) return;

    container.innerHTML = '<div style="padding: 40px; text-align: center;"><p>Loading book details...</p></div>';
    modal.classList.add('active');

    try {
      const res = await fetch(`/api/books/${bookId}`);
      const data = await res.json();
      if (!res.ok || !data.book) {
        container.innerHTML = '<p>Book details could not be loaded.</p>';
        return;
      }

      const book = data.book;
      const reviews = book.reviews || [];
      const effectivePrice = (book.price * (1 - (book.discount_pct / 100))).toFixed(2);
      const isWishlisted = this.wishlist.includes(book.book_id);

      container.innerHTML = `
        <div style="display: flex; gap: 24px; flex-wrap: wrap;">
          <div style="width: 190px; flex-shrink: 0; position: relative;">
            <img src="${book.cover_image || '/static/img/book-placeholder.svg'}" alt="${escapeHtml(book.title)}" onerror="this.onerror=null; this.src='/static/img/book-placeholder.svg';" style="width: 100%; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.15);" />
            <div style="margin-top: 14px; font-size: 0.8rem; color: #64748b; line-height: 1.6;">
              <p><strong>ISBN:</strong> ${book.isbn}</p>
              <p><strong>Pages:</strong> ${book.page_count}</p>
              <p><strong>Year:</strong> ${book.publication_year}</p>
              <p><strong>Language:</strong> ${book.language}</p>
              <p><strong>Inventory:</strong> <span style="color: ${book.stock_qty > 0 ? '#10b981' : '#ef4444'}; font-weight: 700;">${book.stock_qty} in stock</span></p>
            </div>
          </div>
          <div style="flex: 1; min-width: 260px;">
            <span style="font-size: 0.75rem; font-weight: 700; color: var(--burnt-orange); text-transform: uppercase; letter-spacing: 0.05em;">${book.category_name}</span>
            <h2 style="font-size: 1.45rem; font-weight: 800; color: var(--ink-black); margin: 4px 0 8px; letter-spacing: -0.02em;">${book.title}</h2>
            <p style="font-size: 0.88rem; color: var(--ink-muted); margin-bottom: 12px;">by <strong style="color: var(--ink-charcoal);">${book.author_names || 'Unknown'}</strong></p>
            
            <div style="display: flex; align-items: baseline; gap: 12px; margin-bottom: 16px;">
              <span style="font-size: 1.6rem; font-weight: 800; font-family: var(--font-mono); color: var(--burnt-orange);">৳${effectivePrice}</span>
              ${book.discount_pct > 0 ? `<span style="font-size: 0.95rem; font-family: var(--font-mono); text-decoration: line-through; color: var(--ink-faint);">৳${book.price.toFixed(2)}</span>` : ''}
              <span style="font-size: 0.85rem; font-weight: 700; color: var(--accent-gold); margin-left: 8px;">★ ${book.avg_rating || 'New'} (${book.total_reviews} reviews)</span>
            </div>

            <p style="font-size: 0.9rem; line-height: 1.7; color: var(--ink-charcoal); margin-bottom: 20px;">${book.description || 'No description provided.'}</p>
            
            <div style="background: var(--cream-surface); border: 1px solid var(--cream-border); border-radius: var(--radius-md); padding: 14px 18px; margin-bottom: 20px; font-size: 0.82rem; line-height: 1.7;">
              <p><strong>Publisher:</strong> ${book.publisher_name} (${book.publisher_country || 'International'})</p>
              ${book.publisher_website ? `<p><strong>Website:</strong> <a href="${book.publisher_website}" target="_blank" style="color: var(--burnt-orange); font-weight: 600;">${book.publisher_website}</a></p>` : ''}
            </div>

            <div style="display: flex; gap: 12px;">
              ${book.stock_qty <= 0 ? `
                <button class="auth-btn auth-btn-primary" style="flex: 1; opacity: 0.55; cursor: not-allowed; background: var(--ink-faint);" disabled>Sold Out (Out of Stock)</button>
              ` : `
                <button class="auth-btn auth-btn-primary" style="flex: 1;" onclick="App.addToCart(${book.book_id}, '${escapeQuote(book.title)}', ${effectivePrice}, '${escapeQuote(book.cover_image || '')}')">Add to Cart (৳${effectivePrice})</button>
              `}
              <button class="auth-btn auth-btn-ghost" onclick="App.toggleWishlist(${book.book_id})">${isWishlisted ? '♥ Saved in Wishlist' : '♡ Save to Wishlist'}</button>
            </div>
          </div>
        </div>

        <!-- Reviews Section -->
        <div style="margin-top: 32px; border-top: 1px solid #e2e8f0; padding-top: 20px;">
          <h3 style="font-size: 1.1rem; color: #0f172a; margin-bottom: 14px;">Customer Reviews &amp; Feedback (${reviews.length})</h3>
          ${reviews.length === 0 ? '<p style="color: #64748b; font-size: 0.85rem;">No customer reviews yet. Be the first to review this title!</p>' : ''}
          <div style="display: flex; flex-direction: column; gap: 12px;">
            ${reviews.map(r => `
              <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 14px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                  <strong style="font-size: 0.88rem; color: #0f172a;">${r.user_name} <span style="font-weight: normal; color: #64748b; font-size: 0.75rem;">(${r.user_role})</span></strong>
                  <span style="color: #f59e0b; font-size: 0.85rem;">${'★'.repeat(r.rating)}${'☆'.repeat(5 - r.rating)}</span>
                </div>
                <h4 style="font-size: 0.85rem; font-weight: 700; color: #334155; margin-bottom: 4px;">${r.review_title || ''}</h4>
                <p style="font-size: 0.82rem; color: #64748b; line-height: 1.5;">${r.review_text}</p>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    } catch (err) {
      container.innerHTML = '<p>Error fetching book record.</p>';
    }
  },

  // -------------------------------------------------------------------------
  // Admin Dashboard & CRUD Books Controller
  // -------------------------------------------------------------------------
  adminData: null,
  publishers: null,
  authors: null,

  getAdminHeaders() {
    return {
      'Content-Type': 'application/json',
      'X-Admin-Email': (Auth.currentUser && Auth.currentUser.email) ? Auth.currentUser.email : '',
      'X-Admin-Role': (Auth.currentUser && Auth.currentUser.role) ? Auth.currentUser.role : ''
    };
  },

  async openAdminDashboard() {
    if (!Auth.isAdmin()) {
      showToast('Access restricted: Only the administrator can view this dashboard.', 'error');
      return;
    }

    const modal = document.getElementById('admin-dashboard-modal');
    if (modal) modal.classList.add('active');

    try {
      const res = await fetch('/api/admin/dashboard', {
        headers: this.getAdminHeaders()
      });
      if (!res.ok) {
        showToast('Access restricted to Administrator (tamimtahmid270@gmail.com).', 'error');
        if (modal) modal.classList.remove('active');
        return;
      }
      const data = await res.json();
      this.adminData = data;
      this.renderAdminDashboard(data);
    } catch (err) {
      showToast('Could not load admin dashboard data.', 'error');
    }
  },

  closeAdminDashboard() {
    const modal = document.getElementById('admin-dashboard-modal');
    if (modal) modal.classList.remove('active');
  },

  switchAdminTab(tabName) {
    document.querySelectorAll('.admin-tab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    document.querySelectorAll('.admin-panel').forEach(panel => {
      panel.classList.toggle('active', panel.id === `admin-panel-${tabName}`);
    });
  },

  renderAdminDashboard(data) {
    if (!data) return;

    // Metrics
    const m = data.metrics || {};
    const setVal = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };

    // Strictly filter low stock items (<= 20 units; ignore books > 20)
    const strictlyLowItems = (data.low_stock_items || []).filter(b => Number(b.stock_qty) <= 20);

    setVal('metric-total-books', m.total_books || 0);
    setVal('metric-total-categories', m.total_categories || 0);
    setVal('metric-low-stock', strictlyLowItems.length);
    setVal('metric-total-orders', m.total_orders || 0);
    setVal('metric-total-revenue', `৳${parseFloat(m.total_revenue || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);

    // Tab badges
    setVal('admin-tab-book-count', (data.books || []).length);
    setVal('admin-tab-order-count', (data.recent_orders || []).length);
    setVal('admin-tab-lowstock-count', strictlyLowItems.length);

    // Populate category dropdown in admin toolbar if empty
    const catSelect = document.getElementById('admin-books-category-select');
    if (catSelect && catSelect.children.length <= 1 && this.categories) {
      let optHtml = '<option value="">All Categories</option>';
      this.categories.forEach(c => {
        optHtml += `<option value="${c.category_id}">${escapeHtml(c.name)}</option>`;
      });
      catSelect.innerHTML = optHtml;
    }

    // Snapshot: Overview Low Stock Table (Urgent Stock <= 20)
    const ovStockTbody = document.getElementById('overview-lowstock-tbody');
    if (ovStockTbody) {
      const lowItems = strictlyLowItems;
      if (lowItems.length === 0) {
        ovStockTbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #10B981; padding: 16px;">✓ All inventory levels healthy (&gt; 20 units)</td></tr>';
      } else {
        ovStockTbody.innerHTML = lowItems.slice(0, 5).map(b => `
          <tr>
            <td><strong>${escapeHtml(b.title)}</strong></td>
            <td><span class="book-category-tag" style="margin: 0;">${escapeHtml(b.category_name)}</span></td>
            <td><span class="status-badge status-low">🔥 ${b.stock_qty} left</span></td>
            <td><button class="btn-table-action btn-restock" onclick="App.quickRestock(${b.book_id}, '${escapeQuote(b.title)}', ${b.stock_qty})">+ Restock</button></td>
          </tr>
        `).join('');
      }
    }

    // Snapshot: Overview Recent Orders Table
    const ovOrdersTbody = document.getElementById('overview-orders-tbody');
    if (ovOrdersTbody) {
      const orders = data.recent_orders || [];
      if (orders.length === 0) {
        ovOrdersTbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--ink-muted); padding: 16px;">No customer orders placed yet.</td></tr>';
      } else {
        ovOrdersTbody.innerHTML = orders.slice(0, 5).map(o => {
          const currentStatus = o.order_status || o.status || 'Confirmed';
          const statusClass = currentStatus.toLowerCase().replace(/\s+/g, '-');
          return `
          <tr>
            <td><strong style="font-family: var(--font-mono); color: var(--burnt-orange);">${escapeHtml(o.order_code || o.order_number)}</strong></td>
            <td>${escapeHtml(o.customer_name)}</td>
            <td><strong style="font-family: var(--font-mono);">৳${parseFloat(o.total_amount).toFixed(2)}</strong></td>
            <td>
              <select class="order-status-select" onchange="App.updateOrderStatus(${o.order_id}, this.value)" title="Change Order Status">
                <option value="Confirmed" ${currentStatus === 'Confirmed' ? 'selected' : ''}>Confirmed</option>
                <option value="On Transit" ${currentStatus === 'On Transit' ? 'selected' : ''}>On Transit</option>
                <option value="Delivered" ${currentStatus === 'Delivered' ? 'selected' : ''}>Delivered</option>
                <option value="Cancelled" ${currentStatus === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
              </select>
            </td>
          </tr>
        `;
        }).join('');
      }
    }

    // Snapshot: Live Password Resets Table
    const resetsTbody = document.getElementById('overview-resets-tbody');
    if (resetsTbody) {
      const resets = data.active_resets || [];
      if (resets.length === 0) {
        resetsTbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--ink-muted); padding: 14px;">No active password reset requests in database.</td></tr>';
      } else {
        resetsTbody.innerHTML = resets.map(r => `
          <tr>
            <td><strong>${escapeHtml(r.full_name)}</strong></td>
            <td>${escapeHtml(r.email)}</td>
            <td><strong style="font-family: var(--font-mono); color: var(--burnt-orange); font-size: 1.05rem; letter-spacing: 2px;">${escapeHtml(r.reset_code)}</strong></td>
            <td style="font-size: 0.78rem; color: var(--ink-faint);">${escapeHtml(r.expires_at)}</td>
          </tr>
        `).join('');
      }
    }

    // Overview: Customer Support Queries
    const queriesTbody = document.getElementById('overview-queries-tbody');
    if (queriesTbody) {
      const queries = data.recent_queries || [];
      if (queries.length === 0) {
        queriesTbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--ink-muted); padding: 14px;">No customer inquiries received yet.</td></tr>';
      } else {
        queriesTbody.innerHTML = queries.map(q => `
          <tr>
            <td><strong>${escapeHtml(q.customer_name)}</strong></td>
            <td>
              <div><a href="mailto:${escapeHtml(q.customer_email)}" style="color: var(--burnt-orange); font-weight: 600;">${escapeHtml(q.customer_email)}</a></div>
              ${q.customer_phone ? `<div style="font-size: 0.76rem; color: var(--ink-faint);">${escapeHtml(q.customer_phone)}</div>` : ''}
            </td>
            <td><span class="book-category-tag">${escapeHtml(q.topic)}</span></td>
            <td style="max-width: 280px; font-size: 0.82rem; line-height: 1.4; color: var(--ink-base);">${escapeHtml(q.message)}</td>
            <td style="font-size: 0.78rem; color: var(--ink-faint); white-space: nowrap;">${escapeHtml(q.created_at || '')}</td>
          </tr>
        `).join('');
      }
    }

    // Panel 2: Full Books CRUD Table
    this.renderAdminBooksTable(data.books || []);

    // Panel 3: Full Orders Table (with manual Status selector)
    const ordersTbody = document.getElementById('admin-orders-tbody');
    if (ordersTbody) {
      const orders = data.recent_orders || [];
      if (orders.length === 0) {
        ordersTbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: var(--ink-muted); padding: 24px;">No customer orders placed yet.</td></tr>';
      } else {
        ordersTbody.innerHTML = orders.map(o => {
          const currentStatus = o.order_status || o.status || 'Confirmed';
          const statusClass = currentStatus.toLowerCase().replace(/\s+/g, '-');
          return `
          <tr>
            <td><strong style="font-family: var(--font-mono); color: var(--burnt-orange);">${escapeHtml(o.order_code || o.order_number)}</strong></td>
            <td><strong>${escapeHtml(o.customer_name)}</strong></td>
            <td>${escapeHtml(o.customer_phone || 'N/A')}</td>
            <td>${escapeHtml(o.district || o.delivery_district || 'Dhaka')}</td>
            <td>${o.items_count || 1} titles</td>
            <td><strong style="font-family: var(--font-mono);">৳${parseFloat(o.total_amount).toFixed(2)}</strong></td>
            <td>
              <span class="pay-pill">${escapeHtml(o.payment_method)}</span>
              ${o.transaction_id ? `<div style="font-family: var(--font-mono); font-size: 0.72rem; color: var(--ink-faint); margin-top: 3px;">Trx: ${escapeHtml(o.transaction_id)}</div>` : ''}
              <div style="margin-top: 4px;"><span class="${o.payment_status === 'Completed' ? 'badge-status-paid' : 'status-badge status-confirmed'}" style="font-size: 0.68rem; padding: 2px 6px;">${escapeHtml(o.payment_status || 'Pending')}</span></div>
            </td>
            <td>
              <div style="display: flex; flex-direction: column; gap: 5px;">
                <span class="status-badge status-${statusClass}">${escapeHtml(currentStatus)}</span>
                <select class="order-status-select" onchange="App.updateOrderStatus(${o.order_id}, this.value)" title="Manually update order status">
                  <option value="Confirmed" ${currentStatus === 'Confirmed' ? 'selected' : ''}>Confirmed</option>
                  <option value="On Transit" ${currentStatus === 'On Transit' ? 'selected' : ''}>On Transit</option>
                  <option value="Delivered" ${currentStatus === 'Delivered' ? 'selected' : ''}>Delivered</option>
                  <option value="Cancelled" ${currentStatus === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
                </select>
              </div>
            </td>
            <td style="font-size: 0.76rem; color: var(--ink-faint);">${escapeHtml(o.created_at || '')}</td>
          </tr>
        `;
        }).join('');
      }
    }

    // Panel 4: Full Low Stock Table (Strictly <= 20 threshold)
    const stockTbody = document.getElementById('admin-stock-tbody');
    if (stockTbody) {
      const lowItems = (data.low_stock_items || []).filter(b => Number(b.stock_qty) <= 20);
      if (lowItems.length === 0) {
        stockTbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #10B981; padding: 24px;">✓ Inventory is fully stocked across all catalog items (&gt; 20 units)!</td></tr>';
      } else {
        stockTbody.innerHTML = lowItems.map(b => `
          <tr>
            <td><img src="${b.cover_image || ''}" class="admin-thumb" onerror="this.onerror=null; this.src='/static/img/book-placeholder.svg';" /></td>
            <td>
              <strong>${escapeHtml(b.title)}</strong>
              <div style="font-size: 0.76rem; color: var(--ink-faint);">${escapeHtml(b.authors || b.author_names || 'Unknown')} &bull; ISBN: ${escapeHtml(b.isbn || 'N/A')}</div>
            </td>
            <td><span class="book-category-tag">${escapeHtml(b.category_name)}</span></td>
            <td><strong style="color: var(--danger); font-family: var(--font-mono); font-size: 0.95rem;">${b.stock_qty}</strong> units</td>
            <td><span class="status-badge status-low">Stock &le; 20</span></td>
            <td>
              <button class="btn-table-action btn-restock" onclick="App.quickRestock(${b.book_id}, '${escapeQuote(b.title)}', ${b.stock_qty})">+ Restock</button>
            </td>
          </tr>
        `).join('');
      }
    }
  },

  renderAdminBooksTable(books) {
    const tbody = document.getElementById('admin-books-tbody');
    if (!tbody) return;

    if (!books || books.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--ink-muted); padding: 24px;">No books match your admin search filter.</td></tr>';
      return;
    }

    tbody.innerHTML = books.map(b => {
      const discount = parseFloat(b.discount_pct || 0);
      const isLowStock = b.stock_qty <= 20;
      return `
        <tr>
          <td><img src="${b.cover_image || ''}" class="admin-thumb" onerror="this.onerror=null; this.src='/static/img/book-placeholder.svg';" /></td>
          <td>
            <strong>${escapeHtml(b.title)}</strong>
            <div style="font-size: 0.76rem; color: var(--ink-faint);">${escapeHtml(b.authors || 'Unknown')} &bull; ISBN: ${escapeHtml(b.isbn)}</div>
          </td>
          <td><span class="book-category-tag">${escapeHtml(b.category_name)}</span></td>
          <td>
            <strong style="font-family: var(--font-mono);">৳${parseFloat(b.price).toFixed(2)}</strong>
            ${discount > 0 ? `<div style="font-size: 0.72rem; color: var(--burnt-orange); font-weight: 700;">-${discount}% OFF</div>` : ''}
          </td>
          <td>
            <span class="status-badge ${isLowStock ? 'status-low' : 'status-ok'}">
              ${b.stock_qty} in stock
            </span>
          </td>
          <td>${b.publication_year || 'N/A'}</td>
          <td>
            <div class="action-btn-group">
              <button class="btn-table-action btn-edit" title="Edit book details" onclick="App.openEditBookModal(${b.book_id})">Edit</button>
              <button class="btn-table-action btn-delete" title="Remove from catalog" onclick="App.deleteBook(${b.book_id}, '${escapeQuote(b.title)}')">Delete</button>
            </div>
          </td>
        </tr>
      `;
    }).join('');
  },

  filterAdminBooks() {
    if (!this.adminData || !this.adminData.books) return;
    const term = (document.getElementById('admin-books-filter-input')?.value || '').toLowerCase().trim();
    const catId = document.getElementById('admin-books-category-select')?.value;

    const filtered = this.adminData.books.filter(b => {
      const matchesTerm = !term ||
        (b.title && b.title.toLowerCase().includes(term)) ||
        (b.authors && b.authors.toLowerCase().includes(term)) ||
        (b.isbn && b.isbn.toLowerCase().includes(term));
      const matchesCat = !catId || String(b.category_id) === String(catId);
      return matchesTerm && matchesCat;
    });

    this.renderAdminBooksTable(filtered);
  },

  async loadPublishersAndAuthors() {
    if (!this.publishers) {
      try {
        const res = await fetch('/api/publishers');
        const data = await res.json();
        this.publishers = data.publishers || [];
      } catch (e) {
        this.publishers = [];
      }
    }

    if (!this.authors) {
      try {
        const res = await fetch('/api/authors');
        const data = await res.json();
        this.authors = data.authors || [];
      } catch (e) {
        this.authors = [];
      }
    }

    const pubSelect = document.getElementById('crud-book-publisher');
    if (pubSelect && this.publishers.length > 0) {
      pubSelect.innerHTML = this.publishers.map(p => `<option value="${p.publisher_id}">${escapeHtml(p.name)}</option>`).join('');
    }

    const authSelect = document.getElementById('crud-book-author');
    if (authSelect && this.authors.length > 0) {
      authSelect.innerHTML = this.authors.map(a => `<option value="${a.author_id}">${escapeHtml(a.name)}</option>`).join('');
    }

    const catSelect = document.getElementById('crud-book-category');
    if (catSelect && this.categories && this.categories.length > 0) {
      catSelect.innerHTML = this.categories.map(c => `<option value="${c.category_id}">${escapeHtml(c.name)}</option>`).join('');
    }
  },

  async openCreateBookModal() {
    if (!Auth.isAdmin()) {
      showToast('Access restricted: Administrator only.', 'error');
      return;
    }
    await this.loadPublishersAndAuthors();
    document.getElementById('book-crud-form').reset();
    document.getElementById('crud-book-id').value = '';
    document.getElementById('crud-modal-mode-badge').textContent = 'NEW BOOK';
    document.getElementById('crud-modal-title').textContent = 'Add New Book to Catalog';
    document.getElementById('crud-submit-btn').textContent = 'Save Book to Catalog';

    document.getElementById('crud-book-year').value = 2024;
    document.getElementById('crud-book-stock').value = 25;
    document.getElementById('crud-book-pages').value = 420;
    document.getElementById('crud-book-discount').value = 0;

    const modal = document.getElementById('book-crud-modal');
    if (modal) modal.classList.add('active');
  },

  async openEditBookModal(bookId) {
    if (!Auth.isAdmin()) {
      showToast('Access restricted: Administrator only.', 'error');
      return;
    }
    await this.loadPublishersAndAuthors();
    try {
      const res = await fetch(`/api/books/${bookId}`);
      const data = await res.json();
      if (!res.ok || !data.book) {
        showToast('Could not load book details for editing.', 'error');
        return;
      }
      const b = data.book;
      document.getElementById('crud-book-id').value = b.book_id;
      document.getElementById('crud-modal-mode-badge').textContent = 'EDIT BOOK';
      document.getElementById('crud-modal-title').textContent = `Edit Book #${b.book_id}`;
      document.getElementById('crud-submit-btn').textContent = 'Save Changes';

      document.getElementById('crud-book-isbn').value = b.isbn || '';
      document.getElementById('crud-book-title').value = b.title || '';
      document.getElementById('crud-book-category').value = b.category_id || 1;
      document.getElementById('crud-book-publisher').value = b.publisher_id || 1;
      
      const authorSelect = document.getElementById('crud-book-author');
      if (authorSelect && b.authors_list && b.authors_list.length > 0) {
        authorSelect.value = b.authors_list[0].author_id;
      }

      document.getElementById('crud-book-price').value = b.price || 0;
      document.getElementById('crud-book-discount').value = b.discount_pct || 0;
      document.getElementById('crud-book-stock').value = b.stock_qty || 0;
      document.getElementById('crud-book-year').value = b.publication_year || 2024;
      document.getElementById('crud-book-pages').value = b.page_count || 300;
      document.getElementById('crud-book-cover').value = b.cover_image || '';
      document.getElementById('crud-book-desc').value = b.description || '';

      const modal = document.getElementById('book-crud-modal');
      if (modal) modal.classList.add('active');
    } catch (err) {
      showToast('Error opening edit book modal.', 'error');
    }
  },

  closeBookCrudModal() {
    const modal = document.getElementById('book-crud-modal');
    if (modal) modal.classList.remove('active');
  },

  async handleBookCrudSubmit(e) {
    e.preventDefault();
    if (!Auth.isAdmin()) {
      showToast('Access restricted: Administrator only.', 'error');
      return;
    }
    const bookId = document.getElementById('crud-book-id').value;
    const isUpdate = Boolean(bookId);

    const data = {
      isbn: document.getElementById('crud-book-isbn').value.trim(),
      title: document.getElementById('crud-book-title').value.trim(),
      category_id: parseInt(document.getElementById('crud-book-category').value),
      publisher_id: parseInt(document.getElementById('crud-book-publisher').value || 1),
      author_id: parseInt(document.getElementById('crud-book-author').value || 1),
      price: parseFloat(document.getElementById('crud-book-price').value),
      discount_pct: parseFloat(document.getElementById('crud-book-discount').value || 0),
      stock_qty: parseInt(document.getElementById('crud-book-stock').value || 10),
      publication_year: parseInt(document.getElementById('crud-book-year').value || 2024),
      page_count: parseInt(document.getElementById('crud-book-pages').value || 300),
      description: document.getElementById('crud-book-desc').value.trim(),
      cover_image: document.getElementById('crud-book-cover').value.trim() || '/static/img/book-placeholder.svg'
    };

    const url = isUpdate ? `/api/books/${bookId}/update` : '/api/books';
    const method = 'POST';

    try {
      const res = await fetch(url, {
        method,
        headers: this.getAdminHeaders(),
        body: JSON.stringify(data)
      });
      const result = await res.json();
      if (res.ok && result.success) {
        showToast(isUpdate ? 'Book updated successfully!' : 'Book added to catalog successfully!', 'success');
        this.closeBookCrudModal();
        SearchEngine.executeSearch();
        this.loadCategories();
        const adminModal = document.getElementById('admin-dashboard-modal');
        if (adminModal && adminModal.classList.contains('active')) {
          this.openAdminDashboard();
        }
      } else {
        showToast(result.message || 'Error saving book record.', 'error');
      }
    } catch (err) {
      showToast('Network error saving book record.', 'error');
    }
  },

  async deleteBook(bookId, title) {
    if (!Auth.isAdmin()) {
      showToast('Access restricted: Administrator only.', 'error');
      return;
    }
    if (!confirm(`Are you sure you want to remove "${title}" from the catalog?`)) {
      return;
    }

    try {
      const res = await fetch(`/api/books/${bookId}`, {
        method: 'DELETE',
        headers: this.getAdminHeaders()
      });
      const result = await res.json();
      if (res.ok && result.success) {
        showToast(`"${title}" has been deleted from catalog.`, 'success');
        SearchEngine.executeSearch();
        this.loadCategories();
        const adminModal = document.getElementById('admin-dashboard-modal');
        if (adminModal && adminModal.classList.contains('active')) {
          this.openAdminDashboard();
        }
      } else {
        showToast(result.message || 'Error deleting book.', 'error');
      }
    } catch (err) {
      showToast('Network error deleting book.', 'error');
    }
  },

  async quickRestock(bookId, title, currentStock) {
    if (!Auth.isAdmin()) {
      showToast('Access restricted: Administrator only.', 'error');
      return;
    }
    const currentUnits = parseInt(currentStock, 10) || 0;
    const qtyStr = prompt(`Restock Inventory: "${title}"\nCurrent In-Stock: ${currentUnits} units.\n\nHow many units would you like to ADD to stock?`, '10');
    if (!qtyStr || !qtyStr.trim()) return;
    const addedUnits = parseInt(qtyStr.trim(), 10);
    if (isNaN(addedUnits) || addedUnits <= 0) {
      alert('Please enter a valid positive number of units to add (e.g. 10).');
      return;
    }
    const newStock = currentUnits + addedUnits;

    try {
      const res = await fetch(`/api/books/${bookId}/update`, {
        method: 'POST',
        headers: this.getAdminHeaders(),
        body: JSON.stringify({ stock_add: addedUnits, stock_qty: newStock })
      });
      const result = await res.json();
      if (res.ok && result.success) {
        showToast(`Successfully added ${addedUnits} units! New stock: ${newStock} for "${title}".`, 'success');
        this.openAdminDashboard();
        SearchEngine.executeSearch();
      } else {
        showToast(result.message || 'Error updating stock.', 'error');
      }
    } catch (err) {
      showToast('Network error restocking book.', 'error');
    }
  },

  async updateOrderStatus(orderId, newStatus) {
    if (!Auth.isAdmin()) {
      showToast('Access restricted: Administrator only.', 'error');
      return;
    }
    try {
      const res = await fetch('/api/orders/update-status', {
        method: 'POST',
        headers: this.getAdminHeaders(),
        body: JSON.stringify({ order_id: orderId, status: newStatus })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        showToast(data.message || `Order status updated to "${newStatus}".`, 'success');
        this.openAdminDashboard();
      } else {
        showToast(data.message || 'Error updating order status.', 'error');
      }
    } catch (err) {
      showToast('Network error updating order status.', 'error');
    }
  },

  openQueryModal() {
    const modal = document.getElementById('customer-query-modal');
    if (!modal) return;
    const form = document.getElementById('customer-query-form');
    if (form) form.reset();
    const alertBox = document.getElementById('query-feedback');
    if (alertBox) alertBox.style.display = 'none';

    // Autofill user info if logged in
    const user = (typeof Auth !== 'undefined' && Auth.currentUser) ? Auth.currentUser : null;
    if (user) {
      const nameInput = document.getElementById('query-name');
      const emailInput = document.getElementById('query-email');
      if (nameInput && !nameInput.value) nameInput.value = user.full_name || user.username || '';
      if (emailInput && !emailInput.value) emailInput.value = user.email || '';
    }

    modal.classList.add('active');
  },

  closeQueryModal() {
    const modal = document.getElementById('customer-query-modal');
    if (modal) modal.classList.remove('active');
  },

  async handleQuerySubmit(event) {
    if (event) event.preventDefault();
    const name = (document.getElementById('query-name')?.value || '').trim();
    const email = (document.getElementById('query-email')?.value || '').trim();
    const phone = (document.getElementById('query-phone')?.value || '').trim();
    const topic = (document.getElementById('query-topic')?.value || '').trim();
    const message = (document.getElementById('query-message')?.value || '').trim();
    const submitBtn = document.getElementById('query-submit-btn');
    const alertBox = document.getElementById('query-feedback');

    if (!name || !email || !topic || !message) {
      if (alertBox) {
        alertBox.className = 'alert-danger';
        alertBox.style.background = '#FEE2E2';
        alertBox.style.color = '#B91C1C';
        alertBox.style.border = '1px solid #FCA5A5';
        alertBox.style.display = 'block';
        alertBox.textContent = 'Please fill in all required fields (Name, Email, Topic, Details).';
      }
      return;
    }

    const origBtnHtml = submitBtn ? submitBtn.innerHTML : '';
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span>Sending Message...</span>';
    }

    try {
      const res = await fetch('/api/support/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, phone, topic, message })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        showToast('Your inquiry has been dispatched to our support desk!', 'success');
        if (alertBox) {
          alertBox.className = 'alert-success';
          alertBox.style.background = '#ECFDF5';
          alertBox.style.color = '#065F46';
          alertBox.style.border = '1px solid #A7F3D0';
          alertBox.style.display = 'block';
          alertBox.innerHTML = `<strong>Inquiry Sent!</strong> We have emailed PageVault Support (tamimtahmid270@gmail.com) and dispatched a confirmation to your email (${escapeHtml(email)}).`;
        }
        setTimeout(() => {
          this.closeQueryModal();
        }, 2200);
      } else {
        const errMsg = data.message || 'Could not send inquiry. Please try again.';
        if (alertBox) {
          alertBox.className = 'alert-danger';
          alertBox.style.background = '#FEE2E2';
          alertBox.style.color = '#B91C1C';
          alertBox.style.border = '1px solid #FCA5A5';
          alertBox.style.display = 'block';
          alertBox.textContent = errMsg;
        }
        showToast(errMsg, 'error');
      }
    } catch (err) {
      console.error('[Support Query]', err);
      showToast('Network error while dispatching your inquiry.', 'error');
      if (alertBox) {
        alertBox.className = 'alert-danger';
        alertBox.style.background = '#FEE2E2';
        alertBox.style.color = '#B91C1C';
        alertBox.style.border = '1px solid #FCA5A5';
        alertBox.style.display = 'block';
        alertBox.textContent = 'Network communication error. Please try again.';
      }
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = origBtnHtml;
      }
    }
  }
};

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 400);
  }, 3500);
}

// Boot application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  App.init();

  // Page Loader — show on every page load and refresh as requested
  const loader = document.getElementById('page-loader');
  if (loader) {
    setTimeout(() => {
      loader.classList.add('loaded');
      document.body.classList.add('page-revealed');
      setTimeout(() => loader.remove(), 700);
    }, 1800);
  }
});
