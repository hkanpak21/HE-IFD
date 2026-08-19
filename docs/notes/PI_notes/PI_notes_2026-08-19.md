akupcu
11 August, 3:21 pm
could we put more about results? performance during fine tuning? against normal FL?

costs $0.04$ to $0.14$ accuracy against a disclosed model, and $5$\,MiB of traffic per query.


---

akupcu
11 August, 7:12 pm
şekil 1 ve açıklaması aslında "overview" gibi bir alt başlık ile intro'ya gelebilir
akupcu
11 August, 7:14 pm
tüm problemleri tek tek listeledikten sonra bizim çözümümüz budur diye geçilebilir. şu aşamada bir problem bir çözüm sonra bir başka problem bir başka çözüm gibi anlatıldığı için açıkçası biraz karışık duruyor. Hatta problemler bile her biri ayrı paragrafta "Problem 1" "Problem 2" gibi bold başlıklarla yazılabilir.

{Introduction}

---

akupcu
11 August, 3:29 pm
cite

and each would obtain a better
model from the combination than from its own data alone


---

akupcu
11 August, 3:30 pm
cite

its privacy risk is concentrated at training time

---

akupcu
11 August, 3:32 pm
çok iddialı bir cümle. ya kanıt ile desteklemeliyiz, ya da bu kadar iddialı yazmamalıyız

membership inference far stronger than anything possible against the
final model

---
akupcu
11 August, 7:06 pm
anlaşılmıyor (he means this is not clear)

so a coalition of all but one client has nothing to subtract
  from (\cref{sec:split})

---
akupcu
11 August, 7:06 pm
anlaşılmıyor ve daha önce açıklamadık

Only a label leaves the protocol, and a
  label denies the linear solve that logits would permit (\cref{sec:serving}).


---
akupcu
11 August, 7:07 pm
açıklamadık daha önce net bir şekilde

Two arrangements

---

akupcu
11 August, 7:09 pm
arada biraz tekrara düşmüş. Bu da bir katkı değil mi bu arada? Niye contributions altında yazmadık bu bölümü? Aslında arka planı ve "solution overview" kısmını intro'da daha net verip contributions kısmını daha net yazarsak iyi olur. biraz dağınık şu anki haliyle

Our accounting includes the traffic
that recurs on every query.

---
akupcu
11 August, 7:10 pm
bu bölüm aşırı uzun. özellikle related work kısmını kısaltmalıyız ve bir özet tablo sunmalıyız

{Background and Related Work}

--- 

A note from me to add an overview in the beginngin of methodology.

---

akupcu
12 August, 10:33 am
bu eğer yöntemi etkileyen bir şey değilse yeri burası değil, deney bölümünün başı

In our experiments, the data are
heterogeneous: each client's class proportions are drawn from a Dirichlet
distribution of concentration $\alpha$, so a smaller $\alpha$ leaves each client a
few dominant classes and almost none of the rest.


---
akupcu
12 August, 10:39 am
C3 ve C4 ardarda çelişiyor gibi durmuş. netleştirelim
Sinem Sav
17 August, 11:16 am
bence C4 iyi ama C3 biraz daha clear yazilirsa daha net olacak gibi celiskili durmamasi icin 

\item[\textbf{C4}] 

---

akupcu
12 August, 10:40 am
?? plaintext mi demek istiyoruz?

ing the client runs is public, and the tr

---

akupcu
12 August, 10:47 am
figure should be explained

. \Cref{fig:training} shows
the arrangement.

---

akupcu
12 August, 10:49 am
? do we also evaluate generation or not?

We evaluate classification only, and \cref{sec:scope} records what a
generation setting would additionally require, including the restriction to
greedy decoding that \cref{sec:serving} imposes.

---

akupcu
12 August, 10:50 am
the claim and its halves are not clear

both halves of this claim.

---

Sinem Sav
17 August, 11:19 am
what do we mean ?

fixes

---
Sinem Sav
17 August, 11:20 am
this is more like a preliminary no ? why do we want to give this here? 

\subsection{The Threshold Assumption}
\label{sec:threshold}

---
Sinem Sav
17 August, 11:20 am
informal, rephrase

\Cref{func:ideal} describes what a trusted party would do, so that the protocol
can be measured against it. 

---

Sinem Sav
17 August, 11:21 am
is this info requires for Section C ? 

he functionality signals the end of each phase with an explicit
message, because the parties need to know when to 

---

Sinem Sav
17 August, 11:22 am
then this is not the output. it is a requirement.  I'm not familiar with writing the ideal functionality like this so double check with Alptekin hoca? 

No party receives $\thstar$

---

Sinem Sav
17 August, 11:23 am
until here, please shorten and make the changes discussed in the meeting. these "Why blabla makes blabla" titles should be rephrased 

\subsection{Why the Serving Party Is Assumed Honest}
\label{sec:malicious-ext}

---

Sinem Sav
17 August, 11:24 am
???

 Read that way the peer group separates into three cases.