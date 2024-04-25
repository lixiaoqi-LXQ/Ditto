#include "client_cache.hh"

bool lcache_log_on = false;
template <typename... Args>
inline void lcache_log(const char *fmt, Args... arg) {
  if (not lcache_log_on) return;
  char buf[100]{};
  sprintf(buf, "[Local Cache Log] %s\n", fmt);
  printf(buf, arg...);
}

using std::make_shared;

KVBlock::KVBlock(KeyType k, ValType v, uint64_t slot_raddr, const Slot &slot)
    : key(k), val(v) {
  memcpy(&meta.slot, &slot, sizeof(Slot));
  memset(&meta.slot.meta.acc_info.acc_ts, 0, 3 * sizeof(uint64_t));
  meta.raddr = slot_raddr;
};

void KVBlock::update_slot(Priority *prio) {
  meta.slot.meta.acc_info.acc_ts = new_ts();
  meta.slot.meta.acc_info.freq++;
  if (prio != nullptr) {
    meta.slot.meta.acc_info.counter = prio->get_counter_val(&meta.slot.meta, 1);
  }
}

ClientCache::ClientCache() {
  lru_head = make_shared<KVBlock>();
  lru_tail = make_shared<KVBlock>();
  lru_head->set_ptr(nullptr, lru_tail);
  lru_tail->set_ptr(lru_head, nullptr);
}

uint32_t ClientCache::get(const void *key, uint32_t key_len,
                          __OUT void *val_out_buffer) {
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
    return 0;
  }

  // update infomation
  cnter.num_hit++;
  it->second->update_slot();
  lru_set_node_to_head(it->second);
  // log
  lcache_log("get %s hit, freq %u now", key_str.c_str(),
             it->second->get_slot().meta.acc_info.freq);
  // do the job
  auto &val = it->second->get_val();
  memcpy(val_out_buffer, val.c_str(), val.length());
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
    lru_set_node_to_head(it->second);
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

void ClientCache::evict() {
  cnter.num_evict++;
  auto evictim = pick_evict();
  auto iter = hash_map.find(evictim->get_key());
  assert(iter != hash_map.end());
  NodePtr block_ptr = iter->second;
  lcache_log("evict %s, access time %u", iter->first.c_str(),
             block_ptr->get_slot().meta.acc_info.freq);
  // only update for accessed data
  if (block_ptr->get_slot().meta.acc_info.freq != 0) {
#ifdef META_UPDATE_ON
    callback_update_rmeta_(block_ptr->get_slot(), block_ptr->get_slot_raddr());
#endif
    cnter.num_update++;
  }
  hash_map.erase(iter);
}

void ClientCache::insert(const void *key, uint32_t key_len, const void *val,
                         uint32_t val_len, const Slot &lslot,
                         uint64_t slot_raddr) {
  std::string key_str(static_cast<const char *>(key), key_len);
  std::string val_str(static_cast<const char *>(val), val_len);
  assert(key_str.length() == key_len and val_str.length() == val_len);
  insert(key_str, val_str, lslot, slot_raddr);
}

void ClientCache::insert(KVBlock::KeyType key, KVBlock::ValType val,
                         const Slot &lslot, uint64_t slot_raddr) {
  if (CLIENT_CACHE_LIMIT == 0) return;
  assert(hash_map.size() <= CLIENT_CACHE_LIMIT);
  if (hash_map.size() == CLIENT_CACHE_LIMIT) evict();
  auto new_block = make_shared<KVBlock>(key, val, slot_raddr, lslot);
  lru_set_node_to_head(new_block);
  hash_map.insert({key, new_block});
  lcache_log("insert %s", key.c_str());
}

void ClientCache::lru_set_node_to_head(NodePtr n) {
  if (not use_lru_evict) return;
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

ClientCache::NodePtr ClientCache::lru_pop_tail_node() {
  if (not use_lru_evict) return nullptr;
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
    printf("%p(%p, %p)->", node.get(), node->prev().get(), node->next().get());
    node = node->next();
  }
  printf("|\n");
}