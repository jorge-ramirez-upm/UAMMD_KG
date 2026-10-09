// Strict campaign front end for the validated production implementation.
#define KG_ASSOC_CAMPAIGN_PRODUCTION
#define main kg_assoc_validated_production_main
#include "kg_assoc_production.cu"
#undef main

#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

#ifndef KG_ASSOC_CAMPAIGN_STEPS
#define KG_ASSOC_CAMPAIGN_STEPS "100000000"
#endif

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
    std::string equilibratedPrefix;
    std::string output;
    std::string arms;
    std::string armLength;
    std::string seed;
    std::string ea;
    std::string ee;
    bool nonAssociating = false;
    for (int index = 1; index < argc; ++index) {
      const std::string option = argv[index];
      if (option == "--input") {
        input = nextCampaignArgument(index, argc, argv);
      } else if (option == "--equilibrated-prefix") {
        equilibratedPrefix = nextCampaignArgument(index, argc, argv);
      } else if (option == "--output") {
        output = nextCampaignArgument(index, argc, argv);
      } else if (option == "--arms") {
        arms = nextCampaignArgument(index, argc, argv);
      } else if (option == "--narm") {
        armLength = nextCampaignArgument(index, argc, argv);
      } else if (option == "--seed") {
        seed = nextCampaignArgument(index, argc, argv);
      } else if (option == "--Ea") {
        ea = nextCampaignArgument(index, argc, argv);
      } else if (option == "--Ee") {
        ee = nextCampaignArgument(index, argc, argv);
      } else if (option == "--non-associating") {
        nonAssociating = true;
      } else if (option == "--help") {
        std::cout << "kg_assoc_campaign_production "
                     "(--input FILE --arms F --narm N --non-associating | "
                     "--equilibrated-prefix PREFIX --Ea E --Ee E) "
                     "--output PREFIX --seed SEED\n";
        return 0;
      } else {
        throw std::runtime_error("unsupported campaign option: " + option);
      }
    }
    if ((input.empty() == equilibratedPrefix.empty()) || output.empty() || seed.empty()) {
      throw std::runtime_error("equilibrated input, output, and seed are required");
    }
    if (!input.empty() && (arms.empty() || armLength.empty())) {
      throw std::runtime_error("--input requires --arms and --narm");
    }
    if (nonAssociating != !input.empty()) {
      throw std::runtime_error("--non-associating requires a permanent-only --input");
    }
    if (!equilibratedPrefix.empty() && (ea.empty() || ee.empty())) {
      throw std::runtime_error("associating production requires --Ea and --Ee");
    }

    std::vector<std::string> arguments = {
        argv[0], "--steps", KG_ASSOC_CAMPAIGN_STEPS, "--dt", "0.01", "--temperature", "1",
        "--Ea", nonAssociating ? "4" : ea,
        "--Ee", nonAssociating ? "8" : ee,
        "--nu0", nonAssociating ? "0" : "20",
        "--Nevery", "100", "--r-assoc", "1.25", "--diagnostic-every", "1000",
        "--com-every", "10000", "--frame-every", "10000",
        "--progress-every", "100000", "--output", output, "--seed", seed};
    if (input.empty()) {
      arguments.insert(arguments.end(), {"--restart-prefix", equilibratedPrefix});
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
