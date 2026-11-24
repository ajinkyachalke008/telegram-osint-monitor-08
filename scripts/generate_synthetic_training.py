"""Synthetic Training Data Generator for OSINT Illegal Trade Classifier.

Generates realistic, safe, and synthetic training examples for:
- 7 illegal trade categories: drugs, arms, fake_documents, bank_account, atm_card, sim_card, net_banking_kit (>=320 examples each)
- Hard benign negatives: bank notices, pharmacy ads, shooting sports/airsoft, news headlines, general classifieds (>=650 examples)

All contact details and handles are strictly fake (e.g. 90000 00000, demo.seller@ybl).
No instructions on weapon or narcotic synthesis are ever generated.
"""
import json
import random
from pathlib import Path
from typing import List, Dict, Any

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "train_synthetic.jsonl"

# Procedural templates per category
DRUG_TEMPLATES = [
    "Fresh stock of {substance} available in {city}. High quality, door delivery. DM @demo_seller or ping 90000 {num}.",
    "Pure {substance} available {emoji}. Discreet packaging, cash on delivery or crypto accepted. Contact @demo_{substance}dealer.",
    "Best rate {substance} in {city}. Bulk discount available for party orders. Telegram @dealer_{num}.",
    "Looking for {substance}? Available in {city} with discreet courier service {emoji}. Pay via UPI demo.{num}@ybl.",
    "{slang} available now! Direct from source, pure quality {substance}. DM for menu @fast_delivery_{num} {emoji}.",
    "Party stuff available in {city}! {substance} and {slang}. Instant drop in 2 hours. WhatsApp 91000 {num}.",
    "Special discount on {substance} {emoji}. Safe delivery, stealth packing. Contact @trusted_{substance}_{num}.",
    "High quality {slang} ready for delivery. Cashless payments preferred {emoji}. DM @clean_drop_{num}.",
    "Best {substance} available in {city}. Trusted vendor with 500+ reviews. Ping @express_deal_{num}.",
    "A-grade {substance} and {slang} in stock. Fast shipping pan-India. Contact @vendor_{city}_{num} {emoji}."
]

SUBSTANCES = [
    ("mdma", "💊", "meow meow"), ("weed", "🌿", "og kush"), ("charas", "🍁", "maal"),
    ("cocaine", "❄️", "white powder"), ("mephedrone", "🧪", "chitta"), ("heroin", "💉", "smack"),
    ("lsd", "🍄", "acid stamp"), ("meth", "🧊", "crystal ice"), ("ganja", "🚬", "stuff"),
    ("tramadol", "💊", "nasheeli goli"), ("ketamine", "🧪", "k powder"), ("alprazolam", "💊", "sleep pills")
]

ARMS_TEMPLATES = [
    "New {weapon} available with {ammo} rounds in {city}. Tested piece, heavy sound. DM @arms_dealer_{num}.",
    "Original {weapon} in fresh condition. Ready delivery pan-India {emoji}. Payment after video verification. Contact @weapon_hub_{num}.",
    "Looking for {weapon}? Country made and imported pieces in stock in {city}. Ping 92000 {num}.",
    "Fresh lot of {weapon} and {ammo} bore ammunition {emoji}. Safe hand-to-hand delivery available. DM @safety_first_{num}.",
    "Brand new {weapon} with {ammo} bullets. Urgent sale in {city}. Contact @iron_stock_{num}.",
    "{weapon} for sale, fully working condition with extra magazine. DM @silent_vendor_{num} {emoji}.",
    "Imported {weapon} and desi {weapon} available. Quality assured. Telegram @defense_deals_{num}.",
    "Heavy sound {weapon} in {city}. Direct meeting or parcel {emoji}. Ping @fire_arms_{num}.",
    "Stock clearance: {weapon} with {ammo} cartridge box. Safe delivery guaranteed. Contact 93000 {num}.",
    "{weapon} available for security purpose. No papers required. Urgent deal in {city} {emoji}."
]

