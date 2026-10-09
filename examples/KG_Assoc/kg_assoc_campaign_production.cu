// Strict campaign front end for the validated production implementation.
#define main kg_assoc_validated_production_main
#include "kg_assoc_production.cu"
#undef main

#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

std::string nextCampaignArgument(int& index, int argc, char** argv) {
  if (++index >= argc) {
    throw std::runtime_error("missing campaign option value");
  }
  return argv[index];
}

}  // namespace

int main(int argc, char** argv) {
  try {
    std::string input;
    std::string restartPrefix;
    std::string output;
    std::string arms;
    std::string armLength;
    std::string seed;
    bool nonAssociating = false;
    for (int index = 1; index < argc; ++index) {
      const std::string option = argv[index];
      if (option == "--input") {
        input = nextCampaignArgument(index, argc, argv);
      } else if (option == "--restart-prefix") {
        restartPrefix = nextCampaignArgument(index, argc, argv);
      } else if (option == "--output") {
        output = nextCampaignArgument(index, argc, argv);
      } else if (option == "--arms") {
        arms = nextCampaignArgument(index, argc, argv);
      } else if (option == "--narm") {
        armLength = nextCampaignArgument(index, argc, argv);
      } else if (option == "--seed") {
        seed = nextCampaignArgument(index, argc, argv);
      } else if (option == "--non-associating") {
        nonAssociating = true;
      } else if (option == "--help") {
        std::cout << "kg_assoc_campaign_production "
                     "(--input FILE --arms F --narm N | --restart-prefix PREFIX) "
                     "--output PREFIX --seed SEED [--non-associating]\n";
        return 0;
      } else {
        throw std::runtime_error("unsupported campaign option: " + option);
      }
    }
    if ((input.empty() == restartPrefix.empty()) || output.empty() || seed.empty()) {
      throw std::runtime_error("input/restart, output, and seed are required");
    }
    if (!input.empty() && (arms.empty() || armLength.empty())) {
      throw std::runtime_error("--input requires --arms and --narm");
    }
    if (nonAssociating && !restartPrefix.empty()) {
      throw std::runtime_error("non-associating production requires a permanent-only input");
    }

    std::vector<std::string> arguments = {
        argv[0], "--steps", "100000000", "--dt", "0.01", "--temperature", "1",
        "--Ea", "4", "--Ee", "8", "--nu0", nonAssociating ? "0" : "20",
        "--Nevery", "100", "--r-assoc", "1.25", "--diagnostic-every", "1000",
        "--com-every", "10000", "--frame-every", "10000",
        "--progress-every", "100000", "--output", output, "--seed", seed};
    if (input.empty()) {
      arguments.insert(arguments.end(), {"--restart-prefix", restartPrefix});
    } else {
      arguments.insert(arguments.end(), {"--input", input, "--arms", arms,
                                         "--narm", armLength});
    }
    std::vector<char*> rawArguments;
    for (std::string& argument : arguments) {
      rawArguments.push_back(&argument[0]);
    }
    return kg_assoc_validated_production_main(
        static_cast<int>(rawArguments.size()), rawArguments.data());
  } catch (const std::exception& error) {
    std::cerr << "KG_ASSOC_CAMPAIGN_PRODUCTION FAIL: " << error.what() << '\n';
    return 1;
  }
}
