# UX-1.0 Tour Direction and Product Media

- Country collections support legacy tour records whose `countries` field is empty by deriving direction from existing tour text.
- Product cards never silently omit media when an official product URL exists: a lazy same-domain media resolver retrieves the page's Open Graph image.
- The resolver is allow-listed to the official HTTPS Tilda host and caches successful lookups.
