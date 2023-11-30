# purchse phase
* environment could have separate action representing purchase of Ni of each unit i with cost Ci
* would then reject the action if sum(Ci) > current IPC
* more advanced need to check contraint in ability to deploy i.e. 10 slots to deploy Ntot < 10
* can this be reformulated to embed the constraint in the actons?
    * simple case:  only 2 units i = 1,2
        * C1 = 3, C2 = 4
        * 3*N1 + 4*N2 <= IPC
        * Could have 2 new parameters:
            * fraction of total IPC to spend
            * log of ratio of N1, N2
    * how to generalize this to more than 2 parameters?
        * log(N2/N1), log(N3/N1), 
