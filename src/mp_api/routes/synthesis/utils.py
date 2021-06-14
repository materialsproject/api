import re


def make_ellipsis(text, limit=100, remove_trailing=True):
    if len(text) > limit:
        if remove_trailing:
            text = text[:limit]
            # Make results nicer by cutting incomplete words of max 15 characters.
            # For example: "This is an incomplete sente" becomes "This is an incomplete "
            trailing = re.search(r"(?<![\w\d])[\w\d]{,15}$", text)
            if trailing is not None:
                text = text[: trailing.start()] + "..."
        else:
            text = text[len(text) - limit :]
            heading = re.search(r"^[\w\d]{,15}(?![\w\d])", text)
            if heading is not None:
                text = "..." + text[heading.end() :]
    return text


def mask_paragraphs(doc, limit=100):
    if isinstance(doc.get("paragraph_string", None), str):
        doc["paragraph_string"] = make_ellipsis(doc["paragraph_string"], limit=limit)

    return doc


def mask_highlights(doc, limit=100):
    if isinstance(doc.get("highlights", None), list):
        total_chars = 0
        show_hl = []

        for h_obj in doc["highlights"]:
            if total_chars >= limit:
                break
            hls = h_obj["texts"]

            # Identify where the highlighting starts.
            for i, hl in enumerate(hls):
                if hl["type"] == "hit":
                    if i > 0:
                        hls[i - 1]["value"] = make_ellipsis(
                            hls[i - 1]["value"], limit=20, remove_trailing=False
                        )
                        hls = hls[i - 1 :]
                    break

            # Remove excessive chars after the hit.
            for i, hl in enumerate(hls):
                total_chars += len(hl["value"])
                if total_chars >= limit:
                    hl_limit = max(1, limit - (total_chars - len(hl["value"])))
                    hl["value"] = make_ellipsis(hl["value"], limit=hl_limit)
                    hls = hls[: i + 1]
                    break
            h_obj["texts"] = hls
            show_hl.append(h_obj)

        doc["highlights"] = show_hl

    return doc
