# HPU: A Heterogenous Processing Unit for Extracting Fine-grained Task Level Parallelism


Computer architects are increasingly turning towards application specific hardware to offload applications from the CPU to gain performance and power efficiency. However, contemporary hardware accelerators are designed at a coarse granularity, which hampers their re-usability across applications, and hence their programmability. Additionally, offloading a task and servicing the task completion interrupts from these accelerators is costly. In this project, we explore the design of a Heterogeneous Processing Unit (HPU) to exploit fine-grained task level parallelism by tightly integrating the fine-grained hardware accelerators into a traditional CPU pipeline.

## Getting Started

This repository contains a cycle-level simulator written in python. The authors have built it from scratch with their fork of `pycachesim` as the only dependency.

### Prerequisites

* Python 2/3
* [abhiutd/pycachesim](https://github.com/abhiutd/pycachesim)


## Running Simulator
```
# create a new directory
mkdir workspace
cd workspace

# build pycachesim simulator
git clone https://github.com/abhiutd/pycachesim.git
cd pycachesim
python setup.py build
python setup.py install

# run simulation
cd ..
git clone https://github.com/abhiutd/HPU.git
source sourceme.sh
python testbench/simulate.py

# view simulation log
vim system.log
```

## Paper

* [HPU presentation](shorturl.at/dovQT)
* [HPU paper](shorturl.at/ehuvM)

## Authors

* **Kartik Hegde**
* **Abhishek Srivastava**
* **Vikram Sharma Mailthody**


## Acknowledgments

* **Prof. Sarita Adve**
* **Rohit Agrawal**
* **Zaid Qureshi**
