# Response to Reviewers

Dear Editors and Reviewers,

We thank you for the detailed and constructive reviews. The manuscript has been substantially revised. The
principal revision concerns the method, and because it bears on several of the comments, we summarize it
before responding to each comment in turn.

## Change in method

In the previous version, the encryption-friendly model was trained under homomorphic encryption. That design
required polynomial activations in place of ReLU, removed batch normalization, and transmitted large
encrypted objects across many internal steps; it was the source of the accuracy loss, the large per-round
upload, and the degradation at higher client counts noted in the reviews.

In the revised method, no training is performed under encryption. Each client fine-tunes a small adapter on a
frozen, public, pretrained backbone, starting from a shared public initialization, and uploads only the
resulting parameter displacement. The server combines these displacements with a single linear operation
under multiparty CKKS, after which a threshold of clients decrypts the result. No polynomial activations are
used; the encrypted object is the adapter (tens of megabytes rather than hundreds of gigabytes); and the
single encrypted operation is exact, so encryption introduces no accuracy cost. This revision addresses
comments R1-W1, R1-W2, R1-W3, R2-Q3, and R2-Q6, as detailed below.

## Reviewer 1

- **W1 (degradation at higher client counts).** This arose from training from scratch under fragmented data.
  With a frozen pretrained backbone the model no longer degrades: accuracy is stable from 10 to 100 clients.
  The residual gap is a function of label heterogeneity rather than client count, and the revision
  characterizes it explicitly: it is negligible when client data are close to uniform and grows only under
  severe skew.

- **W2 (operator replacement and its unquantified cost).** Operator replacement no longer occurs. The
  backbone is evaluated in plaintext on each client, and only a linear sum is encrypted; this encrypted sum
  reproduces the plaintext result to a relative error of about 1e-9. The cost of the cryptographic protocol is
  therefore isolated and shown to be zero.

- **W3 (upload size and bandwidth).** The per-client upload is now approximately 19 MiB, calculated for a
  rank-8 adapter, in a single round. A dedicated communication analysis, with a figure and a comparison
  table, has been added.

- **W4 (empirical privacy; leakage from the released model).** A formal guarantee is now provided for the
  client contributions: a simulator argument (Proposition 1) establishes that the server's view is
  computationally independent of the private data under standard CKKS assumptions. The only quantity revealed
  in plaintext is the final shared model, which any such protocol must reveal; its residual leakage is
  measured with membership inference.

- **W5 (no NLP; missing ablations).** The evaluation now centers on language tasks (AG-News, TREC, DBpedia,
  Banking77) and includes a vision task (CIFAR-100). Ablations cover the trainable unit (linear head versus
  adapter), label heterogeneity, client count, and trajectory length.

## Reviewer 2

- **Q1 (comparison with prior work).** A comparison table has been added, positioning the method against
  representative one-shot distillation, differentially private one-shot, and encrypted federated-learning
  methods along the axes of one-shot operation, privacy type, number of rounds, reported accuracy, and
  principal limitation.

- **Q2 (end-to-end CKKS measurements).** The full protocol is implemented end to end in multiparty CKKS using
  the Lattigo library (key generation, encryption, aggregation, and threshold decryption), and per-operation
  timings and communication are reported. As the only encrypted operation is a linear sum, the circuit
  requires no rotations, no relinearization, and no bootstrapping; server memory is approximately 38 MiB and
  is independent of the number of clients; and, as there is no encrypted training loop, no convergence
  behavior under encryption arises. Correctness is verified to a relative error of about 1e-9.

- **Q3 (client-side encryption cost).** Client-side encryption is approximately 84 ms per client for the
  adapter, and the upload is 19 MiB; both are derived from measured per-operation rates and reported in the
  cost section.

- **Q4 (malicious or colluding clients).** A future-work paragraph has been added. It states the threat under
  an honest-but-curious assumption and identifies two defenses compatible with encryption: robust aggregation
  evaluated homomorphically (a coordinate-wise median or trimmed mean), and an upload-time norm bound enforced
  by a zero-knowledge proof.

- **Q5 (post-release privacy across N and alpha).** Membership inference against the released model, the only
  plaintext channel, is reported; leakage remains near chance on the language task.

- **Q6 (plaintext weights, CT×PT, no encrypted optimizer states).** This corresponds to the present design.
  The weights and the initialization are public plaintext scalars, only the displacements are encrypted, the
  server performs plaintext-by-ciphertext multiplication and ciphertext addition exclusively, maintains no
  encrypted optimizer state, and operates at multiplicative depth one.

## Reviewer 3

- **1 (participation incentive).** The incentive is now stated explicitly: each client obtains a model that
  classifies the entire label space, including classes absent from its own data, which no client could obtain
  independently.

- **2 (challenges and contributions).** The exposition has been restructured around a single difficulty (a
  linear average of independently trained models fails under heterogeneity), a single solution (a frozen
  pretrained backbone supplies the shared frame and removes the alignment phase), and contributions that map
  directly onto them.

- **3 (motivation placement).** The motivation for one-shot communication and for encryption now appears in
  the introduction.

- **4 (overview figure).** The protocol figure has been redrawn to show the frozen backbone, the shared
  initialization, the encrypted displacements, the depth-one server aggregation, and threshold decryption.

- **5 (limited comparison; method not explained).** The comparison now includes FedDF-, FedMD-, and
  FedAvg-class methods and encrypted baselines, and the experimental section explains the method's operation
  rather than only reporting outcomes.

- **6 (future directions).** Future directions are now presented in a scope-and-limitations discussion,
  separate from the cost analysis.

## Presentation and readability

The manuscript has been rewritten for clarity, with plain language, consistent notation, a single notation
table, and a uniform structure that states the problem, the idea that addresses it, and the supporting
evidence in that order. Unsupported qualitative claims have been removed, and each remaining claim is tied to
a measurement or a formal argument.

We hope these revisions address the concerns raised, and we thank the reviewers for feedback that has
materially improved the paper.
