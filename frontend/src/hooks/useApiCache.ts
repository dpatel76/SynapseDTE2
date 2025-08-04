import { useRef, useCallback } from 'react';

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  promise?: Promise<T>;
}

interface ApiCacheOptions {
  ttl?: number; // Time to live in milliseconds
  dedupeWindow?: number; // Deduplication window in milliseconds
}

/**
 * Custom hook for API request caching and deduplication
 * Prevents rapid duplicate API calls and provides basic caching
 */
export function useApiCache<T>(defaultOptions: ApiCacheOptions = {}) {
  const cache = useRef<Map<string, CacheEntry<T>>>(new Map());
  const pendingRequests = useRef<Map<string, Promise<T>>>(new Map());
  
  const {
    ttl = 30000, // 30 seconds default TTL
    dedupeWindow = 1000 // 1 second deduplication window
  } = defaultOptions;

  const getCachedData = useCallback((key: string): T | null => {
    const entry = cache.current.get(key);
    if (!entry) return null;
    
    const now = Date.now();
    if (now - entry.timestamp > ttl) {
      cache.current.delete(key);
      return null;
    }
    
    return entry.data;
  }, [ttl]);

  const executeCachedRequest = useCallback(async <U extends T>(
    key: string,
    requestFn: () => Promise<U>,
    options: ApiCacheOptions = {}
  ): Promise<U> => {
    // For now, we'll use the default options from the hook
    // const effectiveTtl = options.ttl ?? ttl;
    // const effectiveDedupeWindow = options.dedupeWindow ?? dedupeWindow;
    
    // Check cache first
    const cached = getCachedData(key) as U;
    if (cached) {
      return cached;
    }
    
    // Check if there's a pending request for the same key
    const pendingRequest = pendingRequests.current.get(key) as Promise<U>;
    if (pendingRequest) {
      return pendingRequest;
    }
    
    // Execute the request
    const request = requestFn();
    pendingRequests.current.set(key, request as Promise<T>);
    
    try {
      const result = await request;
      
      // Cache the result
      cache.current.set(key, {
        data: result,
        timestamp: Date.now()
      });
      
      return result;
    } finally {
      // Clean up pending request
      pendingRequests.current.delete(key);
    }
  }, [ttl, dedupeWindow, getCachedData]);

  const invalidateCache = useCallback((keyPattern?: string) => {
    if (!keyPattern) {
      cache.current.clear();
      pendingRequests.current.clear();
      return;
    }
    
    // Invalidate keys matching pattern
    const regex = new RegExp(keyPattern);
    Array.from(cache.current.keys()).forEach(key => {
      if (regex.test(key)) {
        cache.current.delete(key);
      }
    });
    
    Array.from(pendingRequests.current.keys()).forEach(key => {
      if (regex.test(key)) {
        pendingRequests.current.delete(key);
      }
    });
  }, []);

  const prefetchData = useCallback(async <U extends T>(
    key: string,
    requestFn: () => Promise<U>
  ): Promise<void> => {
    // Don't prefetch if already cached or pending
    if (getCachedData(key) || pendingRequests.current.has(key)) {
      return;
    }
    
    try {
      await executeCachedRequest(key, requestFn);
    } catch (error) {
      // Silently ignore prefetch errors
      console.warn('Prefetch failed for key:', key, error);
    }
  }, [getCachedData, executeCachedRequest]);

  return {
    executeCachedRequest,
    getCachedData,
    invalidateCache,
    prefetchData
  };
} 