#pragma once

// TODO:
// - optimize data structure of Key/Val: avoid copies of std::string
// - use memory pool to manage KVBlocks

#include <boost/unordered/unordered_flat_map.hpp>
#include <cassert>
#include <cstring>
#include <functional>
#include <list>
#include <memory>
#include <random>
#include <string>
#include <type_traits>
#include <unordered_map>

#include "dmc_table.h"
#include "dmc_utils.h"
#include "priority.h"

// #define CLIENT_CACHE_LIMIT (10000) // now passed from outside
#define USE_CLIENT_CACHE
#define META_UPDATE_ON
enum CCEVICTION_OPTION { DUMB_SIMPLE, DUMB_RANDOM, LRU };
#define CCEVICTION DUMB_SIMPLE

class KVBlock;
using NodePtr = KVBlock *;
using KeyType = std::string;
using ValType = std::string;

class KVBlock {
  using MetaType = struct {
    uint64_t raddr{0};
    Slot slot{};
  };
  using LRUAtrr = struct {
    NodePtr prev{nullptr};
    NodePtr next{nullptr};
  };

  // key/value
  KeyType key{};
  ValType val{};
  // metadata
  MetaType meta{};
  // LRU list
  LRUAtrr link{};
  // used for sample, set by pool
  bool valid{false};

 public:
  KVBlock() { reserve_for_string(); }
  ~KVBlock() = default;
  KVBlock(const KVBlock &) = delete;

  inline bool is_valid() const { return valid; }
  inline void set_valid() { valid = true; }
  inline void set_invalid() { valid = false; }

  template <typename... Args>
  KVBlock(Args... args) {
    reserve_for_string();
    reset(args...);
  }
  void reset(const KeyType &k, const ValType &v, const uint64_t &slot_raddr,
             const Slot &slot);

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

 private:
  void reserve_for_string() { key.reserve(32), val.reserve(32); }
};

class BlockPool {
  KVBlock blocks[CLIENT_CACHE_LIMIT];
  std::list<unsigned> free_list;

 public:
  BlockPool();

  inline NodePtr alloc();
  template <typename... Args>
  inline NodePtr construct(Args... args);

  inline void free(NodePtr ptr);

  inline NodePtr select_one_valid_randomly();
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
  using HashMap =
      std::conditional<CCEVICTION == DUMB_SIMPLE,
                       std::unordered_map<KeyType, NodePtr>,
                       boost::unordered_flat_map<KeyType, NodePtr>>::type;

  const unsigned cid;
  /* core */
  HashMap hash_map{};
  CCCounter cnter{};
  FuncUpdMeta callback_update_rmeta_{nullptr};
  BlockPool block_pool;

  /* eviction */
  const CCEVICTION_OPTION EVICTION_USED{CCEVICTION};
  // LRU
  NodePtr lru_head{nullptr}, lru_tail{nullptr};

 public:
  ClientCache(unsigned id);
  ~ClientCache();
  void set_call_back(FuncUpdMeta call_back) {
    callback_update_rmeta_ = call_back;
  }
  // counter functions
  const CCCounter &get_counter() const { return cnter; }
  void clear_counters() { clear_times(), memset(&cnter, 0, sizeof(cnter)); }
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
  void multi_evict(size_t n);
  void evict();
  // pick a victim, and maintain eviction structures inside
  NodePtr pick_evict();

  // insert
  void insert(KeyType key, ValType val, const Slot &lslot, uint64_t slot_raddr);

  // LRU functions
  void lru_set_node_to_head(NodePtr n);
  NodePtr lru_get_tail_node() { return lru_tail->prev(); }
  NodePtr lru_pop_tail_node();
  void lru_print(const char *action = "") const;

 public:
  // time measurement
  Timer insert_timer, evict_timer, get_timer;
  Timer any_timer{false};

 private:
  void clear_times() {
    insert_timer.clear(), evict_timer.clear(), get_timer.clear();
  }
  void print_info() const;
};
