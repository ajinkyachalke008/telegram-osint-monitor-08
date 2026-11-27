# PS02 Search-Term Catalogue — Fraud and Consumer-Risk Language

**Purpose:** a transparent starter vocabulary for the local PS02 demo's *search suggestions* and explainable keyword matching. This is not a criminality classifier, an allegation list, or a substitute for investigator review.

## Use rules

1. Treat every hit as a **text match only**. Never label a person, account, channel, post or author as criminal, fraudulent or guilty from a keyword.
2. Do not assign severity scores or automatic risk levels from this catalogue. In the UI, show the matched phrase and its category, not a guilt/risk score.
3. Generic terms such as `fake`, `scam`, `OTP`, `account`, `loan`, `job`, `refund` and `QR` are low-context. They may occur in warnings, news, prevention advice, victim reports or ordinary discussion. Do not treat a single generic word as a strong signal.
4. Keep **exact phrase search** separate from **expanded alias search**. Show which exact phrase/alias matched. Never silently expand a query into every category.
5. Normalize case and Unicode, collapse whitespace, and use phrase/word-boundary matching. Do not introduce leetspeak dictionaries, hidden slang substitutions, coded trading language, or automatic fuzzy matching in this hackathon build.
6. Search stays local and ephemeral. Do not persist raw participant text, author/sender fields, contact/payment identifiers or row-level results. Follow the privacy limits in `PS02_KEYWORD_SEARCH_POLISH_HANDOFF.md`.
7. Keep the existing 37-row committee lexicon as a separate source artefact. Do not overwrite or mutate the supplied CSV.
8. Do not expand the weapons/drugs slang list or add instructions, supply-chain cues, pricing, quantities, delivery methods, concealment or evasion phrases. This catalogue intentionally focuses on consumer-facing fraud and digital-safety typologies.
9. Translations below are starter spellings, not validated regional slang. Keep them editable and label the language/variant. Do not claim exhaustive Hindi, Hinglish, Marathi or Rajasthani coverage.

## A. General fraud, deception and forgery

**Context phrases**
- fraud
- cyber fraud
- online fraud
- financial fraud
- payment fraud
- scam
- online scam
- cheating
- deception
- forgery
- forged document
- fake document
- counterfeit
- duplicate document
- impersonation
- identity theft
- account takeover
- unauthorised transaction
- unauthorized transaction
- suspicious transaction
- fraudulent message
- fake notification
- fake advertisement

**Hindi / Hinglish search variants**
- dhokha
- thagi
- jaalsaazi
- nakli
- farzi
- jaali
- jhootha message
- nakli document
- farzi kagaz
- jaali dastavez
- pehchaan ki chori

## B. Phishing, spoofing and impersonation

**Higher-context phrases**
- phishing
- smishing
- vishing
- reverse phishing
- spoofed email
- fake bank message
- fake bank call
- fake customer care
- fake customer support
- customer care impersonation
- bank impersonation
- government official impersonation
- police impersonation
- social media impersonation
- fake support number
- fake helpline
- fake website
- fake login page
- suspicious login link
- unknown payment link
- digital arrest scam
- business email compromise
- email account takeover

**Hindi / Hinglish search variants**
- bank ke naam par call
- bank adhikari bankar
- customer care bankar
- police bankar dhamki
- sarkari adhikari bankar
- nakli customer care
- fake helpline number

## C. OTP, PIN, password and KYC-related scam language

**Higher-context phrases**
- OTP fraud
- OTP scam
- OTP sharing request
- request to share OTP
- PIN disclosure scam
- CVV collection scam
- password collection scam
- credential theft
- KYC update scam
- fake KYC update
- KYC reactivation scam
- KYC verification link
- account blocking threat
- account unblocking scam
- SIM blocking threat
- fake bank verification
- unauthorised app installation
- remote access scam
- screen sharing scam
- remote device access
- fake video KYC

**Hindi / Hinglish search variants**
- OTP maangna
- OTP share karo
- PIN batao
- KYC update karo
- KYC ke liye link
- account band ho jayega
- SIM band ho jayegi
- account unblock karne ke naam par
- bank verification ke naam par

Do not search for or display actual OTPs, PINs, passwords, CVVs or credential values. Match only the descriptive phrases above.

## D. UPI, QR, card and digital-payment fraud

**Higher-context phrases**
- UPI fraud
- UPI scam
- UPI collect request scam
- fake collect request
- QR code scam
- fake QR code
- payment request scam
- fake payment screenshot
- fake payment confirmation
- false payment receipt
- fake refund
- refund scam
- payment reversal scam
- e-wallet fraud
- digital wallet scam
- card skimming
- card cloning
- debit card fraud
- credit card fraud
- SIM swap fraud
- SIM cloning fraud
- unauthorised debit
- unauthorized transfer
- unauthorised beneficiary
- unauthorized beneficiary

**Hindi / Hinglish search variants**
- paise receive karne ke liye UPI PIN
- paise lene ke liye PIN dalo
- refund ke liye QR scan
- fake payment screenshot
- jhootha payment proof
- UPI collect request
- galat payment confirmation

RBI warns that fake UPI collect requests, misleading QR/payment prompts, phishing/vishing and requests for confidential credentials are recognised fraud patterns. These phrases are search vocabulary, not a determination that any one message is fraudulent.

