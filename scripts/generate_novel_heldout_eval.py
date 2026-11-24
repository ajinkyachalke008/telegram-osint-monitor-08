"""Novel Template Generator for Held-Out Out-of-Distribution Model Evaluation.

Generates a fresh test set using COMPLETELY DIFFERENT sentence templates and phrasing
to evaluate the generalization of the multilingual embedding model:
- Out-of-vocabulary variations
- Regional syntax (Hinglish/Marathi phrasing)
- Distinct benign hard negatives
- Safe fake contacts (e.g. 90000 77777, novel.mule@ybl)
"""
import json
import random
from pathlib import Path
from typing import List, Dict, Any

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "test_heldout_novel_templates.jsonl"

NOVEL_DRUG_TEMPLATES = [
    "Exclusive batch of imported {substance} touched down in {city}. Stealth packing guaranteed {emoji}. Telegram @novel_vendor_{num}.",
    "Looking to score high-purity {substance} tonight? Verified reviews, fastest dispatch in {city}. Signal contact 90000 {num}.",
    "Weekend party inventory: {substance} with door delivery {emoji}. Cryptocurrency only. DM @stealth_pack_{num}.",
    "Finest quality {slang} arriving directly from source. Instant drop anywhere in {city}. Pay via UPI novel.{num}@ybl {emoji}.",
    "Uncut {substance} available for bulk wholesale. No cut, lab tested {emoji}. Reach out on @direct_source_{num}."
]

NOVEL_ARMS_TEMPLATES = [
    "Unlicensed {weapon} with sealed {ammo} box for personal defense in {city}. Direct cash deal, test fire available {emoji}. Ping @fire_source_{num}.",
    "Urgent clearance: {weapon} in immaculate condition with extra mag. Cash on delivery pan-India. Telegram @iron_vendor_{num}.",
    "Country-crafted {weapon} ({ammo}) with heavy sound impact. Video verification ready {emoji}. WhatsApp 90000 {num}.",
    "Factory-condition {weapon} ready for pickup in {city}. Clean piece, no serial numbers. DM @tactical_gear_{num} {emoji}.",
    "Special collection {weapon} with {ammo} cartridges. Serious buyers only in {city}. Ping @heavy_iron_{num}."
]

NOVEL_FAKE_DOC_TEMPLATES = [
    "Need urgent bypass for biometric {doc}? High-grade replica with scannable barcode ready in 12 hours in {city}. DM @bypass_id_{num}.",
    "Government format {doc} without physical verification. Backdated entry into database {emoji}. Call 90000 {num}.",
    "University degrees and original format {doc} with seal stamps. Pan-India courier dispatch. DM @cert_point_{num}.",
    "Instant replacement for lost {doc} with custom QR code print. 100% accepted for loan approval {emoji}. Ping @id_express_{num}.",
    "Forged {doc} made with official card stock and hologram stickers. Safe courier to {city}. Telegram @stamp_craft_{num}."
]

NOVEL_BANK_ACCOUNT_TEMPLATES = [
    "Immediate payout: Rent your dormant {bank} account for gaming loads. 12% daily cut guaranteed {emoji}. Ping @mule_desk_{num}.",
    "High-capacity {account_type} account in {bank} ready for RTGS loads without hold. Daily capacity 25L. DM @acc_market_{num}.",
    "Need trusted {bank} savings/current khata for remittance routing. Attractive daily rent basis in {city} {emoji}. Call 90000 {num}.",
    "Freshly opened {bank} corporate current account with authorized signatory kit. Safe and dispute-free. Contact @corp_desk_{num}.",
    "Provide your idle {bank} bank account and receive 15,000 INR per transaction volume {emoji}. DM @commission_hub_{num}."
]

NOVEL_ATM_CARD_TEMPLATES = [
    "Pre-issued {bank} ATM debit cards with PIN mailed in tamper-evident envelopes. Daily cashout limit 2 Lakhs {emoji}. Telegram @plastic_hub_{num}.",
    "Active debit card with physical plastic for ATM swipe cashout. Fast courier pan-India. WhatsApp 90000 {num}.",
    "Multiple {bank} ATM cards available for daily rental. Instant profit sharing {emoji}. Contact @swipe_master_{num}.",
    "High-tier Platinum debit cards ready for cash withdrawal in {city}. Complete credentials included. DM @card_depot_{num}.",
    "Cloned and pre-activated ATM debit cards with secure PIN codes. Immediate dispatch to {city} {emoji}. Ping @cash_card_{num}."
]

NOVEL_SIM_CARD_TEMPLATES = [
    "Untraceable {operator} prepaid SIM cards registered on third-party identity. Ready for OTPs and social media {emoji}. DM @clean_sim_{num}.",
    "Pre-activated 5G {operator} SIM cards in bulk with active international roaming. Delivered to {city}. WhatsApp 90000 {num}.",
    "Bulk ready-to-use SIMs without Aadhaar linkage. Tested outgoing and incoming {emoji}. Telegram @sim_depot_{num}.",
    "Corporate SIM card batches for automated OTP receipt. Zero KYC paperwork required in {city}. Contact @bulk_otp_{num}.",
    "Pre-KYC completed {operator} nano SIM cards ready for instant mobile activation {emoji}. DM @fast_sims_{num}."
]

NOVEL_NET_BANKING_KIT_TEMPLATES = [
    "Turnkey digital banking kit of {bank}: active SIM, debit card, internet banking login, and chequebook {emoji}. DM @full_kit_{num}.",
    "Ready corporate netbanking kit with hardware OTP token device and maker-checker access in {bank}. Ping @corp_access_{num}.",
    "Complete netbanking kit + registered phone number for gaming and P2P payouts. Daily limit 50 Lakhs in {city} {emoji}. WhatsApp 90000 {num}.",
    "Selling active {bank} internet banking credentials with dedicated registered SIM for OTP forwarding. Contact @turnkey_banking_{num}.",
    "All-in-one {bank} banking kit delivered with physical plastic, passbook, and SIM card {emoji}. Telegram @bank_combo_{num}."
]

