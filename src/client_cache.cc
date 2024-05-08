#include "client_cache.hh"

#include <boost/core/demangle.hpp>
#include <map>

bool lcache_log_on = false;
template <typename... Args>
inline void lcache_log(const char *fmt, Args... arg) {
  if (not lcache_log_on) return;
  char buf[100]{};
  sprintf(buf, "[Local Cache Log] %s\n", fmt);
  printf(buf, arg...);
}

void KVBlock::reset(const KeyType &k, const ValType &v,
                    const uint64_t &slot_raddr, const Slot &slot) {
  key = k;
  val = v;
  memcpy(&meta.slot, &slot, sizeof(Slot));
  memset(&meta.slot.meta.acc_info.acc_ts, 0, 3 * sizeof(uint64_t));
  meta.raddr = slot_raddr;
}

void KVBlock::update_slot(Priority *prio) {
  meta.slot.meta.acc_info.acc_ts = new_ts();
  meta.slot.meta.acc_info.freq++;
  if (prio != nullptr) {
    meta.slot.meta.acc_info.counter = prio->get_counter_val(&meta.slot.meta, 1);
  }
}

BlockPool::BlockPool() {
  for (unsigned i = 0; i < CLIENT_CACHE_LIMIT; i++) {
    blocks[i].set_invalid();
    free_list.push_back(i);
  }
}

NodePtr BlockPool::alloc() {
  unsigned i = *free_list.begin();
  free_list.pop_front();
  lcache_log("pool: alloc %u %p", i, &blocks[i]);
  // FIXME: the validity is undefined
  // blocks[i].set_valid();
  return &blocks[i];
}

template <typename... Args>
NodePtr BlockPool::construct(Args... args) {
  unsigned i = *free_list.begin();
  free_list.pop_front();
  blocks[i].reset(args...);
  blocks[i].set_valid();
  lcache_log("pool: alloc %u %p", i, &blocks[i]);
  return &blocks[i];
}

void BlockPool::free(NodePtr ptr) {
  unsigned i = ptr - blocks;
  blocks[i].set_invalid();
  free_list.push_front(i);
  lcache_log("pool: free %u %p %p", i, ptr, &blocks[i]);
}

NodePtr BlockPool::select_one_valid_randomly() {
  unsigned idx;
  do {
    idx = random() % CLIENT_CACHE_LIMIT;
  } while (not blocks[idx].is_valid());
  return &blocks[idx];
}

ClientCache::ClientCache(unsigned id) : cid(id) {
  switch (EVICTION_USED) {
    case LRU:
      lru_head = new KVBlock();
      lru_tail = new KVBlock();
      lru_head->set_ptr(nullptr, lru_tail);
      lru_tail->set_ptr(lru_head, nullptr);
      break;
    case DUMB_SIMPLE:
      break;  // nothing to do
    case DUMB_RANDOM:
      break;  // nothing to do
    default:
      abort();
  }
  hash_map.reserve(CLIENT_CACHE_LIMIT);
  print_info();
}

ClientCache::~ClientCache() {
  switch (EVICTION_USED) {
    case LRU:
      delete lru_head;
      delete lru_tail;
      break;
    case DUMB_SIMPLE:
    case DUMB_RANDOM:
      break;  // nothing to do
    default:
      abort();
  }
}

uint32_t ClientCache::get(const void *key, uint32_t key_len,
                          __OUT void *val_out_buffer) {
  get_timer.start();
  cnter.num_get++;
#ifndef USE_CLIENT_CACHE
  return 0;
#else

  std::string key_str(static_cast<const char *>(key), key_len);
  assert(key_str.length() == key_len);
  auto it = hash_map.find(key_str);
  if (it == hash_map.end()) {
    lcache_log("get %s miss", key_str.c_str());
    cnter.num_miss++;
    get_timer.stop();
    return 0;
  }

  // update infomation
  cnter.num_hit++;
  it->second->update_slot();
  switch (EVICTION_USED) {
    case LRU:
      lru_set_node_to_head(it->second);
      break;
    case DUMB_SIMPLE:
    case DUMB_RANDOM:
      break;  // nothing to do
    default:
      abort();
  }
  // log
  lcache_log("get %s hit (block ptr %p), freq %u now", key_str.c_str(),
             it->second, it->second->get_slot().meta.acc_info.freq);
  // do the job
  auto &val = it->second->get_val();
  memcpy(val_out_buffer, val.c_str(), val.length());
  get_timer.stop();
  return val.length();
#endif
}

void ClientCache::set(const void *key, uint32_t key_len, const void *val,
                      uint32_t val_len, const Slot &lslot,
                      uint64_t slot_raddr) {
  cnter.num_set++;
#ifndef USE_CLIENT_CACHE
  return;
#else
  std::string key_str(static_cast<const char *>(key), key_len);
  std::string val_str(static_cast<const char *>(val), val_len);
  assert(key_str.length() == key_len and val_str.length() == val_len);
  auto it = hash_map.find(key_str);
  if (it != hash_map.end()) {
    // cached object
    cnter.num_hit++;
    it->second->update_val(val_str);
    it->second->update_slot();
    switch (EVICTION_USED) {
      case LRU:
        lru_set_node_to_head(it->second);
        break;
      case DUMB_SIMPLE:
      case DUMB_RANDOM:
        break;  // nothing to do
      default:
        abort();
    }
    lcache_log("set %s hit, freq %u now", key_str.c_str(),
               it->second->get_slot().meta.acc_info.freq);
    return;
  } else {
    cnter.num_miss++;
    lcache_log("set %s miss", key_str.c_str());
    insert(key_str, val_str, lslot, slot_raddr);
  }
#endif
}

