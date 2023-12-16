# history

## highly simple version
tag:  v0.02

opponent defense fixed at 2 infantry

model has 5 variables, fraction of IPC to spend and log2(ratio) of units to purchase wrt infantry

reward is fraction of IPC for winner

model did better than untrained and learned:
* to spend more IPC (not as well as ultra simple though)
* slightly more artillery than untrained
* slightly fewer fighters, bombers than untrained


## ultra simple version
tag:  v0.01

opponent defense fixed at 2 infantry

model has one variable, fraction of IPC to spend
* action is -0.5 to +0.5 corresponding to fraction of 0 to 1

reward is fraction of IPC for winner

model did better than untrained

model learned - mostly - to spend more IPC:
* 60% of time it spent all IPC
* 90% of the time it spent at least some IPC
* untrained model:  
    * 30% of time it spent all IPC
    * 40% of time it spent no IPC