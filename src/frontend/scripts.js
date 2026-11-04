// static/scripts.js
(function () {
  'use strict';

  // ---- Config (public) ----
  const SUPABASE_URL = 'https://eteavfeiumodbjywzqfa.supabase.co';
  const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV0ZWF2ZmVpdW1vZGJqeXd6cWZhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5NTY1MDIsImV4cCI6MjA3MDUzMjUwMn0.OoB4llKDEtXq0CGgPavqMYEAsZtRF8St_C-YPU-MNPw';

  // ---- Helpers ----
  const byId = (id) => document.getElementById(id);
  function escapeHtml(text) {
    const map = {
      "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#039;"
    };
    return (text || '').toString().replace(/[&<>"']/g, m => map[m]);
  }
  function formatDate(dateString) {
    const d = new Date(dateString);
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric', timeZone: 'UTC' });
  }

  // ---- Mobile menu ----
  function toggleMobileMenu() {
    const navLinks = document.querySelector('.nav-links');
    const mobileToggle = document.querySelector('.mobile-menu-toggle');
    if (!navLinks || !mobileToggle) return;
    navLinks.classList.toggle('active');
    mobileToggle.classList.toggle('active');
  }
  // expose for onclick in HTML
  window.toggleMobileMenu = toggleMobileMenu;

  // ---- Newsletter toggle & outside click ----
  function toggleNewsletter() {
    const signup = byId('newsletterSignup');
    const toggle = byId('newsletterFloatToggle');
    if (!signup || !toggle) return;
    const show = !(signup.style.display === 'block');
    signup.style.display = show ? 'block' : 'none';
    toggle.style.background = show ? 'rgba(38, 72, 107, 0.08)' : '';
  }
  window.toggleNewsletter = toggleNewsletter;

  document.addEventListener('click', function (event) {
    const signup = byId('newsletterSignup');
    const toggle = byId('newsletterFloatToggle');
    if (signup && toggle && signup.style.display === 'block') {
      if (!signup.contains(event.target) && !toggle.contains(event.target)) {
        signup.style.display = 'none';
        toggle.style.background = '';
      }
    }
  });

  // ---- Newsletter submit ----
  async function handleNewsletterSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const email = form.email.value.trim();
    const frequency = form.frequency.value;
    const button = byId('newsletterButton');

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) { showNewsletterMessage('Please enter a valid email address.', 'error'); return; }

    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Subscribing...';

    try {
      const response = await fetch('https://shaymanor.com/add_email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, frequency })
      });
      const result = await response.json();
      if (response.ok && result.status === 200) {
        showNewsletterMessage('Successfully subscribed! Welcome to the newsletter.', 'success');
        form.reset(); const daily = byId('daily'); if (daily) daily.checked = true;
      } else {
        throw new Error(result.message || 'Subscription failed');
      }
    } catch (err) {
      console.error('Newsletter subscription error:', err);
      showNewsletterMessage('Something went wrong. Please try again later.', 'error');
    } finally {
      button.disabled = false;
      button.innerHTML = '<i class="fas fa-paper-plane"></i> Subscribe';
    }
  }

  function showNewsletterMessage(text, type) {
    const message = byId('newsletterMessage');
    if (!message) return;
    message.textContent = text;
    message.className = `newsletter-message ${type}`;
    message.style.display = 'block';
    setTimeout(() => { message.style.display = 'none'; }, 5000);
  }

  // ---- Blog fetch & render (works with or without Marked) ----
  const isBlogPage = /^\/blog(\/|$|\.)/.test(window.location.pathname);
  const blogFetchPromise = isBlogPage
    ? fetch(`${SUPABASE_URL}/rest/v1/site_blog?select=id,title,tldr,body,created_at&order=created_at.desc&limit=20`, {
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          'Content-Type': 'application/json'
        }
      }).then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
    : null;

  function renderPostHtml(post) {
    const tldrText = post.tldr || '';
    const hasPrefix = /^(tl;dr|tldr)[\s:]/i.test(tldrText.trim());
    const tldrClass = hasPrefix ? 'blog-post-tldr has-tldr' : 'blog-post-tldr';
    const rendered = (window.marked && window.marked.parse)
      ? window.marked.parse(post.body || '')
      : `<pre>${escapeHtml(post.body || '')}</pre>`;
    return `
      <article class="blog-post">
        <div class="blog-post-header">
          <h2 class="blog-post-title">${escapeHtml(post.title || 'Untitled')}</h2>
          <div class="blog-post-date">${formatDate(post.created_at)}</div>
        </div>
        ${post.tldr ? `<div class="${tldrClass}">${escapeHtml(post.tldr)}</div>` : ''}
        <div class="blog-post-content">${rendered}</div>
      </article>`;
  }

  async function fetchBlogPosts() {
    const loadingEl = byId('blog-loading');
    const errorEl = byId('blog-error');
    const postsEl = byId('blog-posts');
    if (!loadingEl || !postsEl) return;

    try {
      loadingEl.style.display = 'block';
      if (errorEl) errorEl.style.display = 'none';
      postsEl.innerHTML = '';

      const posts = await (blogFetchPromise || fetch(`${SUPABASE_URL}/rest/v1/site_blog?select=id,title,tldr,body,created_at&order=created_at.desc&limit=20`, {
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          'Content-Type': 'application/json'
        }
      }).then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      }));

      loadingEl.style.display = 'none';
      if (!posts.length) { postsEl.innerHTML = '<div class="no-posts"><p>No blog posts found.</p></div>'; return; }

      // Render above-the-fold posts immediately for fast LCP, then defer the rest
      const initialBatch = posts.slice(0, 3);
      const remainingBatch = posts.slice(3);
      postsEl.innerHTML = initialBatch.map(renderPostHtml).join('');

      if (remainingBatch.length) {
        requestAnimationFrame(() => {
          postsEl.insertAdjacentHTML('beforeend', remainingBatch.map(renderPostHtml).join(''));
        });
      }

    } catch (e) {
      console.error('Error fetching blog posts:', e);
      loadingEl.style.display = 'none';
      if (errorEl) errorEl.style.display = 'block';
    }
  }

  // ---- Project Filtering ----
  function initProjectFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const projectCards = document.querySelectorAll('.all-projects-card');

    if (!filterButtons.length || !projectCards.length) return;

    filterButtons.forEach(button => {
      button.addEventListener('click', function() {
        filterButtons.forEach(btn => btn.classList.remove('active'));
        this.classList.add('active');

        const filterValue = this.getAttribute('data-filter');

        projectCards.forEach((card) => {
          const category = card.getAttribute('data-category');
          if (filterValue === 'all' || category === filterValue) {
            card.classList.remove('hidden');
          } else {
            card.classList.add('hidden');
          }
        });
      });
    });
  }

  // ---- Scroll progress bar (side indicator on all pages) ----
  function initScrollProgress() {
    const container = document.createElement('div');
    container.className = 'scroll-progress';
    const bar = document.createElement('div');
    bar.className = 'scroll-progress-bar';
    container.appendChild(bar);
    // The "scroll" hint only belongs on the index page
    const path = window.location.pathname;
    const isIndex = path === '/' || path === '' || /\/index(\.html)?$/.test(path);
    if (isIndex) {
      const hint = document.createElement('div');
      hint.className = 'scroll-progress-hint';
      container.appendChild(hint);
    }
    document.body.appendChild(container);

    const doc = document.documentElement;
    let maxScroll = Math.max(0, doc.scrollHeight - doc.clientHeight);
    let wasScrolled = null;
    let ticking = false;

    function updatePaint() {
      ticking = false;
      const y = window.scrollY;
      const pct = maxScroll > 0 ? Math.min(Math.max(y / maxScroll, 0), 1) : 0;
      bar.style.transform = `scaleY(${pct})`;
      const isScrolled = y > 2 || maxScroll <= 0;
      if (isScrolled !== wasScrolled) {
        wasScrolled = isScrolled;
        container.classList.toggle('scrolled', isScrolled);
      }
    }

    function onScroll() {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(updatePaint);
      }
    }

    function recalcBounds() {
      maxScroll = Math.max(0, doc.scrollHeight - doc.clientHeight);
      onScroll();
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', recalcBounds, { passive: true });
    if (window.ResizeObserver) {
      new ResizeObserver(recalcBounds).observe(document.body);
    }
    updatePaint();
  }

  // ---- Init on DOM ready ----
  document.addEventListener('DOMContentLoaded', function () {
    // Scroll progress indicator
    initScrollProgress();

    // Newsletter form (only exists on blog page)
    const newsletterForm = byId('newsletterForm');
    if (newsletterForm) newsletterForm.addEventListener('submit', handleNewsletterSubmit);

    // Blog posts (only on blog page)
    if (byId('blog-posts')) fetchBlogPosts();

    // Project filters (only on projects page)
    initProjectFilters();

    // Intersection Observer for sections (fade-in)
    const sections = document.querySelectorAll('.section');
    if (sections.length) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
      sections.forEach(s => observer.observe(s));
    }

    // Navbar scroll effect (passive + state-toggled)
    const navbar = document.querySelector('.navbar');
    if (navbar) {
      let navScrolled = window.scrollY > 50;
      navbar.classList.toggle('scrolled', navScrolled);
      window.addEventListener('scroll', () => {
        const shouldScroll = window.scrollY > 50;
        if (shouldScroll !== navScrolled) {
          navScrolled = shouldScroll;
          navbar.classList.toggle('scrolled', navScrolled);
        }
      }, { passive: true });
    }
  });
})();
