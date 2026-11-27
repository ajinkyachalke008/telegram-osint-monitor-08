"""Repeated-Ad and Coordinated Campaign Detection.

Identifies coordinated criminal marketing across channels:
1. Text Similarity: MinHash (datasketch) with Jaccard distance clustering to detect
   coordinated ad templates, copy-paste spam, and templated mule recruitment ads.
2. Image Similarity: Perceptual Hash (imagehash pHash) with Hamming distance thresholding
   to group duplicate payment screenshots, QR code posters, and flyer variants.
"""
import re
from typing import List, Dict, Any, Tuple, Optional, Union
from collections import defaultdict
from pathlib import Path

try:
    from datasketch import MinHash, MinHashLSH
    DATASKETCH_AVAILABLE = True
except ImportError:
    DATASKETCH_AVAILABLE = False

try:
    import imagehash
    from PIL import Image
    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False


def clean_text_for_similarity(text: str) -> str:
    """Normalize text by stripping links, usernames, and whitespace for template comparison."""
    if not text:
        return ""
    # Remove URLs and @usernames to focus on the marketing template itself
    t = re.sub(r"https?://\S+", "", text)
    t = re.sub(r"@[A-Za-z0-9_]+", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip().lower()


def text_to_shingles(text: str, k: int = 3) -> set:
    """Create word or character 3-grams for Jaccard similarity."""
    cleaned = clean_text_for_similarity(text)
    words = cleaned.split()
    if len(words) < k:
        # Fall back to character 3-grams
        return {cleaned[i:i+k] for i in range(max(1, len(cleaned) - k + 1))}
    return {" ".join(words[i:i+k]) for i in range(len(words) - k + 1)}


def compute_minhash(text: str, num_perm: int = 128) -> Optional[Any]:
    """Compute MinHash signature for text."""
    if not DATASKETCH_AVAILABLE:
        return None
    shingles = text_to_shingles(text)
    if not shingles:
        return None
    m = MinHash(num_perm=num_perm)
    for s in shingles:
        m.update(s.encode("utf-8"))
    return m


def find_text_ad_clusters(posts: List[Dict[str, Any]], threshold: float = 0.65) -> List[Dict[str, Any]]:
    """
    Cluster posts sharing similar ad copy across channels using MinHash.
    Returns list of clusters with duplicate counts, channels involved, and matched text.
    """
    if not posts:
        return []

    # Filter posts with substantial text
    valid_posts = [p for p in posts if len(clean_text_for_similarity(p.get("text", ""))) >= 20]
    if len(valid_posts) < 2:
        return []

    clusters = []
    visited = set()

    if DATASKETCH_AVAILABLE:
        # Precompute minhashes
        minhashes = {}
        for idx, p in enumerate(valid_posts):
            mh = compute_minhash(p.get("text", ""))
            if mh is not None:
                minhashes[idx] = mh

        # Pairwise clustering (for hackathon dataset sizes this is fast and deterministic)
        for i in range(len(valid_posts)):
            if i in visited or i not in minhashes:
                continue

            current_cluster = [valid_posts[i]]
            visited.add(i)

            for j in range(i + 1, len(valid_posts)):
                if j in visited or j not in minhashes:
                    continue
                sim = minhashes[i].jaccard(minhashes[j])
                if sim >= threshold:
                    current_cluster.append(valid_posts[j])
                    visited.add(j)

            if len(current_cluster) > 1:
                # Group stats
                channels = sorted(list({p.get("source", "Unknown") for p in current_cluster}))
                post_ids = [p.get("post_id") for p in current_cluster]
                # Collect identifiers
                all_upis = set()
                all_phones = set()
                for p in current_cluster:
                    ext = p.get("extracted", {})
                    all_upis.update(ext.get("upis", []))
                    all_phones.update(ext.get("phones", []))

                clusters.append({
                    "cluster_id": f"CAMP-TXT-{len(clusters)+1:03d}",
                    "ad_count": len(current_cluster),
                    "cross_channel": len(channels) > 1,
                    "channels": channels,
                    "channel_count": len(channels),
                    "shared_upis": sorted(list(all_upis)),
                    "shared_phones": sorted(list(all_phones)),
                    "sample_text": current_cluster[0].get("text", "")[:250],
                    "posts": current_cluster,
                })
    else:
        # Pure Python fallback using exact shingle Jaccard
        shingle_map = {i: text_to_shingles(p.get("text", "")) for i, p in enumerate(valid_posts)}
        for i in range(len(valid_posts)):
            if i in visited or not shingle_map[i]:
                continue
            current_cluster = [valid_posts[i]]
            visited.add(i)
            s_i = shingle_map[i]
            for j in range(i + 1, len(valid_posts)):
                if j in visited or not shingle_map[j]:
                    continue
                s_j = shingle_map[j]
                inter = len(s_i & s_j)
                union = len(s_i | s_j)
                sim = inter / union if union > 0 else 0
                if sim >= threshold:
                    current_cluster.append(valid_posts[j])
                    visited.add(j)
            if len(current_cluster) > 1:
                channels = sorted(list({p.get("source", "Unknown") for p in current_cluster}))
                clusters.append({
                    "cluster_id": f"CAMP-TXT-{len(clusters)+1:03d}",
                    "ad_count": len(current_cluster),
                    "cross_channel": len(channels) > 1,
                    "channels": channels,
                    "channel_count": len(channels),
                    "shared_upis": [],
                    "shared_phones": [],
                    "sample_text": current_cluster[0].get("text", "")[:250],
                    "posts": current_cluster,
                })

    # Sort clusters by size (largest campaigns first)
    clusters.sort(key=lambda c: c["ad_count"], reverse=True)
    return clusters


def compute_image_phash(image_path: Union[str, Path]) -> Optional[str]:
    """Compute perceptual hash (pHash) of image."""
    if not IMAGEHASH_AVAILABLE or not image_path:
        return None
    p = Path(image_path)
    if not p.exists() or not p.is_file():
        return None
    try:
        with Image.open(p) as img:
            return str(imagehash.phash(img))
    except Exception:
        return None


def find_image_clusters(posts: List[Dict[str, Any]], max_hamming_distance: int = 6) -> List[Dict[str, Any]]:
    """
    Cluster posts sharing identical or modified promotional images / QR codes.
    Uses Perceptual Hash (pHash) with Hamming distance thresholding.
    """
    if not IMAGEHASH_AVAILABLE:
        return []

    # Filter posts with images
    image_posts = []
    for p in posts:
        img_path = p.get("image_path")
        if img_path and Path(img_path).exists():
            h = compute_image_phash(img_path)
            if h:
                image_posts.append((p, h))

    if len(image_posts) < 2:
        return []

    clusters = []
    visited = set()

    for i in range(len(image_posts)):
        if i in visited:
            continue
        p_i, h_i = image_posts[i]
        hash_obj_i = imagehash.hex_to_hash(h_i)
        current_cluster = [p_i]
        visited.add(i)

        for j in range(i + 1, len(image_posts)):
            if j in visited:
                continue
            p_j, h_j = image_posts[j]
            hash_obj_j = imagehash.hex_to_hash(h_j)
            dist = hash_obj_i - hash_obj_j  # Hamming distance
            if dist <= max_hamming_distance:
                current_cluster.append(p_j)
                visited.add(j)

        if len(current_cluster) > 1:
            channels = sorted(list({p.get("source", "Unknown") for p in current_cluster}))
            clusters.append({
                "cluster_id": f"CAMP-IMG-{len(clusters)+1:03d}",
                "image_count": len(current_cluster),
                "cross_channel": len(channels) > 1,
                "channels": channels,
                "sample_image": current_cluster[0].get("image_path"),
                "sample_text": current_cluster[0].get("text", "")[:180],
                "posts": current_cluster,
            })

    clusters.sort(key=lambda c: c["image_count"], reverse=True)
    return clusters



def find_exact_image_clusters(posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group posts that reference byte-identical media by SHA-256."""
    groups = defaultdict(list)
    for post in posts:
        media_hash = str(post.get('media_hash') or '').strip().lower()
        if len(media_hash) == 64 and all(ch in '0123456789abcdef' for ch in media_hash):
            groups[media_hash].append(post)
    results = []
    for media_hash, matches in groups.items():
        if len(matches) < 2:
            continue
        channels = sorted({str(post.get('source') or 'Unknown') for post in matches})
        results.append({
            'cluster_id': f'CAMP-SHA-{len(results) + 1:03d}',
            'sha256': media_hash,
            'post_count': len(matches),
            'channels': channels,
            'cross_channel': len(channels) > 1,
            'sample_image': next((post.get('image_path') for post in matches if post.get('image_path')), None),
            'posts': matches,
        })
    results.sort(key=lambda item: item['post_count'], reverse=True)
    return results
