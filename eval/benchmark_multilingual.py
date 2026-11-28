"""Multilingual Benchmark Suite for English, Hindi Devanagari, Hinglish, and Mixed Code-Switching.

Evaluates:
- Classification Accuracy, Precision, Recall, F1 Score
- False Positive Rate (FPR) and False Negative Rate (FNR)
- Public Advisory / Hard Negative Suppression Rate
- Average Inference Latency (ms/sample)
Outputs benchmark metrics to `data/multilingual_evaluation_results.json`.
"""
import json
import time
import sys
from pathlib import Path
from typing import Dict, List, Any

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from core.multilingual import detect_language_and_script, check_awareness_context
from addons.scorer import RuleScorer
from models.classifier import HybridClassifier

BENCHMARK_OUTPUT_PATH = WORKSPACE_ROOT / "data" / "multilingual_evaluation_results.json"

# Curated benchmark dataset covering all 3 required language formats + mixed code-switching
BENCHMARK_DATASET: List[Dict[str, Any]] = [
    # ------------------ ENGLISH (30 Samples) ------------------
    {"text": "Pure MDMA crystals and top grade cocaine available. Guaranteed door delivery. Ping @sub_vendor", "category": "drugs", "language": "EN"},
    {"text": "Fresh Afghan charas and hashish stock arrived. DM @hash_hub for rates.", "category": "drugs", "language": "EN"},
    {"text": "LSD stamps and ketamine vials ready for dispatch. Fast courier service.", "category": "drugs", "language": "EN"},
    {"text": "Prescription tramadol and alprazolam tablets available without script.", "category": "drugs", "language": "EN"},
    {"text": "Selling 9mm pistol with 2 magazines and 50 brass bullets. Private deal.", "category": "arms", "language": "EN"},
    {"text": "Glock 19 tactical piece available with silencer. Direct delivery.", "category": "arms", "language": "EN"},
    {"text": "Unlicensed 315 bore rifle and cartridges in stock. Serious buyers only.", "category": "arms", "language": "EN"},
    {"text": "Country made pistol 32 bore available. DM @gun_seller for demo.", "category": "arms", "language": "EN"},
    {"text": "Counterfeit Aadhar card and driving license with working QR code print.", "category": "fake_documents", "language": "EN"},
    {"text": "Fake degree certificate and university marksheet fast delivery.", "category": "fake_documents", "language": "EN"},
    {"text": "Duplicate passport and international ID card ready in 48 hours.", "category": "fake_documents", "language": "EN"},
    {"text": "Active HDFC corporate current account for rent. High transaction limit.", "category": "bank_account", "language": "EN"},
    {"text": "Mule bank accounts available for crypto and P2P routing. Instant kit.", "category": "bank_account", "language": "EN"},
    {"text": "ICICI current account with full netbanking login credentials.", "category": "net_banking_kit", "language": "EN"},
    {"text": "Cloned ATM debit cards with PIN. High withdrawal limit at any ATM.", "category": "atm_card", "language": "EN"},
    {"text": "Pre-activated Airtel SIM cards with fake KYC. Bulk rate available.", "category": "sim_card", "language": "EN"},
    {"text": "Jio pre-activated SIMs no biometric needed. Ready to use.", "category": "sim_card", "language": "EN"},
    {"text": "Full banking kit: SIM, ATM card, netbanking user ID and checkbook.", "category": "net_banking_kit", "language": "EN"},
    {"text": "Corporate bank account sale for cyber flow. Guaranteed no freeze.", "category": "bank_account", "language": "EN"},
    {"text": "Synthetic weed and vape juice available for wholesale.", "category": "drugs", "language": "EN"},
    # English Benign & Hard Negatives
    {"text": "Good morning team, let us review the quarterly sales projection today.", "category": "benign", "language": "EN"},
    {"text": "Two-bedroom apartment for rent in South Delhi. Contact owner directly.", "category": "benign", "language": "EN"},
    {"text": "Used Honda City car for sale in excellent condition. Test drive open.", "category": "benign", "language": "EN"},
    {"text": "Mathematics and Physics private tutor available for Class 10 students.", "category": "benign", "language": "EN"},
    {"text": "SECURITY ADVISORY: Never share your OTP, netbanking password or ATM PIN. HDFC Bank official notice.", "category": "benign", "language": "EN", "is_advisory": True},
    {"text": "Beware of fraud calls claiming to be from your bank. Report to cybercrime helpline 1930.", "category": "benign", "language": "EN", "is_advisory": True},
    {"text": "State Rifle Shooting Championship trials announced for youth shooters.", "category": "benign", "language": "EN", "is_advisory": True},
    {"text": "Apollo Pharmacy reminder: Buy antibiotics only on valid doctor prescription from licensed counter.", "category": "benign", "language": "EN", "is_advisory": True},
    {"text": "Police busted interstate gang of illegal arms smugglers and seized weapons.", "category": "benign", "language": "EN", "is_advisory": True},
    {"text": "Public awareness notice: Rental of bank accounts for cybercrime is a punishable offense under PMLA.", "category": "benign", "language": "EN", "is_advisory": True},

    # ------------------ HINDI DEVANAGARI (30 Samples) ------------------
    {"text": "देसी कट्टा और ३१५ बोर कारतूस उपलब्ध है। तुरंत डिलीवरी के लिए संपर्क करें।", "category": "arms", "language": "HI"},
    {"text": "तमंचा और पिस्तौल का नया स्टॉक आ गया है। यूपी बिहार डायरेक्ट डिलीवरी।", "category": "arms", "language": "HI"},
    {"text": "अवैध हथियार और रिवाल्वर की होम डिलीवरी। असली लोहा पीस।", "category": "arms", "language": "HI"},
    {"text": "बंदूक और गोली चाहिए तो टेलीग्राम पर संपर्क करें। फुल लोडेड पीस।", "category": "arms", "language": "HI"},
    {"text": "एमडीएमए और चरस की ताजा खेप उपलब्ध है। मुंबई डिलीवरी तुरंत।", "category": "drugs", "language": "HI"},
    {"text": "सफेद पाउडर और अफीम का माल तैयार है। ऑर्डर बुक करें।", "category": "drugs", "language": "HI"},
    {"text": "ब्राउन शुगर और गांजा होलसेल रेट में उपलब्ध है।", "category": "drugs", "language": "HI"},
    {"text": "नशीली गोली और ट्रामाडोल का बड़ा स्टॉक उपलब्ध है।", "category": "drugs", "language": "HI"},
    {"text": "नकली आधार कार्ड और फर्जी पैन कार्ड बनवाने के लिए मैसेज करें।", "category": "fake_documents", "language": "HI"},
    {"text": "फर्जी दस्तावेज और जाली अंकतालिका तैयार की जाती है।", "category": "fake_documents", "language": "HI"},
    {"text": "नकली पहचान पत्र और ड्राइविंग लाइसेंस तुरंत प्रिंट करें।", "category": "fake_documents", "language": "HI"},
    {"text": "बैंक खाता रेंट पर चाहिए कमीशन बेस पर। चालू करंट खाता।", "category": "bank_account", "language": "HI"},
    {"text": "म्यूल खाता और मर्चेंट खाता सेल के लिए उपलब्ध है।", "category": "bank_account", "language": "HI"},
    {"text": "नेटबैंकिंग किट और एटीएम कार्ड सहित फुल किट उपलब्ध।", "category": "net_banking_kit", "language": "HI"},
    {"text": "क्लोन एटीएम कार्ड और डेबिट कार्ड हाई लिमिट के साथ।", "category": "atm_card", "language": "HI"},
    {"text": "चालू सिम और फर्जी केवाईसी सिम बिना आधार के चालू।", "category": "sim_card", "language": "HI"},
    {"text": "एयरटेल प्री एक्टिवेटेड सिम थोक भाव में उपलब्ध।", "category": "sim_card", "language": "HI"},
    {"text": "बायोमेट्रिक बाईपास सॉफ्टवेयर और फिंगरप्रिंट क्लोन टूल।", "category": "fake_documents", "language": "HI"},
    {"text": "कोटक बैंक करंट खाता उपलब्ध, अनलिमिटेड लेन-देन।", "category": "bank_account", "language": "HI"},
    {"text": "देसी पिस्टल और रिवाल्वर पीस उपलब्ध है, कैश ऑन डिलीवरी।", "category": "arms", "language": "HI"},
    # Hindi Benign & Hard Negatives
    {"text": "सुप्रभात, आज जयपुर का मौसम बहुत ही सुहावना है।", "category": "benign", "language": "HI"},
    {"text": "किराए के लिए दो कमरे का फ्लैट मानसरोवर में उपलब्ध है।", "category": "benign", "language": "HI"},
    {"text": "पुरानी मारुति सुजुकी कार बिक्री के लिए उपलब्ध है। संपर्क करें।", "category": "benign", "language": "HI"},
    {"text": "दसवीं कक्षा के विद्यार्थियों के लिए गणित की कोचिंग शुरू।", "category": "benign", "language": "HI"},
    {"text": "सावधान रहें: कभी किसी को अपना ओटीपी या बैंक पासवर्ड शेयर न करें। साइबर हेल्पलाइन 1930.", "category": "benign", "language": "HI", "is_advisory": True},
    {"text": "जनहित में जारी: बैंक कभी फोन पर पिन या पासवर्ड नहीं मांगता। सतर्क रहें।", "category": "benign", "language": "HI", "is_advisory": True},
    {"text": "पुलिस ने फर्जी सिम बेचने वाले गिरोह को गिरफ्तार किया। ऐसे संदेशों से बचें।", "category": "benign", "language": "HI", "is_advisory": True},
    {"text": "धोखाधड़ी से बचें: अज्ञात लिंक पर क्लिक न करें। साइबर क्राइम में शिकायत दर्ज करें।", "category": "benign", "language": "HI", "is_advisory": True},
    {"text": "राज्य स्तरीय राइफल शूटिंग चैंपियनशिप का आयोजन एसएमएस स्टेडियम में होगा।", "category": "benign", "language": "HI", "is_advisory": True},
    {"text": "डॉक्टर के पर्चे के बिना कोई भी दवा न लें। अधिकृत मेडिकल स्टोर से ही खरीदें।", "category": "benign", "language": "HI", "is_advisory": True},

    # ------------------ HINGLISH (ROMANISED HINDI) (30 Samples) ------------------
    {"text": "Bhai desi katta aur 315 bore piece chahiye to ping karo, fast delivery milega.", "category": "arms", "language": "HI_LATN"},
    {"text": "Tamancha aur hathiyar ready stock me hai. Full loaded piece.", "category": "arms", "language": "HI_LATN"},
    {"text": "Asla aur goli ka fresh consignment aaya hai, UP Bihar delivery available.", "category": "arms", "language": "HI_LATN"},
    {"text": "Desi pistol aur bandook cash on delivery par milega contact karo.", "category": "arms", "language": "HI_LATN"},
    {"text": "High quality maal aur afeem available hai, home delivery guaranteed.", "category": "drugs", "language": "HI_LATN"},
    {"text": "Chitta aur smack pure stuff available. Fast dispatch parcel.", "category": "drugs", "language": "HI_LATN"},
    {"text": "Charas aur ganja score karna hai to DM karo, wholesale rate.", "category": "drugs", "language": "HI_LATN"},
    {"text": "Nasheeli goli aur white powder ready hai. Ping fast.", "category": "drugs", "language": "HI_LATN"},
    {"text": "Nakli aadhar card aur farzi pan card banwayein sirf 30 minute me.", "category": "fake_documents", "language": "HI_LATN"},
    {"text": "Farzi dastavez aur duplicate marksheet ready with verification.", "category": "fake_documents", "language": "HI_LATN"},
    {"text": "Nakli driving license aur pehchan patra print karwayein.", "category": "fake_documents", "language": "HI_LATN"},
    {"text": "Mule khata rent par chahiye daily commission basis par, payment guaranteed.", "category": "bank_account", "language": "HI_LATN"},
    {"text": "Kotak current khata aur merchant account sale ke liye ready hai.", "category": "bank_account", "language": "HI_LATN"},
    {"text": "Full kit milega: ATM debit card, netbanking login aur registered SIM.", "category": "net_banking_kit", "language": "HI_LATN"},
    {"text": "Clone ATM card with PIN available, daily withdrawal guaranteed.", "category": "atm_card", "language": "HI_LATN"},
    {"text": "Chalu SIM card aur fake kyc sim bina biometric ke available.", "category": "sim_card", "language": "HI_LATN"},
    {"text": "Pre activated airtel sim ready stock me hai wholesale rate par.", "category": "sim_card", "language": "HI_LATN"},
    {"text": "Biometric bypass aur aadhar print crack software available.", "category": "fake_documents", "language": "HI_LATN"},
    {"text": "Current account rent par do aur daily 2% commission kamao.", "category": "bank_account", "language": "HI_LATN"},
    {"text": "Desi katta piece aur cartridges ready, video call demo available.", "category": "arms", "language": "HI_LATN"},
    # Hinglish Benign & Hard Negatives
    {"text": "Namaste dosto, kal sham ko match dekhne chalte hain.", "category": "benign", "language": "HI_LATN"},
    {"text": "Ghar par banya hua tasty khana tiffin service available Jaipur me.", "category": "benign", "language": "HI_LATN"},
    {"text": "Purana laptop sell karna hai good condition Dell i5.", "category": "benign", "language": "HI_LATN"},
    {"text": "English speaking classes start ho rahi hai next week se.", "category": "benign", "language": "HI_LATN"},
    {"text": "Savdhan rahe: apna OTP kisi ko share mat karo, ye farzi call ho sakta hai. Helpline 1930.", "category": "benign", "language": "HI_LATN", "is_advisory": True},
    {"text": "Bank alert: Kisi bhi anjan vyakti ko bank account details na batayein. Satark rahe.", "category": "benign", "language": "HI_LATN", "is_advisory": True},
    {"text": "Police ne nakli sim bechne wale ko pakda. Satark rahe aur complaint karein.", "category": "benign", "language": "HI_LATN", "is_advisory": True},
    {"text": "Dhokhadhadi se bache: lottery ya prize money ke farzi message par vishwas na karein.", "category": "benign", "language": "HI_LATN", "is_advisory": True},
    {"text": "Doctor ke prescription ke bina dawa mat lijiye, official medical store se lein.", "category": "benign", "language": "HI_LATN", "is_advisory": True},
    {"text": "Police advisory: Bank account rent par dena kanoon apradh hai, jail ho sakti hai.", "category": "benign", "language": "HI_LATN", "is_advisory": True},

    # ------------------ MIXED / CODE-SWITCHING (30 Samples) ------------------
    {"text": "Original MDMA पाउडर उपलब्ध है, contact on telegram for direct home delivery.", "category": "drugs", "language": "MIXED"},
    {"text": "Fresh Afghan charas and चरस ready stock. Ping @deals for fast dispatch.", "category": "drugs", "language": "MIXED"},
    {"text": "High purity cocaine available, मुंबई और दिल्ली में immediate courier.", "category": "drugs", "language": "MIXED"},
    {"text": "Ketamine vials and नशीली गोली for bulk orders only. Contact vendor.", "category": "drugs", "language": "MIXED"},
    {"text": "New stock of desi katta और 315 bore कारतूस ready for dispatch.", "category": "arms", "language": "MIXED"},
    {"text": "Glock 9mm pistol और असला available. UP delivery within 24 hours.", "category": "arms", "language": "MIXED"},
    {"text": "Full loaded तमंचा and brass bullets for cash payment.", "category": "arms", "language": "MIXED"},
    {"text": "Unlicensed rifle बंदूक with 50 rounds ammo. DM for price.", "category": "arms", "language": "MIXED"},
    {"text": "Fake Aadhar card और पैन कार्ड print service with valid QR code.", "category": "fake_documents", "language": "MIXED"},
    {"text": "Counterfeit degree certificate और अंकतालिका fast parcel delivery.", "category": "fake_documents", "language": "MIXED"},
    {"text": "Duplicate passport and पहचान पत्र ready in 2 days.", "category": "fake_documents", "language": "MIXED"},
    {"text": "Active HDFC bank account रेंट पर चाहिए for crypto P2P transactions.", "category": "bank_account", "language": "MIXED"},
    {"text": "Fresh corporate current khata available with netbanking kit.", "category": "net_banking_kit", "language": "MIXED"},
    {"text": "Cloned debit cards और एटीएम कार्ड with PIN. High withdrawal limit.", "category": "atm_card", "language": "MIXED"},
    {"text": "Full banking kit: चालू सिम, ATM card and cheque book included.", "category": "net_banking_kit", "language": "MIXED"},
    {"text": "Pre-activated Jio सिम बिना बायोमेट्रिक के. Ready to use immediately.", "category": "sim_card", "language": "MIXED"},
    {"text": "Airtel fake kyc sim cards थोक भाव में. Contact on telegram.", "category": "sim_card", "language": "MIXED"},
    {"text": "Biometric bypass software और आधार crack kit download link.", "category": "fake_documents", "language": "MIXED"},
    {"text": "High transaction limit करंट अकाउंट available for high flow.", "category": "bank_account", "language": "MIXED"},
    {"text": "Desi pistol और गोली ready, parcel shipping all over India.", "category": "arms", "language": "MIXED"},
    # Mixed Benign & Hard Negatives
    {"text": "Good morning sabhi ko, office meeting 11 baje start hogi.", "category": "benign", "language": "MIXED"},
    {"text": "Flat for rent मानसरोवर में available hai, contact owner.", "category": "benign", "language": "MIXED"},
    {"text": "Used laptop बिक्री के लिए available in good condition.", "category": "benign", "language": "MIXED"},
    {"text": "Online coaching classes for 10th and 12th board exams.", "category": "benign", "language": "MIXED"},
    {"text": "SECURITY NOTICE: Never share your OTP or पासवर्ड. साइबर हेल्पलाइन 1930.", "category": "benign", "language": "MIXED", "is_advisory": True},
    {"text": "Official Bank Advisory: बैंक कभी OTP नहीं मांगता. Beware of fraudulent calls.", "category": "benign", "language": "MIXED", "is_advisory": True},
    {"text": "Police alert: Fake SIM कार्ड बेचने वाले गिरफ्तार हुए. Be cautious.", "category": "benign", "language": "MIXED", "is_advisory": True},
    {"text": "Fraud alert: Do not click unknown links, धोखाधड़ी से बचें report to 1930.", "category": "benign", "language": "MIXED", "is_advisory": True},
    {"text": "State rifle shooting championship एसएमएस स्टेडियम में होगी. Registered athletes only.", "category": "benign", "language": "MIXED", "is_advisory": True},
    {"text": "Doctor prescription is mandatory for controlled medicines. अधिकृत मेडिकल स्टोर.", "category": "benign", "language": "MIXED", "is_advisory": True},
]


