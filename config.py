BRANDS = [
    "RYZE Superfoods",
    "IM8 Health",
    "WildMint Cosmetics",
    "Sven's Island Kitsch",
    "Norse Organics",
    "Dr. Emmy",
    "Froya",
    "Best Dental Advice",
    "Coco and Eve",
    "Lalueur",
    "Feroldis",
    "Markt",
]

FILTERS = {
    "ad_reached_countries": ["US", "GB", "AU", "CA", "NZ", "IE", "ZA", "NG", "IN", "SG", "PH", "MY"],  # major English-speaking markets
    "languages": ["en"],               # English
    "ad_active_status": "ALL",         # active + inactive
    "ad_type": "ALL",
    "media_type": "ALL",
}

FIELDS = [
    "id",
    "page_name",
    "page_id",
    "ad_creation_time",
    "ad_delivery_start_time",
    "ad_delivery_stop_time",
    "ad_creative_bodies",
    "ad_creative_link_titles",
    "ad_creative_link_descriptions",
    "ad_creative_link_captions",
    "ad_snapshot_url",
    "publisher_platforms",
    "impressions",
    "spend",
    "currency",
    "demographic_distribution",
    "target_ages",
    "target_gender",
]

META_API_VERSION = "v21.0"
META_API_BASE = f"https://graph.facebook.com/{META_API_VERSION}/ads_archive"
PAGE_LIMIT = 50  # ads per page (max 100)
