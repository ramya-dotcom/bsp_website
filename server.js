// server.js
// Express server to fetch tweets from Twitter API

const express = require('express');
const axios = require('axios');
const cors = require('cors');
const fs = require('fs');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Twitter API v2 Bearer Token (set in .env)
const BEARER_TOKEN = process.env.TWITTER_BEARER_TOKEN;

// Enable CORS for all requests
app.use(cors());

// Persistent caching for tweets using a JSON file
const CACHE_FILE = 'tweetCache.json';

// Load persistent cache from file
let tweetCache = {};
try {
  if (fs.existsSync(CACHE_FILE)) {
    tweetCache = JSON.parse(fs.readFileSync(CACHE_FILE, 'utf-8'));
  }
} catch (e) {
  console.error('Failed to load cache file:', e.message);
  tweetCache = {};
}
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

// Helper to save cache to file
function saveCache() {
  try {
    fs.writeFileSync(CACHE_FILE, JSON.stringify(tweetCache), 'utf-8');
  } catch (e) {
    console.error('Failed to save cache file:', e.message);
  }
}

// Helper to fetch tweets from Twitter API v2 with persistent caching
async function fetchTweets(username, max_results = 2) {
  const cacheKey = `${username}:${max_results}`;
  const now = Date.now();
  if (tweetCache[cacheKey] && (now - tweetCache[cacheKey].timestamp < CACHE_DURATION)) {
    return tweetCache[cacheKey].data;
  }
  try {
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
    // Cache the result
    tweetCache[cacheKey] = {
      data: tweetsResp.data,
      timestamp: now
    };
    saveCache();
    return tweetsResp.data;
  } catch (err) {
    console.error('Twitter API error:', err.response ? err.response.data : err.message);
    throw err;
  }
}

// API endpoint to get tweets for a handle
app.get('/api/tweets/Mayawati', async (req, res) => { 
  const max = req.query.max || 2;
  try {
    const tweets = await fetchTweets('Mayawati', max);
    res.json(tweets);
  } catch (err) {
    console.error('API endpoint error:', err.response ? err.response.data : err.message);
    res.status(500).json({ error: err.message, details: err.response ? err.response.data : undefined });
  }
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
