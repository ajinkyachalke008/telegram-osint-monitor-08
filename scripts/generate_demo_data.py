"""Seeded Demo Dataset Generator for Hackathon Evaluation.

Generates realistic, completely fake demonstration datasets:
- 12 distinct simulated channels
- Cross-channel syndicates (same fake UPI/Phone operating in multiple channels)
- Coordinated ad copy (for MinHash clustering)
- Sample PIL flyer images for image duplicate clustering
- JSON and CSV output under sample_data/
"""
import os
import json
import csv
import random
from pathlib import Path
from typing import List, Dict, Any

from PIL import Image, ImageDraw, ImageFont

SAMPLE_DATA_DIR = Path(__file__).resolve().parent.parent / "sample_data"
SAMPLE_IMAGES_DIR = SAMPLE_DATA_DIR / "demo_images"


def generate_flyer_image(filename: str, title: str, subtitle: str, color: tuple):
    SAMPLE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (400, 200), color=color)
    draw = ImageDraw.Draw(img)
    # Simple bounding boxes and text
    draw.rectangle([10, 10, 390, 190], outline=(255, 255, 255), width=3)
    draw.text((25, 40), title, fill=(255, 255, 255))
    draw.text((25, 90), subtitle, fill=(255, 255, 200))
    draw.text((25, 140), "TEST SYNTHETIC DEMO ONLY", fill=(200, 200, 200))
    path = SAMPLE_IMAGES_DIR / filename
    img.save(path)
    return str(path)