WEAPONS = [
    ("pistol", "9mm", "🔫"), ("revolver", "32 bore", "💥"), ("glock", "9mm", "🔫"),
    ("country made pistol", "315 bore", "💣"), ("desi katta", "12 bore", "💥"),
    ("rifle", "7.65mm", "🎯"), ("air pistol modified", "pellets", "⚡"), ("tamancha", "315 bore", "🔥")
]

FAKE_DOCS_TEMPLATES = [
    "Urgent {doc} required? We make 100% genuine looking {doc} with online verification {emoji}. DM @doc_maker_{num}.",
    "Get instant {doc} in 24 hours. Valid for all official submissions in {city}. Contact @fast_docs_{num}.",
    "Original format {doc} and degree certificates. With watermark and QR code {emoji}. WhatsApp 94000 {num}.",
    "Need duplicate {doc} urgently? Backdated entries available. DM @easy_docs_service_{num}.",
    "High quality replica {doc} for loan and KYC purpose. 100% pass guarantee. Contact @kyc_bypass_{num} {emoji}.",
    "Custom {doc} printing with scannable barcode and chip. Delivery in {city}. Ping @print_master_{num}.",
    "Instant {doc} making service. No documents needed, just send photo. Telegram @instant_id_{num}.",
    "Get your {doc} ready without going to office. 100% safe and confidential {emoji}. Call 95000 {num}.",
    "Backdated university degree and {doc} with online marksheets. Contact @degree_pro_{num}.",
    "Genuine stamp and hologram {doc} available. Pan-India courier. DM @stamp_master_{num} {emoji}."
]

DOCS = [
    ("aadhar card", "📄"), ("pan card", "💳"), ("driving license", "🚗"),
    ("passport", "🛂"), ("voter id", "🗳️"), ("university degree", "🎓"),
    ("experience certificate", "📜"), ("salary slip", "💵"), ("rent agreement", "🏠")
]

BANK_ACCOUNT_TEMPLATES = [
    "Fresh {account_type} bank account available for rent/sale in {bank}. Fully active with netbanking and ATM kit {emoji}. DM @bank_hub_{num}.",
    "High limit {account_type} account in {bank}. Daily 10L+ transaction capacity without hold. Contact @fin_deals_{num}.",
    "Looking for {account_type} accounts for gaming/crypto transactions? Daily rent basis available {emoji}. WhatsApp 96000 {num}.",
    "Ready {bank} corporate current account with corporate netbanking and cheque book. Urgent deal in {city}. DM @corp_acc_{num}.",
    "Need {bank} savings account for 2-3 days rent? Attractive commission per transaction {emoji}. Contact @fast_rent_{num}.",
    "Available {account_type} accounts in {bank}. Clean KYC, zero chargeback. DM @account_pool_{num}.",
    "Fresh KYC done {bank} account for crypto P2P. No dispute guarantee. Ping @p2p_accounts_{num}.",
    "Sell your idle {bank} bank account and earn daily commission of 10,000 INR {emoji}. Contact @money_rent_{num}.",
    "Corporate and individual {account_type} bank accounts for high volume load. Available in {city}. Call 97000 {num}.",
    "Ready-to-use {bank} {account_type} account with active mobile banking and email access. DM @direct_bank_{num} {emoji}."
]

ACCOUNTS = [
    ("savings", "HDFC"), ("current", "ICICI"), ("corporate current", "Axis"),
    ("savings", "SBI"), ("current", "Kotak"), ("high-limit current", "Yes Bank"),
    ("savings", "Canara"), ("current", "IndusInd")
]

