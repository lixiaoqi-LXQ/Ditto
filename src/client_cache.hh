#pragma once

#include <cassert>
#include <cstring>
#include <functional>
#include <memory>
#include <string>
#include <unordered_map>

#include "dmc_table.h"
#include "dmc_utils.h"
#include "priority.h"

// #define ValBufLen (64)
// #define CLIENT_CACHE_LIMIT (10000)
#define USE_CLIENT_CACHE
#define META_UPDATE_ON
static const bool use_lru_evict = true;

class KVBlock {
 public:
  using NodePtr = std::shared_ptr<KVBlock>;
  using KeyType = std::string;
  using ValType = std::string;
  using MetaType = struct {
    uint64_t raddr{0};
    Slot slot{};
  };
  using LRUAtrr = struct {
    NodePtr prev{nullptr};
    NodePtr next{nullptr};
  };
  // using ValType = struct {
  //   char data[ValBufLen]{};
  //   uint32_t len{0};
  // };

 private:
  // key/value
  KeyType key{};
  ValType val{};
  // metadata
  MetaType meta{};
  // LRU list
  LRUAtrr link{};

 public:
  KVBlock() = default;
  KVBlock(const KVBlock &) = delete;
  KVBlock(KeyType k, ValType v, uint64_t slot_raddr, const Slot &slot);

  // functions for key value info
  const KeyType &get_key() const { return key; }
  const ValType &get_val() const { return val; }
  void update_val(const ValType &v) { val = v; }

  // functions for slot
  const Slot &get_slot() const { return meta.slot; }
  uint64_t get_slot_raddr() const { return meta.raddr; }
  void update_slot(Priority *prio = nullptr);

  // functions for LRU
  NodePtr prev() { return link.prev; }
  NodePtr next() { return link.next; }
  void set_ptr(NodePtr p, NodePtr n) { link.prev = p, link.next = n; }
  void set_prev(NodePtr node) { link.prev = node; }
  void set_next(NodePtr node) { link.next = node; }

  /* NOTE: deprecated functions
  void copy_val_to(__OUT void *val) const { memcpy(val, _data, v_len); }
  uint32_t get_val_len() const { return v_len; }
  void update_val(uint32_t len, const void *data_src) {
      string = (char *)assert(0 < len && len <= ValBufLen);
      memcpy(_data, data_src, len);
      v_len = len;
  } */
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
  using NodePtr = KVBlock::NodePtr;
  using FuncUpdMeta = std::function<bool(const Slot &lslot, uint64_t raddr)>;
  using HashMap = std::unordered_map<std::string, NodePtr>;

  NodePtr lru_head{nullptr}, lru_tail{nullptr};
  HashMap hash_map{};
  CCCounter cnter{};
  FuncUpdMeta callback_update_rmeta_{nullptr};

 public:
  ClientCache();
  void set_call_back(FuncUpdMeta call_back) {
    callback_update_rmeta_ = call_back;
  }
  // counter functions
  const CCCounter &get_nums() const { return cnter; }
  void clear_counters() { memset(&cnter, 0, sizeof(cnter)); }
  bool is_full() const { return hash_map.size() == CLIENT_CACHE_LIMIT; }
  size_t count() const { return hash_map.size(); }

  // get/set
  uint32_t get(const void *key, uint32_t key_len, __OUT void *val);
  void set(const void *key, uint32_t key_len, const void *val, uint32_t val_len,
           const Slot &lslot, uint64_t slot_raddr);
  void insert(const void *key, uint32_t key_len, const void *val,
              uint32_t val_len, const Slot &lslot, uint64_t slot_raddr);

 private:
  // evcit
  void evict();
  NodePtr pick_evict() {
    return use_lru_evict ? lru_pop_tail_node() : hash_map.begin()->second;
  }

  // insert
  void insert(KVBlock::KeyType key, KVBlock::ValType val, const Slot &lslot,
              uint64_t slot_raddr);

  // LRU functions
  void lru_set_node_to_head(NodePtr n);
  NodePtr lru_get_tail_node() { return lru_tail->prev(); }
  NodePtr lru_pop_tail_node();
  void lru_print(const char *action = "") const;
};
