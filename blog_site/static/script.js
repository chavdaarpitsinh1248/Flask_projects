document.addEventListener('DOMContentLoaded', function () {
  const commentForm = document.getElementById('comment-form');
  const csrf = commentForm?.dataset.csrf || '';

  // LIKE
  const likeBtn = document.getElementById('like-btn');
  if (likeBtn) {
    likeBtn.addEventListener('click', function () {
      const postId = this.dataset.postId;
      fetch(`/like/${postId}`, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrf },
        credentials: 'same-origin'
      })
        .then(r => r.json())
        .then(data => {
          const likeCountEl = document.getElementById('like-count');
          if (likeCountEl) likeCountEl.textContent = data.total_likes;
          if (data.liked) {
            likeBtn.classList.remove('btn-outline-success');
            likeBtn.classList.add('btn-success');
          } else {
            likeBtn.classList.remove('btn-success');
            likeBtn.classList.add('btn-outline-success');
          }
        }).catch(console.error);
    });
  }

  // Add top-level comment via AJAX
  if (commentForm) {
    commentForm.addEventListener('submit', function (e) {
      e.preventDefault();
      const postId = this.dataset.postId;
      const content = this.querySelector('textarea[name="content"]').value.trim();
      if (!content) return alert('Comment cannot be empty.');
      fetch(`/post/${postId}/ajax_comment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
        credentials: 'same-origin',
        body: JSON.stringify({ content: content, parent_id: null })
      })
        .then(r => r.json())
        .then(data => {
          if (!data.success) return alert(data.error);
          const commentList = document.getElementById('comment-list');
          const li = document.createElement('li');
          li.className = 'list-group-item';
          li.id = `comment-${data.comment_id}`;
          li.setAttribute('data-id', data.comment_id);
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
          commentList.prepend(li);
          initCommentButtons(li);
          commentForm.reset();
        }).catch(console.error);
    });
  }

  // attach handlers to a comment li
  function initCommentButtons(li) {
    // REPLY
    li.querySelector('.reply-btn')?.addEventListener('click', function () {
      const parentId = this.dataset.id;
      const container = li.querySelector(`#reply-form-${parentId}`);
      if (!container) return;
      if (container.querySelector('form')) return; // already open
      container.innerHTML = `<form class="reply-form"><textarea class="form-control mb-2" rows="2" required></textarea>
        <button class="btn btn-sm btn-primary">Reply</button> <button type="button" class="btn btn-sm btn-secondary cancel">Cancel</button></form>`;
      container.querySelector('.cancel').addEventListener('click', () => container.innerHTML = '');
      container.querySelector('form').addEventListener('submit', function (e) {
        e.preventDefault();
        const content = this.querySelector('textarea').value.trim();
        if (!content) return alert('Comment cannot be empty.');
        const postId = commentForm.dataset.postId;
        fetch(`/post/${postId}/ajax_comment`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
          credentials: 'same-origin',
          body: JSON.stringify({ content: content, parent_id: parentId })
        })
          .then(r => r.json())
          .then(data => {
            if (!data.success) return alert(data.error);
            let ul = li.querySelector('ul.list-group');
            if (!ul) { ul = document.createElement('ul'); ul.className = 'list-group mt-2'; li.appendChild(ul); }
            const replyLi = document.createElement('li');
            const parentIndentMatch = li.className.match(/ms-(\d+)/);
            const parentIndent = parentIndentMatch ? parseInt(parentIndentMatch[1], 10) : 0;
            const newIndent = parentIndent + 4;
            replyLi.className = `list-group-item ms-${newIndent}`;
            replyLi.id = `comment-${data.comment_id}`;
            replyLi.setAttribute('data-id', data.comment_id);
            replyLi.innerHTML = `<strong>${data.username}</strong>: <span class="comment-content">${data.content}</span>
            <br><small class="text-muted">${data.created_at}</small>
            <div class="mt-2">
              <button class="btn btn-sm btn-link reply-btn" data-id="${data.comment_id}">Reply</button>
              <button class="btn btn-sm btn-link edit-comment" data-id="${data.comment_id}">Edit</button>
              <button class="btn btn-sm btn-link text-danger delete-comment" data-id="${data.comment_id}">Delete</button>
            </div>
            <div class="reply-form-container" id="reply-form-${data.comment_id}"></div>`;
            ul.appendChild(replyLi);
            initCommentButtons(replyLi);
            container.innerHTML = '';
          }).catch(console.error);
      });
    });

    // EDIT
    li.querySelector('.edit-comment')?.addEventListener('click', function () {
      const commentId = this.dataset.id;
      const contentSpan = li.querySelector('.comment-content');
      const old = contentSpan.textContent.trim();
      const container = li.querySelector('.reply-form-container');
      container.innerHTML = `<form class="edit-form"><textarea class="form-control mb-2" rows="2">${old}</textarea>
        <button class="btn btn-sm btn-success">Save</button> <button type="button" class="btn btn-sm btn-secondary cancel">Cancel</button></form>`;
      container.querySelector('.cancel').addEventListener('click', () => container.innerHTML = '');
      container.querySelector('form').addEventListener('submit', function (e) {
        e.preventDefault();
        const newContent = this.querySelector('textarea').value.trim();
        if (!newContent) return alert('Comment cannot be empty.');
        fetch(`/comment/${commentId}/ajax_edit`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
          credentials: 'same-origin',
          body: JSON.stringify({ content: newContent })
        }).then(r => r.json()).then(data => {
          if (!data.success) return alert(data.error);
          contentSpan.textContent = data.content;
          container.innerHTML = '';
        }).catch(console.error);
      });
    });

    // DELETE
    li.querySelector('.delete-comment')?.addEventListener('click', function () {
      const commentId = this.dataset.id;
      if (!confirm('Are you sure you want to delete this comment?')) return;
      fetch(`/comment/${commentId}/ajax_delete`, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrf },
        credentials: 'same-origin'
      }).then(r => r.json()).then(data => {
        if (!data.success) return alert(data.error);
        li.remove();
      }).catch(console.error);
    });
  }

  // Initialize existing comments
  document.querySelectorAll('#comment-list > li').forEach(initCommentButtons);
});

async function fetchNotifications() {
  const response = await fetch('/notif/notifications');
  const data = await response.json();
  const notifList = document.getElementById('notifList');
  const notifCountEl = document.getElementById('notifCount');

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
}

// fetch every 20s
setInterval(fetchNotifications, 20000);
fetchNotifications();

// mark as read when dropdown clicked
document.getElementById('notifDropdown').addEventListener('click', async () => {
  await fetch('/notif/notifications/mark_read', { method: 'POST' });
  document.getElementById('notifCount').textContent = '';
});
