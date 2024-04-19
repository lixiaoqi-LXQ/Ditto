#pragma once

#include <cassert>
#include <cstring>
#include <functional>
#include <string>
#include <unordered_map>

#include "dmc_table.h"
#include "dmc_utils.h"
#include "priority.h"

#define ValBufLen (64)
// #define CLIENT_CACHE_LIMIT (10000)
#define USE_CLIENT_CACHE

class ValueBlock {
  // value
  uint32_t _v_len;
  char _data[ValBufLen];

  // metadata
  const uint64_t _slot_raddr;
  Slot _slot;

 public:
  ValueBlock() = delete;
  ValueBlock(const ValueBlock &) = delete;
  ValueBlock(uint32_t len, const void *data_src, const Slot &slot,
             uint64_t slot_raddr)
      : _slot_raddr(slot_raddr) {
    update_val(len, data_src);
    init_slot(slot);
  };

  // functions for value info
  void copy_val_to(__OUT void *val) const { memcpy(val, _data, _v_len); }
  uint32_t get_val_len() const { return _v_len; }
  void update_val(uint32_t len, const void *data_src) {
    assert(0 < len && len <= ValBufLen);
    memcpy(_data, data_src, len);
    _v_len = len;
  }
  // functions for slot
  const Slot &get_slot() { return _slot; }
  uint64_t get_slot_raddr() const { return _slot_raddr; }
  void update_slot(Priority *prio = nullptr) {
    _slot.meta.acc_info.acc_ts = new_ts();
    _slot.meta.acc_info.freq++;
    if (prio != nullptr) {
      _slot.meta.acc_info.counter = prio->get_counter_val(&_slot.meta, 1);
    }
  }

 private:
  void copy_slot(const Slot &slot) { memcpy(&_slot, &slot, sizeof(Slot)); }
  void init_slot(const Slot &slot) {
    copy_slot(slot);
    reset_slot();
  }
  void reset_slot() {
    _slot.meta.acc_info.acc_ts = _slot.meta.acc_info.counter =
        _slot.meta.acc_info.freq = 0;
  }
};

struct CCCounter {
  uint32_t num_get{0};
  uint32_t num_set{0};
  uint32_t num_miss{0};
  uint32_t num_hit{0};
  uint32_t num_evict{0};
  uint32_t num_update{0};  // update metadata
};

class ClientCache {
  using FuncUpdMeta = std::function<bool(const Slot &lslot, uint64_t raddr)>;
  using CacheStructure = std::unordered_map<std::string, ValueBlock>;

  CacheStructure _cache{};
  CCCounter _cnter{};
  FuncUpdMeta _callback_update_rmeta_{nullptr};

 public:
  void set_call_back(FuncUpdMeta call_back) {
    _callback_update_rmeta_ = call_back;
  }
  // counter functions
  const CCCounter &get_nums() const { return _cnter; }
  void clear_counters() { memset(&_cnter, 0, sizeof(_cnter)); }
  bool is_full() const { return _cache.size() == CLIENT_CACHE_LIMIT; }
  size_t count() const { return _cache.size(); }

  // get/set
  uint32_t get(const void *key, uint32_t key_len, __OUT void *val);
  void set(const void *key, uint32_t key_len, const void *val, uint32_t val_len,
           const Slot &lslot, uint64_t slot_raddr);

 private:
  void evict();
  CacheStructure::iterator pick_evict() { return _cache.begin(); }
  void insert(std::string key, const void *val, uint32_t val_len,
              const Slot &lslot, uint64_t slot_raddr);
  // void evict_and_insert(const void *key, uint32_t key_len, const void *val,
  //                       uint32_t val_len);
};
