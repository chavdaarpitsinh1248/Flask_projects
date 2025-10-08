document.addEventListener('DOMContentLoaded', () => {
  const commentForm = document.getElementById('comment-form');
  const csrf = commentForm?.dataset.csrf || '';

  // ------------------ LIKE ------------------
  const likeBtn = document.getElementById('like-btn');
  if (likeBtn) likeBtn.addEventListener('click', () => handleLike(likeBtn, csrf));

  // ------------------ COMMENTS ------------------
  if (commentForm) commentForm.addEventListener('submit', e => handleNewComment(e, commentForm, csrf));
  document.querySelectorAll('#comment-list > li').forEach(initCommentButtons);

  // ------------------ NOTIFICATIONS ------------------
  const notifDropdown = document.getElementById('notifDropdown');
  const notifList = document.getElementById('notifList');
  const notifCountEl = document.getElementById('notifCount');

  // Mark notifications as read when dropdown is clicked
  if (notifDropdown) {
    notifDropdown.addEventListener('click', async () => {
      try {
        await fetch('/notif/notifications/mark_read', { method: 'POST', headers: { 'X-CSRFToken': csrf } });
        if (notifCountEl) notifCountEl.textContent = '';
      } catch (err) { console.error(err); }
    });
  }

  // Fetch notifications every 20s
  setInterval(fetchNotifications, 20000);
  fetchNotifications();

  // ------------------ FUNCTIONS ------------------

  async function fetchNotifications() {
    try {
      const response = await fetch('/notif/notifications');
      const data = await response.json();
      const notifList = document.getElementById('notifList');
      const notifCountEl = document.getElementById('notifCount');
      if (!notifList || !notifCountEl) return;

      notifList.innerHTML = '';
      if (data.notifications.length > 0) {
        notifCountEl.textContent = data.notifications.length;
        data.notifications.forEach(n => {
          const li = document.createElement('li');
          li.innerHTML = `<a class="dropdown-item" href="${n.link || '#'}">${n.message}</a>`;
          notifList.appendChild(li);
        });
      } else {
        notifCountEl.textContent = '';
        notifList.innerHTML = '<li><a class="dropdown-item" href="#">No new notifications</a></li>';
      }
    } catch (err) { console.error(err); }
  }


  // --------- LIKE & COMMENT FUNCTIONS ---------
  async function handleLike(btn, csrf) {
    const postId = btn.dataset.postId;
    try {
      const res = await fetch(`/post/${postId}/ajax_like`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
        credentials: 'same-origin'
      });
      const data = await res.json();
      if (!data.success) return;

      const likeCountEl = document.getElementById('like-count');
      if (likeCountEl) likeCountEl.textContent = data.like_count;
      btn.classList.toggle('btn-success', data.liked);
      btn.classList.toggle('btn-outline-success', !data.liked);
    } catch (err) { console.error(err); }
  }

  async function handleNewComment(e, form, csrf) {
    e.preventDefault();
    const postId = form.dataset.postId;
    const content = form.querySelector('textarea[name="content"]').value.trim();
    if (!content) return alert('Comment cannot be empty.');

    try {
      const res = await fetch(`/post/${postId}/ajax_comment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
        credentials: 'same-origin',
        body: JSON.stringify({ content, parent_id: null })
      });
      const data = await res.json();
      if (!data.success) return alert(data.error);

      const li = createCommentLi(data);
      document.getElementById('comment-list').prepend(li);
      initCommentButtons(li);
      form.reset();
    } catch (err) { console.error(err); }
  }

  function createCommentLi(data, level = 0) {
    const li = document.createElement('li');
    li.className = `list-group-item ms-${level * 4}`;
    li.id = `comment-${data.comment_id}`;
    li.dataset.id = data.comment_id;
    li.innerHTML = `
      <strong>${data.username}</strong>: <span class="comment-content">${data.content}</span>
      <br><small class="text-muted">${data.created_at}</small>
      <div class="mt-2">
        <button class="btn btn-sm btn-link reply-btn" data-id="${data.comment_id}">Reply</button>
        <button class="btn btn-sm btn-link edit-comment" data-id="${data.comment_id}">Edit</button>
        <button class="btn btn-sm btn-link text-danger delete-comment" data-id="${data.comment_id}">Delete</button>
      </div>
      <div class="reply-form-container" id="reply-form-${data.comment_id}"></div>
    `;
    return li;
  }

  function initCommentButtons(li) {
    const commentId = li.dataset.id;

    // Reply
    li.querySelector('.reply-btn')?.addEventListener('click', () => openReplyForm(li, commentId));

    // Edit
    li.querySelector('.edit-comment')?.addEventListener('click', () => openEditForm(li, commentId));

    // Delete
    li.querySelector('.delete-comment')?.addEventListener('click', async () => {
      if (!confirm('Are you sure you want to delete this comment?')) return;
      try {
        const res = await fetch(`/comment/${commentId}/ajax_delete`, {
          method: 'POST',
          headers: { 'X-CSRFToken': csrf },
          credentials: 'same-origin'
        });
        const data = await res.json();
        if (!data.success) return alert(data.error);
        li.remove();
      } catch (err) { console.error(err); }
    });
  }

  function openReplyForm(li, parentId) {
    const container = li.querySelector(`#reply-form-${parentId}`);
    if (container.querySelector('form')) return;
    container.innerHTML = `<form class="reply-form">
      <textarea class="form-control mb-2" rows="2" required></textarea>
      <button class="btn btn-sm btn-primary">Reply</button>
      <button type="button" class="btn btn-sm btn-secondary cancel">Cancel</button>
    </form>`;
    container.querySelector('.cancel').addEventListener('click', () => container.innerHTML = '');
    container.querySelector('form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const content = e.target.querySelector('textarea').value.trim();
      if (!content) return alert('Comment cannot be empty.');
      const postId = commentForm.dataset.postId;

      try {
        const res = await fetch(`/post/${postId}/ajax_comment`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
          credentials: 'same-origin',
          body: JSON.stringify({ content, parent_id: parentId })
        });
        const data = await res.json();
        if (!data.success) return alert(data.error);

        const replyLi = createCommentLi(data, getIndentLevel(li) + 1);
        let ul = li.querySelector('ul.list-group');
        if (!ul) { ul = document.createElement('ul'); ul.className = 'list-group mt-2'; li.appendChild(ul); }
        ul.appendChild(replyLi);
        initCommentButtons(replyLi);
        container.innerHTML = '';
      } catch (err) { console.error(err); }
    });
  }

  function openEditForm(li, commentId) {
    const contentSpan = li.querySelector('.comment-content');
    const container = li.querySelector('.reply-form-container');
    const old = contentSpan.textContent.trim();
    container.innerHTML = `<form class="edit-form">
      <textarea class="form-control mb-2" rows="2">${old}</textarea>
      <button class="btn btn-sm btn-success">Save</button>
      <button type="button" class="btn btn-sm btn-secondary cancel">Cancel</button>
    </form>`;
    container.querySelector('.cancel').addEventListener('click', () => container.innerHTML = '');
    container.querySelector('form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const newContent = e.target.querySelector('textarea').value.trim();
      if (!newContent) return alert('Comment cannot be empty.');
      try {
        const res = await fetch(`/comment/${commentId}/ajax_edit`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
          credentials: 'same-origin',
          body: JSON.stringify({ content: newContent })
        });
        const data = await res.json();
        if (!data.success) return alert(data.error);
        contentSpan.textContent = data.content;
        container.innerHTML = '';
      } catch (err) { console.error(err); }
    });
  }

  function getIndentLevel(li) {
    const match = li.className.match(/ms-(\d+)/);
    return match ? parseInt(match[1]) / 4 : 0;
  }

  async function fetchNotifications() {
    try {
      const response = await fetch('/notif/notifications');
      const data = await response.json();
      const notifList = document.getElementById('notifList');
      const notifCountEl = document.getElementById('notifCount');
      if (!notifList || !notifCountEl) return;

      notifList.innerHTML = '';
      if (data.notifications.length > 0) {
        notifCountEl.textContent = data.notifications.length;
        data.notifications.forEach(n => {
          const li = document.createElement('li');
          li.innerHTML = `<a href="${n.link}">${n.message}</a>`;
          notifList.appendChild(li);
        });
      } else {
        notifCountEl.textContent = '';
        notifList.innerHTML = '<li>No new notifications</li>';
      }
    } catch (err) { console.error(err); }
  }
});
