# Multilingual Slang & Threat Catalogue

## 1. Overview & Policy

This catalogue documents the comprehensive multilingual vocabulary integrated into `addons/lexicon.yaml` and `core/multilingual.py`. The lexicon covers three primary language representations:
- **English (`slang_en`):** Conventional contraband and illicit trade terminology.
- **Hindi Devanagari (`slang_hi`):** Native Indic script terms, including nukta variations and colloquial spellings.
- **Hinglish (`slang_hinglish`):** Phonetically Romanised Hindi words and regional phrasing.
- **Marathi (`slang_marathi`):** Regional state slang terms.
- **Coded Phrases (`coded_words`):** Evasion phrases, numeric codes, and trade obfuscations.
- **Emojis (`emojis`):** Visual indicators associated with underground channels.

---

## 2. Statutory Legal & Policy Guardrails

> [!IMPORTANT]
> **Weapons Mentions — CONTEXT ONLY Policy:**
> In strict accordance with hackathon committee boundaries, isolated mentions of weapons or firearms are treated as **CONTEXT ONLY** and do NOT produce automated suspicion scores or risk elevation. Suspicion is elevated strictly when corroborated by financial recruitment patterns, illicit delivery offers, or unverified seller contacts.

> [!NOTE]
> **Section 63 BSA Legal Disclaimer:**
> *"A keyword match is a search result, not proof of wrongdoing. Context, provenance, integrity and independent verification are necessary before any legal or operational reliance."*

---

## 3. Comprehensive Category Lexicon

### Category 1: Narcotics & Controlled Substances (`drugs`)
- **Default Weight:** 2.5 | **Weight Multiplier:** 1.0
- **English (`slang_en`):**
  `mdma`, `mephedrone`, `meow meow`, `weed`, `og kush`, `charas`, `hashish`, `heroin`, `cocaine`, `meth`, `crystal meth`, `lsd`, `acid stamp`, `ganja`, `brown sugar`, `tramadol`, `alprazolam`, `ketamine`
- **Hindi Devanagari (`slang_hi`):**
  `एमडीएमए`, `मेफेड्रोन`, `चरस`, `गांजा`, `अफीम`, `भांग`, `सफेद पाउडर`, `नशीली गोली`, `ब्राउन शुगर`, `हेरोइन`, `कोकीन`, `नशा`
- **Hinglish (`slang_hinglish`):**
  `maal`, `chitta`, `afeem`, `bhang`, `smack`, `nasheeli goli`, `white powder`, `high quality maal`, `stuff available`, `score maal`
- **Marathi (`slang_marathi`):**
  `gard`, `charas`, `nasha`, `padarth`, `goli`
- **Coded Words (`coded_words`):**
  `420`, `c0ke`, `w33d`, `white stone`, `ice crystal`, `pure stuff`, `home delivery available`, `instant parcel`, `drop shipping weed`
- **Emojis:**
  `🍁`, `🌿`, `💊`, `❄️`, `💉`, `🍄`, `💨`, `🧪`

---

### Category 2: Illegal Weapons & Ammunition (`arms`)
- **Default Weight:** 3.0 | **Weight Multiplier:** 1.2
- **English (`slang_en`):**
  `pistol`, `revolver`, `glock`, `country made pistol`, `ammo`, `bullets`, `9mm`, `315 bore`, `32 bore`, `7.65mm`, `rifle`, `shotgun`, `silencer`, `magazine`, `cartridge`
- **Hindi Devanagari (`slang_hi`):**
  `पिस्तौल`, `रिवाल्वर`, `कट्टा`, `देसी कट्टा`, `तमंचा`, `बंदूक`, `हथियार`, `गोली`, `कारतूस`, `असला`, `राइफल`, `छुरी`, `लोहा`, `देसी पिस्टल`, `चाकु`, `तलवार`
- **Hinglish (`slang_hinglish`):**
  `katta`, `desi katta`, `tamancha`, `bandook`, `chhuri`, `hathiyar`, `goli`, `asla`, `desi pistol`, `loha`, `maal pistol`, `revolver piece`
- **Marathi (`slang_marathi`):**
  `gavti katta`, `banduk`, `chaku`, `talwar`, `katti`, `lohandi saman`
- **Coded Words (`coded_words`):**
  `315 piece`, `32 piece`, `iron piece`, `toy available`, `safety tool`, `full loaded piece`, `brass rounds`, `direct delivery bihar`, `up delivery`
- **Emojis:**
  `🔫`, `🗡️`, `💣`, `⚔️`, `🛡️`

---

### Category 3: Forged Identity Documents & Credentials (`fake_documents`)
- **Default Weight:** 2.0 | **Weight Multiplier:** 1.1
- **English (`slang_en`):**
  `fake aadhar`, `counterfeit pan`, `fake driving license`, `fake passport`, `fake voter id`, `forged marksheet`, `degree certificate fake`, `psd template aadhar`, `biometric bypass`, `aadhar print software`, `crack aadhar software`
- **Hindi Devanagari (`slang_hi`):**
  `नकली आधार`, `फर्जी पैन`, `जाली दस्तावेज`, `नकली पहचान पत्र`, `फर्जी मार्कशीट`, `जाली पासपोर्ट`, `अंकतालिका`, `ड्राइविंग लाइसेंस`, `बायोमेट्रिक बाईपास`, `फिंगरप्रिंट क्लोन`
