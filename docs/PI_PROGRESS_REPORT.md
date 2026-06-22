# HE-IFD — İlerleme Notu (22.06.2026)

Sayılar `results/` altındaki koşulardan; üyelik çıkarımı (MIA) testleri son skorlama aşamasında, ilgili yerde belirtildi.

## Yöntemdeki durum

- Protokol özünde aynı: her istemci donuk bir omurga üzerinde küçük bir LoRA adaptörü + başlık eğitiyor, şifreli yer değiştirmeyi (Δ) gönderiyor, sunucu çok-taraflı CKKS altında derinlik-1 ağırlıklı toplamı alıyor, eşik ile ortak çözülüyor.
- Merkezi iddia aslında yanlıştı: standart LoRA'da (A ve B birlikte eğitilince) güncelleme çiftdoğrusal, yani çarpanları ayrı ayrı ortalamak güncellemelerin ortalaması değil. "Toplama doğrusaldır / task arithmetic'tir" iddiası tutmuyordu; pratikte tohum (seed) çöküşleri olarak görünüyordu (AG-News bir tohumda ~0.27).
- Çözüm: **A'yı ortak başlangıçta donduruyoruz, sadece B'yi eğitiyoruz** (FFA-LoRA, kaynak gösteriliyor, bize ait değil). Böylece toplam tam olarak doğrusal oluyor, şifreli yük yarıya iniyor, birleştirme kararlı.
- Hem ortalama hem varyans iyileşti: AG-News 0.75±0.09 (eski 0.68±0.15), TREC 0.72±0.05 (eski 0.57±0.13); kazanç çöküş tohumlarında yoğunlaşıyor (0.65 vs 0.48).

## Yeni katkı: şifreli çoklu-aday yayını + istemci oyu ile seçim

- Kör sunucu birleştirme kuralını veriye göre uyarlayamaz; biz bunu çözümden sonra, ek HE maliyeti olmadan geri kazanıyoruz.
- Sunucu tek geçişte birkaç derinlik-1 aday üretiyor: λ-ölçekleme ailesi, Fisher- ve sınıf-sayısı-ağırlıklı birleştirmeler (pay/payda numarasıyla), ve birini-dışarıda-bırak (leave-one-out) toplamları.
- İstemciler adayların hepsini çözüp yerel doğrulama kümesinde oyla en iyisini seçiyor.
- Oy, test-en-iyi adayı 39 hücrenin 34'ünde seçiyor. Sabit tek bir kural her yerde kazanmıyor (count-head 28/39, Fisher 10/39).
- Yüksek heterojenlikte (α=0.1) seçilen model düz ağırlıklı ortalamayı +24 / +21 / +13 / +38 puan geçiyor (AG-News / TREC / DBpedia / Banking77).
- HE-FL'de bu desenin (çoklu-aday eşik çözümü + çözüm sonrası seçim) öncülü yok; temiz bir protokol katkısı. Sızıntı muhasebesi açık.

## Kapsama açığı (en zayıf noktamızdı)

- Banking77'de (77 sınıf, α=0.1) merkezi modele açık 0.52 idi.
- Freeze-A + count-head + oy ile 0.77'ye çıktı, açık 0.11; ek iletişim ve gizlilik bütçesi yok.
- DBpedia K=400'de 0.94 (merkeziye 0.05 yakın).

## Deneyler

- **Görüntü (donuk ViT-B/16):** eskiden negatif sonuçtu (CIFAR-100'de adaptör −0.01 katkı). Yeni yöntemde pozitif: CIFAR-100 0.78 (merkezi 0.87). Modalitelerarası iddia artık kanıtlı.
- **Eşleştirilmiş kurulumlar** (önceki turun "kurulumlar uyuşmuyor" itirazına yanıt): CIFAR-10 N=5 (DENSE) → 0.96 (onlar 0.50/0.60); CIFAR-10 N=20 α=0.04 (FedAUXfdp, DP) → 0.94 (onlar ε=0.5'te 0.75); Tiny-ImageNet N=10 α=0.1 (FedSD2C) → 0.73. Model sınıfı bizimki (donuk ViT + adaptör), belirtiliyor.
- **LLM ölçeği:** donuk Qwen2.5-0.5B ile çalışıyor — DBpedia 0.87–0.88 (düz ortalama 0.44'e çöküyor), AG-News 0.71–0.72. Şifreli nesne hâlâ 26 şifre metni / 13 MiB; sadece adaptör şifreleniyor, 0.5B omurga değil.
- **Kripto maliyeti (Lattigo, uçtan uca):** gerçek freeze-A yükünde (~150k parametre) istemci başına 19 şifre metni / 9.5 MiB (eski yükün yarısı), tek tur; sunucu toplama 76 ms (N=10) – 0.72 s (N=100), eşik çözüm 44 ms – 0.43 s, bootstrapping yok; çözülen sonuç düz hesaba göre göreli ℓ₂ ≈ 10⁻⁹. Çoklu-aday k çözüm ekliyor (12 aday ~0.5 s).
- **Üyelik çıkarımı (MIA):** artık ölçülüyor, varsayılmıyor — dış saldırgan ve ortak-istemci saldırganı (kendi verisini önsel kullanan katılımcı). İlk skorlanan hücre (AG-News) tesadüf düzeyinde: AUC 0.49–0.51, %1 FPR'de TPR ≈ %1. Kalan 11 hücre kümede skorlama aşamasında; tam tablo yakında eklenecek.

## Konumlandırma

- "İlk tek-atış federe ince-ayar" iddiası alınmış (arXiv:2412.04650), freeze-A da FFA-LoRA'nın.
- Açık ve savunulabilir iddia: **çok-taraflı HE altında ilk tek-atış federe öğrenme protokolü** — tüm HE-FL çok turlu, tüm tek-atış FL ya düz metin ya DP.
- Eş-tasarım (freeze-A → tam, derinlik-1 şifreli birleştirme) ve çoklu-aday yayını boşta. Taslaklar `docs/paper/drafts/` altında.

## Hedef dergi/konferanslar

- **IEEE TNSE** — şu anki hedef, süreçte.
- **IEEE TIFS** — muhtemelen en iyi uyum (HE + ölçülmüş MIA + tehdit modeli).
- **PoPETs/PETS** — gizlilik + MIA çerçevesine uygun, hızlı.
- **IEEE TDSC** — doğal ev ama v1'in reddedildiği yer (ortak hakem havuzu riski; yöntem artık epey farklı).
- **USENIX Security / CCS / NDSS / IEEE S&P** — protokolü üst konferansa taşımak istersek; NDSS/USENIX takvimi uygun.
- **NeurIPS / ICML / TMLR** — ikincil; HE maliyet argümanı orada daha az değerli.

Önerim: TNSE'yi sürdürelim; yeniden konumlandırırsak TIFS veya PoPETs en uygun, daha yükseğe nişan alırsak NDSS/USENIX.
