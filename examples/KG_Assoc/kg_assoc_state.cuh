#ifndef EXAMPLES_KG_ASSOC_STATE_CUH
#define EXAMPLES_KG_ASSOC_STATE_CUH

#include <thrust/device_vector.h>
#include <algorithm>
#include <stdexcept>
#include <vector>

namespace kg_assoc {

// Particle indices are stable UAMMD ids.  -1 means free; this keeps the same
// one-partner state on host and device without making topology part of I/O.
class StickerState {
 public:
  StickerState(int particleCount, std::vector<int> stickers,
               bool allocateDeviceState = true)
      : isSticker_(particleCount, false), partner_(particleCount, -1),
        stickers_(std::move(stickers)) {
    for (int i : stickers_) {
      if (i < 0 || i >= particleCount || isSticker_[i])
        throw std::runtime_error("invalid or duplicate sticker index");
      isSticker_[i] = true;
    }
    if (allocateDeviceState) {
      devicePartner_.assign(particleCount, -1);
      syncDevice();
    }
  }

  bool isSticker(int i) const { return i >= 0 && i < int(isSticker_.size()) && isSticker_[i]; }
  int partner(int i) const { return partner_.at(i); }
  bool bonded(int i, int j) const { return partner(i) == j && partner(j) == i; }
  const std::vector<int>& stickers() const { return stickers_; }
  thrust::device_vector<int>& devicePartner() { return devicePartner_; }
  const thrust::device_vector<int>& devicePartner() const { return devicePartner_; }

  void make(int i, int j) {
    if (!isSticker(i) || !isSticker(j) || i == j || partner(i) != -1 || partner(j) != -1)
      throw std::runtime_error("invalid associating creation");
    partner_[i] = j; partner_[j] = i;
  }
  void breakPair(int i, int j) {
    if (!bonded(i, j)) throw std::runtime_error("invalid associating break");
    partner_[i] = -1; partner_[j] = -1;
  }
  void loadPartners(const std::vector<int>& partners) {
    if (partners.size() != partner_.size()) {
      throw std::runtime_error("associating restart partner count mismatch");
    }
    for (int i = 0; i < static_cast<int>(partners.size()); ++i) {
      const int j = partners[i];
      if (!isSticker(i) && j != -1) {
        throw std::runtime_error("non-sticker has temporary partner in restart");
      }
      if (j == -1) {
        continue;
      }
      if (!isSticker(i) || !isSticker(j) || j == i || partners.at(j) != i) {
        throw std::runtime_error("invalid temporary partner mapping in restart");
      }
    }
    partner_ = partners;
    validate();
    syncDevice();
  }
  void syncDevice() {
    if (!devicePartner_.empty()) {
      devicePartner_ = partner_;
    }
  }
  void validate() const {
    for (int i : stickers_) {
      int j = partner_[i];
      if (j == -1) continue;
      if (!isSticker(j) || j == i || partner_[j] != i)
        throw std::runtime_error("non-reciprocal associating partner state");
    }
  }
 private:
  std::vector<bool> isSticker_;
  std::vector<int> partner_;
  std::vector<int> stickers_;
  thrust::device_vector<int> devicePartner_;
};
}  // namespace kg_assoc
#endif
