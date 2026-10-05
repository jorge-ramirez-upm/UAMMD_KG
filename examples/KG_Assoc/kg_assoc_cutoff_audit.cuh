#ifndef EXAMPLES_KG_ASSOC_CUTOFF_AUDIT_CUH
#define EXAMPLES_KG_ASSOC_CUTOFF_AUDIT_CUH

#include "kg_assoc_kinetics.cuh"

#include <algorithm>
#include <array>
#include <cmath>
#include <iomanip>
#include <ostream>

namespace kg_assoc {

constexpr std::array<double, 6> kCutoffAuditThresholds = {
    1.122462048309373, 1.15, 1.20, 1.25, 1.30, 1.40};

struct CutoffAudit {
  long long observations = 0;
  double maximumDistance = 0.0;
  std::array<long long, kCutoffAuditThresholds.size()> outside = {};
  std::array<double, kCutoffAuditThresholds.size()> missingBreakWeight = {};
  double totalBreakWeight = 0.0;

  void observe(double distance, double k, double r0, double ee,
               double temperature) {
    ++observations;
    maximumDistance = std::max(maximumDistance, distance);
    const double breakWeight = metropolisFactor(
        deltaU(distance, k, r0, ee), temperature, false);
    totalBreakWeight += breakWeight;
    for (std::size_t index = 0; index < kCutoffAuditThresholds.size(); ++index) {
      if (distance > kCutoffAuditThresholds[index]) {
        ++outside[index];
        missingBreakWeight[index] += breakWeight;
      }
    }
  }

  void write(std::ostream& output, const char* prefix = "") const {
    output << std::setprecision(12)
           << prefix << "active_bond_observations " << observations << "\n"
           << prefix << "maximum_active_bond_distance " << maximumDistance << "\n";
    for (std::size_t index = 0; index < kCutoffAuditThresholds.size(); ++index) {
      output << prefix << "cutoff " << kCutoffAuditThresholds[index]
             << " fraction_outside "
             << (observations ? static_cast<double>(outside[index]) / observations : 0.0)
             << " count_outside " << outside[index]
             << " missing_breaking_propensity "
             << (totalBreakWeight ? missingBreakWeight[index] / totalBreakWeight : 0.0)
             << "\n";
    }
  }
};

}  // namespace kg_assoc

#endif
