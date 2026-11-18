def make_title(item):
    # Never infer missing details. User verifies all values before approval.
    parts = [item.brand, item.item_type, item.gender, item.size, item.colour, item.keywords]
    return " ".join(str(part).strip() for part in parts if part and str(part).strip())[:80].rstrip()
