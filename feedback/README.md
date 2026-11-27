# Customer feedback queue

`queue.json` is the list of customer feedback the owner has approved for posting. The Friday auto-post uses the
next `status: "unused"` entry (about one post in four) and then marks it `posted`. Nothing is ever invented:
if the queue has no unused entry, no feedback post is made.

Entry format:
```json
{
  "id": "2026-11-27-short-slug",
  "name": "First name or full name exactly as the customer agreed to show it",
  "time": "1d",                         // optional, shown under the name
  "text": "Customer's words, copied exactly",
  "photo": "event-slug",                // optional: feedback/photos/event-slug.jpg (square-ish photo of the order/event)
  "consent": true,                      // owner confirmed the customer is OK with name, words and photo being shown
  "status": "unused",                   // unused | posted
  "posted_at": null
}
```
This repo is public, so only add a photo or name here when the customer has agreed.
Render with `make_brand_post.py` using a `feedback` block, see `library/brand/example-feedback.json`.
