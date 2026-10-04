---
layout: post
title: "ISCA 2025: Toward Full-System Heterogeneous Simulation: Merging gem5-SALAM with Mainline gem5"
author: Akanksha Chaudhari, Matt Sinclair(UW-Madison).
date:   2025-07-30
---

# Towards Full-System Heterogeneous Simulation in gem5

As SoC architectures grow increasingly heterogeneous, they now integrate not only CPUs and GPUs but also tightly coupled programmable accelerators tailored for specific workloads. These accelerators are critical for emerging domains such as mobile inference, AR/VR, real-time vision, and edge analytics. Unlike traditional CPU-GPU systems, modern heterogeneous platforms demand fine-grained coordination among diverse compute engines, shared memory subsystems, and software-managed execution models. Capturing these interactions requires a cycle-level, full-system simulator.

While gem5 has long supported detailed CPU simulation and, more recently, full-system GPU modeling, support for programmable accelerators remained external via tools like gem5-SALAM—built on gem5 v21.1. Although SALAM added accelerator-specific capabilities such as cycle-level datapath modeling, memory-mapped scratchpads, and hardware synthesis integration, it was isolated from the mainline. As a result, it could not leverage recent ISA, memory system, or configuration infrastructure updates, nor benefit from upstream validation.

To close this gap, we integrated SALAM’s accelerator infrastructure into gem5 mainline (develop branch v25). This unification elevates accelerators to first-class components alongside CPUs and GPUs, enabling full-system heterogeneous simulation under a single software stack. The result is a unified framework for modeling heterogeneous SoCs with realistic OS support, shared resource contention, and software-controlled task orchestration.

## Integration at a Glance

We integrated SALAM’s accelerator modeling infrastructure into gem5-develop through a series of architectural, interface, and validation updates.

We began by integrating key accelerator modeling components from SALAM into gem5. These include the `LLVMInterface`, which executes LLVM IR kernels using a cycle-accurate datapath; the `CommInterface`, which provides software-visible control and interrupt signaling; and a suite of configurable memory components such as scratchpads, DMA engines, and stream buffers. Together, these elements enable detailed and flexible modeling of a wide range of accelerator microarchitectures and memory hierarchies. To support realistic SoC integration, accelerators and local memories can be grouped into an `AccCluster`, reflecting the modular structure of accelerator subsystems commonly found in commercial SoCs. For rapid prototyping, we also integrated and automated SALAM’s hardware profile generator, which converts user-defined timing specifications into executable datapath models -- eliminating the need for manual microarchitectural implementation. Finally, we refactored CACTI-SALAM for compatibility with gem5’s infrastructure, enabling timing and energy estimation for scratchpad memories using CACTI’s file-based configuration methodology. These changes bring cycle-level accelerator modeling, full-system memory interaction, and scalable design space exploration into gem5 mainline.

We then updated SALAM’s accelerator infrastructure to match gem5’s latest design conventions. This included refactoring classes to use modern SimObject patterns, replacing unsafe pointer casts in LLVM instruction handling with type-safe 32-bit variables, and switching to gem5’s standardized random number generator for latency modeling. We fixed off-by-one errors in address range definitions to follow gem5’s inclusive-exclusive semantics, aligned environment and ISA configuration with gem5’s current setup, and added dynamic LLVM detection using `llvm-config` to simplify SCons-based compilation for datapath simulation.

Finally, we validated the integrated framework by ensuring it passed gem5’s pre-commit checks and full regression test suite. Additionally, we adapted SALAM’s original system validation tests to run within the unified environment and cross-validated the outputs against the original SALAM baseline to confirm functional equivalence. We plan to upstream these accelerator tests to the gem5-resources repository to support broader validation of the integrated SALAM components within gem5.

## What This Enables

### Broader Heterogeneity Studies

With accelerators now fully integrated into gem5 mainline, researchers can simulate complete heterogeneous systems comprising CPUs, GPUs, and custom accelerators—co-existing under a single OS kernel and sharing interconnects and memory. This allows detailed studies of performance interference, resource arbitration, and synchronization mechanisms across diverse compute engines, grounded in full-system behavior rather than simplified models.

### System-Level Exploration

The framework supports rich exploration of architectural tradeoffs at the system level. Users can evaluate different memory organizations—such as private scratchpads, shared LLCs, or DMA-managed SPMs—and compare strategies for offloading, synchronization, and kernel placement. Static vs. dynamic scheduling, locality-aware memory partitioning, and software-managed DMA schemes can all be studied in realistic OS-driven settings.

