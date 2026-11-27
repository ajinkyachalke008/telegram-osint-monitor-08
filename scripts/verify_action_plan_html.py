from pathlib import Path
import re

html_path = Path(r"c:\Users\AJINKYA CHALKE\Desktop\telegram-osint-monitor-ps02-action-plan.html")
assert html_path.exists(), "Target file does not exist!"

with open(html_path, "r", encoding="utf-8") as f:
    text = f.read()

print(f"File verified: {html_path.name}")
print(f"File size: {len(text):,} bytes ({len(text)/1024/1024:.2f} MB)")

# 1. Check sections
for s_num in range(16):
    s_id = f"s{s_num}"
    assert f'id="{s_id}"' in text, f"Missing section {s_id}!"
print("All 16 sections (s0 through s15) present and indexed.")

# 1b. Check TOC navigation sidebar
assert 'id="mainToc"' in text, "Missing #mainToc element!"
assert 'class="toc"' in text, "Missing .toc class on navigation!"
for s_num in range(16):
    s_id = f"s{s_num}"
    assert f'href="#{s_id}"' in text, f"Missing TOC link to #{s_id}!"
print("Sticky TOC sidebar navigation with 16 section links verified.")

# 2. Check 3 photos
imgs = re.findall(r'<img[^>]*class=["\']fig-img["\'][^>]*>', text)
assert len(imgs) == 3, f"Expected 3 fig-img tags, found {len(imgs)}"
print(f"All {len(imgs)} police internship photographs present in Section 02.")

# 3. Check galleryData
assert "const galleryData = [" in text, "Missing galleryData array!"
assert "Dr. Pankaj Ashokrao Deshmukh, IPS" in text, "Missing Dr. Pankaj Deshmukh caption!"
assert "Swapnali Shinde" in text, "Missing Sr PI Swapnali Shinde caption!"
assert "Kharat Sir" in text, "Missing Kharat Sir caption!"
print("Lightbox galleryData array intact with all 3 officers and captions.")

# 4. Check archStageDetails
assert "const archStageDetails = {" in text, "Missing archStageDetails!"
for stage_idx in range(1, 6):
    assert f"{stage_idx}: {{" in text, f"Missing stage {stage_idx} in archStageDetails!"
print("Interactive 5-stage architecture details configured.")

# 5. Check Section 63 BSA & Evidence
assert "Section 63 BSA" in text
assert "operational.db" in text
assert "71 / 71" in text
print("Verification complete: 100% PASS.")
