/**
 * PageVault - Search & Live Typeahead Controller
 */

const SearchEngine = {
  state: {
    q: '',
    category_id: null,
    min_price: '',
    max_price: '',
    min_rating: '',
    in_stock: false,
    sort: 'relevance',
    page: 1,
    page_size: 12
  },

  latestQueryResult: null,
  debounceTimer: null,

  init() {
    this.bindEvents();
    this.initTypeahead();
    this.executeSearch();
  },

  bindEvents() {
    // 1. Top Navbar Search Form
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');

    if (searchForm) {
      searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.closeSuggestions();
        this.state.q = searchInput.value.trim();
        this.state.page = 1;
        this.executeSearch();
      });
    }

    // 2. Sidebar Price Filter
    const applyPriceBtn = document.getElementById('apply-price-btn');
    if (applyPriceBtn) {
      applyPriceBtn.addEventListener('click', () => {
        this.state.min_price = document.getElementById('price-min').value;
        this.state.max_price = document.getElementById('price-max').value;
        this.state.page = 1;
        this.executeSearch();
      });
    }

    // 3. Sidebar Rating Filter
    document.querySelectorAll('input[name="filter-rating"]').forEach(radio => {
      radio.addEventListener('change', (e) => {
        this.state.min_rating = e.target.value;
        this.state.page = 1;
        this.executeSearch();
      });
    });

    // 4. Sidebar In-Stock Toggle
    const stockToggle = document.getElementById('stock-only-toggle');
    if (stockToggle) {
      stockToggle.addEventListener('change', (e) => {
        this.state.in_stock = e.target.checked;
        this.state.page = 1;
        this.executeSearch();
      });
    }

    // 5. Sort By Dropdown
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
      sortSelect.addEventListener('change', (e) => {
        this.state.sort = e.target.value;
        this.state.page = 1;
        this.executeSearch();
      });
    }

    // 6. Reset Filters Button
    const resetBtn = document.getElementById('reset-filters-btn');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => this.resetFilters());
    }

    // Dismiss suggestions on outside click
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.nav-search-bar')) {
        this.closeSuggestions();
      }
    });
  },

  initTypeahead() {
    const searchInput = document.getElementById('search-input');
    const dropdown = document.getElementById('search-suggestions-dropdown');
    if (!searchInput || !dropdown) return;

    searchInput.addEventListener('input', (e) => {
      const term = e.target.value.trim();
      clearTimeout(this.debounceTimer);

      if (term.length < 2) {
        this.closeSuggestions();
        return;
      }

      this.debounceTimer = setTimeout(async () => {
        try {
          const res = await fetch(`/api/suggestions?q=${encodeURIComponent(term)}`);
          const data = await res.json();
          const suggestions = data.suggestions || [];

          if (suggestions.length === 0) {
            dropdown.innerHTML = `<div style="padding: 12px; font-size: 0.85rem; color: #64748b; text-align: center;">No matching titles for "${escapeHtml(term)}"</div>`;
            dropdown.style.display = 'block';
            return;
          }

          dropdown.innerHTML = suggestions.map(b => `
            <div class="suggestion-item" onclick="App.openBookModal(${b.book_id}); SearchEngine.closeSuggestions();">
              <img class="suggestion-thumb" src="${b.cover_image || 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1474154022i/3.jpg'}" alt="${escapeHtml(b.title)}" onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop&q=80';" />
              <div class="suggestion-info">
                <div class="suggestion-title">${escapeHtml(b.title)}</div>
                <div class="suggestion-meta">${escapeHtml(b.author_names || 'Unknown')} • <span style="color: var(--burnt-orange); font-weight: 600;">${escapeHtml(b.category_name)}</span></div>
              </div>
              <div class="suggestion-price">৳${parseFloat(b.effective_price || b.price).toFixed(2)}</div>
            </div>
          `).join('') + `
            <div class="suggestion-footer" onclick="SearchEngine.state.q = '${escapeQuote(term)}'; SearchEngine.executeSearch(); SearchEngine.closeSuggestions();">
              View all results for "${escapeHtml(term)}" →
            </div>
          `;
          dropdown.style.display = 'block';
        } catch (err) {
          dropdown.style.display = 'none';
        }
      }, 200);
    });

    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.closeSuggestions();
      }
    });
  },

  closeSuggestions() {
    const dropdown = document.getElementById('search-suggestions-dropdown');
    if (dropdown) dropdown.style.display = 'none';
  },

  selectCategory(categoryId) {
    this.state.category_id = categoryId;
    this.state.page = 1;

    document.querySelectorAll('.category-filter-btn').forEach(btn => {
      const btnCatId = btn.dataset.categoryId;
      if (!categoryId && (!btnCatId || btnCatId === 'all')) {
        btn.classList.add('active');
      } else if (categoryId && btnCatId === String(categoryId)) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    this.executeSearch();
  },

  resetFilters() {
    this.state.q = '';
    this.state.category_id = null;
    this.state.min_price = '';
    this.state.max_price = '';
    this.state.min_rating = '';
    this.state.in_stock = false;
    this.state.sort = 'relevance';
    this.state.page = 1;

    const sInput = document.getElementById('search-input');
    if (sInput) sInput.value = '';
    const minP = document.getElementById('price-min');
    if (minP) minP.value = '';
    const maxP = document.getElementById('price-max');
    if (maxP) maxP.value = '';
    const stockT = document.getElementById('stock-only-toggle');
    if (stockT) stockT.checked = false;
    const sortS = document.getElementById('sort-select');
    if (sortS) sortS.value = 'relevance';

    document.querySelectorAll('input[name="filter-rating"]').forEach(r => r.checked = false);
    const allRatingRadio = document.querySelector('input[name="filter-rating"][value=""]');
    if (allRatingRadio) allRatingRadio.checked = true;

    document.querySelectorAll('.category-filter-btn').forEach(b => {
      b.classList.toggle('active', b.dataset.categoryId === 'all');
    });

    this.closeSuggestions();
    this.executeSearch();
  },

  async executeSearch() {
    const grid = document.getElementById('books-grid');
    if (!grid) return;

    grid.innerHTML = '<div class="empty-state"><p>Loading book catalog...</p></div>';

    const params = new URLSearchParams();
    if (this.state.q) params.set('q', this.state.q);
    if (this.state.category_id) params.set('category_id', this.state.category_id);
    if (this.state.min_price) params.set('min_price', this.state.min_price);
    if (this.state.max_price) params.set('max_price', this.state.max_price);
    if (this.state.min_rating) params.set('min_rating', this.state.min_rating);
    if (this.state.in_stock) params.set('in_stock', 'true');
    if (this.state.sort) params.set('sort', this.state.sort);
    params.set('page', this.state.page);
    params.set('page_size', this.state.page_size);

    try {
      const res = await fetch(`/api/search?${params.toString()}`);
      const data = await res.json();
      this.latestQueryResult = data;

      this.renderBooks(data.books);
      this.renderPagination(data.page, data.total_pages);
    } catch (err) {
      grid.innerHTML = '<div class="empty-state"><h3>Connection Error</h3><p>Could not connect to database server.</p></div>';
    }
  },

  renderBooks(books) {
    const grid = document.getElementById('books-grid');
    const countSpan = document.getElementById('total-results-count');

    if (countSpan && this.latestQueryResult) {
      countSpan.textContent = this.latestQueryResult.total_count;
    }

    if (!books || books.length === 0) {
      grid.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <div class="empty-state-icon">📚</div>
          <h3>No Books Found Matching Your Search</h3>
          <p>Try loosening your search terms or clearing the category and price filters.</p>
          <button class="auth-btn auth-btn-primary" onclick="SearchEngine.resetFilters()">Clear Filters</button>
        </div>
      `;
      return;
    }

    const wishlist = App.wishlist || [];

    grid.innerHTML = books.map(book => {
      const discount = parseFloat(book.discount_pct || 0);
      const originalPrice = parseFloat(book.price).toFixed(2);
      const effectivePrice = parseFloat(book.effective_price || book.price).toFixed(2);
      const rating = parseFloat(book.avg_rating || 0).toFixed(1);
      const reviews = book.total_reviews || 0;
      const authors = book.authors || 'Unknown Author';
      const isWishlisted = wishlist.includes(book.book_id);

      // Urgency badges
      let secondaryBadge = '';
      if (rating >= 4.8) {
        secondaryBadge = '<span class="book-secondary-badge badge-bestseller">⭐ Bestseller</span>';
      } else if (book.stock_qty <= 20 && book.stock_qty > 0) {
        secondaryBadge = `<span class="book-secondary-badge badge-lowstock">🔥 Only ${book.stock_qty} Left</span>`;
      } else if (book.publication_year >= 2020) {
        secondaryBadge = '<span class="book-secondary-badge badge-new">🌱 New</span>';
      }

      return `
        <article class="book-card" data-book-id="${book.book_id}">
          <div class="book-cover-container">
            <img class="book-cover-img" 
                 src="${book.cover_image || 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1474154022i/3.jpg'}" 
                 alt="${escapeHtml(book.title)}" 
                 loading="lazy" 
                 onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop&q=80';" />
            
            <!-- Wishlist Heart Button -->
            <button class="wishlist-toggle-btn ${isWishlisted ? 'active' : ''}" 
                    title="${isWishlisted ? 'Remove from Wishlist' : 'Add to Wishlist'}"
                    onclick="App.toggleWishlist(${book.book_id}, event)">
              ${isWishlisted ? '♥' : '♡'}
            </button>

            ${discount > 0 ? `<span class="book-discount-badge">-${discount}% OFF</span>` : ''}
            ${secondaryBadge}
            <span class="book-category-tag">${book.category_name}</span>
          </div>
          <div class="book-info">
            <h3 class="book-title" title="${escapeHtml(book.title)}">${book.title}</h3>
            <p class="book-authors" title="${escapeHtml(authors)}">${authors}</p>
            <div class="book-meta-row">
              <div class="book-rating">
                <span class="rating-star-icon">★</span>
                <span>${rating > 0 ? rating : 'New'}</span>
                <span class="reviews-count">(${reviews})</span>
              </div>
              <div class="book-pricing">
                ${discount > 0 ? `<span class="original-price">৳${originalPrice}</span>` : ''}
                <span class="effective-price">৳${effectivePrice}</span>
              </div>
            </div>
            <div class="book-card-actions">
              <button class="btn-details" onclick="App.openBookModal(${book.book_id})">View Details</button>
              <button class="btn-buy" onclick="App.addToCart(${book.book_id}, '${escapeQuote(book.title)}', ${effectivePrice}, '${escapeQuote(book.cover_image || '')}')">Add to Cart</button>
            </div>
          </div>
        </article>
      `;
    }).join('');
  },

  renderPagination(currentPage, totalPages) {
    const container = document.getElementById('pagination-container');
    if (!container) return;

    if (totalPages <= 1) {
      container.innerHTML = '';
      return;
    }

    let html = `
      <button class="page-btn" ${currentPage === 1 ? 'disabled' : ''} onclick="SearchEngine.goToPage(${currentPage - 1})">← Prev</button>
    `;

    for (let p = 1; p <= totalPages; p++) {
      html += `
        <button class="page-btn ${p === currentPage ? 'active' : ''}" onclick="SearchEngine.goToPage(${p})">${p}</button>
      `;
    }

    html += `
      <button class="page-btn" ${currentPage === totalPages ? 'disabled' : ''} onclick="SearchEngine.goToPage(${currentPage + 1})">Next →</button>
    `;

    container.innerHTML = html;
  },

  goToPage(page) {
    this.state.page = page;
    this.executeSearch();
    window.scrollTo({ top: 120, behavior: 'smooth' });
  }
};

function escapeQuote(str) {
  if (!str) return '';
  return str.replace(/'/g, "\\'");
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
}