ATM_CARD_TEMPLATES = [
    "Brand new {bank} ATM debit card with PIN and welcome kit available. Daily withdrawal limit 1 Lakh {emoji}. DM @atm_supply_{num}.",
    "Selling active ATM card of {bank} with full credentials. Ready to swipe pan-India. Contact @card_hub_{num}.",
    "Need ATM card for cashout? High limit debit cards available with OTP forwarding {emoji}. WhatsApp 98000 {num}.",
    "Multiple {bank} ATM cards available for rent. High commission paid for daily usage. Ping @cashout_cards_{num}.",
    "Pre-activated debit card with physical plastic and ATM PIN. Delivered to {city} {emoji}. DM @card_express_{num}.",
    "{bank} Platinum debit card with international usage enabled. Ready delivery. Telegram @card_master_{num}.",
    "ATM card + netbanking combo for rent. Instant dispatch with tracking. Contact @swift_card_{num} {emoji}.",
    "Fresh ATM debit cards with 2 Lakh daily ATM withdrawal limit. Safe and clean. DM @atm_king_{num}.",
    "Bulk supply of {bank} debit cards with complete PIN and kits. Serious buyers only. Call 99000 {num}.",
    "Looking for {bank} ATM cards for remittance cashout. Instant commission. DM @cash_desk_{num} {emoji}."
]

SIM_CARD_TEMPLATES = [
    "Pre-activated {operator} SIM cards available in {city}. Pre-KYC completed, ready to use immediately {emoji}. DM @sim_vendor_{num}.",
    "Bulk {operator} SIM cards without personal ID. OTP verification ready. Contact @otp_sim_{num}.",
    "Fake KYC {operator} SIM cards for Telegram and WhatsApp creation. 100% active {emoji}. WhatsApp 91100 {num}.",
    "Need ready SIM cards for calling and SMS? {operator} SIMs available in stock. DM @sim_point_{num}.",
    "Pre-activated 4G/5G {operator} SIM cards delivered in {city}. Cash on delivery available. Ping @fast_sims_{num} {emoji}.",
    "Bulk pack of 50 {operator} SIM cards for marketing and verification. Cheap rates. Telegram @bulk_sim_{num}.",
    "Pre-KYC done {operator} SIM cards with 3 months validity. No paperwork required {emoji}. Contact @sim_hub_{num}.",
    "Buy pre-activated {operator} SIM card for international accounts. Instant dispatch to {city}. Call 91200 {num}.",
    "Ready-to-use {operator} SIM for OTP services. High delivery rate. DM @quick_otp_{num} {emoji}.",
    "Clean {operator} SIM cards in bulk with active outgoing and incoming. Contact @sim_distributor_{num}."
]

OPERATORS = ["Airtel", "Jio", "Vodafone Vi", "BSNL"]

NET_BANKING_KIT_TEMPLATES = [
    "Complete net banking kit of {bank} for sale: User ID, password, registered SIM, and ATM card {emoji}. DM @kit_supplier_{num}.",
    "Full corporate netbanking kit with maker-checker tokens and physical cheque book in {bank}. Contact @corp_kit_{num}.",
    "Ready net banking kit with active SIM and OTP forwarding bot. 100% smooth transactions in {city}. WhatsApp 91300 {num} {emoji}.",
    "Selling fresh {bank} net banking kit. All credentials included, ready for immediate login. DM @kit_deals_{num}.",
    "Full kit available: {bank} savings account + Netbanking credentials + ATM card + Pre-activated SIM card {emoji}. Telegram @full_kit_{num}.",
    "High limit net banking kit of {bank} for high volume load. Zero dispute guaranteed. Ping @heavy_kit_{num}.",
    "Net banking kit + registered SIM available for rent on 10% commission. DM @rent_kit_{num} {emoji}.",
    "Complete {bank} digital banking kit delivered securely to {city}. Tested and active. Call 91400 {num}.",
    "Pre-packaged net banking kit with debit card and active SIM for gaming/P2P load. Contact @p2p_kit_{num} {emoji}.",
    "Fresh {bank} netbanking access with security questions, debit card, and token device. DM @secure_kit_{num}."
]

