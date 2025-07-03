// twitterFeed.js
// Browser-side code to fetch and render tweets in the updates section
async function fetchTweets() {
  const container = document.getElementById('tweets-container');
  if (!container) return;
  try {
    const res = await fetch('http://localhost:3000/api/tweets/Mayawati');
    if (!res.ok) throw new Error('Network response was not ok: ' + res.status);
    const data = await res.json();
    if (data && data.data && data.data.length > 0) {
      container.innerHTML = data.data.slice(0, 2).map(tweet => `
        <div class="tweet-card">
          <div class="tweet-date">${new Date(tweet.created_at).toLocaleString()}</div>
          <div class="tweet-text">${tweet.text.replace(/(https?:\/\/\S+)/g, '<a href=\"$1\" target=\"_blank\">$1</a>')}</div>
        </div>
      `).join('');
    } else {
      container.textContent = 'No tweets found.';
    }
  } catch (err) {
    container.textContent = 'Error: ' + err.message;
  }
}
document.addEventListener('DOMContentLoaded', fetchTweets);
