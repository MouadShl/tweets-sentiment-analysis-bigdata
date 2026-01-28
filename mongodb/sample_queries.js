use reddit_stream

// Latest processed documents
db.processed_reddit.find().sort({ event_ts: -1 }).limit(20)

// Top subreddits by volume in last hour (via aggregates)
const since = new Date(Date.now() - 60*60*1000)
db.aggregates_5m.aggregate([
  { $match: { window_start: { $gte: since } } },
  { $group: { _id: "$subreddit", volume: { $sum: "$volume" } } },
  { $sort: { volume: -1 } },
  { $limit: 10 }
])
