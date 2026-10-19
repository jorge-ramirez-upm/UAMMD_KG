#pragma once

// Benchmark-only traversal prototype.  It deliberately reuses OwnedCorrelator6
// and the exact Bank::write reduction; only the update loop order differs.
#include "../stream_correlator.h"

#include <condition_variable>
#include <mutex>
#include <thread>

namespace chain_major {

class Bank {
  streaming::Parameters cfg;
  std::vector<std::unique_ptr<streaming::OwnedCorrelator6>> chains;
 public:
  std::uint64_t frames = 0;
  Bank(std::size_t count, streaming::Parameters parameters, std::size_t budget)
      : cfg(parameters) {
    cfg.validate();
    if (!count || count > budget / (streaming::OwnedCorrelator6::bytes(cfg) + sizeof(void*)))
      throw std::runtime_error("per-chain correlators exceed --correlator-mib memory budget");
    chains.reserve(count);
    for (std::size_t c = 0; c < count; ++c)
      chains.push_back(std::make_unique<streaming::OwnedCorrelator6>(cfg));
  }
  std::size_t size() const { return chains.size(); }
  void consumeRange(const streaming::Sample* data, std::size_t count,
                    std::size_t first, std::size_t last) {
    for (std::size_t c = first; c < last; ++c)
      for (std::size_t f = 0; f < count; ++f)
        chains[c]->push(data[f * chains.size() + c]);
  }
  void write(const std::string& path, double spacing) {
    // Kept textually equivalent to streaming::Bank::write so output byte order
    // and all chain-cluster arithmetic remain the reference order.
    struct Bin { double lag; unsigned long pairs; std::array<streaming::Moments, 7> moments; };
    std::vector<Bin> bins;
    for (std::size_t c = 0; c < chains.size(); ++c) {
      auto& corr = *chains[c]; corr.evaluate();
      if (!c) {
        bins.resize(corr.size());
        for (unsigned i = 0; i < corr.size(); ++i) {
          bins[i].lag = corr.gett(i); bins[i].pairs = corr.getn(i);
        }
      }
      if (bins.size() != corr.size()) throw std::runtime_error("chain lag grids differ");
      for (unsigned i = 0; i < corr.size(); ++i) {
        if (bins[i].pairs != corr.getn(i) || bins[i].lag != corr.gett(i))
          throw std::runtime_error("chain counts or lag grids differ");
        double g = 0;
        for (int j = 0; j < 6; ++j) {
          const double x = corr.getf(i, j);
          if (!std::isfinite(x)) throw std::runtime_error("nonfinite correlation");
          bins[i].moments[j].add(x, c + 1); g += x * (j < 3 ? 1. / 5 : 1. / 30);
        }
        bins[i].moments[6].add(g, c + 1);
      }
    }
    std::ofstream out; out.exceptions(std::ios::badbit | std::ios::failbit); out.open(path);
    out << "lag_samples,lag_time,block_samples,g,g_se,Cxy,Cxz,Cyz,Cxx_yy,Cxx_zz,Cyy_zz,pairs_per_chain,pairs_total,Cxy_se,Cxz_se,Cyz_se,Cxx_yy_se,Cxx_zz_se,Cyy_zz_se\n" << std::setprecision(17);
    for (auto& b : bins) {
      std::uint64_t block = 1;
      while (b.lag >= double(cfg.slots) * block) block *= cfg.coarsening;
      out << b.lag << ',' << b.lag * spacing << ',' << block << ',' << b.moments[6].mean
          << ',' << b.moments[6].se(chains.size());
      for (int j = 0; j < 6; ++j) out << ',' << b.moments[j].mean;
      out << ',' << b.pairs << ',' << b.pairs * chains.size();
      for (int j = 0; j < 6; ++j) out << ',' << b.moments[j].se(chains.size());
      out << '\n';
    }
  }
};

class Workers {
  using Clock = std::chrono::steady_clock;
  static double seconds(Clock::time_point point) {
    return std::chrono::duration<double>(Clock::now() - point).count();
  }
  Bank& bank; std::size_t chains; unsigned count;
  std::vector<std::thread> helpers; std::vector<double> times;
  std::mutex mutex; std::condition_variable start, done;
  bool stopping = false; std::size_t generation = 0, remaining = 0, frames = 0;
  const streaming::Sample* data = nullptr; std::exception_ptr failure;
  void range(unsigned id) {
    const auto begin = Clock::now();
    bank.consumeRange(data, frames, chains * id / count, chains * (id + 1) / count);
    times[id] += seconds(begin);
  }
  void helper(unsigned id) noexcept {
    std::size_t seen = 0; std::unique_lock<std::mutex> lock(mutex);
    for (;;) {
      start.wait(lock, [&] { return stopping || seen != generation; });
      if (stopping) return;
      seen = generation; lock.unlock(); std::exception_ptr error;
      try { range(id); } catch (...) { error = std::current_exception(); }
      lock.lock(); if (error && !failure) failure = error;
      if (!--remaining) done.notify_one();
    }
  }
  void stop() noexcept {
    { std::lock_guard<std::mutex> lock(mutex); stopping = true; }
    start.notify_all(); for (auto& helper : helpers) if (helper.joinable()) helper.join();
  }
 public:
  double wall_seconds = 0, barrier_seconds = 0;
  Workers(Bank& source, std::size_t count_chains, unsigned requested)
      : bank(source), chains(count_chains), count(streaming::workerCount(requested, count_chains)), times(count) {
    try { for (unsigned id = 1; id < count; ++id) helpers.emplace_back([this, id] { helper(id); }); }
    catch (...) { stop(); throw; }
  }
  ~Workers() { stop(); }
  Workers(const Workers&) = delete;
  void consume(const streaming::Sample* samples, std::size_t input_frames) {
    const auto begin = Clock::now();
    if (count == 1) {
      data = samples; frames = input_frames; range(0);
      const double elapsed = seconds(begin); wall_seconds += elapsed; bank.frames += input_frames; return;
    }
    {
      std::lock_guard<std::mutex> lock(mutex);
      if (failure) std::rethrow_exception(failure);
      data = samples; frames = input_frames; remaining = count - 1; ++generation;
    }
    start.notify_all(); std::exception_ptr error;
    try { range(0); } catch (...) { error = std::current_exception(); }
    const auto wait = Clock::now();
    {
      std::unique_lock<std::mutex> lock(mutex);
      done.wait(lock, [&] { return remaining == 0; });
      if (error && !failure) failure = error;
      barrier_seconds += seconds(wait); wall_seconds += seconds(begin);
      if (failure) std::rethrow_exception(failure);
    }
    bank.frames += input_frames;
  }
  double aggregateSeconds() const { double total = 0; for (double value : times) total += value; return total; }
};

} // namespace chain_major