## E. Identity-document and certificate fraud

**Higher-context phrases**
- fake Aadhaar
- fake Aadhar
- forged Aadhaar
- duplicate Aadhaar
- fake PAN
- forged PAN
- duplicate PAN
- fake voter ID
- forged voter ID
- fake driving licence
- fake driving license
- fake passport
- fake government ID
- counterfeit identity card
- fake certificate
- forged certificate
- fake marksheet
- forged marksheet
- fake degree
- forged degree
- fake invoice
- forged invoice
- fake receipt
- fake bank statement
- forged bank statement
- fabricated document

**Hindi / Hinglish search variants**
- nakli Aadhaar
- farzi Aadhaar
- jaali Aadhaar card
- nakli PAN card
- farzi PAN
- duplicate pahchan patra
- nakli certificate
- farzi marksheet
- jaali dastavez

A mention of Aadhaar, PAN or a certificate alone is not a fraud indicator. Prefer a complete phrase that expresses falsification, forgery or duplication.

## F. Loan, job, task and advance-fee scams

**Higher-context phrases**
- online job fraud
- fake job offer
- recruitment scam
- work from home scam
- task scam
- captcha job scam
- fake data entry job
- job registration fee scam
- upfront job fee
- security deposit job scam
- advance fee fraud
- advance payment scam
- loan app fraud
- fake loan app
- instant loan scam
- fake loan website
- loan processing fee scam
- loan approval fee
- upfront loan fee
- loan document forgery
- recovery agent impersonation

**Hindi / Hinglish search variants**
- naukri ke naam par thagi
- ghar baithe job scam
- job registration fee
- pehle payment karo
- security deposit ke naam par
- loan processing fee scam
- loan dilane ke naam par paise

## G. Investment, lottery and money-circulation scams

**Higher-context phrases**
- investment scam
- fake investment platform
- fake trading app
- guaranteed return scam
- guaranteed profit claim
- Ponzi scheme
- pyramid scheme
- money circulation scheme
- multi-level marketing fraud
- fake stock tip
- crypto investment scam
- fake crypto platform
- lottery fraud
- prize money scam
- fake winner message
- advance fee prize scam
- recovery scam
- refund recovery scam

**Hindi / Hinglish search variants**
- double paisa scheme
- guaranteed munafa
- pakka return
- lottery lagi hai
- inaam jeetne ka message
- prize release fee
- investment ke naam par thagi

Do not infer fraud from terms such as `investment`, `crypto`, `profit`, `loan` or `lottery` by themselves.

## H. Marketplace, delivery and consumer-purchase scams

**Higher-context phrases**
- fake seller
- counterfeit product
- fake product listing
- duplicate branded product
- payment taken no delivery
- non-delivery scam
- fake order confirmation
- fake delivery message
- courier scam
- parcel scam
- customs fee scam
- fake tracking link
- fake refund request
- marketplace impersonation
- fake buyer payment proof
- fraudulent advertisement

**Hindi / Hinglish search variants**
- nakli samaan
- fake product
- paise lekar delivery nahi
- jhootha order confirmation
- parcel ke naam par fraud
- courier ke naam par thagi

## I. Extortion, blackmail and malicious-software reports

**Higher-context phrases**
- extortion
- online blackmail
- sextortion
- ransom demand
- ransomware
- malware attack
- malicious app
- fake mobile app
- spyware
- account hacked
- account compromise
- social media account takeover
- data leak threat
- threat to publish private material

Treat these as highly sensitive categories. The demo should show only aggregate category counts or a redacted text match, never intimate imagery or personal victim details.

## Suggested search UX behaviour

- Default suggestions should favour the higher-context multi-word phrases above.
- A user may still manually search a single word, but the UI should label it **broad search** and explain that it may produce false positives.
- Show the matched phrase, category, platform/chat source and IST timestamp only where the source data supports them.
- Add a simple explanation: **“Search match ≠ verified fraud. Context and independent review are required.”**
- Exact phrase and expanded alias modes must report separate counts and must not merge them into one unexplained total.
- Keep false positives visible in QA testing; do not tune the search list to maximise the number of suspicious-looking results.

## Official reference points

The category selection is informed by public fraud-awareness material—not by a claim that every phrase is a legally defined offence:

- Reserve Bank of India, *Consumer Awareness — Cyber Threats and Frauds* (28 January 2022): phishing, vishing, remote access, UPI collect requests, fake QR/payment prompts, impersonation and requests for credentials. <https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=53185>
- RBI, *Payments Banks — Digital Payment Security Controls Directions, 2026* (updated 1 October 2026): phishing, vishing, remote access and digital-payment security controls. <https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=13624>
- National Cyber Crime Reporting Portal: public categories and awareness material for online job fraud, vishing, smishing, sextortion and related cybercrime reporting. <https://cybercrime.gov.in/webform/crimecatdes.aspx>
- Indian Cyber Crime Coordination Centre (I4C), Cyber Crime Portal video categories: fake refund, digital arrest, investment, card/SIM swap, UPI, social-media, ransomware, job/loan, matrimonial, malware, e-wallet, business-email compromise and AEPS fraud. <https://cybercrime.gov.in/Webform/video-category.aspx>

This list is a starter search catalogue. Review and localise it with the hackathon committee/domain experts before any production or operational use.
