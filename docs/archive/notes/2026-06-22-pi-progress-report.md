# HE-IFD — İlerleme Notu (22.06.2026)

Sayılar `results/` altındaki run'lardan; MIA (membership inference) testleri son scoring aşamasında, ilgili yerde belirtildi.

## Method'taki durum

- Protocol özünde aynı: her client, frozen bir backbone üzerinde küçük bir LoRA adapter + head eğitiyor, encrypted displacement Δ'yı gönderiyor, server multiparty CKKS altında depth-1 weighted sum alıyor, threshold decryption ile ortak çözülüyor.
- Merkezi claim aslında yanlıştı: standart LoRA'da (A ve B birlikte eğitilince) update BⱼAⱼ bilinear, yani factor'leri ayrı ayrı ortalamak update'lerin ortalaması değil. "Aggregation linear / task arithmetic" claim'i tutmuyordu; pratikte seed collapse olarak görünüyordu (AG-News bir seed'de ~0.27).
- Çözüm: **A'yı shared init'te freeze ediyoruz, sadece B'yi eğitiyoruz** (FFA-LoRA, cite ediliyor, bize ait değil). Böylece aggregation tam olarak linear oluyor, encrypted payload yarıya iniyor, merge stabil.
- Hem mean hem variance iyileşti: AG-News 0.75±0.09 (eski 0.68±0.15), TREC 0.72±0.05 (eski 0.57±0.13); kazanç collapse seed'lerde yoğunlaşıyor (0.65 vs 0.48).

## Yeni katkı: encrypted multi-candidate release + client-vote selection

- Blind server, aggregation rule'unu veriye göre adapt edemez; biz bunu decryption sonrası, ek HE maliyeti olmadan geri kazanıyoruz.
- Server tek pass'te birkaç depth-1 candidate üretiyor: λ-scaling family, Fisher- ve class-count-weighted merge'ler (numerator/denominator trick ile), ve leave-one-out aggregate'ler.
- Client'lar candidate'ların hepsini decrypt edip local holdout üzerinde vote ile en iyisini seçiyor.
- Vote, test-best candidate'ı 39 cell'in 34'ünde seçiyor. Sabit tek bir rule her yerde kazanmıyor (count-head 28/39, Fisher 10/39).
- Yüksek heterogeneity'de (α=0.1) selected model, plain weighted average'ı +24 / +21 / +13 / +38 puan geçiyor (AG-News / TREC / DBpedia / Banking77).
- HE-FL'de bu pattern'in (multi-candidate threshold decryption + post-decryption selection) precedent'i yok; temiz bir protocol katkısı. Leakage accounting açık.

## Coverage gap (en zayıf noktamızdı)

- Banking77'de (77 class, α=0.1) centralized'a gap 0.52 idi.
- Freeze-A + count-head + vote ile 0.77'ye çıktı, gap 0.11; ek communication ve privacy budget yok.
- DBpedia K=400'de 0.94 (centralized'a 0.05 yakın).

## Deney tabloları

Ortak default: RoBERTa-base (frozen), N=10, α=0.1, K=200, r=8, 3 seed {42,43,44}, freeze-A. Her tablo bu default'tan bir ekseni değiştirir.

**S1 — freeze-A vs both-A-B**
| | |
|---|---|
| Dataset / backbone | AG-News (4), TREC (6) / RoBERTa-base |
| Setup | N=10, α=0.1, K=200, r=8, 3 seed |
| Değişen | freeze_a ∈ {True, False} |
| Hedef | freeze-A, seed collapse'leri ve "linear aggregation" claim'ini düzeltiyor mu |
| Sonuç | AG-News 0.75±0.09 vs 0.68±0.15; TREC 0.72±0.05 vs 0.57±0.13; variance 2–3× düşük, payload yarıya iniyor |

**S2 — semantic head init**
| | |
|---|---|
| Dataset / backbone | AG-News, TREC, DBpedia (14), Banking77 (77) / RoBERTa-base |
| Setup | N=10, α=0.1, K=200, r=8, 3 seed; sem_init ∈ {on, off} |
| Değişen | head θ₀ = class-name embedding (zero-shot) vs standart init |
| Hedef | semantic init, coverage gap'i kapatıyor mu |
| Sonuç | Kapatmıyor; Banking77 0.72 (sem) vs 0.77 (no-sem). Method'tan çıkarıldı, ablation kaldı |

**S4 — trajectory length (K) × learning rate**
| | |
|---|---|
| Dataset / backbone | DBpedia / RoBERTa-base |
| Setup | N=10, α=0.1, r=8, seed 42 |
| Değişen | K ∈ {100, 200, 400}, lr ∈ {5e-4, 1e-3} |
| Hedef | freeze-A için en iyi trajectory/lr |
| Sonuç | Monoton: K=100→0.90, K=200→0.93, K=400→0.94; lr 1e-3 ≥ 5e-4 |

