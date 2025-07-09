def filter_segments_for_closure_only(step2_result: dict):
    """
    Filter: keep only closure pairs.
    - If sentence is pure closure: keep pair as is.
    - If sentence is mixed closure + redirection: convert to single_location.
    - If sentence is pure redirection: skip.
    """
    segments = []
    singles = []

    for seg in step2_result["segments"]:
        sentence = seg["sentence"].lower()
        is_closure = any(kw in sentence for kw in ["penutupan", "penyekatan", "blokir", "ditutup"])
        is_redir = any(kw in sentence for kw in ["dialihkan", "pengalihan", "via", "melalui"])

        if is_closure and not is_redir:
            segments.append(seg)

        elif is_closure and is_redir:
            # Mixed: keep 'from' as single closure location
            single = {
                "location": seg["from"],
                "reason": "closure from mixed",
                "sentence": seg["sentence"]
            }
            singles.append(single)

        # else: pure redirection ➜ skip

    # Keep fallback singles from step2 too
    singles += step2_result.get("single_locations", [])

    return {
        "segments": segments,
        "single_locations": singles
    }
