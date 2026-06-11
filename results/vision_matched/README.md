# vision_matched — fa05 matched-setup comparators + s6 vision arm (ViT-B/16)

Freeze-A method at the PUBLISHED partitions of the comparator papers (model
class is ours — frozen ViT-B/16 + freeze-A LoRA r8 + head; controlled axes are
dataset / N / Dirichlet alpha). Paper-verbatim numbers to quote beside ours
(from comparators/REPORTED_RESULTS.md):

- DENSE (NeurIPS'22): CIFAR-10 N=5, alpha=0.1 -> 50.26, alpha=0.3 -> 59.76
- Co-Boosting (ICLR'24): CIFAR-10 alpha=0.1 -> 57.09 +- 0.94 (plaintext SOTA-ish)
- FedAUXfdp (IJCAI-W'22): CIFAR-10 N=20, Dir alpha in {0.01,0.04,0.16,10.24},
  (eps,delta)-DP; quote their accuracy at matching alpha + eps
- FedSD2C (NeurIPS'24): Tiny-ImageNet N=10, alpha in {0.1,0.3,0.5}

Stages: s6 (CIFAR-100 N=10 a0.1), dense, fedaux, fedsd2c — `sbatch
jobs/vision_matched.sh` (array index = stage). CSV:
`dataset,match,backbone,N,alpha,seed,K,r,freeze_a,n_trainable,A0,Astar,acc_fisher,acc_counthead,selected,acc_selected,A_central,gap`
