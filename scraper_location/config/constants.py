# Keyword yang digunakan di berbagai tempat
WHITELIST_ACTIONS = {"ditutup", "penutupan", "pengalihan", "macet", "terhambat", "tersendat", "padat","merambat","lambat"}
BLACKLIST_WORDS = {"arisan", "pengajian", "ulang tahun", "rapat", "pkk"}
DIRECTION_WORDS = ["dari", "ke", "menuju", "arah","sampai"]
LOCATION_KEYWORDS = {"jalan", "tol", "raya", "exit", "jl", "bundaran"}
IGNORED_LOCATION_TOKENS = {"di", ".", ":", ",", ";","mulai", "ke", "ini", "L","saat"}
IGNORED_ENTITY_PHRASES = {"pendengar ss","agus pendengar ss", "yoyok pendengar ss", "pendengar suara surabaya", "alvonsus pendengar ss", "ss"}
CONTEXT_KEYWORDS = {
    "jalan", "jl.", "jl", "tol", "exit", "gate", "gerbang",
    "layang", "simpang", "persimpangan", "putar", "u-turn",
    "arah", "menuju", "raya", "akses", "jembatan",
    "km", "km.", "perempatan", "bundaran",
    "lokasi", "depan", "belakang", "sekitar",
    "traffic", "macet", "penutupan", "pengalihan", "dari", "ke","sampai"
}
TRAFFIC_SUFFIXES = {"macet", "padat", "lancar"}
GOOD_TYPES = {"route", "street_address", "intersection", "administrative_area_level_4","administrative_area_level_3"}