- **Hinglish (`slang_hinglish`):**
  `nakli aadhar`, `farzi pan`, `duplicate marksheet`, `farzi dastavez`, `nakli voter id`, `fake certificate`, `jaali documents`, `biometric bypass tool`, `aadhar print crack`
- **Marathi (`slang_marathi`):**
  `khote kagadpatra`, `nakli pramanpatra`, `farji aadhar`, `khoti marksheet`
- **Coded Words (`coded_words`):**
  `bypass kit`, `instant print software`, `all india delivery docs`, `full verified doc`, `original look alike`
- **Emojis:**
  `📄`, `🪪`, `🖨️`, `📁`, `📑`

---

### Category 4: Illicit Mule Bank Accounts (`bank_account`)
- **Default Weight:** 2.5 | **Weight Multiplier:** 1.3
- **English (`slang_en`):**
  `mule account`, `current account rent`, `savings account sale`, `corporate account for rent`, `bank account hire`, `dormant account active`, `merchant account rent`, `p2p bank account`, `crypto flow account`, `fresh current account`, `hdfc account rent`, `icici current account`, `axis bank account sale`
- **Hindi Devanagari (`slang_hi`):**
  `म्यूल खाता`, `खाता रेंट`, `बैंक खाता सेल`, `करंट खाता`, `बचत खाता`, `चालू खाता`, `खाता कमीशन`, `मर्चेंट खाता`, `कोटक बैंक खाता`, `खाता चाहिए`
- **Hinglish (`slang_hinglish`):**
  `mule khata`, `khata rent`, `current account rent par`, `khata commission par`, `bank account chahiye`, `fresh khata`, `fastag khata`, `daily limit khata`, `corporate khata`
- **Marathi (`slang_marathi`):**
  `khate bhadyane`, `bank khate sale`, `mule khate`, `current khate`
- **Coded Words (`coded_words`):**
  `high limit channel`, `daily 50L limit`, `instant payout account`, `clean transaction load`, `zero hold account`, `p2p load khata`
- **Emojis:**
  `🏦`, `💳`, `💰`, `💸`, `📈`

---

### Category 5: Cloned ATM & Payment Cards (`atm_card`)
- **Default Weight:** 2.0 | **Weight Multiplier:** 1.0
- **English (`slang_en`):**
  `cloned atm card`, `skimmer card`, `atm debit kit`, `blank card pin`, `dump card`, `track 2 dump`, `cvv shop`, `carding tool`, `pos machine clone`
- **Hindi Devanagari (`slang_hi`):**
  `क्लोन एटीएम`, `डेबिट कार्ड सेल`, `कार्डिंग`, `क्लोन कार्ड`, `एटीएम कार्ड पिन`
- **Hinglish (`slang_hinglish`):**
  `clone atm`, `card with pin`, `debit card dump`, `atm card ready`, `blank card available`
- **Marathi (`slang_marathi`):**
  `atm card clone`, `nakli card`, `paisa kadha card`
- **Coded Words (`coded_words`):**
  `plastic piece ready`, `swipe machine ready`, `unlimited cash card`, `daily 2L withdrawal`
- **Emojis:**
  `💳`, `🏧`, `💵`, `🪙`

---

### Category 6: Fraudulent / Pre-Activated SIM Cards (`sim_card`)
- **Default Weight:** 2.0 | **Weight Multiplier:** 1.1
- **English (`slang_en`):**
  `fake kyc sim`, `pre activated sim`, `chalu sim`, `bulk sim cards`, `airtel pre activated`, `jio pre activated`, `vi active sim`, `foreign sim otp`, `non kyc sim`, `esim activated`
- **Hindi Devanagari (`slang_hi`):**
  `चालू सिम`, `फर्जी सिम`, `बिना केवाईसी सिम`, `एयरटेल चालू सिम`, `जियो सिम एक्टिवेटेड`, `थोक सिम कार्ड`
- **Hinglish (`slang_hinglish`):**
  `chalu sim`, `pre active sim`, `fake kyc sim`, `bina biometric sim`, `ready sim card`, `bulk sim available`
- **Marathi (`slang_marathi`):**
  `chalu sim`, `bina aadhar sim`, `tayyari sim`
- **Coded Words (`coded_words`):**
  `otp bypass sim`, `telegram creation sim`, `calling sim ready`, `anonymous chip`
- **Emojis:**
  `📶`, `📱`, `📲`, `📟`

---

### Category 7: Comprehensive Net Banking Kits (`net_banking_kit`)
- **Default Weight:** 2.5 | **Weight Multiplier:** 1.4
- **English (`slang_en`):**
  `net banking kit`, `full banking kit`, `corporate net banking login`, `passbook cheque book kit`, `otp sim included kit`, `complete bank kit`, `merchant gateway kit`, `upi merchant kit`
- **Hindi Devanagari (`slang_hi`):**
  `नेटबैंकिंग किट`, `फुल बैंकिंग किट`, `पासबुक चेकबुक किट`, `संपूर्ण बैंक किट`, `नेट बैंकिंग आईडी पासवर्ड`
- **Hinglish (`slang_hinglish`):**
  `full banking kit`, `netbanking credentials kit`, `chequebook passbook kit`, `full setup ready`, `kit with atm sim`
- **Marathi (`slang_marathi`):**
  `sampurna bank kit`, `net banking kit`
- **Coded Words (`coded_words`):**
  `all in one kit`, `ready to run kit`, `instant deployment kit`, `master kit`
- **Emojis:**
  `💼`, `🔐`, `📦`, `🧰`
