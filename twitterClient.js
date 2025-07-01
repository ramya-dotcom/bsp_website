// twitterClient.js
// Helper for Twitter API requests (used by server.js)

const axios = require('axios');
require('dotenv').config();

const BEARER_TOKEN = process.env.TWITTER_BEARER_TOKEN;

async function getUserId(username) {
  const url = `https://api.twitter.com/2/users/by/username/${username}`;
  const resp = await axios.get(url, {
    headers: { Authorization: `Bearer ${BEARER_TOKEN}` }
  });
  return resp.data.data.id;
}

async function getUserTweets(userId, max_results = 5) {
  const url = `https://api.twitter.com/2/users/${userId}/tweets?max_results=${max_results}&tweet.fields=created_at,text`;
  const resp = await axios.get(url, {
    headers: { Authorization: `Bearer ${BEARER_TOKEN}` }
  });
  return resp.data;
}

module.exports = { getUserId, getUserTweets };
