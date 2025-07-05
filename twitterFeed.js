// twitterFeed.js
// Browser-side code to fetch and render tweets in the updates section
async function fetchTweets() {
  const container = document.getElementById('tweets-container');
  if (!container) return;
  try {
    const res = await fetch('http://localhost:3000/api/tweets/Behen Kumari. Mayawati');
    if (!res.ok) throw new Error('Network response was not ok: ' + res.status);
    const data = await res.json();
    if (data && data.data && data.data.length > 0) {
      container.innerHTML = data.data.slice(0, 2).map(tweet => {
        const tweetUrl = `https://twitter.com/Behen Kumari. Mayawati/status/${tweet.id}`;
        const tweetDate = new Date(tweet.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
        return `
          <blockquote class="twitter-tweet">
            <p lang="en" dir="ltr">${tweet.text}</p>
            &mdash; Behen Kumari. Mayawati <a href="${tweetUrl}">${tweetDate}</a>
          </blockquote>
        `;
      }).join('');
      // Load Twitter widgets.js to render embeds
      if (window.twttr && window.twttr.widgets) {
        window.twttr.widgets.load(container);
      } else {
        const script = document.createElement('script');
        script.setAttribute('src', 'https://platform.twitter.com/widgets.js');
        script.setAttribute('async', '');
        script.setAttribute('charset', 'utf-8');
        document.body.appendChild(script);
      }
    } else {
      container.textContent = 'No tweets found.';
    }
  } catch (err) {
    container.textContent = 'Error: ' + err.message;
  }
}
document.addEventListener('DOMContentLoaded', fetchTweets);
