# MongoDB schema, indexes & sample queries (Person 2 outputs)

Database: `reddit_stream`

## Collections

### raw_reddit
Raw documents as read from Kafka after JSON parsing.

### processed_reddit
Cleaned + enriched documents for analytics/dashboard.
Key fields:
- `event_ts` (timestamp from `created_utc`)
- `text` (cleaned, lowercased, URL removed, punctuation removed)

### aggregates_5m
Gold table for dashboard metrics:
- `window_start`, `window_end`
- `topic`, `subreddit`
- `volume`, `avg_score`

## Indexes

Run in `mongosh`:

```js
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
```

## Sample queries

```js
use reddit_stream

db.processed_reddit.find().sort({ event_ts: -1 }).limit(20)

const since = new Date(Date.now() - 60*60*1000)
db.aggregates_5m.aggregate([
  { $match: { window_start: { $gte: since } } },
  { $group: { _id: "$subreddit", volume: { $sum: "$volume" } } },
  { $sort: { volume: -1 } },
  { $limit: 10 }
])
```
