#pragma once

#include <cassert>
#include <cstring>
#include <string>
#include <unordered_map>

#include "dmc_utils.h"

#define ValBufLen (64)
#define N_CACHE_LIMIT (10000)
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

class ClientCache {
  std::unordered_map<std::string, ValueBlock> _cache;
  struct Counter {
    uint32_t num_miss{0};
    uint32_t num_hit{0};
    uint32_t num_evict{0};
  } _cnter;

 public:
  const struct Counter &get_nums() const { return _cnter; }
  uint32_t get_num_miss() const { return _cnter.num_miss; }
  uint32_t get_num_hit() const { return _cnter.num_hit; }
  uint32_t get_num_evict() const { return _cnter.num_evict; }
  uint32_t get(const void *key, uint32_t key_len, __OUT void *val) {
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
#ifndef USE_CLIENT_CACHE
    return;
#else
    std::string key_str(static_cast<const char *>(key));
    assert(key_str.length() == key_len or key_str.length() + 1 == key_len);
    auto it = _cache.find(key_str);
    if (it != _cache.end()) {
      // cached object
      // _cnter.num_hit++;
      it->second.update(val_len, val);
      return;
    }
    // _cnter.num_miss++;
    if (_cache.size() >= N_CACHE_LIMIT) evict();
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
