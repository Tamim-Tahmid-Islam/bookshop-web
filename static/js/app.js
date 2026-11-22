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
    this.updateRecentlyViewedBadge();
  },

  getRecentlyViewed() {
    try {
      const stored = localStorage.getItem('pagevault_recently_viewed');
      if (stored) {
        const arr = JSON.parse(stored);
        if (Array.isArray(arr)) {
          return arr.map(x => parseInt(x)).filter(x => !isNaN(x) && x > 0);
        }
      }
    } catch (e) {
      // Ignore error
    }
    return [];
  },

  trackRecentlyViewed(bookId) {
    if (!bookId) return;
    try {
      const id = parseInt(bookId);
      if (isNaN(id) || id <= 0) return;
      let list = this.getRecentlyViewed();
      list = list.filter(item => item !== id);
      list.unshift(id);
      if (list.length > 30) list = list.slice(0, 30);
      localStorage.setItem('pagevault_recently_viewed', JSON.stringify(list));
      this.updateRecentlyViewedBadge();
    } catch (e) {
      // Ignore error
    }
  },

  updateRecentlyViewedBadge() {
    const badge = document.getElementById('recently-viewed-badge');
    if (!badge) return;
    const count = this.getRecentlyViewed().length;
    if (count > 0) {
      badge.textContent = `${count} viewed`;
    } else {
      badge.textContent = 'History';
    }
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

  _lastSidebarToggleTime: 0,

  // -------------------------------------------------------------------------
  // Sidebar Navigation (Desktop Collapse & Mobile Responsive Drawer)
  // -------------------------------------------------------------------------
  toggleSidebar(e) {
    if (e) {
      if (typeof e.preventDefault === 'function') e.preventDefault();
      if (typeof e.stopPropagation === 'function') e.stopPropagation();
    }
    const now = Date.now();
    if (now - this._lastSidebarToggleTime < 220) return;
    this._lastSidebarToggleTime = now;

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
      if (toggleBtn) {
        toggleBtn.classList.toggle('active', !sidebar.classList.contains('collapsed'));
      }
    }
  },

  closeMobileSidebar(e) {
    if (e) {
      if (typeof e.preventDefault === 'function') e.preventDefault();
      if (typeof e.stopPropagation === 'function') e.stopPropagation();
    }
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const toggleBtn = document.getElementById('sidebar-toggle-btn');
    if (sidebar) sidebar.classList.remove('mobile-open');
    if (overlay) overlay.classList.remove('active');
    if (toggleBtn && window.innerWidth <= 900) toggleBtn.classList.remove('active');
    document.body.classList.remove('sidebar-open-locked');
  },

  bindGlobalEvents() {
    // 1. Sidebar toggle (desktop collapse + mobile drawer toggle)
    const toggleBtn = document.getElementById('sidebar-toggle-btn');
    if (toggleBtn) {
      toggleBtn.onclick = (e) => this.toggleSidebar(e);
    }

    // 2. Mobile sidebar overlay click to dismiss
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    if (sidebarOverlay) {
      sidebarOverlay.onclick = (e) => this.closeMobileSidebar(e);
    }

    // 3. Mobile sidebar drawer close button (×)
    const mobileCloseBtn = document.getElementById('sidebar-close-btn');
    if (mobileCloseBtn) {
      mobileCloseBtn.onclick = (e) => this.closeMobileSidebar(e);
    }

    // 4. Mobile sidebar drawer header hamburger toggle
    const mobileToggleBtn = document.getElementById('sidebar-mobile-toggle-btn');
    if (mobileToggleBtn) {
      mobileToggleBtn.onclick = (e) => this.closeMobileSidebar(e);
    }

    // 5. Dismiss mobile sidebar when clicking anywhere outside it on phone
    document.addEventListener('click', (e) => {
      if (window.innerWidth > 900) return;
      const sidebar = document.getElementById('sidebar');
      if (!sidebar || !sidebar.classList.contains('mobile-open')) return;
      // Prevent immediately dismissing on the opening click event
      if (Date.now() - this._lastSidebarToggleTime < 300) return;
      const tBtn = document.getElementById('sidebar-toggle-btn');
      if (sidebar.contains(e.target)) return;
      if (tBtn && (tBtn === e.target || tBtn.contains(e.target))) return;
      this.closeMobileSidebar(e);
    });

    // 6. Escape key dismisses mobile sidebar
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

    // Auto-fill and guarantee logged in user info
    const authBadge = document.getElementById('checkout-auth-badge');
    const authName = document.getElementById('checkout-auth-name');
    const authEmail = document.getElementById('checkout-auth-email');
    const nameField = document.getElementById('checkout-name');
    const emailField = document.getElementById('checkout-email');

    if (Auth.currentUser) {
      if (authBadge) authBadge.style.display = 'flex';
      if (authName) authName.textContent = Auth.currentUser.full_name || Auth.currentUser.username || 'Customer';
      if (authEmail) authEmail.textContent = Auth.currentUser.email || '';

      if (nameField) nameField.value = Auth.currentUser.full_name || Auth.currentUser.username || '';
      if (emailField) emailField.value = Auth.currentUser.email || '';
    } else {
      if (authBadge) authBadge.style.display = 'none';
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

    const name = (document.getElementById('checkout-name').value.trim()) || (Auth.currentUser ? (Auth.currentUser.full_name || Auth.currentUser.username) : 'Valued Customer');
    const phone = document.getElementById('checkout-phone').value.trim();
    let email = document.getElementById('checkout-email') ? document.getElementById('checkout-email').value.trim() : '';
    if (!email && Auth.currentUser && Auth.currentUser.email) {
      email = Auth.currentUser.email.trim();
    }
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
        this.closeCartDrawer();

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

          const placedAtEl = document.getElementById('success-placed-at');
          if (placedAtEl) {
            placedAtEl.textContent = data.created_at || (new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) + ' at ' + new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }));
          }

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

    this.trackRecentlyViewed(bookId);

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
      const relatedBooks = book.related_books || [];
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

        <!-- Related Books in Domain Section -->
        ${relatedBooks.length > 0 ? `
          <div class="related-books-section">
            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 14px;">
              <div>
                <h3 style="font-size: 1.1rem; font-weight: 700; color: var(--ink-black); margin: 0 0 4px;">Related Books in this Domain</h3>
                <p style="font-size: 0.8rem; color: var(--ink-muted); margin: 0;">Explore companion titles and popular works in <strong>${escapeHtml(book.category_name || 'this category')}</strong></p>
              </div>
              <span style="font-size: 0.75rem; font-weight: 600; color: var(--burnt-orange); background: var(--warm-cream); padding: 3px 8px; border-radius: 4px;">${relatedBooks.length} recommendations</span>
            </div>
            <div class="related-books-grid">
              ${relatedBooks.map(rb => {
                const rbPrice = parseFloat(rb.effective_price || rb.price).toFixed(2);
                const isOutOfStock = rb.stock_qty <= 0;
                return `
                  <div class="related-book-card" onclick="App.openBookModal(${rb.book_id})" title="View details of ${escapeQuote(rb.title)}">
                    <div class="related-book-thumb">
                      <img class="related-book-img" 
                           src="${rb.cover_image || '/static/img/book-placeholder.svg'}" 
                           alt="${escapeHtml(rb.title)}" 
                           loading="lazy" 
                           onerror="this.onerror=null; this.src='/static/img/book-placeholder.svg';" />
                      ${rb.discount_pct > 0 ? `<span style="position: absolute; top: 4px; left: 4px; background: #dc2626; color: white; font-size: 0.65rem; font-weight: 700; padding: 1px 4px; border-radius: 3px;">-${rb.discount_pct}%</span>` : ''}
                      ${isOutOfStock ? `<span style="position: absolute; bottom: 4px; left: 4px; background: rgba(0,0,0,0.75); color: #fca5a5; font-size: 0.65rem; font-weight: 700; padding: 1px 4px; border-radius: 3px;">Sold Out</span>` : ''}
                    </div>
                    <h4 style="font-size: 0.82rem; font-weight: 700; color: var(--ink-black); margin: 0 0 3px; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;" title="${escapeHtml(rb.title)}">${escapeHtml(rb.title)}</h4>
                    <p style="font-size: 0.72rem; color: var(--ink-muted); margin: 0 0 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${escapeHtml(rb.author_names || '')}">${escapeHtml(rb.author_names || 'Unknown')}</p>
                    <div style="margin-top: auto; display: flex; justify-content: space-between; align-items: baseline;">
                      <span style="font-size: 0.88rem; font-weight: 800; font-family: var(--font-mono); color: var(--burnt-orange);">৳${rbPrice}</span>
                      <span style="font-size: 0.72rem; font-weight: 600; color: #f59e0b;">★ ${rb.avg_rating > 0 ? rb.avg_rating : 'New'}</span>
                    </div>
                  </div>
                `;
              }).join('')}
            </div>
          </div>
        ` : ''}

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

    // Overview: User Book Requests
    const requestsTbody = document.getElementById('overview-requests-tbody');
    if (requestsTbody) {
      const requests = data.recent_requests || [];
      if (requests.length === 0) {
        requestsTbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--ink-muted); padding: 14px;">No book requests submitted yet.</td></tr>';
      } else {
        requestsTbody.innerHTML = requests.map(r => `
          <tr>
            <td><strong style="color: var(--ink-black);">${escapeHtml(r.book_title)}</strong></td>
            <td>
              <div>${escapeHtml(r.author_name || 'Not specified')}</div>
              ${r.isbn ? `<div style="font-size: 0.76rem; font-family: var(--font-mono); color: var(--ink-faint);">${escapeHtml(r.isbn)}</div>` : ''}
            </td>
            <td><strong>${escapeHtml(r.requester_name)}</strong></td>
            <td>
              <div><a href="mailto:${escapeHtml(r.requester_email)}" style="color: var(--burnt-orange); font-weight: 600;">${escapeHtml(r.requester_email)}</a></div>
              ${r.requester_phone ? `<div style="font-size: 0.76rem; color: var(--ink-faint);">${escapeHtml(r.requester_phone)}</div>` : ''}
            </td>
            <td style="max-width: 240px; font-size: 0.82rem; line-height: 1.4; color: var(--ink-base);">
              ${r.genre_or_topic ? `<span class="book-category-tag" style="margin-bottom: 4px; display: inline-block;">${escapeHtml(r.genre_or_topic)}</span><br>` : ''}
              ${escapeHtml(r.notes || '')}
            </td>
            <td style="font-size: 0.78rem; color: var(--ink-faint); white-space: nowrap;">${escapeHtml(r.created_at || '')}</td>
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
  },

  openRequestBookModal(prefillTitle = '') {
    const modal = document.getElementById('request-book-modal');
    if (!modal) return;
    const form = document.getElementById('request-book-form');
    if (form) form.reset();
    const alertBox = document.getElementById('request-book-feedback');
    if (alertBox) alertBox.style.display = 'none';

    if (prefillTitle) {
      const titleInput = document.getElementById('req-book-title');
      if (titleInput) titleInput.value = prefillTitle;
    }

    // Autofill user info if logged in
    const user = (typeof Auth !== 'undefined' && Auth.currentUser) ? Auth.currentUser : null;
    if (user) {
      const nameInput = document.getElementById('req-name');
      const emailInput = document.getElementById('req-email');
      if (nameInput && !nameInput.value) nameInput.value = user.full_name || user.username || '';
      if (emailInput && !emailInput.value) emailInput.value = user.email || '';
    }

    modal.classList.add('active');
  },

  closeRequestBookModal() {
    const modal = document.getElementById('request-book-modal');
    if (modal) modal.classList.remove('active');
  },

  async handleRequestBookSubmit(event) {
    if (event) event.preventDefault();
    const book_title = (document.getElementById('req-book-title')?.value || '').trim();
    const author_name = (document.getElementById('req-author-name')?.value || '').trim();
    const isbn = (document.getElementById('req-isbn')?.value || '').trim();
    const requester_name = (document.getElementById('req-name')?.value || '').trim();
    const requester_phone = (document.getElementById('req-phone')?.value || '').trim();
    const requester_email = (document.getElementById('req-email')?.value || '').trim();
    const genre_or_topic = (document.getElementById('req-genre')?.value || '').trim();
    const notes = (document.getElementById('req-notes')?.value || '').trim();
    const submitBtn = document.getElementById('request-book-submit-btn');
    const alertBox = document.getElementById('request-book-feedback');

    if (!book_title || !requester_name || !requester_email) {
      if (alertBox) {
        alertBox.className = 'alert-danger';
        alertBox.style.background = '#FEE2E2';
        alertBox.style.color = '#B91C1C';
        alertBox.style.border = '1px solid #FCA5A5';
        alertBox.style.display = 'block';
        alertBox.textContent = 'Please fill in the required fields (Book Title, Your Name, Email Address).';
      }
      return;
    }

    const origBtnHtml = submitBtn ? submitBtn.innerHTML : '';
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span>Submitting Request...</span>';
    }

    const user = (typeof Auth !== 'undefined' && Auth.currentUser) ? Auth.currentUser : null;
    const user_id = user ? user.user_id : null;

    try {
      const res = await fetch('/api/book-requests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          book_title,
          author_name,
          isbn,
          requester_name,
          requester_phone,
          requester_email,
          genre_or_topic,
          notes,
          user_id
        })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        showToast('Your book request has been submitted!', 'success');
        if (alertBox) {
          alertBox.className = 'alert-success';
          alertBox.style.background = '#ECFDF5';
          alertBox.style.color = '#065F46';
          alertBox.style.border = '1px solid #A7F3D0';
          alertBox.style.display = 'block';
          alertBox.innerHTML = `<strong>Request Received!</strong> We have queued &ldquo;${escapeHtml(book_title)}&rdquo; for catalog sourcing. A confirmation email was dispatched to ${escapeHtml(requester_email)}.`;
        }
        setTimeout(() => {
          this.closeRequestBookModal();
        }, 2400);
      } else {
        const errMsg = data.message || 'Could not submit your request. Please try again.';
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
      console.error('[Book Request]', err);
      showToast('Network error while submitting your request.', 'error');
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
  },

  userOrdersCache: [],
  currentCancellingOrder: null,

  openMyOrdersModal() {
    const modal = document.getElementById('my-orders-modal');
    if (!modal) return;
    modal.classList.add('active');
    this.loadUserOrders();
  },

  closeMyOrdersModal() {
    const modal = document.getElementById('my-orders-modal');
    if (modal) modal.classList.remove('active');
  },

  async loadUserOrders(customParams = {}) {
    const container = document.getElementById('my-orders-list');
    if (!container) return;

    container.innerHTML = `
      <div style="text-align: center; padding: 36px 20px; color: var(--taupe-muted);">
        <div style="font-size: 1.8rem; margin-bottom: 8px;">⏳</div>
        <div>Loading your order history and cancellation status...</div>
      </div>
    `;

    const user = (typeof Auth !== 'undefined' && Auth.currentUser) ? Auth.currentUser : null;
    const params = new URLSearchParams();

    if (customParams.order_code) {
      params.set('order_code', customParams.order_code.trim());
    } else if (user) {
      if (user.user_id) params.set('user_id', user.user_id);
      if (user.email) params.set('email', user.email);
      if (user.full_name) params.set('name', user.full_name);
    } else {
      // Guest with no specific order searched
      container.innerHTML = `
        <div class="empty-state" style="padding: 32px 20px;">
          <div class="empty-state-icon">📦</div>
          <h3>Track Your Orders</h3>
          <p>Please enter your <strong>Order Code</strong> (e.g. <code>PV-123456-789</code>) in the lookup bar above, or <a href="javascript:void(0)" onclick="App.closeMyOrdersModal(); Auth.showModal('login');" style="color: var(--burnt-orange); font-weight: 700;">Sign In</a> to view your full order history.</p>
        </div>
      `;
      return;
    }

    try {
      const res = await fetch(`/api/user/orders?${params.toString()}`);
      const data = await res.json();
      const orders = data.orders || [];
      if (Array.isArray(orders)) {
        // Guarantee latest orders are always sorted strictly at the top of the list
        orders.sort((a, b) => (parseInt(b.order_id, 10) || 0) - (parseInt(a.order_id, 10) || 0));
      }
      this.userOrdersCache = orders;
      this.renderUserOrders(orders);
    } catch (err) {
      console.error('[Load Orders]', err);
      container.innerHTML = `
        <div class="empty-state" style="padding: 24px;">
          <h3>Connection Error</h3>
          <p>Could not load order history at this time. Please try refreshing.</p>
          <button class="btn btn-secondary" onclick="App.refreshUserOrders()">Retry</button>
        </div>
      `;
    }
  },

  renderUserOrders(orders) {
    const container = document.getElementById('my-orders-list');
    if (!container) return;

    if (!orders || orders.length === 0) {
      container.innerHTML = `
        <div class="empty-state" style="padding: 36px 20px;">
          <div class="empty-state-icon">📚</div>
          <h3>No Orders Found</h3>
          <p>You haven't placed any orders matching this criteria yet. Explore our curated collections to start building your library!</p>
          <div style="margin-top: 14px;">
            <button class="btn btn-primary" onclick="App.closeMyOrdersModal(); window.scrollTo({top: 0, behavior: 'smooth'});">
              Explore Book Catalog &rarr;
            </button>
          </div>
        </div>
      `;
      return;
    }

    container.innerHTML = orders.map(o => {
      const isCancelled = o.is_cancelled || (o.order_status === 'Cancelled');
      const statusClass = (o.order_status || 'confirmed').toLowerCase().replace(/\s+/g, '-');
      const items = o.items || [];
      const isOnline = o.is_online_paid;

      // Status pill label
      let statusLabel = o.order_status || 'Confirmed';
      if (isCancelled) statusLabel = 'Cancelled';

      // 12-hour cancellation footer section
      let cancelSectionHtml = '';
      if (isCancelled) {
        cancelSectionHtml = `
          <div style="width: 100%; background: #FEF2F2; border: 1px solid #FECACA; border-radius: 8px; padding: 12px 14px; font-size: 0.82rem; color: #991B1B;">
            <div style="font-weight: 700; display: flex; align-items: center; gap: 6px;">
              <span>❌ Order Cancelled</span>
              ${o.formatted_cancelled_at ? `<span style="font-weight: normal; color: #7F1D1D;">on ${escapeHtml(o.formatted_cancelled_at)}</span>` : ''}
            </div>
            ${o.cancel_reason ? `<div style="margin-top: 4px; color: #7F1D1D;">Reason: <em>${escapeHtml(o.cancel_reason)}</em></div>` : ''}
            ${isOnline && o.refund_amount > 0 ? `
              <div style="margin-top: 6px; padding-top: 6px; border-top: 1px dashed #FECACA; font-weight: 700; color: #065F46;">
                💳 Refund of ৳${parseFloat(o.refund_amount).toFixed(2)} initiated to your ${escapeHtml(o.payment_method)} (৳${parseFloat(o.delivery_fee).toFixed(2)} delivery fee deducted). Processing in 3–5 business days.
              </div>
            ` : ''}
          </div>
        `;
      } else if (o.can_cancel) {
        cancelSectionHtml = `
          <div class="cancel-timer-badge active">
            <span>⏱️ Cancellation Eligible:</span>
            <strong>${o.hours_left}h ${o.mins_left}m remaining</strong>
          </div>
          <button type="button" class="btn-cancel-order" onclick="App.promptCancelOrder(${o.order_id})">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
            Cancel Order
          </button>
        `;
      } else {
        cancelSectionHtml = `
          <div class="cancel-timer-badge expired" title="Orders older than 12 hours cannot be self-cancelled as they are in warehouse fulfillment.">
            <span>🔒 Cancellation Window Closed (&gt;12h from order placement)</span>
          </div>
          <button type="button" class="btn btn-secondary" style="font-size: 0.78rem; padding: 5px 12px;" onclick="App.closeMyOrdersModal(); App.openQueryModal();">
            Need Help? Contact Support
          </button>
        `;
      }

      return `
        <div class="order-history-card">
          <div class="order-history-header">
            <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
              <span class="order-code-badge">#${escapeHtml(o.order_code)}</span>
              <button type="button" class="btn btn-text" style="font-size: 0.74rem; padding: 2px 6px;" onclick="navigator.clipboard.writeText('${escapeQuote(o.order_code)}'); showToast('Order code copied!', 'info');" title="Copy Order Code">Copy</button>
            </div>
            <span class="order-status-pill order-status-${statusClass}">${escapeHtml(statusLabel)}</span>
          </div>

          <div class="order-history-meta">
            <div class="order-meta-item">
              <label>📅 Date &amp; Time Placed</label>
              <strong>${escapeHtml(o.formatted_created_at || o.created_at || 'Recently')}</strong>
            </div>
            <div class="order-meta-item">
              <label>💳 Payment Method</label>
              <strong>${escapeHtml(o.payment_method || 'Cash on Delivery')}</strong>
              ${o.transaction_id ? `<span style="font-size: 0.7rem; color: var(--taupe-muted); display: block;">Trx: ${escapeHtml(o.transaction_id)}</span>` : ''}
            </div>
            <div class="order-meta-item">
              <label>📍 Delivery Destination</label>
              <strong>${escapeHtml(o.customer_name)}</strong>
              <span style="font-size: 0.74rem; color: var(--taupe-muted); display: block;">${escapeHtml(o.district)} &bull; ${escapeHtml(o.customer_phone)}</span>
            </div>
            <div class="order-meta-item">
              <label>💰 Total Amount</label>
              <strong style="color: var(--burnt-orange); font-size: 0.95rem;">৳${parseFloat(o.total_amount).toFixed(2)}</strong>
              <span style="font-size: 0.7rem; color: var(--taupe-muted); display: block;">(Subtotal ৳${parseFloat(o.subtotal).toFixed(2)} + Fee ৳${parseFloat(o.delivery_fee).toFixed(2)})</span>
            </div>
          </div>

          <div class="order-history-items">
            ${items.map(it => `
              <div class="order-history-item-row">
                <div class="order-item-left">
                  <img class="order-item-thumb" src="${it.cover_image || '/static/img/book-placeholder.svg'}" alt="${escapeHtml(it.title || '')}" onerror="this.onerror=null; this.src='/static/img/book-placeholder.svg';" />
                  <div class="order-item-details">
                    <div class="order-item-title">${escapeHtml(it.title || 'Book Title')}</div>
                    <div class="order-item-qty">Quantity: ${it.quantity} &times; ৳${parseFloat(it.unit_price).toFixed(2)}</div>
                  </div>
                </div>
                <div class="order-item-price">৳${parseFloat(it.total_price).toFixed(2)}</div>
              </div>
            `).join('')}
          </div>

          <div class="order-history-footer">
            ${cancelSectionHtml}
          </div>
        </div>
      `;
    }).join('');
  },

  lookupSpecificOrder() {
    const input = document.getElementById('order-lookup-input');
    const code = (input?.value || '').trim();
    if (!code) {
      showToast('Please enter an Order Reference Code (e.g. PV-123456-789).', 'info');
      return;
    }
    this.loadUserOrders({ order_code: code });
  },

  refreshUserOrders() {
    const input = document.getElementById('order-lookup-input');
    if (input) input.value = '';
    this.loadUserOrders();
  },

  promptCancelOrder(orderId) {
    const order = (this.userOrdersCache || []).find(o => o.order_id === orderId);
    if (!order) {
      showToast('Order details not found.', 'error');
      return;
    }

    this.currentCancellingOrder = order;
    const modal = document.getElementById('cancel-order-modal');
    if (!modal) return;

    const summaryBox = document.getElementById('cancel-order-summary-box');
    const feedbackBox = document.getElementById('cancel-modal-feedback');
    if (feedbackBox) feedbackBox.style.display = 'none';

    const isOnline = order.is_online_paid;
    const totalAmount = parseFloat(order.total_amount || 0.0);
    const deliveryFee = parseFloat(order.delivery_fee || 60.0);
    const refundAmount = parseFloat(order.refundable_amount || Math.max(0.0, totalAmount - deliveryFee));

    if (summaryBox) {
      summaryBox.innerHTML = `
        <div style="background: #FAF7F2; border: 1px solid var(--cream-border); border-radius: 8px; padding: 14px 16px; margin-bottom: 14px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <strong style="font-size: 0.95rem; color: var(--ink-black);">Order Reference:</strong>
            <span style="font-family: var(--font-mono); font-weight: 700; color: var(--burnt-orange);">#${escapeHtml(order.order_code)}</span>
          </div>
          <div style="font-size: 0.82rem; color: var(--ink-muted); margin-bottom: 8px;">
            Placed on: <strong>${escapeHtml(order.formatted_created_at || order.created_at)}</strong>
          </div>
          <div style="font-size: 0.82rem; color: var(--ink-charcoal);">
            Items: <strong>${(order.items || []).length} title(s)</strong> (${(order.items || []).map(i => escapeHtml(i.title)).join(', ')})
          </div>
        </div>

        <div class="refund-breakdown-box">
          <div style="font-weight: 700; color: var(--ink-black); margin-bottom: 10px; display: flex; align-items: center; gap: 6px;">
            <span>${isOnline ? '💳 Online Payment Refund Breakdown' : 'ℹ️ Cash on Delivery Cancellation'}</span>
          </div>
          
          <div class="refund-line">
            <span>Total Order Value:</span>
            <strong>৳${totalAmount.toFixed(2)}</strong>
          </div>
          <div class="refund-line">
            <span>Payment Method:</span>
            <strong>${escapeHtml(order.payment_method)}</strong>
          </div>

          ${isOnline ? `
            <div class="refund-line" style="color: #991B1B;">
              <span>Deducted Delivery Fee (Dispatch Preparation):</span>
              <strong>-৳${deliveryFee.toFixed(2)}</strong>
            </div>
            <div class="refund-line total" style="color: #065F46;">
              <span>Net Refundable Amount:</span>
              <strong style="font-size: 1.05rem;">৳${refundAmount.toFixed(2)}</strong>
            </div>
            <div style="margin-top: 10px; font-size: 0.78rem; color: #78350F; background: #FEF3C7; padding: 8px 12px; border-radius: 6px; line-height: 1.4;">
              <strong>Refund Policy:</strong> Since your payment was verified online, <strong>৳${refundAmount.toFixed(2)}</strong> will be automatically credited back to your original ${escapeHtml(order.payment_method)} account within <strong>3 to 5 business days</strong>. The delivery preparation fee (৳${deliveryFee.toFixed(2)}) is deducted per our 12-hour cancellation policy.
            </div>
          ` : `
            <div class="refund-line total" style="color: #065F46;">
              <span>Charges Incurred:</span>
              <strong style="font-size: 1.05rem;">৳0.00</strong>
            </div>
            <div style="margin-top: 10px; font-size: 0.78rem; color: #065F46; background: #ECFDF5; padding: 8px 12px; border-radius: 6px; line-height: 1.4;">
              As this order is scheduled for Cash on Delivery, no funds were deducted. Your order will be cancelled immediately at zero fee.
            </div>
          `}
        </div>
      `;
    }

    modal.classList.add('active');
  },

  closeCancelModal() {
    const modal = document.getElementById('cancel-order-modal');
    if (modal) modal.classList.remove('active');
    this.currentCancellingOrder = null;
  },

  async executeOrderCancellation() {
    if (!this.currentCancellingOrder) return;
    const order = this.currentCancellingOrder;
    const reasonSelect = document.getElementById('cancel-reason-select');
    const notesInput = document.getElementById('cancel-reason-notes');
    const feedbackBox = document.getElementById('cancel-modal-feedback');
    const confirmBtn = document.getElementById('confirm-cancel-btn');

    let fullReason = reasonSelect ? reasonSelect.value : 'Customer requested cancellation';
    if (notesInput && notesInput.value.trim()) {
      fullReason += ` (${notesInput.value.trim()})`;
    }

    const origBtnHtml = confirmBtn ? confirmBtn.innerHTML : '';
    if (confirmBtn) {
      confirmBtn.disabled = true;
      confirmBtn.innerHTML = '<span>Processing Cancellation...</span>';
    }

    const user = (typeof Auth !== 'undefined' && Auth.currentUser) ? Auth.currentUser : null;

    try {
      const res = await fetch('/api/orders/cancel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          order_id: order.order_id,
          user_id: user ? user.user_id : null,
          email: user ? user.email : (order.customer_email || ''),
          cancel_reason: fullReason
        })
      });

      const data = await res.json();
      if (res.ok && data.success) {
        showToast(`Order #${order.order_code} has been cancelled.`, 'success');
        if (feedbackBox) {
          feedbackBox.className = 'alert-success';
          feedbackBox.style.background = '#ECFDF5';
          feedbackBox.style.color = '#065F46';
          feedbackBox.style.border = '1px solid #A7F3D0';
          feedbackBox.style.display = 'block';
          feedbackBox.innerHTML = `<strong>Order Cancelled!</strong> ${escapeHtml(data.message)}`;
        }
        setTimeout(() => {
          this.closeCancelModal();
          this.loadUserOrders();
        }, 2200);
      } else {
        const errMsg = data.message || 'Could not cancel this order.';
        if (feedbackBox) {
          feedbackBox.className = 'alert-danger';
          feedbackBox.style.background = '#FEE2E2';
          feedbackBox.style.color = '#B91C1C';
          feedbackBox.style.border = '1px solid #FCA5A5';
          feedbackBox.style.display = 'block';
          feedbackBox.textContent = errMsg;
        }
        showToast(errMsg, 'error');
      }
    } catch (err) {
      console.error('[Cancel Order]', err);
      showToast('Network error while cancelling order.', 'error');
      if (feedbackBox) {
        feedbackBox.className = 'alert-danger';
        feedbackBox.style.background = '#FEE2E2';
        feedbackBox.style.color = '#B91C1C';
        feedbackBox.style.border = '1px solid #FCA5A5';
        feedbackBox.style.display = 'block';
        feedbackBox.textContent = 'Network communication error. Please try again.';
      }
    } finally {
      if (confirmBtn) {
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = origBtnHtml;
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

  // Page Loader — sleek, responsive reveal animation without buffering lag
  const loader = document.getElementById('page-loader');
  if (loader) {
    setTimeout(() => {
      loader.classList.add('loaded');
      document.body.classList.add('page-revealed');
      setTimeout(() => {
        try { loader.remove(); } catch(e) {}
      }, 500);
    }, 450);
  }
});
