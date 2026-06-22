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

## Deneyler

- **Vision (frozen ViT-B/16):** eskiden negative result'tı (CIFAR-100'de adapter −0.01 katkı). Yeni method'da positive: CIFAR-100 0.78 (centralized 0.87). Cross-modality claim artık kanıtlı.
- **Matched setup'lar** (önceki round'un "setup'lar uyuşmuyor" itirazına yanıt): CIFAR-10 N=5 (DENSE) → 0.96 (onlar 0.50/0.60); CIFAR-10 N=20 α=0.04 (FedAUXfdp, DP) → 0.94 (onlar ε=0.5'te 0.75); Tiny-ImageNet N=10 α=0.1 (FedSD2C) → 0.73. Model class bizimki (frozen ViT + adapter), belirtiliyor.
- **LLM scale:** frozen Qwen2.5-0.5B ile çalışıyor — DBpedia 0.87–0.88 (plain average 0.44'e collapse oluyor), AG-News 0.71–0.72. Encrypted object hâlâ 26 ciphertext / 13 MiB; sadece adapter encrypt ediliyor, 0.5B backbone değil.
- **Crypto cost (Lattigo, end-to-end):** gerçek freeze-A payload'unda (~150k parametre) client başına 19 ciphertext / 9.5 MiB (eski payload'un yarısı), tek round; server aggregation 76 ms (N=10) – 0.72 s (N=100), threshold decrypt 44 ms – 0.43 s, bootstrapping yok; decrypt sonucu plaintext'e göre relative ℓ₂ ≈ 10⁻⁹. Multi-candidate k decryption ekliyor (12 candidate ~0.5 s).
- **MIA:** artık ölçülüyor, assert edilmiyor — external adversary ve fellow-client adversary (kendi datasını prior kullanan participant). İlk scorlanan cell (AG-News) chance seviyesinde: AUC 0.49–0.51, %1 FPR'de TPR ≈ %1. Kalan 11 cell cluster'da scoring aşamasında; full tablo yakında eklenecek.

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
