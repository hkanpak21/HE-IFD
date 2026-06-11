# llm_scale — fa03 LLM-scale feasibility (causal LM backbone)

One-shot freeze-A LoRA federation on a frozen causal LM (Qwen2.5-0.5B default;
TinyLlama-1.1B optional). Left-pad + last-token pooling (causal attention),
fp32 LoRA(+head) with gradient checkpointing. Same partition / trajectories /
depth-1 candidates / client-vote as the headline method (imports the
finetune_improve core). 4 cells: {ag_news, dbpedia_14} × seeds {42,43}.

Feasibility question: does the one-shot merge hold at causal-LM scale
(positive increment, no collapse)? Also reports n_trainable + the implied
CKKS ciphertext count (feeds the fa06 cost table) and per-client wall-clock
(the latency claim's dominant term).

CSV: `task,backbone,N,alpha,seed,K,r,freeze_a,n_trainable,ciphertexts,A0,Astar,acc_counthead,selected,acc_selected,A_central,increment,gap,wall`