BENIGN_TEMPLATES = [
    # Legit bank security notices
    "SECURITY ALERT: {bank} never asks for your OTP, Netbanking password, UPI PIN, or CVV. Beware of fraudsters offering fake loans or account rentals.",
    "Official Notice from {bank}: Update your KYC by visiting your nearest branch with original Aadhaar card and PAN card. Do not click on unknown links.",
    "FRAUD WARNING: Please note that renting or selling your bank account or ATM card is illegal under PMLA and RBI guidelines. Report suspicious callers to 1930.",
    "Important advisory for {bank} customers: Enable two-factor authentication on your mobile banking app. Never share debit card PIN with anyone.",
    "RBI Public Awareness Notice: Do not fall for mule account recruitment schemes on social media promising easy commission. It leads to legal prosecution.",
    "Dear customer, your {bank} account statement for the month has been sent to your registered email. Check transactions regularly.",
    "Advisory: Always lock your debit card via mobile app when traveling internationally to prevent unauthorized transactions.",
    "Public Service Announcement: Fraudsters are using fake SMS for electricity bill payments. Verify only through official state electricity portals.",
    "RBI Guidelines: Reporting unauthorized banking transactions within 3 days ensures zero liability for customer. Save national cybercrime helpline 1930.",
    "Security Tip: Memorize your ATM card PIN and never write it on the back of the card or share it via WhatsApp.",
    
    # Legit pharmacies and medical notices
    "Apollo Pharmacy Health Tip: Paracetamol and cough syrup should only be taken as per doctor prescription. Visit our licensed counter in {city}.",
    "MedPlus Reminder: Carry a valid doctor prescription for scheduled drugs and antibiotics. Self-medication is hazardous to health.",
    "Government Health Notice: Free vaccination and diabetic screening camp in {city} civil hospital this Sunday. Free generic medicines available.",
    "Jan Aushadhi Kendra offers affordable quality medicines. Paracetamol, vitamins, and antacids at 80% discounted rates with valid prescription.",
    "Doctor consultation available at City Clinic {city}: Expert diagnosis for chronic pain and fever. Medicines dispensed only against licensed prescriptions.",
    "Health Advisory: Beware of spurious drugs online. Always purchase medicines from state-licensed registered pharmacies with valid tax invoice.",
    "Ayurvedic wellness center in {city}: Natural herbal supplements, ashwagandha, and pure triphala churna available for immunity boosting.",
    "Hospital Bulletin: Blood donation camp organized in {city} on national health day. Join us to save lives.",

    # Shooting sports, airsoft, martial arts
    "State Rifle Shooting Championship announced for 10m air rifle and air pistol in {city}. Registration open for certified junior athletes.",
    "Airsoft and Paintball tactical arena opens in {city}! Book weekend slots for team adventure games. Equipment and safety gear provided on site.",
    "National Shooting Federation trials: 50m rifle 3 positions and 25m rapid fire pistol trials schedule published for national games.",
    "Target shooting practice session at National Sports Academy. Licensed air pellets and safety goggles available in the pro shop.",
    "Martial arts and self-defense workshop for women in {city} this Saturday. Learn situational awareness and certified unarmed defense techniques.",
    
    # News headlines and crime reports
    "News Flash: Police in {city} busted an interstate gang involved in selling forged documents and fake certificates. Accused sent to judicial custody.",
    "Crime Desk: Cyber police freeze 40 mule bank accounts linked to investment scams across three states. Investigations underway.",
    "Special Task Force seized contraband drugs near highway checkpoint in {city}. Kingpin arrested under NDPS Act.",
    "Editorial: Strengthening digital surveillance to curb cybercrime and fake SIM card syndicates operating near interstate borders.",
    "Press Release: Local administration conducts surprise inspection of illegal stamp paper vendors near district court.",
    "Legal update: High Court denies bail to cyber fraud kingpin running illegal call centers and banking mule networks.",

    # General classifieds
    "2 BHK semi-furnished apartment for rent in {city}, prime location near metro station. Family preferred. Contact owner at 90111 22233.",
    "Pre-owned Honda City 2021 model for sale in {city}. Single owner, comprehensive insurance, regular company service. Call for inspection.",
    "Experienced mathematics and science tutor available for CBSE class 10 and 12 in {city}. Small batches and personal attention.",
    "Used office furniture and wooden workstations for sale at reasonable price. Available for immediate pickup in industrial estate.",
    "Software Engineer opening at reputed tech firm in {city}. Skills: Python, React, PostgreSQL. Send resume to careers@company-example.com.",
    "Wedding photography and cinematic videography package discounts available for upcoming festive season in {city}."
]