def run_multilingual_benchmark() -> Dict[str, Any]:
    print("Initializing RuleScorer and HybridClassifier...")
    scorer = RuleScorer()
    clf = HybridClassifier(auto_load=True)

    results_by_lang = {
        "EN": {"total": 0, "multiclass_correct": 0, "tp": 0, "fp": 0, "fn": 0, "tn": 0, "latencies": []},
        "HI": {"total": 0, "multiclass_correct": 0, "tp": 0, "fp": 0, "fn": 0, "tn": 0, "latencies": []},
        "HI-LATN": {"total": 0, "multiclass_correct": 0, "tp": 0, "fp": 0, "fn": 0, "tn": 0, "latencies": []},
        "MIXED": {"total": 0, "multiclass_correct": 0, "tp": 0, "fp": 0, "fn": 0, "tn": 0, "latencies": []},
    }

    advisory_samples = 0
    advisory_suppressed = 0

    print(f"Running benchmark on {len(BENCHMARK_DATASET)} multi-lingual records...")

    for sample in BENCHMARK_DATASET:
        text = sample["text"]
        expected_cat = sample["category"]
        raw_lang = sample["language"]
        expected_lang = "HI-LATN" if raw_lang in ("HI-LATN", "HI_LATN") else raw_lang
        is_advisory = sample.get("is_advisory", False)

        t0 = time.perf_counter()
        res = clf.classify(text)
        lat_ms = (time.perf_counter() - t0) * 1000.0

        lang_bucket = expected_lang if expected_lang in results_by_lang else "MIXED"
        bucket = results_by_lang[lang_bucket]
        bucket["total"] += 1
        bucket["latencies"].append(lat_ms)

        pred_cat = res.category
        is_pred_illegal = res.is_actionable and pred_cat != "benign"
        is_actual_illegal = expected_cat != "benign"

        # 1. Strict multiclass category classification
        if pred_cat == expected_cat:
            bucket["multiclass_correct"] += 1

        # 2. Binary threat detection (illegal vs benign)
        if is_actual_illegal and is_pred_illegal:
            bucket["tp"] += 1
        elif not is_actual_illegal and is_pred_illegal:
            bucket["fp"] += 1
        elif is_actual_illegal and not is_pred_illegal:
            bucket["fn"] += 1
        else:
            bucket["tn"] += 1

        if is_advisory:
            advisory_samples += 1
            if not is_pred_illegal:
                advisory_suppressed += 1

    # Aggregate metrics
    summary = {}
    tot_samples = 0
    tot_mc_correct = 0
    tot_tp = 0
    tot_fp = 0
    tot_fn = 0
    tot_tn = 0
    all_latencies = []

    for lang, b in results_by_lang.items():
        n = b["total"]
        if n == 0:
            continue
        tot_samples += n
        tot_mc_correct += b["multiclass_correct"]
        tot_tp += b["tp"]
        tot_fp += b["fp"]
        tot_fn += b["fn"]
        tot_tn += b["tn"]
        all_latencies.extend(b["latencies"])

        mc_acc = b["multiclass_correct"] / n
        bin_acc = (b["tp"] + b["tn"]) / n
        prec = b["tp"] / (b["tp"] + b["fp"]) if (b["tp"] + b["fp"]) > 0 else 1.0
        rec = b["tp"] / (b["tp"] + b["fn"]) if (b["tp"] + b["fn"]) > 0 else 1.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        fpr = b["fp"] / (b["fp"] + b["tn"]) if (b["fp"] + b["tn"]) > 0 else 0.0
        fnr = b["fn"] / (b["fn"] + b["tp"]) if (b["fn"] + b["tp"]) > 0 else 0.0
        avg_lat = sum(b["latencies"]) / len(b["latencies"])

        metrics_obj = {
            "total_samples": n,
            "multiclass_accuracy": round(mc_acc, 4),
            "multiclass_accuracy_pct": round(mc_acc * 100, 2),
            "binary_accuracy": round(bin_acc, 4),
            "binary_accuracy_pct": round(bin_acc * 100, 2),
            "binary_precision": round(prec, 4),
            "binary_recall": round(rec, 4),
            "binary_f1": round(f1, 4),
            "false_positive_rate": round(fpr, 4),
            "false_negative_rate": round(fnr, 4),
            "avg_latency_ms": round(avg_lat, 2)
        }
        summary[lang] = metrics_obj
        if lang == "HI-LATN":
            summary["HI_LATN"] = metrics_obj

    overall_mc_acc = tot_mc_correct / tot_samples if tot_samples > 0 else 0.0
    overall_bin_acc = (tot_tp + tot_tn) / tot_samples if tot_samples > 0 else 0.0
    overall_prec = tot_tp / (tot_tp + tot_fp) if (tot_tp + tot_fp) > 0 else 1.0
    overall_rec = tot_tp / (tot_tp + tot_fn) if (tot_tp + tot_fn) > 0 else 1.0
    overall_f1 = (2 * overall_prec * overall_rec) / (overall_prec + overall_rec) if (overall_prec + overall_rec) > 0 else 0.0
    overall_fpr = tot_fp / (tot_fp + tot_tn) if (tot_fp + tot_tn) > 0 else 0.0
    overall_fnr = tot_fn / (tot_fn + tot_tp) if (tot_fn + tot_tp) > 0 else 0.0
    overall_lat = sum(all_latencies) / len(all_latencies) if all_latencies else 0.0

    advisory_fp_rate = (advisory_samples - advisory_suppressed) / advisory_samples if advisory_samples > 0 else 0.0

    output_data = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "metadata": {
            "evaluation_scope": "curated_ground_truth_test_fixtures",
            "total_test_samples": tot_samples,
            "language_slices": ["EN", "HI", "HI-LATN", "MIXED"],
            "samples_per_slice": 30,
            "legal_compliance": "Section 63 BSA compliant forensic extraction; zero model retraining on user data",
            "disclaimer": "Metrics represent verified curated laboratory test fixtures. Real-world open-web precision and false-positive rates may vary due to emerging evasion tactics and uncataloged adversarial slang."
        },
        "overall_metrics": {
            "multiclass_accuracy": round(overall_mc_acc, 4),
            "multiclass_accuracy_pct": round(overall_mc_acc * 100, 2),
            "binary_accuracy": round(overall_bin_acc, 4),
            "binary_accuracy_pct": round(overall_bin_acc * 100, 2),
            "binary_precision": round(overall_prec, 4),
            "binary_recall": round(overall_rec, 4),
            "binary_f1": round(overall_f1, 4),
            "false_positive_rate": round(overall_fpr, 4),
            "false_negative_rate": round(overall_fnr, 4),
            "avg_latency_ms": round(overall_lat, 2),
        },
        "summary_by_language": summary,
        "advisory_suppression": {
            "total_advisories": advisory_samples,
            "suppressed_clean": advisory_suppressed,
            "false_positives": advisory_samples - advisory_suppressed,
            "false_positive_rate": round(advisory_fp_rate * 100, 2),
            "suppression_success_rate": round((advisory_suppressed / advisory_samples) * 100, 2) if advisory_samples > 0 else 100.0
        }
    }

    BENCHMARK_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(BENCHMARK_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n Multilingual Benchmark Complete!")
    print(f"Strict Multiclass Accuracy: {output_data['overall_metrics']['multiclass_accuracy_pct']}%")
    print(f"Binary Threat Accuracy: {output_data['overall_metrics']['binary_accuracy_pct']}% | F1: {output_data['overall_metrics']['binary_f1']}")
    print(f"Advisory Suppression Rate: {output_data['advisory_suppression']['suppression_success_rate']}% (FPR: {output_data['advisory_suppression']['false_positive_rate']}%)")
    print(f"Results saved to: {BENCHMARK_OUTPUT_PATH}")
    return output_data


if __name__ == "__main__":
    run_multilingual_benchmark()
