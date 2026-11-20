/**
 * PageVault - Authentication & Forgot Password Module
 */

const Auth = {
  currentUser: null,

  init() {
    this.loadSession();
    this.bindEvents();
    this.updateUI();
  },

  loadSession() {
    try {
      const stored = localStorage.getItem('pagevault_user');
      if (stored) {
        this.currentUser = JSON.parse(stored);
      }
    } catch (e) {
      this.currentUser = null;
    }
  },

  saveSession(user) {
    this.currentUser = user;
    localStorage.setItem('pagevault_user', JSON.stringify(user));
    this.updateUI();
  },

  clearSession() {
    this.currentUser = null;
    localStorage.removeItem('pagevault_user');
    this.updateUI();
    showToast('You have been logged out.');
  },

  updateUI() {
    const authLoggedOut = document.getElementById('auth-logged-out');
    const authLoggedIn = document.getElementById('auth-logged-in');
    const userNameSpan = document.getElementById('user-full-name');
    const userRoleBadge = document.getElementById('user-role-badge');
    const addBookNavBtn = document.getElementById('add-book-nav-btn');

    if (this.currentUser) {
      if (authLoggedOut) authLoggedOut.style.display = 'none';
      if (authLoggedIn) authLoggedIn.style.display = 'flex';
      if (userNameSpan) userNameSpan.textContent = this.currentUser.full_name;
      if (userRoleBadge) userRoleBadge.textContent = this.currentUser.role;
      if (addBookNavBtn) {
        // Admin or Librarian can add books
        addBookNavBtn.style.display = (this.currentUser.role === 'Admin' || this.currentUser.role === 'Librarian') ? 'inline-flex' : 'none';
      }
    } else {
      if (authLoggedOut) authLoggedOut.style.display = 'flex';
      if (authLoggedIn) authLoggedIn.style.display = 'none';
      if (addBookNavBtn) addBookNavBtn.style.display = 'none';
    }
  },

  bindEvents() {
    // Open Auth Modal
    const openLoginBtn = document.getElementById('open-login-btn');
    if (openLoginBtn) {
      openLoginBtn.addEventListener('click', () => this.showModal('login'));
    }

    const openRegisterBtn = document.getElementById('open-register-btn');
    if (openRegisterBtn) {
      openRegisterBtn.addEventListener('click', () => this.showModal('register'));
    }

    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => this.clearSession());
    }

    // Modal Tabs
    document.querySelectorAll('.auth-tab-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const tab = e.target.dataset.tab;
        this.switchTab(tab);
      });
    });

    // Forgot Password link inside login form
    const forgotPwLink = document.getElementById('goto-forgot-pw-link');
    if (forgotPwLink) {
      forgotPwLink.addEventListener('click', (e) => {
        e.preventDefault();
        this.switchTab('forgot');
      });
    }

    // Back to Login link inside forgot password form
    const backToLoginLink = document.getElementById('back-to-login-link');
    if (backToLoginLink) {
      backToLoginLink.addEventListener('click', (e) => {
        e.preventDefault();
        this.switchTab('login');
      });
    }

    // Login Form Submit
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
      loginForm.addEventListener('submit', (e) => this.handleLogin(e));
    }

    // Register Form Submit
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
      registerForm.addEventListener('submit', (e) => this.handleRegister(e));
    }

    // Forgot Password Step 1: Request Code
    const forgotForm = document.getElementById('forgot-form');
    if (forgotForm) {
      forgotForm.addEventListener('submit', (e) => this.handleForgotRequest(e));
    }

    // Forgot Password Step 2: Reset Form
    const resetForm = document.getElementById('reset-form');
    if (resetForm) {
      resetForm.addEventListener('submit', (e) => this.handleResetSubmit(e));
    }
  },

  showModal(tab = 'login') {
    const modal = document.getElementById('auth-modal');
    if (modal) {
      modal.classList.add('active');
      this.switchTab(tab);
    }
  },

  closeModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) modal.classList.remove('active');
  },

  switchTab(tabName) {
    document.querySelectorAll('.auth-tab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    document.querySelectorAll('.auth-panel').forEach(panel => {
      panel.style.display = 'none';
    });

    const activePanel = document.getElementById(`auth-panel-${tabName}`);
    if (activePanel) activePanel.style.display = 'block';
  },

  async handleLogin(e) {
    e.preventDefault();
    const idField = document.getElementById('login-identifier');
    const pwField = document.getElementById('login-password');

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identifier: idField.value, password: pwField.value })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        this.saveSession(data.user);
        this.closeModal();
        showToast(data.message, 'success');
      } else {
        showToast(data.message || 'Login failed.', 'error');
      }
    } catch (err) {
      showToast('Connection error connecting to server.', 'error');
    }
  },

  async handleRegister(e) {
    e.preventDefault();
    const username = document.getElementById('reg-username').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    const fullName = document.getElementById('reg-fullname').value;

    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password, full_name: fullName })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        showToast('Registration successful! Please sign in.', 'success');
        this.switchTab('login');
        document.getElementById('login-identifier').value = email;
      } else {
        showToast(data.message || 'Registration failed.', 'error');
      }
    } catch (err) {
      showToast('Network error during registration.', 'error');
    }
  },

  async handleForgotRequest(e) {
    e.preventDefault();
    const email = document.getElementById('forgot-email').value;
    try {
      const res = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        showToast('Reset verification token created!', 'success');
        
        // Show demo simulation box with the code and token
        const demoBox = document.getElementById('demo-token-display');
        const codeSpan = document.getElementById('demo-generated-code');
        const tokenInput = document.getElementById('reset-token-input');
        
        if (demoBox && codeSpan) {
          codeSpan.textContent = data.code;
          demoBox.style.display = 'block';
        }
        if (tokenInput) {
          tokenInput.value = data.code; // Pre-fill with the code for convenience!
        }

        // Switch to Step 2: Reset Form view
        document.getElementById('forgot-step-1').style.display = 'none';
        document.getElementById('forgot-step-2').style.display = 'block';
      } else {
        showToast(data.message || 'Error creating reset token.', 'error');
      }
    } catch (err) {
      showToast('Network error submitting reset request.', 'error');
    }
  },

  async handleResetSubmit(e) {
    e.preventDefault();
    const tokenOrCode = document.getElementById('reset-token-input').value;
    const newPassword = document.getElementById('reset-new-password').value;
    const confirmPassword = document.getElementById('reset-confirm-password').value;

    if (newPassword !== confirmPassword) {
      showToast('Passwords do not match.', 'error');
      return;
    }

    try {
      const res = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token_or_code: tokenOrCode, new_password: newPassword })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        showToast(data.message, 'success');
        // Reset form views
        document.getElementById('forgot-step-1').style.display = 'block';
        document.getElementById('forgot-step-2').style.display = 'none';
        const demoBox = document.getElementById('demo-token-display');
        if (demoBox) demoBox.style.display = 'none';
        this.switchTab('login');
      } else {
        showToast(data.message || 'Password reset failed.', 'error');
      }
    } catch (err) {
      showToast('Network error updating password.', 'error');
    }
  }
};
