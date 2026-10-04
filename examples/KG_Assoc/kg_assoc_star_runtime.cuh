#ifndef EXAMPLES_KG_ASSOC_STAR_RUNTIME_CUH
#define EXAMPLES_KG_ASSOC_STAR_RUNTIME_CUH

#include "kg_assoc_kinetics.cuh"
#include "kg_assoc_star_topology.cuh"

#include <cmath>
#include <set>
#include <stdexcept>
#include <unordered_map>
#include <utility>
#include <vector>

#include <uammd.cuh>

namespace kg_assoc {

struct BoxLengths {
  double x = 0.0;
  double y = 0.0;
  double z = 0.0;
};

struct StickerCoordinate {
  int id = -1;
  uammd::real3 position = uammd::make_real3(uammd::real(0.0));
};

struct AssociationCounts {
  int freeStickers = 0;
  int bonds = 0;
  int intraStarBonds = 0;
  int interStarBonds = 0;
};

inline std::vector<int> extractStickerIds(const kg::LammpsData& data) {
  std::vector<int> stickerIds;
  for (int index = 0; index < data.natoms; ++index) {
    if (data.type.at(index) == 2) {
      stickerIds.push_back(index);
    }
  }
  return stickerIds;
}

inline std::set<std::pair<int, int>> permanentBondPairs(
    const kg::LammpsData& data) {
  std::set<std::pair<int, int>> permanentBonds;
  for (const auto& lammpsBond : data.bonds) {
    const int first = lammpsBond.first - 1;
    const int second = lammpsBond.second - 1;
    if (first < 0 || second < 0 || first >= data.natoms || second >= data.natoms) {
      throw std::runtime_error("permanent bond has invalid 1-based LAMMPS ID");
    }
    const std::pair<int, int> bond = std::minmax(first, second);
    if (!permanentBonds.insert(bond).second) {
      throw std::runtime_error("duplicate permanent bond at atom IDs " +
                               std::to_string(first + 1) + " and " +
                               std::to_string(second + 1));
    }
  }
  return permanentBonds;
}

inline double minimumImage(double displacement, double length) {
  return displacement - length * std::nearbyint(displacement / length);
}

inline int cellIndex(double coordinate, double length, int cells) {
  const double cellLength = length / static_cast<double>(cells);
  int index = static_cast<int>(std::floor((coordinate + 0.5 * length) / cellLength));
  if (index < 0) {
    return 0;
  }
  if (index >= cells) {
    return cells - 1;
  }
  return index;
}

inline long long cellKey(int x, int y, int z, int cellsX, int cellsY) {
  return static_cast<long long>(x) + static_cast<long long>(cellsX) *
      (static_cast<long long>(y) + static_cast<long long>(cellsY) * z);
}

inline std::vector<Candidate> findStickerCandidates(
    const std::vector<StickerCoordinate>& stickers,
    const BoxLengths& lengths,
    double cutoff) {
  if (lengths.x <= 0.0 || lengths.y <= 0.0 || lengths.z <= 0.0 || cutoff <= 0.0) {
    throw std::runtime_error("invalid sticker candidate-search box or cutoff");
  }

  const int cellsX = std::max(1, static_cast<int>(std::floor(lengths.x / cutoff)));
  const int cellsY = std::max(1, static_cast<int>(std::floor(lengths.y / cutoff)));
  const int cellsZ = std::max(1, static_cast<int>(std::floor(lengths.z / cutoff)));
  std::unordered_map<long long, std::vector<StickerCoordinate>> cells;
  for (const StickerCoordinate& sticker : stickers) {
    if (sticker.id < 0 || !std::isfinite(sticker.position.x) ||
        !std::isfinite(sticker.position.y) || !std::isfinite(sticker.position.z)) {
      throw std::runtime_error("invalid sticker coordinate in candidate search");
    }
    const int x = cellIndex(sticker.position.x, lengths.x, cellsX);
    const int y = cellIndex(sticker.position.y, lengths.y, cellsY);
    const int z = cellIndex(sticker.position.z, lengths.z, cellsZ);
    cells[cellKey(x, y, z, cellsX, cellsY)].push_back(sticker);
  }

  std::set<std::pair<int, int>> seen;
  std::vector<Candidate> candidates;
  const double cutoffSquared = cutoff * cutoff;
  for (const auto& cell : cells) {
    for (const StickerCoordinate& first : cell.second) {
      const int cellX = cellIndex(first.position.x, lengths.x, cellsX);
      const int cellY = cellIndex(first.position.y, lengths.y, cellsY);
      const int cellZ = cellIndex(first.position.z, lengths.z, cellsZ);
      for (int offsetX = -1; offsetX <= 1; ++offsetX) {
        for (int offsetY = -1; offsetY <= 1; ++offsetY) {
          for (int offsetZ = -1; offsetZ <= 1; ++offsetZ) {
            const int neighbourX = (cellX + offsetX + cellsX) % cellsX;
            const int neighbourY = (cellY + offsetY + cellsY) % cellsY;
            const int neighbourZ = (cellZ + offsetZ + cellsZ) % cellsZ;
            const auto neighbour = cells.find(
                cellKey(neighbourX, neighbourY, neighbourZ, cellsX, cellsY));
            if (neighbour == cells.end()) {
              continue;
            }
            for (const StickerCoordinate& second : neighbour->second) {
              if (first.id == second.id) {
                continue;
              }
              const std::pair<int, int> pair = std::minmax(first.id, second.id);
              if (!seen.insert(pair).second) {
                continue;
              }
              const double dx = minimumImage(
                  static_cast<double>(second.position.x - first.position.x), lengths.x);
              const double dy = minimumImage(
                  static_cast<double>(second.position.y - first.position.y), lengths.y);
              const double dz = minimumImage(
                  static_cast<double>(second.position.z - first.position.z), lengths.z);
              const double distanceSquared = dx * dx + dy * dy + dz * dz;
              if (distanceSquared < cutoffSquared) {
                candidates.push_back({pair.first, pair.second, std::sqrt(distanceSquared)});
              }
            }
          }
        }
      }
    }
  }
  return candidates;
}

inline std::vector<Candidate> findStickerCandidates(
    std::shared_ptr<uammd::ParticleData> particles,
    const StickerState& state,
    const BoxLengths& lengths,
    double cutoff) {
  auto positions = particles->getPos(uammd::access::cpu, uammd::access::read);
  auto idToIndex = particles->getIdOrderedIndices(uammd::access::cpu);
  std::vector<StickerCoordinate> coordinates;
  coordinates.reserve(state.stickers().size());
  for (const int id : state.stickers()) {
    if (id < 0 || id >= particles->getNumParticles()) {
      throw std::runtime_error("sticker ID is outside ParticleData");
    }
    const int index = idToIndex[id];
    coordinates.push_back({id, uammd::make_real3(positions[index])});
  }
  return findStickerCandidates(coordinates, lengths, cutoff);
}

inline double stickerDistance(
    std::shared_ptr<uammd::ParticleData> particles,
    int firstId,
    int secondId,
    const BoxLengths& lengths) {
  auto positions = particles->getPos(uammd::access::cpu, uammd::access::read);
  auto idToIndex = particles->getIdOrderedIndices(uammd::access::cpu);
  const uammd::real3 first = uammd::make_real3(positions[idToIndex[firstId]]);
  const uammd::real3 second = uammd::make_real3(positions[idToIndex[secondId]]);
  const double dx = minimumImage(static_cast<double>(second.x - first.x), lengths.x);
  const double dy = minimumImage(static_cast<double>(second.y - first.y), lengths.y);
  const double dz = minimumImage(static_cast<double>(second.z - first.z), lengths.z);
  return std::sqrt(dx * dx + dy * dy + dz * dz);
}

inline AssociationCounts summarizeAssociationState(
    const kg::LammpsData& data,
    const StickerState& state,
    const std::set<std::pair<int, int>>& permanentBonds,
    long long creations,
    long long breaks) {
  state.validate();
  AssociationCounts counts;
  for (const int first : state.stickers()) {
    const int second = state.partner(first);
    if (second == -1) {
      ++counts.freeStickers;
      continue;
    }
    if (!state.isSticker(second)) {
      throw std::runtime_error("transient endpoint is not a sticker");
    }
    if (second < first) {
      continue;
    }
    const std::pair<int, int> pair = std::minmax(first, second);
    if (permanentBonds.count(pair) != 0) {
      throw std::runtime_error("transient bond duplicates permanent KG bond: atom IDs " +
                               std::to_string(first + 1) + " and " +
                               std::to_string(second + 1));
    }
    ++counts.bonds;
    if (data.mol.at(first) == data.mol.at(second)) {
      ++counts.intraStarBonds;
    } else {
      ++counts.interStarBonds;
    }
  }
  if (counts.freeStickers + 2 * counts.bonds != static_cast<int>(state.stickers().size())) {
    throw std::runtime_error("free-sticker association invariant failed");
  }
  if (counts.bonds != creations - breaks) {
    throw std::runtime_error("creation/break association invariant failed");
  }
  if (counts.bonds != counts.intraStarBonds + counts.interStarBonds) {
    throw std::runtime_error("intra/inter association invariant failed");
  }
  return counts;
}

inline AssociationCounts checkAssociationInvariants(
    std::shared_ptr<uammd::ParticleData> particles,
    const kg::LammpsData& data,
    const StickerState& state,
    const std::set<std::pair<int, int>>& permanentBonds,
    const BoxLengths& lengths,
    double r0,
    long long creations,
    long long breaks) {
  if (static_cast<int>(data.bonds.size()) != data.nbonds ||
      static_cast<int>(permanentBonds.size()) != data.nbonds) {
    throw std::runtime_error("permanent bond count changed or is not unique");
  }

  auto positions = particles->getPos(uammd::access::cpu, uammd::access::read);
  auto velocities = particles->getVel(uammd::access::cpu, uammd::access::read);
  for (int index = 0; index < particles->getNumParticles(); ++index) {
    const uammd::real3 position = uammd::make_real3(positions[index]);
    const uammd::real3 velocity = velocities[index];
    if (!std::isfinite(position.x) || !std::isfinite(position.y) ||
        !std::isfinite(position.z) || !std::isfinite(velocity.x) ||
        !std::isfinite(velocity.y) || !std::isfinite(velocity.z)) {
      throw std::runtime_error("nonfinite particle state at storage index " +
                               std::to_string(index));
    }
  }

  const AssociationCounts counts = summarizeAssociationState(
      data, state, permanentBonds, creations, breaks);
  for (const int first : state.stickers()) {
    const int second = state.partner(first);
    if (second <= first) {
      continue;
    }
    const double distance = stickerDistance(particles, first, second, lengths);
    if (!std::isfinite(distance) || distance >= r0) {
      throw std::runtime_error("active associating FENE bond invalid: atom IDs " +
                               std::to_string(first + 1) + " and " +
                               std::to_string(second + 1) + " r=" +
                               std::to_string(distance));
    }
  }
  return counts;
}

}  // namespace kg_assoc

#endif
