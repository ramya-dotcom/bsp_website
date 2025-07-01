// server.js
// Express server to fetch tweets from Twitter API

const express = require('express');
const axios = require('axios');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Twitter API v2 Bearer Token (set in .env)
const BEARER_TOKEN = process.env.TWITTER_BEARER_TOKEN;

// Helper to fetch tweets from Twitter API v2
async function fetchTweets(username, max_results = 5) {
  // Get user ID from username
  const userUrl = `https://api.twitter.com/2/users/by/username/${username}`;
  const userResp = await axios.get(userUrl, {
    headers: { Authorization: `Bearer ${BEARER_TOKEN}` }
  });
  const userId = userResp.data.data.id;

  // Get tweets for user ID
  const tweetsUrl = `https://api.twitter.com/2/users/${userId}/tweets?max_results=${max_results}&tweet.fields=created_at,text`;
  const tweetsResp = await axios.get(tweetsUrl, {
    headers: { Authorization: `Bearer ${BEARER_TOKEN}` }
  });
  return tweetsResp.data;
}

// API endpoint to get tweets for a handle
app.get('/api/tweets/Mayawati', async (req, res) => { 
  const max = req.query.max || 5;
  try {
    const tweets = await fetchTweets('Mayawati', max);
    res.json(tweets);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