def generate_demo_dataset():
    SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(1337)

    # Generate 3 fake flyer images (2 similar, 1 distinct)
    img1 = generate_flyer_image("ad_flyer_1.png", "BANK ACCOUNTS AVAILABLE", "COMMISSION 10%", (30, 60, 120))
    img2 = generate_flyer_image("ad_flyer_2.png", "BANK ACCOUNTS AVAILABLE", "COMMISSION 10%", (30, 60, 125)) # duplicate
    img3 = generate_flyer_image("ad_flyer_3.png", "FAST DELIVERY PAN INDIA", "CONTACT DEMO DEALER", (120, 40, 40))

    # Shared Cross-Channel Actors (Obviously fake)
    SHARED_UPI_1 = "mule.syndicate@ybl"
    SHARED_PHONE_1 = "90000 11111"
    SHARED_WALLET_1 = "TYDzsYUEHG1AwueRyNng69nsT5Dn3URPUS" # valid checksum mock
    SHARED_USER_1 = "@fast_cash_hub"

    SHARED_UPI_2 = "escrow.demo@okhdfcbank"
    SHARED_PHONE_2 = "90000 22222"

    channels = [
        "t.me/delhi_classifieds_demo",
        "t.me/mumbai_trade_network",
        "t.me/p2p_banking_hub_fake",
        "t.me/mule_accounts_market",
        "t.me/fast_docs_india_demo",
        "t.me/arms_classifieds_sim",
        "t.me/crypto_cashout_pune",
        "t.me/jaipur_classifieds_sim",
        "t.me/bengaluru_tech_deals",
        "t.me/hyderabad_fast_service",
        "t.me/kolkata_bazaar_demo",
        "t.me/gujarat_merchants_sim"
    ]

    records = []

    # 1. Coordinated Cross-Channel Mule Syndicate Campaign (Posts 1 - 4 across 3 channels)
    template_ad_1 = "Fresh ICICI current account and ATM card available for rent. High limit load, zero dispute. Commission 15% daily. Ping {user} or UPI {upi} or Call {phone}."
    
    records.append({
        "platform": "telegram",
        "source": channels[0],
        "post_id": "1001",
        "timestamp": "2026-11-20T10:00:00Z",
        "text": template_ad_1.format(user=SHARED_USER_1, upi=SHARED_UPI_1, phone=SHARED_PHONE_1),
        "image_path": img1,
        "category": "bank_account",
        "provenance": "SIMULATED"
    })
    records.append({
        "platform": "telegram",
        "source": channels[1],
        "post_id": "2001",
        "timestamp": "2026-11-20T10:15:00Z",
        "text": template_ad_1.format(user=SHARED_USER_1, upi=SHARED_UPI_1, phone=SHARED_PHONE_1),
        "image_path": img2, # duplicate image
        "category": "bank_account",
        "provenance": "SIMULATED"
    })
    records.append({
        "platform": "telegram",
        "source": channels[3],
        "post_id": "3001",
        "timestamp": "2026-11-20T11:00:00Z",
        "text": f"Rent your idle HDFC or Axis bank khata. Earn daily commission of 10,000 INR. Contact {SHARED_USER_1} or UPI {SHARED_UPI_1}.",
        "image_path": None,
        "category": "bank_account",
        "provenance": "SIMULATED"
    })

    # 2. Cross-Channel Crypto Cashout Syndicate (Channels 2 and 6)
    records.append({
        "platform": "telegram",
        "source": channels[2],
        "post_id": "4001",
        "timestamp": "2026-11-21T12:00:00Z",
        "text": f"Corporate net banking kit with ATM and SIM available for crypto P2P load. USDT TRC20 deposit to {SHARED_WALLET_1}. WhatsApp {SHARED_PHONE_1}.",
        "image_path": None,
        "category": "net_banking_kit",
        "provenance": "SIMULATED"
    })
    records.append({
        "platform": "telegram",
        "source": channels[6],
        "post_id": "5001",
        "timestamp": "2026-11-21T12:30:00Z",
        "text": f"High limit corporate accounts in Axis Bank ready to swipe. Instant payout to TRC20 {SHARED_WALLET_1}. Contact @crypto_dealer_demo.",
        "image_path": None,
        "category": "bank_account",
        "provenance": "SIMULATED"
    })

    # 3. Arms & Contraband Ads with Shared Contact (Channels 5 and 7)
    records.append({
        "platform": "telegram",
        "source": channels[5],
        "post_id": "6001",
        "timestamp": "2026-11-22T14:00:00Z",
        "text": f"Country made pistol 315 bore available with 10 cartridges. Safe parcel delivery in Jaipur. Advance via UPI {SHARED_UPI_2}. Ping 90000 22222.",
        "image_path": None,
        "category": "arms",
        "provenance": "SIMULATED"
    })
    records.append({
        "platform": "telegram",
        "source": channels[7],
        "post_id": "7001",
        "timestamp": "2026-11-22T15:00:00Z",
        "text": f"32 bore revolver with brass bullets for security. Hand-to-hand deal or courier. Pay token via UPI {SHARED_UPI_2} or Call {SHARED_PHONE_2}.",
        "image_path": None,
        "category": "arms",
        "provenance": "SIMULATED"
    })

    # 4. Drugs / Narcotics Ad (Channel 4)
    records.append({
        "platform": "telegram",
        "source": channels[4],
        "post_id": "8001",
        "timestamp": "2026-11-22T16:00:00Z",
        "text": "Fresh charas and mdma pills available in Mumbai. Pure maal, door delivery in 2 hours. WhatsApp 90000 44444. Demo payment demo.drug@ybl.",
        "image_path": img3,
        "category": "drugs",
        "provenance": "SIMULATED"
    })

    # 5. Fake Documents (Channel 8)
    records.append({
        "platform": "telegram",
        "source": channels[8],
        "post_id": "9001",
        "timestamp": "2026-11-23T09:00:00Z",
        "text": "Urgent fake Aadhaar and forged PAN card in 24 hours. Scannable QR code and online verification bypass. Ping @doc_maker_demo.",
        "image_path": None,
        "category": "fake_documents",
        "provenance": "SIMULATED"
    })

    # 6. SIM Cards (Channel 9)
    records.append({
        "platform": "telegram",
        "source": channels[9],
        "post_id": "9101",
        "timestamp": "2026-11-23T10:00:00Z",
        "text": "Pre-activated Airtel and Jio SIM cards without Aadhaar. Ready to use for WhatsApp and Telegram. DM @sim_vendor_demo.",
        "image_path": None,
        "category": "sim_card",
        "provenance": "SIMULATED"
    })

    # 7. Benign Hard Negative Bank Advisory (Channel 10)
    records.append({
        "platform": "telegram",
        "source": channels[10],
        "post_id": "9201",
        "timestamp": "2026-11-23T11:00:00Z",
        "text": "SECURITY ALERT: HDFC Bank never asks for your OTP, Netbanking password, UPI PIN, or CVV. Beware of fraudsters offering fake loans or account rentals.",
        "image_path": None,
        "category": "benign",
        "provenance": "SIMULATED"
    })

    # 8. Benign Hard Negative Pharmacy (Channel 11)
    records.append({
        "platform": "telegram",
        "source": channels[11],
        "post_id": "9301",
        "timestamp": "2026-11-23T12:00:00Z",
        "text": "Apollo Pharmacy Health Notice: Paracetamol and cough syrup require a licensed doctor prescription. Visit our counter in Pune.",
        "image_path": None,
        "category": "benign",
        "provenance": "SIMULATED"
    })

    # Write JSON
    json_path = SAMPLE_DATA_DIR / "demo_multiplatform_dataset.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    # Write CSV
    csv_path = SAMPLE_DATA_DIR / "demo_dataset.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["platform", "source", "post_id", "timestamp", "text", "image_path", "category", "provenance"])
        writer.writeheader()
        for r in records:
            writer.writerow(r)

    print(f"Generated {len(records)} seeded demo records into:")
    print(f"  - {json_path}")
    print(f"  - {csv_path}")
    return records


if __name__ == "__main__":
    generate_demo_dataset()
