Where to Cache

- External Caching
- CDN (Content Delivery Network)
- Client-Side Caching
- In-Process Caching

Cache Architectures

- Cache-Aside (Lazy Loading)
- Write-Through Caching
- Write-Behind (Write-Back) Caching
- Read-Through Caching

Cache Eviction Policies

- LRU (Least Recently Used)
- LFU (Least Frequently Used)
- FIFO (First In First Out)
- TTL (Time To Live)


Common Caching Problems

- Cache Stampede (Thundering Herd)
    - **Request coalescing (single flight)** Allow only one request to rebuild the cache while others wait for the result. This is the most effective solution.
    - **Cache warming** Refresh popular keys proactively before they expire. This only helps when using TTL-based expiration. If you invalidate cache on writes instead, warming does not prevent stampedes.
- Cache Consistency
    - **Cache invalidation on writes**: Delete the cache entry after updating the database so it gets repopulated with fresh data.
    - **Short TTLs for stale tolerance**: Let slightly stale data live temporarily if eventual consistency is acceptable.
    - **Accept eventual consistency** For feeds, metrics, and analytics, a short delay is usually fine.
- Hot Keys:
    - **Replicate hot keys** Store the same value on multiple cache nodes and load balance reads across them.
    - Add a local fallback cache: Keep extremely hot values in-process to avoid pounding Redis.
    - Apply rate limiting: Slow down abusive traffic patterns on specific keys.

Caching in System Design Interviews

- When to Bring Up Caching
- How to Introduce Caching

Conclusion

**Don't jump straight to caching. You need to establish why it's necessary first.**