**S5 — rank compensation**
| | |
|---|---|
| Dataset / backbone | Banking77 / RoBERTa-base |
| Setup | N=10, α=0.1, K=200, sem_init on, 3 seed |
| Değişen | r ∈ {8, 16, 32} |
| Hedef | A'yı freeze edince kaybolan capacity'yi yüksek rank telafi ediyor mu |
| Sonuç | Etmiyor; r=8 0.724 ≥ r=16 0.711 ≥ r=32 0.693. r=8 sabit |

**S7 / fa04 — Byzantine-lite robustness (leave-one-out + vote)**
| | |
|---|---|
| Dataset / backbone | DBpedia, AG-News / RoBERTa-base |
| Setup | N=10, α=0.1, K=200, r=8, 3 seed; 1 poison client (largest shard) |
| Değişen | attack ∈ {sign_flip, gauss, label_flip} |
| Hedef | LOO candidate + vote, zehirli client'ı dışlıyor mu |
| Sonuç | 18 cell'in 17'sinde attacker dışlandı, oracle accuracy'ye dönüldü; savunmasız plain aggregate 0.07–0.70'e düşüyor |

**fa05 / s6 — vision + matched setup'lar (frozen ViT-B/16 + adapter)**
| | |
|---|---|
| Setup | N ve α ilgili comparator'ın published partition'ı; 3 seed |
| Hedef | (1) vision modality kanıtlı mı (eski both-A-B'de negative'di), (2) matched setup'ta comparator'lara karşı |
| Sonuç | CIFAR-100 (s6, N=10 α=0.1) 0.78 vs centralized 0.87 (eskiden −0.01, artık positive). CIFAR-10 N=5 (DENSE) 0.96 vs 0.50/0.60. CIFAR-10 N=20 α=0.04 (FedAUXfdp DP) 0.94 vs 0.75 (ε=0.5). Tiny-ImageNet N=10 α=0.1 (FedSD2C) 0.73 |

**fa03 — LLM scale**
| | |
|---|---|
| Dataset / backbone | AG-News, DBpedia / frozen Qwen2.5-0.5B (causal LM) |
| Setup | N=10, α=0.1, K=200, r=8, 2 seed |
| Hedef | protocol billion-param-class backbone'da çalışıyor mu, cost adapter'a mı bağlı |
| Sonuç | DBpedia 0.87–0.88 (plain 0.44'e collapse), AG-News 0.71–0.72; encrypted object 26 ciphertext / 13 MiB (0.5B backbone değil, sadece adapter) |

**fa06 — crypto cost (Lattigo, multiparty CKKS, end-to-end)**
| | |
|---|---|
| Setup | gerçek freeze-A payload ~150k param; ring 2¹⁴, scale 2⁴⁵, depth-1; N ∈ {10, 100} |
| Hedef | gerçek payload'da communication + computation cost + correctness |
| Sonuç | 19 ciphertext / 9.5 MiB per client (eski yükün yarısı), tek round; aggregation 76 ms (N=10)–0.72 s (N=100), threshold decrypt 44 ms–0.43 s, bootstrapping yok; relative ℓ₂ ≈ 10⁻⁹. Multi-candidate k decryption ekliyor (~0.5 s / 12 candidate) |

**fa02 — membership inference (MIA)**
| | |
|---|---|
| Dataset / backbone | AG-News, TREC, DBpedia, Banking77 / RoBERTa-base |
| Setup | released model (count-head aggregate); 1 target + 16 shadow / cell, 3 seed |
| Değişen | adversary ∈ {external, fellow-client}; attack ∈ {loss-threshold, LiRA} |
| Hedef | released model gerçekten az mı sızdırıyor (assert değil, ölçüm) |
| Sonuç | İlk scorlanan cell (AG-News) chance: AUC 0.49–0.51, %1 FPR'de TPR ≈ %1 (her iki adversary). **Kalan 11 cell scoring aşamasında; full tablo yakında** |

## Positioning

- "First one-shot federated fine-tuning" claim'i alınmış (arXiv:2412.04650), freeze-A da FFA-LoRA'nın.
- Açık ve savunulabilir claim: **multiparty HE altında ilk one-shot federated learning protocol'ü** — tüm HE-FL multi-round, tüm one-shot FL ya plaintext ya DP.
- Co-design (freeze-A → exact, depth-1 encrypted merge) ve multi-candidate release boşta. Draft'lar `docs/paper/drafts/` altında.

## Hedef venue'lar

- **IEEE TNSE** — şu anki hedef, süreçte.
- **IEEE TIFS** — muhtemelen en iyi fit (HE + ölçülmüş MIA + threat model).
- **PoPETs/PETS** — privacy + MIA framing'ine uygun, hızlı.
- **IEEE TDSC** — doğal ev ama v1'in reject edildiği yer (ortak reviewer pool riski; method artık epey farklı).
- **USENIX Security / CCS / NDSS / IEEE S&P** — protocol'ü üst conference'a taşımak istersek; NDSS/USENIX takvimi uygun.
- **NeurIPS / ICML / TMLR** — ikincil; HE cost argümanı orada daha az değerli.

Önerim: TNSE'yi sürdürelim; reposition edersek TIFS veya PoPETs en uygun, daha yükseğe nişan alırsak NDSS/USENIX.
