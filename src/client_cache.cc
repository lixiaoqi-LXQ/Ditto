#include "client_cache.hh"

uint32_t ClientCache::get(const void *key, uint32_t key_len, __OUT void *val) {
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
  it->second.copy_val_to(val);
  it->second.update_slot();
  return it->second.get_val_len();
#endif
}

void ClientCache::set(const void *key, uint32_t key_len, const void *val,
                      uint32_t val_len, const Slot &lslot,
                      uint64_t slot_raddr) {
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
    it->second.update_val(val_len, val);
    it->second.update_slot();
    return;
  }
  _cnter.num_miss++;
  if (_cache.size() >= CLIENT_CACHE_LIMIT) evict();
  insert(key_str, val, val_len, lslot, slot_raddr);
#endif
}

void ClientCache::evict() {
  _cnter.num_evict++;
  auto iter = pick_evict();
  auto &value_block = iter->second;
  // only update for accessed data
  if (value_block.get_slot().meta.acc_info.freq != 0) {
    printd(L_INFO, "local cache evicting %s, access time %u",
           iter->first.c_str(), value_block.get_slot().meta.acc_info.freq);
    _callback_update_rmeta_(value_block.get_slot(),
                            value_block.get_slot_raddr());
    _cnter.num_update++;
  }
  _cache.erase(iter);
}

void ClientCache::insert(std::string key, const void *val, uint32_t val_len,
                         const Slot &lslot, uint64_t slot_raddr) {
  _cache.emplace(std::piecewise_construct, std::forward_as_tuple(key),
                 std::forward_as_tuple(val_len, val, lslot, slot_raddr));
}

// void ClientCache::evict_and_insert(const void *key, uint32_t key_len,
//                                    const void *val, uint32_t val_len) {
// #ifndef USE_CLIENT_CACHE
//   return;
// #else
//   std::string key_str(static_cast<const char *>(key));
//   assert(key_str.length() == key_len or key_str.length() + 1 == key_len);
//   evict();
//   insert(key_str, val, val_len);
// #endif
// }