NOVEL_BENIGN_TEMPLATES = [
    "Cyber Crime Cell Advisory: Do not allow third parties to use your {bank} account for financial transactions. Account rental is a punishable offense under PMLA.",
    "State Bank Alert: Never click on unverified links claiming to update your PAN or Aadhaar card for mobile banking. Report fraud to 1930.",
    "Authorized Medical Store: Paracetamol, cough syrup, and antibiotics require a registered medical practitioner prescription. Located in {city}.",
    "Government Healthcare Initiative: Free health checkup camp and distribution of generic hypertension medications at {city} Civil Hospital.",
    "Rifle & Pistol Shooting Club {city}: Open registrations for 10m target shooting summer training camp. Licensed sports air guns provided.",
    "State Police Press Release: Cybercrime unit in {city} uncovers illegal call center syndicate. Several forged documents and illegal SIMs recovered.",
    "Residential Property Listing: 3 BHK apartment available for long-term lease in {city}, prime society with dedicated parking. Call owner directly.",
    "Corporate Job Opening: Senior Python Engineer required at leading fintech in {city}. Experience with SQL, Docker, and REST APIs."
]

CITIES = ["Nagpur", "Coimbatore", "Bhopal", "Patna", "Visakhapatnam", "Vadodara", "Guwahati", "Nashik"]
BANKS = ["HDFC", "ICICI", "Axis Bank", "SBI", "Kotak Mahindra", "Punjab National Bank"]
OPERATORS = ["Jio", "Airtel", "Vodafone Vi"]
SUBSTANCES = [
    ("mephedrone", "🧪", "meow meow"), ("charas", "🍁", "maal"),
    ("cocaine", "❄️", "white stone"), ("mdma", "💊", "ecstasy pills"),
    ("weed", "🌿", "hydroponic greens")
]
WEAPONS = [
    ("pistol", "9mm", "🔫"), ("revolver", "32 bore", "💥"),
    ("country made katta", "315 bore", "💣"), ("air rifle", "pellets", "🎯")
]
DOCS = [
    ("pan card", "💳"), ("aadhaar card", "📄"), ("driving license", "🚗"),
    ("passport", "🛂"), ("degree marksheet", "🎓")
]


def generate_novel_dataset(count_per_category: int = 50) -> List[Dict[str, Any]]:
    records = []
    rng = random.Random(2026)

    cats = [
        ("drugs", NOVEL_DRUG_TEMPLATES),
        ("arms", NOVEL_ARMS_TEMPLATES),
        ("fake_documents", NOVEL_FAKE_DOC_TEMPLATES),
        ("bank_account", NOVEL_BANK_ACCOUNT_TEMPLATES),
        ("atm_card", NOVEL_ATM_CARD_TEMPLATES),
        ("sim_card", NOVEL_SIM_CARD_TEMPLATES),
        ("net_banking_kit", NOVEL_NET_BANKING_KIT_TEMPLATES)
    ]

    for cat_name, templates in cats:
        for _ in range(count_per_category):
            tpl = rng.choice(templates)
            city = rng.choice(CITIES)
            num = f"{rng.randint(10000, 99999)}"
            bank = rng.choice(BANKS)

            if cat_name == "drugs":
                sub, emoji, slang = rng.choice(SUBSTANCES)
                text = tpl.format(substance=sub, emoji=emoji, slang=slang, city=city, num=num)
            elif cat_name == "arms":
                wep, ammo, emoji = rng.choice(WEAPONS)
                text = tpl.format(weapon=wep, ammo=ammo, emoji=emoji, city=city, num=num)
            elif cat_name == "fake_documents":
                doc, emoji = rng.choice(DOCS)
                text = tpl.format(doc=doc, emoji=emoji, city=city, num=num)
            elif cat_name == "bank_account":
                acc = rng.choice(["current", "savings", "corporate current"])
                emoji = rng.choice(["💼", "🏦", "💰", "💸"])
                text = tpl.format(account_type=acc, bank=bank, city=city, num=num, emoji=emoji)
            elif cat_name == "atm_card":
                emoji = rng.choice(["💳", "🏧", "💸", "✅"])
                text = tpl.format(bank=bank, city=city, num=num, emoji=emoji)
            elif cat_name == "sim_card":
                op = rng.choice(OPERATORS)
                emoji = rng.choice(["📲", "📶", "⚡"])
                text = tpl.format(operator=op, city=city, num=num, emoji=emoji)
            elif cat_name == "net_banking_kit":
                emoji = rng.choice(["💼", "🔐", "🏧"])
                text = tpl.format(bank=bank, city=city, num=num, emoji=emoji)
            else:
                text = tpl

            records.append({
                "text": text,
                "category": cat_name,
                "is_illegal": 1,
                "template_origin": "NOVEL_HELD_OUT_BENCHMARK"
            })

    # Benign novel samples
    for _ in range(count_per_category * 2): # 100 benign
        tpl = rng.choice(NOVEL_BENIGN_TEMPLATES)
        city = rng.choice(CITIES)
        bank = rng.choice(BANKS)
        text = tpl.format(city=city, bank=bank)
        records.append({
            "text": text,
            "category": "benign",
            "is_illegal": 0,
            "template_origin": "NOVEL_HELD_OUT_BENCHMARK"
        })

    rng.shuffle(records)
    return records


def main():
    records = generate_novel_dataset(count_per_category=50)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Generated {len(records)} novel held-out records into {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
