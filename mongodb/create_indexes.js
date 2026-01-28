use reddit_stream

db.raw_reddit.createIndex({ id: 1 }, { unique: true, sparse: true })
db.raw_reddit.createIndex({ created_utc: -1 })
db.raw_reddit.createIndex({ subreddit: 1, created_utc: -1 })

db.processed_reddit.createIndex({ event_ts: -1 })
db.processed_reddit.createIndex({ subreddit: 1, event_ts: -1 })
db.processed_reddit.createIndex({ author: 1, event_ts: -1 })
db.processed_reddit.createIndex({ topic: 1, event_ts: -1 })

db.aggregates_5m.createIndex({ window_start: -1, topic: 1 })
db.aggregates_5m.createIndex({ subreddit: 1, window_start: -1 })
