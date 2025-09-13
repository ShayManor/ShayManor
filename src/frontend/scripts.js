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
    toggle.style.background = show ? 'rgba(0, 245, 255, 0.2)' : 'rgba(0, 245, 255, 0.1)';
  }
  window.toggleNewsletter = toggleNewsletter;

  document.addEventListener('click', function (event) {
    const signup = byId('newsletterSignup');
    const toggle = byId('newsletterFloatToggle');
    if (signup && toggle && signup.style.display === 'block') {
      if (!signup.contains(event.target) && !toggle.contains(event.target)) {
        signup.style.display = 'none';
        toggle.style.background = 'rgba(0, 245, 255, 0.1)';
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
  async function fetchBlogPosts() {
    const loadingEl = byId('blog-loading');
    const errorEl = byId('blog-error');
    const postsEl = byId('blog-posts');
    if (!loadingEl || !postsEl) return;

    try {
      loadingEl.style.display = 'block';
      if (errorEl) errorEl.style.display = 'none';
      postsEl.innerHTML = '';

      const res = await fetch(`${SUPABASE_URL}/rest/v1/site_blog?order=created_at.desc`, {
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          'Content-Type': 'application/json'
        }
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const posts = await res.json();

      loadingEl.style.display = 'none';
      if (!posts.length) { postsEl.innerHTML = '<div class="no-posts"><p>No blog posts found.</p></div>'; return; }

      const html = posts.map(post => {
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
      }).join('');
      postsEl.innerHTML = html;

    } catch (e) {
      console.error('Error fetching blog posts:', e);
      loadingEl.style.display = 'none';
      if (errorEl) errorEl.style.display = 'block';
    }
  }

  // ---- Init on DOM ready ----
  document.addEventListener('DOMContentLoaded', function () {
    // Newsletter form (only exists on blog page)
    const newsletterForm = byId('newsletterForm');
    if (newsletterForm) newsletterForm.addEventListener('submit', handleNewsletterSubmit);

    // Blog posts (only on blog page)
    if (byId('blog-posts')) fetchBlogPosts();

    // Intersection Observer for sections (fade-in)
    const sections = document.querySelectorAll('.section');
    if (sections.length) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => { if (entry.isIntersecting) entry.target.classList.add('visible'); });
      }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
      sections.forEach(s => observer.observe(s));
    }

    // Navbar scroll effect
    const navbar = document.querySelector('.navbar');
    if (navbar) {
      window.addEventListener('scroll', () => {
        navbar.style.background = (window.scrollY > 50)
          ? 'rgba(10, 10, 10, 0.98)'
          : 'rgba(10, 10, 10, 0.95)';
      });
    }
  });
})();
