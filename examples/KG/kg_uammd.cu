// kg_uammd.cu
//
// Main orchestration file for the Kremer-Grest UAMMD example.
//
// Utility tasks are split into small modules:
//   - kg_cli.*        command-line parsing and defaults
//   - kg_lammps_io.*  LAMMPS readers/writers and restart helpers
//   - kg_interactors.* force/interactor construction
//   - kg_runtime.*    particle setup, validation, thermo, and reporting
//
// Important conventions to keep in mind while reading:
//   - LAMMPS atom IDs in the input file are 1-based.
//   - UAMMD particle indexing is 0-based.

#include <uammd.cuh>

#include "Integrator/VerletNVT.cuh"
#include "kg_cli.cuh"
#include "kg_interactors.cuh"
#include "kg_lammps_io.cuh"
#include "kg_runtime.cuh"

#include <chrono>
#include <fstream>
#include <iostream>

// --------------------------
// main
// --------------------------
int main(int argc, char** argv){
  using namespace uammd;
  using kg::SimParams;
  using kg::deriveDumpFilename;
  using kg::deriveRestartFilename;
  using kg::deriveThermoFilename;

  auto sys = std::make_shared<System>(argc, argv);

  // 1. Read user options or fall back to defaults.
  SimParams par;
  try{
    par = kg::parseArgs(argc, argv);
  } catch(const std::exception& e){
    std::cerr << "Argument error: " << e.what() << "\nUse --help\n";
    return 1;
  }

  // 2. Load the initial configuration from a LAMMPS data file.
  // This provides:
  //   - the atom coordinates
  //   - atom types and molecule IDs
  //   - bond connectivity
  //   - simulation box dimensions
  kg::LammpsData ld;
  try{
    ld = kg::readLammpsDataFile(par.dataFile);
  } catch(const std::exception& e){
    std::cerr << "LAMMPS data read error: " << e.what() << "\n";
    return 1;
  }

  // 2b. Derive output filenames directly from the input data filename.
  // Example:
  //   input.lammpsdat -> input.lammpstrj
  //   input.lammpsdat -> input.restart1.lammpsdat / input.restart2.lammpsdat
  //   path/input.lammpsdat -> input.thermo
  std::string dumpFile;
  std::string thermoFile;
  try{
    dumpFile = deriveDumpFilename(par.dataFile);
    thermoFile = deriveThermoFilename(par.dataFile);
  } catch(const std::exception& e){
    std::cerr << "Output filename error: " << e.what() << "\n";
    return 1;
  }
  if(par.gzipDump){
    dumpFile += ".gz";
  }

  // 3. Translate the LAMMPS box/particle data into the centered periodic
  // representation expected by UAMMD, then run CPU-side validation before
  // any force or integration kernels are launched.
  const auto simulationBox = kg::makeSimulationBox(ld);
  const auto pd = kg::createParticleDataFromLammps(ld, sys, simulationBox);
  try{
    kg::validateInputConfiguration(ld, par, simulationBox);
  } catch(const std::exception& e){
    std::cerr << e.what() << "\n";
    return 1;
  }

  // 4. Translate the LAMMPS bond topology into the auxiliary format expected
  // by UAMMD's bonded-force module, if FENE is enabled.
  std::string bondData;
  if(par.enableFENE){
    bondData = kg::buildUammdBondDataFromLammps(ld, par.feneK, par.feneR0);
  }

  // 5. Create the two interaction terms that define the KG model:
  //   - WCA repulsion between all particles
  //   - FENE springs along each chain bond
  std::shared_ptr<Interactor> wca;
  std::shared_ptr<Interactor> fene;
  if(par.enableWCA){
    wca = kg::createWCAInteractor_CellList(pd, simulationBox.box, ld.atomTypes, par.epsilon,
                                           par.sigma, par.skin,
                                           par.forceWCANBody);
  }
  if(par.enableFENE){
    fene = kg::createFENEInteractor(pd, simulationBox.box, bondData);
  }

  // 6. Configure the time integrator.
  // `GronbechJensen` is UAMMD's Langevin-style NVT integrator.
  using NVT = VerletNVT::GronbechJensen;
  NVT::Parameters ip;
  ip.temperature = (real)par.temperature;
  ip.friction    = (real)par.friction;
  ip.dt          = (real)par.dt;
  ip.initVelocities = false; // we handle optional startup initialization explicitly
  if(par.initializeVelocities){
    kg::initializeVelocitiesAtTemperature(pd, par.temperature, false);
  }
  auto integrator = std::make_shared<NVT>(pd, ip);

  // Register both force contributions with the integrator so each time step
  // includes nonbonded and bonded forces.
  if(wca){
    integrator->addInteractor(wca);
  }
  if(fene){
    integrator->addInteractor(fene);
  }

  // 7. Open the trajectory and thermo outputs before the run starts so later
  // writes can stream directly from the time loop.
  kg::DumpWriter dump(dumpFile, par.gzipDump);
  if(!dump.good()){
    std::cerr << "Cannot open dump file: " << dumpFile << "\n";
    return 1;
  }

  std::ofstream thermo(thermoFile);
  if(!thermo){
    std::cerr << "Cannot open thermo file: " << thermoFile << "\n";
    return 1;
  }
  const std::string thermoHeader = kg::formatThermoHeader();
  thermo << thermoHeader << "\n";

  // Print a short run summary through UAMMD's message system.
  kg::logRunConfiguration(par, ld, thermoHeader);

  // 8. Write the initial state before any integration step has happened.
  kg::appendLAMMPSDumpFrame(dump, 0, ld, pd, ld.xlo, ld.xhi, ld.ylo, ld.yhi, ld.zlo, ld.zhi);

  const auto thermo0 =
      kg::computeThermoSnapshot(integrator, pd, wca, fene, ld, simulationBox,
                                par.epsilon,
                                par.sigma, par.enableWCA && par.enableFENE,
                                simulationBox.box.getVolume(), ld.natoms);
  const std::string thermoRow0 = kg::formatThermoRow(0, thermo0);
  System::log<System::MESSAGE>("[KG] %s", thermoRow0.c_str());
  thermo << thermoRow0 << "\n";

  // Optionally write an initial restart as well. This gives us a clean snapshot
  // of the starting configuration using the same machinery as later restarts.
  if(par.restartEvery > 0){
    try{
      kg::writeLAMMPSDataRestart(deriveRestartFilename(par.dataFile, 1), 0, ld, pd);
    } catch(const std::exception& e){
      std::cerr << "Restart write error: " << e.what() << "\n";
      return 1;
    }
  }

  // 9. Main simulation loop.
  // Each iteration advances the system by one time step and then performs any
  // scheduled outputs for energy, trajectory, and restart data.
  const auto loopStart = std::chrono::steady_clock::now();
  for(int step=1; step<=par.steps; ++step){
    // Advance positions/velocities by one integrator step, including all forces.
    integrator->forwardTime();

    if(par.thermoEvery>0 && step % par.thermoEvery == 0){
      const auto thermoNow =
          kg::computeThermoSnapshot(integrator, pd, wca, fene, ld, simulationBox,
                                    par.epsilon, par.sigma,
                                    par.enableWCA && par.enableFENE,
                                    simulationBox.box.getVolume(), ld.natoms);
      const std::string thermoRow = kg::formatThermoRow(step, thermoNow);
      System::log<System::MESSAGE>("[KG] %s", thermoRow.c_str());
      thermo << thermoRow << "\n";
    }

    if(par.dumpEvery>0 && step % par.dumpEvery == 0){
      // Append one trajectory frame for visualization or post-processing.
      kg::appendLAMMPSDumpFrame(dump, step, ld, pd, ld.xlo, ld.xhi, ld.ylo, ld.yhi, ld.zlo, ld.zhi);
    }

    if(par.restartEvery>0 && step % par.restartEvery == 0){
      // Alternate between two filenames.
      // This is a common restart strategy because there is always at least one
      // previously completed restart file if a write is interrupted.
      int which = ((step / par.restartEvery) % 2) ? 2 : 1;
      std::string fn;
      try{
        fn = deriveRestartFilename(par.dataFile, which);
        kg::writeLAMMPSDataRestart(fn, step, ld, pd);
      } catch(const std::exception& e){
        std::cerr << "Restart write error: " << e.what() << "\n";
        return 1;
      }
    }
  }
  const auto loopEnd = std::chrono::steady_clock::now();
  const double loopSeconds =
      std::chrono::duration<double>(loopEnd - loopStart).count();

  System::log<System::MESSAGE>("%s",
      kg::formatPerformanceSummary(loopSeconds, par.steps, ld.natoms, par.dt).c_str());
  System::log<System::MESSAGE>("[KG] Done");
  return 0;
}
