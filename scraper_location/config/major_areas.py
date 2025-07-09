import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def flatten(nested_list):
    return [item[0] for item in nested_list]

def load_json(filename):
    path = os.path.join(BASE_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return flatten(json.load(f))

KECAMATAN_SURABAYA = load_json("daftar_kecamatan_surabaya.json")
KECAMATAN_SIDOARJO = load_json("daftar_kecamatan_sidoarjo.json")
KELURAHAN_SURABAYA = load_json("daftar_kelurahan_surabaya.json")
KELURAHAN_SIDOARJO = load_json("daftar_kelurahan_sidoarjo.json")

MAJOR_AREAS = {
    "kota": ["surabaya", "sidoarjo"],

    "surabaya": {
        "kecamatan": KECAMATAN_SURABAYA,
        "kelurahan": KELURAHAN_SURABAYA,
    },
    "sidoarjo": {
        "kecamatan": KECAMATAN_SIDOARJO,
        "kelurahan": KELURAHAN_SIDOARJO,
    },
}