NodePtr ClientCache::pick_evict() {
  NodePtr ret;
  switch (EVICTION_USED) {
    case LRU:
      ret = lru_pop_tail_node();
      break;
    case DUMB_SIMPLE:
      ret = hash_map.begin()->second;
      break;
    case DUMB_RANDOM: {
      // true method for random evict
      ret = block_pool.select_one_valid_randomly();
      break;
    }
    default:
      abort();
  }
  return ret;
}

void ClientCache::evict() {
  evict_timer.start();
  cnter.num_evict++;
  auto victim = pick_evict();  // @cost: 200ns
  lcache_log("evict %s (block ptr %p), access time %u",
             victim->get_key().c_str(), victim,
             victim->get_slot().meta.acc_info.freq);
  // only update for accessed data
  if (victim->get_slot().meta.acc_info.freq != 0) {
#ifdef META_UPDATE_ON
    callback_update_rmeta_(victim->get_slot(),
                           victim->get_slot_raddr());  // @cost: 500ns
#endif
    cnter.num_update++;
  }
  auto num_evicted = hash_map.erase(victim->get_key());  // @cost: 700ns
  assert(num_evicted == 1);
  block_pool.free(victim);
  evict_timer.stop();
}

void ClientCache::multi_evict(size_t n) {
  evict_timer.start();

  n = std::min(n, count());
  cnter.num_evict += n;
  // std::vector<NodePtr> victims;
  for (int i = 0; i < n; i++) {
    auto victim = pick_evict();
    auto iter = hash_map.find(victim->get_key());
    assert(iter != hash_map.end());
    NodePtr block_ptr = iter->second;
    lcache_log("evict-%u %s, access time %u", i + 1, iter->first.c_str(),
               block_ptr->get_slot().meta.acc_info.freq);
    //   // only update for accessed data
    //   if (block_ptr->get_slot().meta.acc_info.freq != 0) {
    // #ifdef META_UPDATE_ON
    //     callback_update_rmeta_(block_ptr->get_slot(),
    //     block_ptr->get_slot_raddr());
    // #endif
    //     cnter.num_update++;
    //   }
    hash_map.erase(iter);
  }

  evict_timer.stop();
}

void ClientCache::insert(const void *key, uint32_t key_len, const void *val,
                         uint32_t val_len, const Slot &lslot,
                         uint64_t slot_raddr) {
#ifndef USE_CLIENT_CACHE
  return;
#else
  std::string key_str(static_cast<const char *>(key), key_len);
  std::string val_str(static_cast<const char *>(val), val_len);
  assert(key_str.length() == key_len and val_str.length() == val_len);
  insert(key_str, val_str, lslot, slot_raddr);
#endif
}

void ClientCache::insert(KeyType key, ValType val, const Slot &lslot,
                         uint64_t slot_raddr) {
  if (CLIENT_CACHE_LIMIT == 0) return;
  assert(hash_map.size() <= CLIENT_CACHE_LIMIT);
  bool should_evcit = hash_map.size() == CLIENT_CACHE_LIMIT;
  if (should_evcit) evict();
  // multi_evict(CLIENT_CACHE_LIMIT * 0.01);

  insert_timer.start();
  auto new_block = block_pool.construct(key, val, slot_raddr, lslot);
  hash_map.insert({key, new_block});
  switch (EVICTION_USED) {
    case LRU:
      lru_set_node_to_head(new_block);
      break;
    case DUMB_SIMPLE:
      break;
    case DUMB_RANDOM: {
      break;
    }
    default:
      abort();
  }
  lcache_log("insert %s (block ptr: %p)", key.c_str(), new_block);
  insert_timer.stop();
}

void ClientCache::lru_set_node_to_head(NodePtr n) {
  if (n->prev() != nullptr and n->next() != nullptr) {
    n->prev()->set_next(n->next());
    n->next()->set_prev(n->prev());
    n->set_ptr(nullptr, nullptr);
  }
  assert(n->prev() == nullptr and n->next() == nullptr);
  n->set_ptr(lru_head, lru_head->next());
  lru_head->next()->set_prev(n);
  lru_head->set_next(n);
  // lru_print("insert node to head");
}

NodePtr ClientCache::lru_pop_tail_node() {
  auto tail = lru_tail->prev();
  assert(tail != lru_head);
  tail->prev()->set_next(lru_tail);
  lru_tail->set_prev(tail->prev());
  tail->set_ptr(nullptr, nullptr);
  // lru_print("pop node from tail");
  return tail;
}

void ClientCache::lru_print(const char *action) const {
  printd(L_INFO, "print lru after %s", action);
  NodePtr node = lru_head;
  while (node != nullptr) {
    // printf("%p(%p, %p)->", node.get(), node->prev().get(),
    // node->next().get());
    node = node->next();
  }
  printf("|\n");
}

static const std::map<CCEVICTION_OPTION, const char *> EvictionNameMap{
    {DUMB_SIMPLE, "DUMB-SIMPLE"},
    {DUMB_RANDOM, "DUMB-RANDOM"},
    {LRU, "LRU"},
};

void ClientCache::print_info() const {
  printf("Client Cache Config\n");
#ifdef USE_CLIENT_CACHE
  printf("\tClient ID : %u\n", cid);
  printf("\tClient Cache Limit: %lld\n", CLIENT_CACHE_LIMIT);
  printf("\tEviction Method: %s\n", EvictionNameMap.at(EVICTION_USED));
  printf("\tHash Table Data Structure: %s\n",
         boost::core::demangle(typeid(hash_map).name()).c_str());
#ifdef META_UPDATE_ON
  printf("\tShould Update Remote Metadata: true\n");
#else
  printf("\tShould Update Remote Metadata: false\n");
#endif
#else
  printf("\tDo Not Use Client Cache\n");
#endif
}