### Domain-Specific Workload Support

This infrastructure also enables architectural research targeting emerging domains like real-time vision, mobile inference, AR/VR, and edge computing. These applications demand predictable latency, software-accelerator coordination, and careful memory management. The integrated framework allows researchers to model and study these workloads using real software stacks and bootable Linux images, with accelerator behavior simulated at cycle-level fidelity.

### Exploratory Studies in Non-Traditional Regimes

Finally, the toolchain enables exploration of accelerator operation under emerging regimes such as transient overclocking and advanced cooling. In our workshop paper, we use this framework to study one such case of a non-traditional operating regime: multi-GHz frequency scaling in accelerators, enabled by advanced cooling techniques such as immersion and cryogenic systems. We present a preliminary analysis of performance and power upper bounds across this range. The results show how system bottlenecks shift with increasing frequency, highlighting the importance of evaluating accelerator behavior in the context of host latency and memory interactions. Full details of the experimental setup and findings are included in our ISCA ’25 workshop paper.

Users can apply this framework to the use cases discussed above using built-in accelerator models and benchmarks, or extend it further by modeling their own custom accelerators.

## Modeling Your Own Accelerator

Creating a new accelerator model in the integrated gem5 framework is simple. You begin by writing the desired accelerator algorithm in C/C++ and compiling to LLVM IR.  A YAML-based hardware profile specifies instruction timing, functional unit latencies, and memory ports. This profile is processed by the hardware-profile generator to produce a cycle-level timing model.

The user then places the accelerator inside an `AccCluster`, attaches scratchpads or DMAs as needed, and configures the system topology using gem5’s Python interface. A host-side program running in the simulated OS coordinates with the accelerator via memory-mapped control registers and interrupts. The complete system is simulated using `run_system.sh`, producing statistics, optional power reports, and host-side console output.

## Getting Started

To get started, set the following environment variables to your gem5 and benchmark root directories:

```bash
export M5_PATH=/path/to/gem5
export ACC_BENCH_PATH=/path/to/benchmarks
```

Clone and build gem5:

```bash
git clone https://github.com/akanksha-sc/gem5
cd gem5
scons build/ARM/gem5.opt -j$(nproc)
```

To generate a custom hardware profile (optional):

```bash
$M5_PATH/tools/hw_generator/HWProfileGenerator.py -b <benchmark_name>
```

To run CACTI-SALAM (optional energy/area estimation):

```bash
cd $M5_PATH/tools/cacti-SALAM
./run_cacti_salam.py --bench-list $ACC_BENCH_PATH/benchmarks.list
```

Run a benchmark (custom or built-in like `bfs`):

```bash
$M5_PATH/tools/run_system.sh --bench <benchmark_name> --bench-path <benchmark_path>
```

This boots Linux, launches a user-space driver, and simulates the accelerator. Outputs include `stats.txt` (performance counters), `system.terminal` (host console output), `SALAM_power.csv` (power/area estimates, if CACTI-SALAM is used). Additional examples and documentation included in `src/hwacc/docs`.

## Conclusion

This integration positions gem5 as a unified, full-system simulator for heterogeneous SoCs—combining CPUs, GPUs, and programmable accelerators under one framework with realistic timing, software, and architectural detail. It opens the door to studies ranging from co-scheduling and memory-system tuning to high-frequency accelerator and advanced-cooling analyses. Next steps include merging the support into gem5 mainline, expanding the benchmark suite with domain-specific workloads, and extending full-system accelerator support to additional ISAs. We hope this foundation accelerates heterogeneous-system research across the community.

## Acknowledgments

This work is supported in part by the Semiconductor Research Corporation and by the DOE’s Office of Science, Office of Advanced Scientific Computing Research through EXPRESS: 2023 Exploratory Research for Extreme Scale Science.

## References

* A. Chaudhari and M. D. Sinclair. “Toward Full-System Heterogeneous Simulation: Merging gem5-SALAM with Mainline gem5.” 6th gem5 Users’ Workshop, June 2025.
* S. Rogers, J. Slycord, M. Baharani and H. Tabkhi, "gem5-SALAM: A System Architecture for LLVM-based Accelerator Modeling," 2020 53rd Annual IEEE/ACM International Symposium on Microarchitecture (MICRO), Athens, Greece, 2020, pp. 471-482, doi: 10.1109/MICRO50266.2020.00047.
