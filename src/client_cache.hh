#pragma once

#include <cassert>
#include <cstring>
#include <string>
#include <unordered_map>

#include "dmc_utils.h"

#define ValBufLen (64)
// #define CLIENT_CACHE_LIMIT (10000)
#define USE_CLIENT_CACHE

class ValueBlock {
  uint32_t _v_len;
  char _data[ValBufLen];

 public:
  ValueBlock() = delete;
  ValueBlock(const ValueBlock &) = delete;
  ValueBlock(uint32_t len, const void *data_src) { update(len, data_src); };

  void copyto(__OUT void *val) const { memcpy(val, _data, _v_len); }
  uint32_t get_len() const { return _v_len; }

  void update(uint32_t len, const void *data_src) {
    assert(0 < len && len <= ValBufLen);
    memcpy(_data, data_src, len);
    _v_len = len;
  }
};

struct CCCounter {
  uint32_t num_get{0};
  uint32_t num_set{0};
  uint32_t num_miss{0};
  uint32_t num_hit{0};
  uint32_t num_evict{0};
};

class ClientCache {
  std::unordered_map<std::string, ValueBlock> _cache;
  CCCounter _cnter;

 public:
  // counter functions
  const CCCounter &get_nums() const { return _cnter; }
  void clear_counters() { memset(&_cnter, 0, sizeof(_cnter)); }
  bool is_full() const { return _cache.size() == CLIENT_CACHE_LIMIT; }
  u_int32_t count() const { return _cache.size(); }

  // get/set
  uint32_t get(const void *key, uint32_t key_len, __OUT void *val) {
    _cnter.num_get++;
#ifndef USE_CLIENT_CACHE
    return 0;
#else
    std::string key_str(static_cast<const char *>(key));
    assert(key_str.length() == key_len or key_str.length() + 1 == key_len);
    auto it = _cache.find(key_str);
    if (it == _cache.end()) {
      _cnter.num_miss++;
      return 0;
    }
    _cnter.num_hit++;
    it->second.copyto(val);
    return it->second.get_len();
#endif
  }

  void set(const void *key, uint32_t key_len, const void *val,
           uint32_t val_len) {
    _cnter.num_set++;
#ifndef USE_CLIENT_CACHE
    return;
#else
    std::string key_str(static_cast<const char *>(key));
    assert(key_str.length() == key_len or key_str.length() + 1 == key_len);
    auto it = _cache.find(key_str);
    if (it != _cache.end()) {
      // cached object
      _cnter.num_hit++;
      it->second.update(val_len, val);
      return;
    }
    _cnter.num_miss++;
    if (_cache.size() >= CLIENT_CACHE_LIMIT) evict();
    insert(key_str, val, val_len);
#endif
  }

 private:
  void evict() {
    _cnter.num_evict++;
    _cache.erase(_cache.begin());
  }
  void insert(std::string key, const void *val, uint32_t val_len) {
    _cache.emplace(std::piecewise_construct, std::forward_as_tuple(key),
                   std::forward_as_tuple(val_len, val));
  }
  void evict_and_insert(const void *key, uint32_t key_len, const void *val,
                        uint32_t val_len) {
#ifndef USE_CLIENT_CACHE
    return;
#else
    std::string key_str(static_cast<const char *>(key));
    assert(key_str.length() == key_len or key_str.length() + 1 == key_len);
    evict();
    insert(key_str, val, val_len);
#endif
  }
};
