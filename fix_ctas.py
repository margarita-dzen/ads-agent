"""
Patch CTA fields in already-translated language JSON files.
The original translation pipeline received a corrupted EN payload (CTA truncated to 1 char),
so the model could not translate CTAs properly. This script overrides each ad's CTA with the
correct native-language version, derived from the now-correctly-parsed English source.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from translate_veins import build_source_payload

TRANS_DIR = Path("/Users/magi/Downloads/Veins New ads/translations")
EN_RAW = Path("/Users/magi/Downloads/Veins New ads/ad_copy_EN.json")

# Normalize key: treat "Try It For" and "Try It for" as the same
def normalize(s: str) -> str:
    return s.strip()

CTA_TABLE = {
    # Each row: English (normalized title-case) -> dict of language code -> translation
    "Shop Now": {
        "EN": "Shop Now",
        "BG": "Поръчай сега",
        "FR": "Acheter maintenant",
        "RO": "Cumpără acum",
        "SK": "Kúpiť teraz",
        "CZ": "Koupit nyní",
        "DE": "Jetzt kaufen",
        "IT": "Acquista ora",
        "ES": "Comprar ahora",
        "NL": "Nu kopen",
        "PT": "Comprar agora",
        "PL": "Kup teraz",
        "HU": "Vásárlás most",
        "HR": "Kupi sada",
        "SI": "Kupi zdaj",
        "RS": "Kupi sada",
    },
    "Try It for €9.99": {
        "EN": "Try It for €9.99",
        "BG": "Изпробвай за 9,99 €",
        "FR": "Essayez pour 9,99 €",
        "RO": "Încearcă pentru 9,99 €",
        "SK": "Vyskúšajte za 9,99 €",
        "CZ": "Vyzkoušejte za 9,99 €",
        "DE": "Für 9,99 € testen",
        "IT": "Provala a 9,99 €",
        "ES": "Pruébala por 9,99 €",
        "NL": "Probeer voor € 9,99",
        "PT": "Experimente por 9,99 €",
        "PL": "Wypróbuj za 9,99 €",
        "HU": "Próbáld ki 9,99 €",
        "HR": "Isprobaj za 9,99 €",
        "SI": "Preizkusi za 9,99 €",
        "RS": "Isprobaj za 9,99 €",
    },
    "Shop the Cream": {
        "EN": "Shop the Cream",
        "BG": "Купи крема",
        "FR": "Achetez la crème",
        "RO": "Cumpără crema",
        "SK": "Kúpiť krém",
        "CZ": "Koupit krém",
        "DE": "Creme kaufen",
        "IT": "Acquista la crema",
        "ES": "Comprar la crema",
        "NL": "Koop de crème",
        "PT": "Comprar o creme",
        "PL": "Kup krem",
        "HU": "Vásárolj krémet",
        "HR": "Kupi kremu",
        "SI": "Kupi kremo",
        "RS": "Kupi kremu",
    },
    "Read the Full Study": {
        "EN": "Read the Full Study",
        "BG": "Прочети цялото проучване",
        "FR": "Lire l'étude complète",
        "RO": "Citește studiul complet",
        "SK": "Prečítať celú štúdiu",
        "CZ": "Přečíst celou studii",
        "DE": "Ganze Studie lesen",
        "IT": "Leggi lo studio completo",
        "ES": "Leer el estudio completo",
        "NL": "Lees het hele onderzoek",
        "PT": "Ler o estudo completo",
        "PL": "Przeczytaj całe badanie",
        "HU": "Olvasd el a teljes tanulmányt",
        "HR": "Pročitaj cijelo istraživanje",
        "SI": "Preberi celotno študijo",
        "RS": "Pročitaj celo istraživanje",
    },
    "Try It Now": {
        "EN": "Try It Now",
        "BG": "Изпробвай сега",
        "FR": "Essayez maintenant",
        "RO": "Încearcă acum",
        "SK": "Vyskúšať teraz",
        "CZ": "Vyzkoušet nyní",
        "DE": "Jetzt testen",
        "IT": "Provala ora",
        "ES": "Pruébala ahora",
        "NL": "Probeer het nu",
        "PT": "Experimente já",
        "PL": "Wypróbuj teraz",
        "HU": "Próbáld ki most",
        "HR": "Isprobaj sada",
        "SI": "Preizkusi zdaj",
        "RS": "Isprobaj sada",
    },
    "Shop Now and Feel the Difference in 20 Days": {
        "EN": "Shop Now and Feel the Difference in 20 Days",
        "BG": "Поръчай сега и усети разликата за 20 дни",
        "FR": "Achetez maintenant, sentez la différence en 20 jours",
        "RO": "Comandă acum și simte diferența în 20 de zile",
        "SK": "Kúpiť teraz a cítiť rozdiel za 20 dní",
        "CZ": "Koupit nyní a cítit rozdíl za 20 dní",
        "DE": "Jetzt kaufen, Unterschied in 20 Tagen spüren",
        "IT": "Acquista ora, senti la differenza in 20 giorni",
        "ES": "Compra ahora y siente la diferencia en 20 días",
        "NL": "Koop nu en voel het verschil in 20 dagen",
        "PT": "Compre agora e sinta a diferença em 20 dias",
        "PL": "Kup teraz i poczuj różnicę w 20 dni",
        "HU": "Vásárolj most, 20 nap alatt érzed a különbséget",
        "HR": "Kupi sada i osjeti razliku za 20 dana",
        "SI": "Kupi zdaj in občuti razliko v 20 dneh",
        "RS": "Kupi sada i osjeti razliku za 20 dana",
    },
    "See How It Works": {
        "EN": "See How It Works",
        "BG": "Виж как действа",
        "FR": "Voir comment ça marche",
        "RO": "Vezi cum funcționează",
        "SK": "Pozri ako to funguje",
        "CZ": "Podívej se, jak to funguje",
        "DE": "So funktioniert es",
        "IT": "Scopri come funziona",
        "ES": "Descubre cómo funciona",
        "NL": "Ontdek hoe het werkt",
        "PT": "Vê como funciona",
        "PL": "Zobacz, jak działa",
        "HU": "Nézd meg, hogyan működik",
        "HR": "Saznaj kako djeluje",
        "SI": "Poglej, kako deluje",
        "RS": "Saznaj kako deluje",
    },
    "Read More": {
        "EN": "Read More",
        "BG": "Научи повече",
        "FR": "En savoir plus",
        "RO": "Citește mai mult",
        "SK": "Čítať viac",
        "CZ": "Číst dál",
        "DE": "Mehr erfahren",
        "IT": "Scopri di più",
        "ES": "Saber más",
        "NL": "Lees meer",
        "PT": "Saber mais",
        "PL": "Czytaj więcej",
        "HU": "Tudj meg többet",
        "HR": "Saznaj više",
        "SI": "Več informacij",
        "RS": "Saznaj više",
    },
    "See My Results": {
        "EN": "See My Results",
        "BG": "Виж резултатите",
        "FR": "Voir mes résultats",
        "RO": "Vezi rezultatele",
        "SK": "Pozri výsledky",
        "CZ": "Podívej se na výsledky",
        "DE": "Ergebnisse ansehen",
        "IT": "Guarda i risultati",
        "ES": "Ver los resultados",
        "NL": "Bekijk de resultaten",
        "PT": "Ver os resultados",
        "PL": "Zobacz wyniki",
        "HU": "Nézd meg az eredményeket",
        "HR": "Pogledaj rezultate",
        "SI": "Poglej rezultate",
        "RS": "Pogledaj rezultate",
    },
    "Try the 20-Day Protocol": {
        "EN": "Try the 20-Day Protocol",
        "BG": "Изпробвай 20-дневния протокол",
        "FR": "Essayez le protocole de 20 jours",
        "RO": "Încearcă protocolul de 20 de zile",
        "SK": "Vyskúšajte 20-dňový protokol",
        "CZ": "Vyzkoušejte 20denní protokol",
        "DE": "20-Tage-Protokoll testen",
        "IT": "Prova il protocollo di 20 giorni",
        "ES": "Prueba el protocolo de 20 días",
        "NL": "Probeer het 20-dagenprotocol",
        "PT": "Experimente o protocolo de 20 dias",
        "PL": "Wypróbuj 20-dniowy protokół",
        "HU": "Próbáld a 20 napos protokollt",
        "HR": "Isprobaj 20-dnevni protokol",
        "SI": "Preizkusi 20-dnevni protokol",
        "RS": "Isprobaj 20-dnevni protokol",
    },
    "Shop Relief Now": {
        "EN": "Shop Relief Now",
        "BG": "Поръчай облекчението сега",
        "FR": "Achetez le soulagement",
        "RO": "Cumpără alinarea acum",
        "SK": "Kúpiť úľavu teraz",
        "CZ": "Koupit úlevu hned",
        "DE": "Linderung jetzt kaufen",
        "IT": "Compra sollievo ora",
        "ES": "Compra alivio ahora",
        "NL": "Koop verlichting nu",
        "PT": "Comprar alívio agora",
        "PL": "Kup ulgę teraz",
        "HU": "Vásárolj enyhülést most",
        "HR": "Kupi olakšanje sada",
        "SI": "Kupi olajšanje zdaj",
        "RS": "Kupi olakšanje sada",
    },
    "Get Smooth Legs Now": {
        "EN": "Get Smooth Legs Now",
        "BG": "Гладки крака още сега",
        "FR": "Des jambes lisses, maintenant",
        "RO": "Picioare netede chiar acum",
        "SK": "Hladké nohy hneď teraz",
        "CZ": "Hladké nohy hned teď",
        "DE": "Glatte Beine ab heute",
        "IT": "Gambe lisce, ora",
        "ES": "Piernas suaves ya",
        "NL": "Gladde benen, nu",
        "PT": "Pernas lisas, agora",
        "PL": "Gładkie nogi już teraz",
        "HU": "Sima lábak már most",
        "HR": "Glatke noge već sada",
        "SI": "Gladke noge takoj",
        "RS": "Glatke noge već sada",
    },
    "Shop Now, Starting at €9.99": {
        "EN": "Shop Now, Starting at €9.99",
        "BG": "Поръчай сега, от 9,99 €",
        "FR": "Achetez dès 9,99 €",
        "RO": "Cumpără acum, de la 9,99 €",
        "SK": "Kúpiť teraz, od 9,99 €",
        "CZ": "Koupit nyní, od 9,99 €",
        "DE": "Jetzt kaufen, ab 9,99 €",
        "IT": "Acquista ora, da 9,99 €",
        "ES": "Comprar desde 9,99 €",
        "NL": "Nu kopen, vanaf € 9,99",
        "PT": "Compre já, desde 9,99 €",
        "PL": "Kup teraz, od 9,99 €",
        "HU": "Vásárolj most, már 9,99 €",
        "HR": "Kupi sada, već za 9,99 €",
        "SI": "Kupi zdaj, že za 9,99 €",
        "RS": "Kupi sada, već za 9,99 €",
    },
    "Get Yours for €9.99": {
        "EN": "Get Yours for €9.99",
        "BG": "Вземи го за 9,99 €",
        "FR": "Le vôtre pour 9,99 €",
        "RO": "Ia-l pentru 9,99 €",
        "SK": "Získať za 9,99 €",
        "CZ": "Získej za 9,99 €",
        "DE": "Hol dir die Creme für 9,99 €",
        "IT": "Prendi la tua a 9,99 €",
        "ES": "Hazte con la tuya por 9,99 €",
        "NL": "Haal de jouwe voor € 9,99",
        "PT": "Adquire o teu por 9,99 €",
        "PL": "Zamów za 9,99 €",
        "HU": "Szerezd be 9,99 €-ért",
        "HR": "Naruči za 9,99 €",
        "SI": "Naroči za 9,99 €",
        "RS": "Naruči za 9,99 €",
    },
    "Read the Reviews and Try It": {
        "EN": "Read the Reviews and Try It",
        "BG": "Прочети ревютата и изпробвай",
        "FR": "Lisez les avis et essayez",
        "RO": "Citește recenziile și încearcă",
        "SK": "Prečítať recenzie a vyskúšať",
        "CZ": "Přečíst recenze a vyzkoušet",
        "DE": "Bewertungen lesen und testen",
        "IT": "Leggi le recensioni e provala",
        "ES": "Lee las reseñas y pruébala",
        "NL": "Lees de reviews en probeer",
        "PT": "Lê as avaliações e experimenta",
        "PL": "Przeczytaj opinie i wypróbuj",
        "HU": "Olvasd a véleményeket és próbáld",
        "HR": "Pročitaj recenzije i isprobaj",
        "SI": "Preberi mnenja in preizkusi",
        "RS": "Pročitaj recenzije i isprobaj",
    },
    "Show Me How It Works": {
        "EN": "Show Me How It Works",
        "BG": "Покажи ми как действа",
        "FR": "Montrez-moi comment ça marche",
        "RO": "Arată-mi cum funcționează",
        "SK": "Ukáž mi, ako to funguje",
        "CZ": "Ukaž mi, jak to funguje",
        "DE": "Zeig mir, wie es wirkt",
        "IT": "Mostrami come funziona",
        "ES": "Muéstrame cómo funciona",
        "NL": "Laat zien hoe het werkt",
        "PT": "Mostra-me como funciona",
        "PL": "Pokaż mi, jak działa",
        "HU": "Mutasd, hogyan működik",
        "HR": "Pokaži kako djeluje",
        "SI": "Pokaži, kako deluje",
        "RS": "Pokaži kako deluje",
    },
    "Shop the Soothing Cream": {
        "EN": "Shop the Soothing Cream",
        "BG": "Купи успокояващия крем",
        "FR": "Achetez la crème apaisante",
        "RO": "Cumpără crema calmantă",
        "SK": "Kúpiť upokojujúci krém",
        "CZ": "Koupit zklidňující krém",
        "DE": "Beruhigende Creme kaufen",
        "IT": "Acquista la crema lenitiva",
        "ES": "Comprar la crema calmante",
        "NL": "Koop de verzachtende crème",
        "PT": "Comprar o creme calmante",
        "PL": "Kup kojący krem",
        "HU": "Vásárold a nyugtató krémet",
        "HR": "Kupi umirujuću kremu",
        "SI": "Kupi pomirjajočo kremo",
        "RS": "Kupi umirujuću kremu",
    },
    "Shop Now, Just €9.99": {
        "EN": "Shop Now, Just €9.99",
        "BG": "Поръчай сега, само 9,99 €",
        "FR": "Achetez à seulement 9,99 €",
        "RO": "Comandă acum, doar 9,99 €",
        "SK": "Kúpiť teraz, len 9,99 €",
        "CZ": "Koupit teď, jen 9,99 €",
        "DE": "Jetzt kaufen, nur 9,99 €",
        "IT": "Acquista ora, solo 9,99 €",
        "ES": "Cómprala por solo 9,99 €",
        "NL": "Nu kopen, slechts € 9,99",
        "PT": "Compre já, apenas 9,99 €",
        "PL": "Kup teraz, tylko 9,99 €",
        "HU": "Vásárolj most, csak 9,99 €",
        "HR": "Kupi sada, samo 9,99 €",
        "SI": "Kupi zdaj, samo 9,99 €",
        "RS": "Kupi sada, samo 9,99 €",
    },
    "Try It For 20 Days": {
        "EN": "Try It For 20 Days",
        "BG": "Изпробвай за 20 дни",
        "FR": "Essayez pendant 20 jours",
        "RO": "Încearcă 20 de zile",
        "SK": "Vyskúšať na 20 dní",
        "CZ": "Vyzkoušet na 20 dní",
        "DE": "20 Tage lang testen",
        "IT": "Provala per 20 giorni",
        "ES": "Pruébala 20 días",
        "NL": "Probeer 20 dagen lang",
        "PT": "Experimente 20 dias",
        "PL": "Wypróbuj przez 20 dni",
        "HU": "Próbáld 20 napig",
        "HR": "Isprobaj 20 dana",
        "SI": "Preizkusi 20 dni",
        "RS": "Isprobaj 20 dana",
    },
    "Shop Now for €9.99": {
        "EN": "Shop Now for €9.99",
        "BG": "Поръчай сега за 9,99 €",
        "FR": "Achetez maintenant pour 9,99 €",
        "RO": "Comandă acum cu 9,99 €",
        "SK": "Kúpiť teraz za 9,99 €",
        "CZ": "Koupit teď za 9,99 €",
        "DE": "Jetzt kaufen für 9,99 €",
        "IT": "Acquista ora a 9,99 €",
        "ES": "Compra ahora por 9,99 €",
        "NL": "Nu kopen voor € 9,99",
        "PT": "Compre já por 9,99 €",
        "PL": "Kup teraz za 9,99 €",
        "HU": "Vásárolj most 9,99 €-ért",
        "HR": "Kupi sada za 9,99 €",
        "SI": "Kupi zdaj za 9,99 €",
        "RS": "Kupi sada za 9,99 €",
    },
    "Shop Now, Feel the Difference": {
        "EN": "Shop Now, Feel the Difference",
        "BG": "Поръчай сега, усети разликата",
        "FR": "Achetez et sentez la différence",
        "RO": "Comandă acum, simte diferența",
        "SK": "Kúpiť teraz, cítiť rozdiel",
        "CZ": "Koupit teď, cítit rozdíl",
        "DE": "Jetzt kaufen, Unterschied spüren",
        "IT": "Acquista ora, senti la differenza",
        "ES": "Cómprala y siente la diferencia",
        "NL": "Nu kopen, voel het verschil",
        "PT": "Compre já, sinta a diferença",
        "PL": "Kup teraz, poczuj różnicę",
        "HU": "Vásárolj most, érezd a különbséget",
        "HR": "Kupi sada, osjeti razliku",
        "SI": "Kupi zdaj, občuti razliko",
        "RS": "Kupi sada, oseti razliku",
    },
}


def main():
    en_raw = json.loads(EN_RAW.read_text())
    source = build_source_payload(en_raw)
    fn_to_cta_en = {r["filename"]: normalize(r["cta"]) for r in source}

    missing_keys = set()
    for fn, cta in fn_to_cta_en.items():
        key = normalize(cta)
        if key.lower() == "try it for €9.99":
            key = "Try It for €9.99"
        if key not in CTA_TABLE:
            missing_keys.add(key)
    if missing_keys:
        print("UNMAPPED CTAs (won't be translated):")
        for k in sorted(missing_keys):
            print(f"  {k!r}")

    en_payload = []
    for r in source:
        en_payload.append({
            "filename": r["filename"],
            "headlines": r["headlines"],
            "primary_text": r["primary_text"],
            "cta": r["cta"],
        })
    (TRANS_DIR / "EN.json").write_text(json.dumps(en_payload, indent=2, ensure_ascii=False))
    print(f"Refreshed EN.json with correct CTAs ({len(en_payload)} ads)")

    for lang_file in sorted(TRANS_DIR.glob("*.json")):
        code = lang_file.stem
        if code == "EN":
            continue
        if not lang_file.exists():
            continue
        data = json.loads(lang_file.read_text())
        if not data:
            continue
        if isinstance(data[0].get("cta"), str) and len(data[0].get("cta", "")) > 3:
            print(f"[{code}] already has long CTAs, skipping")
            continue
        patched = 0
        for r in data:
            en_cta = fn_to_cta_en.get(r["filename"], "")
            key = normalize(en_cta)
            if key.lower() == "try it for €9.99":
                key = "Try It for €9.99"
            if key in CTA_TABLE and code in CTA_TABLE[key]:
                r["cta"] = CTA_TABLE[key][code]
                patched += 1
        lang_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"[{code}] patched {patched}/{len(data)} CTAs")


if __name__ == "__main__":
    main()
