/**
 * PageVault - DBMS Teaching Lab & Query Inspector Controller
 */

const DBMSInspector = {
  currentData: null,

  init() {
    this.bindEvents();
  },

  bindEvents() {
    const triggerBtn = document.getElementById('open-dbms-inspector');
    if (triggerBtn) {
      triggerBtn.addEventListener('click', () => this.openModal());
    }

    const triggerLink = document.getElementById('view-full-sql-link');
    if (triggerLink) {
      triggerLink.addEventListener('click', () => this.openModal());
    }

    const closeBtn = document.getElementById('close-dbms-btn');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.closeModal());
    }

    // Tabs
    document.querySelectorAll('.dbms-tab-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const tab = e.target.closest('.dbms-tab-btn').dataset.tab;
        this.switchTab(tab);
      });
    });

    // Copy SQL button
    const copyBtn = document.getElementById('copy-sql-btn');
    if (copyBtn) {
      copyBtn.addEventListener('click', () => this.copySQL());
    }
  },

  updateData(queryData) {
    this.currentData = queryData;
    this.render();
  },

  openModal() {
    const modal = document.getElementById('dbms-modal');
    if (modal) {
      modal.classList.add('active');
      this.render();
    }
  },

  closeModal() {
    const modal = document.getElementById('dbms-modal');
    if (modal) modal.classList.remove('active');
  },

  switchTab(tabName) {
    document.querySelectorAll('.dbms-tab-btn').forEach(b => {
      b.classList.toggle('active', b.dataset.tab === tabName);
    });

    document.querySelectorAll('.dbms-panel').forEach(p => {
      p.classList.remove('active');
    });

    const targetPanel = document.getElementById(`dbms-panel-${tabName}`);
    if (targetPanel) targetPanel.classList.add('active');
  },

  render() {
    if (!this.currentData) return;

    // 1. Stats strip
    const timeEl = document.getElementById('dbms-exec-ms');
    const rowsEl = document.getElementById('dbms-row-count');
    const engineEl = document.getElementById('dbms-engine-type');

    if (timeEl) timeEl.textContent = `${this.currentData.execution_time_ms} ms`;
    if (rowsEl) rowsEl.textContent = `${this.currentData.books ? this.currentData.books.length : 0} returned (of ${this.currentData.total_count})`;
    if (engineEl) engineEl.textContent = this.currentData.db_engine;

    // 2. Syntax-highlighted SQL
    const sqlCodeBlock = document.getElementById('dbms-sql-code');
    if (sqlCodeBlock && this.currentData.mysql_query) {
      sqlCodeBlock.innerHTML = this.highlightSQL(this.currentData.mysql_query);
    }

    // 3. Bound Parameters
    const paramsTable = document.getElementById('dbms-params-tbody');
    if (paramsTable) {
      const params = this.currentData.parameters || [];
      if (params.length === 0) {
        paramsTable.innerHTML = '<tr><td colspan="3" style="color: #64748b; text-align: center;">No dynamic parameters bound (Unfiltered Query).</td></tr>';
      } else {
        paramsTable.innerHTML = params.map((p, idx) => `
          <tr>
            <td style="font-family: var(--font-mono); color: #38bdf8;">$${idx + 1}</td>
            <td style="font-family: var(--font-mono); color: #cbd5e1;">${escapeHtml(String(p))}</td>
            <td style="color: #10b981; font-size: 0.75rem;">Prepared Statement Bound (SQL Injection Protected)</td>
          </tr>
        `).join('');
      }
    }

    // 4. EXPLAIN Plan Table
    const explainTable = document.getElementById('dbms-explain-tbody');
    if (explainTable) {
      const plan = this.currentData.explain_plan || [];
      explainTable.innerHTML = plan.map(row => {
        const typeClass = `type-${(row.type || '').toLowerCase()}`;
        return `
          <tr>
            <td>${row.id}</td>
            <td>${row.select_type}</td>
            <td style="color: #a855f7; font-weight: 700;">${row.table}</td>
            <td><span class="type-badge ${typeClass}">${row.type}</span></td>
            <td style="color: #64748b;">${row.possible_keys}</td>
            <td style="color: #38bdf8; font-weight: 600;">${row.key}</td>
            <td>${row.key_len}</td>
            <td style="color: #64748b;">${row.ref}</td>
            <td style="font-weight: 700; color: #fbbf24;">${row.rows}</td>
            <td>${row.filtered}%</td>
            <td style="font-size: 0.75rem; color: #94a3b8;">${row.Extra}</td>
          </tr>
        `;
      }).join('');
    }

    // 5. Relational Algebra
    const algebraEl = document.getElementById('dbms-algebra-formula');
    if (algebraEl && this.currentData.relational_algebra) {
      algebraEl.textContent = this.currentData.relational_algebra;
    }
  },

  highlightSQL(sql) {
    let text = escapeHtml(sql);

    // Keywords
    const keywords = [
      'SELECT', 'FROM', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'JOIN', 'ON',
      'WHERE', 'AND', 'OR', 'NOT', 'GROUP BY', 'HAVING', 'ORDER BY', 'ASC', 'DESC',
      'LIMIT', 'OFFSET', 'AS', 'IN', 'BETWEEN', 'LIKE', 'MATCH', 'AGAINST',
      'BOOLEAN MODE', 'NATURAL LANGUAGE MODE'
    ];

    keywords.forEach(kw => {
      const regex = new RegExp(`\\b(${kw})\\b`, 'gi');
      text = text.replace(regex, '<span class="sql-keyword">$1</span>');
    });

    // Functions
    const funcs = ['ROUND', 'COALESCE', 'AVG', 'COUNT', 'GROUP_CONCAT', 'CONCAT', 'DISTINCT'];
    funcs.forEach(fn => {
      const regex = new RegExp(`\\b(${fn})\\b`, 'gi');
      text = text.replace(regex, '<span class="sql-func">$1</span>');
    });

    // Comments
    text = text.replace(/(--.*$)/gm, '<span class="sql-comment">$1</span>');

    return text;
  },

  copySQL() {
    if (this.currentData && this.currentData.mysql_query) {
      navigator.clipboard.writeText(this.currentData.mysql_query).then(() => {
        showToast('MySQL Query copied to clipboard!', 'success');
      });
    }
  }
};

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
}