CITIES = ["Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Pune", "Jaipur", "Kolkata", "Ahmedabad", "Chandigarh", "Lucknow", "Indore", "Surat"]
BANKS = ["HDFC", "SBI", "ICICI", "Axis Bank", "Kotak Mahindra", "Punjab National Bank", "Canara Bank", "Bank of Baroda"]


def generate_dataset(min_per_illegal: int = 330, min_benign: int = 680) -> List[Dict[str, Any]]:
    records = []
    rng = random.Random(42)

    categories_config = [
        ("drugs", DRUG_TEMPLATES, 1),
        ("arms", ARMS_TEMPLATES, 1),
        ("fake_documents", FAKE_DOCS_TEMPLATES, 1),
        ("bank_account", BANK_ACCOUNT_TEMPLATES, 1),
        ("atm_card", ATM_CARD_TEMPLATES, 1),
        ("sim_card", SIM_CARD_TEMPLATES, 1),
        ("net_banking_kit", NET_BANKING_KIT_TEMPLATES, 1)
    ]

    for cat_name, templates, is_illegal in categories_config:
        count = 0
        while count < min_per_illegal:
            tpl = rng.choice(templates)
            city = rng.choice(CITIES)
            num = f"{rng.randint(10000, 99999)}"
            bank = rng.choice(BANKS)

            if cat_name == "drugs":
                sub, emoji, slang = rng.choice(SUBSTANCES)
                text = tpl.format(substance=sub, emoji=emoji, slang=slang, city=city, num=num)
            elif cat_name == "arms":
                weapon, ammo, emoji = rng.choice(WEAPONS)
                text = tpl.format(weapon=weapon, ammo=ammo, emoji=emoji, city=city, num=num)
            elif cat_name == "fake_documents":
                doc, emoji = rng.choice(DOCS)
                text = tpl.format(doc=doc, emoji=emoji, city=city, num=num)
            elif cat_name == "bank_account":
                acc_type, bank_name = rng.choice(ACCOUNTS)
                emoji = rng.choice(["💳", "💰", "🏦", "🚀"])
                text = tpl.format(account_type=acc_type, bank=bank_name, city=city, num=num, emoji=emoji)
            elif cat_name == "atm_card":
                emoji = rng.choice(["💳", "🏧", "💸", "✅"])
                text = tpl.format(bank=bank, city=city, num=num, emoji=emoji)
            elif cat_name == "sim_card":
                op = rng.choice(OPERATORS)
                emoji = rng.choice(["📲", "📶", "⚡", "🔥"])
                text = tpl.format(operator=op, city=city, num=num, emoji=emoji)
            elif cat_name == "net_banking_kit":
                emoji = rng.choice(["💼", "🔐", "🏧", "💰"])
                text = tpl.format(bank=bank, city=city, num=num, emoji=emoji)
            else:
                text = tpl

            # Add minor variations or obfuscations occasionally
            if rng.random() < 0.25:
                # Add a fake telegram handle or dummy phone
                text += f" Contact @demo_{cat_name}_{num}."

            records.append({
                "text": text,
                "category": cat_name,
                "is_illegal": 1,
                "provenance": "SIMULATED"
            })
            count += 1

    # Benign examples
    benign_count = 0
    while benign_count < min_benign:
        tpl = rng.choice(BENIGN_TEMPLATES)
        city = rng.choice(CITIES)
        bank = rng.choice(BANKS)
        text = tpl.format(city=city, bank=bank)

        records.append({
            "text": text,
            "category": "benign",
            "is_illegal": 0,
            "provenance": "SIMULATED"
        })
        benign_count += 1

    rng.shuffle(records)
    return records


def main():
    records = generate_dataset(min_per_illegal=330, min_benign=700)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Generated {len(records)} synthetic records into {OUTPUT_PATH}")
    
    # Class distribution report
    dist: Dict[str, int] = {}
    for r in records:
        dist[r["category"]] = dist.get(r["category"], 0) + 1
    for k, v in dist.items():
        print(f"  - {k}: {v}")


if __name__ == "__main__":
    main()
