#ifndef EXAMPLES_KG_ASSOC_CORRELATOR_CHECKPOINT_CUH
#define EXAMPLES_KG_ASSOC_CORRELATOR_CHECKPOINT_CUH

#include "../KG/correlator.h"

#include <cstdint>
#include <istream>
#include <ostream>
#include <stdexcept>
#include <string>

namespace kg_assoc {

// Correlator6 deliberately exposes no persistence API.  This derived class
// serializes its complete protected multi-tau ladder without changing KG code.
class CheckpointableCorrelator6 : public Correlator6 {
 public:
  CheckpointableCorrelator6(unsigned int levels = 40,
                            unsigned int slots = 16,
                            unsigned int blocking = 2)
      : Correlator6(levels, slots, blocking) {
    initialize();
  }

  void save(std::ostream& output) const {
    const char magic[] = "KG_CORRELATOR6_V1";
    writeBytes(output, magic, sizeof(magic));
    writeValue(output, numcorrelators);
    writeValue(output, p);
    writeValue(output, m);
    writeValue(output, dmin);
    writeValue(output, length);
    writeValue(output, npcorr);
    writeValue(output, npcorrmax);
    writeValue(output, nexp);
    writeValue(output, kmax);

    for (unsigned int level = 0; level < numcorrelators; ++level) {
      for (unsigned int slot = 0; slot < p; ++slot) {
        writeValue(output, shift[level][slot]);
        writeValue(output, shift2[level][slot]);
        writeValue(output, shift3[level][slot]);
        writeValue(output, shift4[level][slot]);
        writeValue(output, shift5[level][slot]);
        writeValue(output, shift6[level][slot]);
        writeValue(output, correlation[level][slot]);
        writeValue(output, correlation2[level][slot]);
        writeValue(output, correlation3[level][slot]);
        writeValue(output, correlation4[level][slot]);
        writeValue(output, correlation5[level][slot]);
        writeValue(output, correlation6[level][slot]);
        writeValue(output, ncorrelation[level][slot]);
      }
      writeValue(output, accumulator[level]);
      writeValue(output, accumulator2[level]);
      writeValue(output, accumulator3[level]);
      writeValue(output, accumulator4[level]);
      writeValue(output, accumulator5[level]);
      writeValue(output, accumulator6[level]);
      writeValue(output, naccumulator[level]);
      writeValue(output, insertindex[level]);
    }
    if (!output) {
      throw std::runtime_error("failed to write Correlator6 checkpoint");
    }
  }

  void load(std::istream& input) {
    char magic[18] = {};
    readBytes(input, magic, sizeof(magic));
    if (std::string(magic) != "KG_CORRELATOR6_V1") {
      throw std::runtime_error("unsupported Correlator6 checkpoint");
    }

    unsigned int levels = 0;
    unsigned int slots = 0;
    unsigned int blocking = 0;
    unsigned int savedDmin = 0;
    unsigned int savedLength = 0;
    readValue(input, levels);
    readValue(input, slots);
    readValue(input, blocking);
    readValue(input, savedDmin);
    readValue(input, savedLength);
    if (levels != numcorrelators || slots != p || blocking != m ||
        savedDmin != dmin || savedLength != length) {
      throw std::runtime_error("Correlator6 checkpoint dimensions do not match");
    }
    readValue(input, npcorr);
    readValue(input, npcorrmax);
    readValue(input, nexp);
    readValue(input, kmax);
    if (kmax >= numcorrelators || npcorr > length || npcorrmax > length) {
      throw std::runtime_error("invalid Correlator6 checkpoint counters");
    }

    for (unsigned int level = 0; level < numcorrelators; ++level) {
      for (unsigned int slot = 0; slot < p; ++slot) {
        readValue(input, shift[level][slot]);
        readValue(input, shift2[level][slot]);
        readValue(input, shift3[level][slot]);
        readValue(input, shift4[level][slot]);
        readValue(input, shift5[level][slot]);
        readValue(input, shift6[level][slot]);
        readValue(input, correlation[level][slot]);
        readValue(input, correlation2[level][slot]);
        readValue(input, correlation3[level][slot]);
        readValue(input, correlation4[level][slot]);
        readValue(input, correlation5[level][slot]);
        readValue(input, correlation6[level][slot]);
        readValue(input, ncorrelation[level][slot]);
      }
      readValue(input, accumulator[level]);
      readValue(input, accumulator2[level]);
      readValue(input, accumulator3[level]);
      readValue(input, accumulator4[level]);
      readValue(input, accumulator5[level]);
      readValue(input, accumulator6[level]);
      readValue(input, naccumulator[level]);
      readValue(input, insertindex[level]);
      if (naccumulator[level] >= m || insertindex[level] >= p) {
        throw std::runtime_error("invalid Correlator6 checkpoint cursor");
      }
    }
    if (!input || input.peek() != std::istream::traits_type::eof()) {
      throw std::runtime_error("truncated or trailing Correlator6 checkpoint data");
    }
  }

 private:
  template <class Value>
  static void writeValue(std::ostream& output, const Value& value) {
    writeBytes(output, reinterpret_cast<const char*>(&value), sizeof(value));
  }

  template <class Value>
  static void readValue(std::istream& input, Value& value) {
    readBytes(input, reinterpret_cast<char*>(&value), sizeof(value));
  }

  static void writeBytes(std::ostream& output, const char* data, std::size_t size) {
    output.write(data, static_cast<std::streamsize>(size));
  }

  static void readBytes(std::istream& input, char* data, std::size_t size) {
    input.read(data, static_cast<std::streamsize>(size));
  }
};

}  // namespace kg_assoc

#endif
