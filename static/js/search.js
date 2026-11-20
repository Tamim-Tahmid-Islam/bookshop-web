/**
 * PageVault - Search & Live Typeahead Controller
 * Advanced multi-faceted filtering, active chips bar, and enhanced numbered pagination
 */

const SearchEngine = {
  state: {
    q: '',
    category_id: null,
    publisher_id: null,
    era: 'all',
    year_min: null,
    year_max: null,
    min_price: '',
    max_price: '',
    min_rating: '',
    in_stock: false,
    on_sale: false,
    sort: 'relevance',
    page: 1,
    page_size: 12
  },

  latestQueryResult: null,
  debounceTimer: null,
  categoriesCache: {},
  publishersCache: {},

  init() {
    this.bindEvents();
    this.initTypeahead();
    this.loadPublishers();
    this.executeSearch();
  },

  async loadPublishers() {
    const select = document.getElementById('publisher-filter-select');
    if (!select) return;

    try {
      const res = await fetch('/api/publishers');
      const data = await res.json();
      const publishers = data.publishers || [];

      publishers.forEach(p => {
        this.publishersCache[p.publisher_id] = p.name;
      });

      let html = '<option value="">All Publishers</option>';
      publishers.forEach(p => {
        html += `<option value="${p.publisher_id}">${escapeHtml(p.name)} (${p.book_count || 0})</option>`;
      });
      select.innerHTML = html;
    } catch (err) {
      console.warn('Could not load publishers for filter select', err);
    }
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

    // 2. Publisher Filter Dropdown
    const pubSelect = document.getElementById('publisher-filter-select');
    if (pubSelect) {
      pubSelect.addEventListener('change', (e) => {
        const val = e.target.value;
        this.state.publisher_id = val ? parseInt(val) : null;
        this.state.page = 1;
        this.executeSearch();
      });
    }

    // 3. Era Preset Pills
    document.querySelectorAll('.era-pill').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const era = e.currentTarget.dataset.era;
        this.setEra(era);
      });
    });

    // 4. Quick Price Preset Chips
    document.querySelectorAll('.price-chip').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const min = e.currentTarget.dataset.min || '';
        const max = e.currentTarget.dataset.max || '';
        this.setPricePreset(min, max, e.currentTarget);
      });
    });

    // 5. Sidebar Price Range Inputs
    const applyPriceBtn = document.getElementById('apply-price-btn');
    if (applyPriceBtn) {
      applyPriceBtn.addEventListener('click', () => {
        this.state.min_price = document.getElementById('price-min').value;
        this.state.max_price = document.getElementById('price-max').value;
        // clear active state on preset chips
        document.querySelectorAll('.price-chip').forEach(c => c.classList.remove('active'));
        this.state.page = 1;
        this.executeSearch();
      });
    }

    // 6. On-Sale / Discounted Toggle
    const saleToggle = document.getElementById('onsale-only-toggle');
    if (saleToggle) {
      saleToggle.addEventListener('change', (e) => {
        this.state.on_sale = e.target.checked;
        this.state.page = 1;
        this.executeSearch();
      });
    }

    // 7. Sidebar Star Rating Filter
    document.querySelectorAll('input[name="filter-rating"]').forEach(radio => {
      radio.addEventListener('change', (e) => {
        this.state.min_rating = e.target.value;
        this.state.page = 1;
        this.executeSearch();
      });
    });

    // 8. Sidebar In-Stock Toggle
    const stockToggle = document.getElementById('stock-only-toggle');
    if (stockToggle) {
      stockToggle.addEventListener('change', (e) => {
        this.state.in_stock = e.target.checked;
        this.state.page = 1;
        this.executeSearch();
      });
    }

    // 9. Sort By Dropdown
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
      sortSelect.addEventListener('change', (e) => {
        this.state.sort = e.target.value;
        this.state.page = 1;
        this.executeSearch();
      });
    }

    // 10. Reset Filters Button
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

  setEra(era) {
    this.state.era = era;
    if (era === 'classics') {
      this.state.year_min = null;
      this.state.year_max = 1899;
    } else if (era === '20th') {
      this.state.year_min = 1900;
      this.state.year_max = 1999;
    } else if (era === 'modern') {
      this.state.year_min = 2000;
      this.state.year_max = 2015;
    } else if (era === 'recent') {
      this.state.year_min = 2016;
      this.state.year_max = null;
    } else {
      this.state.year_min = null;
      this.state.year_max = null;
    }

    document.querySelectorAll('.era-pill').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.era === era);
    });

    this.state.page = 1;
    this.executeSearch();
  },

  setPricePreset(min, max, targetBtn) {
    const minInput = document.getElementById('price-min');
    const maxInput = document.getElementById('price-max');
    if (minInput) minInput.value = min;
    if (maxInput) maxInput.value = max;

    this.state.min_price = min;
    this.state.max_price = max;

    document.querySelectorAll('.price-chip').forEach(c => c.classList.remove('active'));
    if (targetBtn) targetBtn.classList.add('active');

    this.state.page = 1;
    this.executeSearch();
  },

  setPageSize(size) {
    this.state.page_size = parseInt(size) || 12;
    this.state.page = 1;
    this.executeSearch();
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
              <img class="suggestion-thumb" src="${b.cover_image || '/static/img/book-placeholder.svg'}" alt="${escapeHtml(b.title)}" onerror="this.onerror=null; this.src='/static/img/book-placeholder.svg';" />
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
    this.state.publisher_id = null;
    this.state.era = 'all';
    this.state.year_min = null;
    this.state.year_max = null;
    this.state.min_price = '';
    this.state.max_price = '';
    this.state.min_rating = '';
    this.state.in_stock = false;
    this.state.on_sale = false;
    this.state.sort = 'relevance';
    this.state.page = 1;

    const sInput = document.getElementById('search-input');
    if (sInput) sInput.value = '';
    const minP = document.getElementById('price-min');
    if (minP) minP.value = '';
    const maxP = document.getElementById('price-max');
    if (maxP) maxP.value = '';
    const pubSel = document.getElementById('publisher-filter-select');
    if (pubSel) pubSel.value = '';
    const stockT = document.getElementById('stock-only-toggle');
    if (stockT) stockT.checked = false;
    const saleT = document.getElementById('onsale-only-toggle');
    if (saleT) saleT.checked = false;
    const sortS = document.getElementById('sort-select');
    if (sortS) sortS.value = 'relevance';

    document.querySelectorAll('.era-pill').forEach(b => {
      b.classList.toggle('active', b.dataset.era === 'all');
    });

    document.querySelectorAll('.price-chip').forEach(c => c.classList.remove('active'));

    document.querySelectorAll('input[name="filter-rating"]').forEach(r => r.checked = false);
    const allRatingRadio = document.querySelector('input[name="filter-rating"][value=""]');
    if (allRatingRadio) allRatingRadio.checked = true;

    document.querySelectorAll('.category-filter-btn').forEach(b => {
      b.classList.toggle('active', b.dataset.categoryId === 'all');
    });

    this.closeSuggestions();
    this.executeSearch();
  },

  removeFilter(type) {
    if (type === 'q') {
      this.state.q = '';
      const input = document.getElementById('search-input');
      if (input) input.value = '';
    } else if (type === 'category') {
      this.selectCategory(null);
      return;
    } else if (type === 'publisher') {
      this.state.publisher_id = null;
      const select = document.getElementById('publisher-filter-select');
      if (select) select.value = '';
    } else if (type === 'era') {
      this.setEra('all');
      return;
    } else if (type === 'price') {
      this.state.min_price = '';
      this.state.max_price = '';
      const minInput = document.getElementById('price-min');
      const maxInput = document.getElementById('price-max');
      if (minInput) minInput.value = '';
      if (maxInput) maxInput.value = '';
      document.querySelectorAll('.price-chip').forEach(c => c.classList.remove('active'));
    } else if (type === 'rating') {
      this.state.min_rating = '';
      const allRating = document.querySelector('input[name="filter-rating"][value=""]');
      if (allRating) allRating.checked = true;
    } else if (type === 'stock') {
      this.state.in_stock = false;
      const toggle = document.getElementById('stock-only-toggle');
      if (toggle) toggle.checked = false;
    } else if (type === 'on_sale') {
      this.state.on_sale = false;
      const toggle = document.getElementById('onsale-only-toggle');
      if (toggle) toggle.checked = false;
    }

    this.state.page = 1;
    this.executeSearch();
  },

  renderActiveChips() {
    const bar = document.getElementById('active-filters-bar');
    const container = document.getElementById('active-chips-container');
    if (!bar || !container) return;

    const chips = [];

    if (this.state.q) {
      chips.push({
        type: 'q',
        html: `Keyword: <strong>"${escapeHtml(this.state.q)}"</strong>`
      });
    }

    if (this.state.category_id) {
      const activeCatBtn = document.querySelector(`.category-filter-btn[data-category-id="${this.state.category_id}"]`);
      const catName = activeCatBtn ? activeCatBtn.querySelector('span:first-child')?.textContent : `Category #${this.state.category_id}`;
      chips.push({
        type: 'category',
        html: `Category: <strong>${escapeHtml(catName)}</strong>`
      });
    }

    if (this.state.publisher_id) {
      const pubName = this.publishersCache[this.state.publisher_id] || `Publisher #${this.state.publisher_id}`;
      chips.push({
        type: 'publisher',
        html: `Publisher: <strong>${escapeHtml(pubName)}</strong>`
      });
    }

    if (this.state.era && this.state.era !== 'all') {
      const eraNames = {
        classics: 'Classics (< 1900)',
        '20th': '1900–1999',
        modern: '2000–2015',
        recent: '2016–Present'
      };
      chips.push({
        type: 'era',
        html: `Era: <strong>${eraNames[this.state.era] || this.state.era}</strong>`
      });
    }

    if (this.state.min_price || this.state.max_price) {
      let priceText = '';
      if (this.state.min_price && this.state.max_price) {
        priceText = `৳${this.state.min_price} – ৳${this.state.max_price}`;
      } else if (this.state.min_price) {
        priceText = `&ge; ৳${this.state.min_price}`;
      } else {
        priceText = `&le; ৳${this.state.max_price}`;
      }
      chips.push({
        type: 'price',
        html: `Price: <strong>${priceText}</strong>`
      });
    }

    if (this.state.on_sale) {
      chips.push({
        type: 'on_sale',
        html: `<strong>On Sale Only</strong>`
      });
    }

    if (this.state.min_rating) {
      chips.push({
        type: 'rating',
        html: `Rating: <strong>${this.state.min_rating}+ ★</strong>`
      });
    }

    if (this.state.in_stock) {
      chips.push({
        type: 'stock',
        html: `<strong>In Stock Only</strong>`
      });
    }

    if (chips.length > 0) {
      container.innerHTML = chips.map(chip => `
        <span class="active-filter-chip">
          <span>${chip.html}</span>
          <button type="button" title="Remove filter" onclick="SearchEngine.removeFilter('${chip.type}')">&times;</button>
        </span>
      `).join('');
      bar.style.display = 'block';
    } else {
      bar.style.display = 'none';
      container.innerHTML = '';
    }
  },

  async executeSearch() {
    const grid = document.getElementById('books-grid');
    if (!grid) return;

    grid.innerHTML = '<div class="empty-state"><p>Loading book catalog...</p></div>';

    const params = new URLSearchParams();
    if (this.state.q) params.set('q', this.state.q);
    if (this.state.category_id) params.set('category_id', this.state.category_id);
    if (this.state.publisher_id) params.set('publisher_id', this.state.publisher_id);
    if (this.state.year_min) params.set('year_min', this.state.year_min);
    if (this.state.year_max) params.set('year_max', this.state.year_max);
    if (this.state.min_price) params.set('min_price', this.state.min_price);
    if (this.state.max_price) params.set('max_price', this.state.max_price);
    if (this.state.min_rating) params.set('min_rating', this.state.min_rating);
    if (this.state.in_stock) params.set('in_stock', 'true');
    if (this.state.on_sale) params.set('on_sale', 'true');
    if (this.state.sort) params.set('sort', this.state.sort);
    params.set('page', this.state.page);
    params.set('page_size', this.state.page_size);

    try {
      const res = await fetch(`/api/search?${params.toString()}`);
      const data = await res.json();
      this.latestQueryResult = data;

      this.renderBooks(data.books);
      this.renderPagination(data.page, data.total_pages, data.total_count, data.start_index, data.end_index);
      this.renderActiveChips();
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
                 src="${book.cover_image || '/static/img/book-placeholder.svg'}" 
                 alt="${escapeHtml(book.title)}" 
                 loading="lazy" 
                 onerror="this.onerror=null; this.src='/static/img/book-placeholder.svg';" />
            
            <!-- Wishlist Heart Button -->
            <button class="wishlist-toggle-btn ${isWishlisted ? 'active' : ''}" 
                    title="${isWishlisted ? 'Remove from Wishlist' : 'Add to Wishlist'}"
                    onclick="App.toggleWishlist(${book.book_id}, event)">
              ${isWishlisted ? '♥' : '♡'}
            </button>

            ${discount > 0 ? `<span class="book-discount-badge">-${discount}% OFF</span>` : ''}
            ${secondaryBadge}
            <span class="book-category-tag">${escapeHtml(book.category_name)}</span>
          </div>
          <div class="book-info">
            <h3 class="book-title" title="${escapeHtml(book.title)}">${escapeHtml(book.title)}</h3>
            <p class="book-authors" title="${escapeHtml(authors)}">${escapeHtml(authors)}</p>
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

  renderPagination(currentPage, totalPages, totalCount = 0, startIndex = 1, endIndex = 12) {
    const container = document.getElementById('pagination-container');
    const infoSpan = document.getElementById('pagination-info');

    if (infoSpan) {
      if (totalCount === 0) {
        infoSpan.innerHTML = 'Showing <strong>0</strong> books';
      } else {
        infoSpan.innerHTML = `Showing <strong>${startIndex}–${endIndex}</strong> of <strong>${totalCount}</strong> books`;
      }
    }

    if (!container) return;

    if (totalPages <= 1) {
      container.innerHTML = '';
      return;
    }

    let html = `
      <button class="page-btn" ${currentPage === 1 ? 'disabled' : ''} onclick="SearchEngine.goToPage(${currentPage - 1})" title="Previous Page">← Prev</button>
    `;

    // Smart numbered pagination with ellipsis
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
      html += `<button class="page-btn ${1 === currentPage ? 'active' : ''}" onclick="SearchEngine.goToPage(1)">1</button>`;
      if (startPage > 2) {
        html += `<span class="page-btn ellipsis">...</span>`;
      }
    }

    for (let p = startPage; p <= endPage; p++) {
      html += `
        <button class="page-btn ${p === currentPage ? 'active' : ''}" onclick="SearchEngine.goToPage(${p})">${p}</button>
      `;
    }

    if (endPage < totalPages) {
      if (endPage < totalPages - 1) {
        html += `<span class="page-btn ellipsis">...</span>`;
      }
      html += `<button class="page-btn ${totalPages === currentPage ? 'active' : ''}" onclick="SearchEngine.goToPage(${totalPages})">${totalPages}</button>`;
    }

    html += `
      <button class="page-btn" ${currentPage === totalPages ? 'disabled' : ''} onclick="SearchEngine.goToPage(${currentPage + 1})" title="Next Page">Next →</button>
    `;

    container.innerHTML = html;
  },

  goToPage(page) {
    if (page < 1) return;
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
