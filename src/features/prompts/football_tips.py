import json


def build_tips_prompt(api_data):
    return (
        "Pro každý uvedený zápas připrav věcnou a opatrnou sázkovou analýzu. "
        "Vyber jeden konkrétní hlavní tip a uveď přesně sázkový trh i výběr "
        "(např. 1X2 – domácí výhra, dvojitá šance – 1X, počet gólů – méně než 3,5). "
        "Vysvětli, které dodané statistiky tip podporují, a uveď nejdůležitější riziko "
        "nebo důvod, proč tip nemusí vyjít. Přidej nejvýše jednu alternativu, jen pokud "
        "pro ni data dávají smysl. Využij formu, tabulku a vzájemné zápasy, jsou-li dostupné; "
        "H2H ber jen jako doplňující kontext. Nevymýšlej zranění, kurzy ani statistiky. "
        "Bez kurzů neposuzuj hodnotu sázky. Pokud podklady nestačí na rozumný tip, "
        "doporuč bez sázky a vysvětli proč. Jistota může být pouze nízká nebo střední; "
        "vysokou jistotu nikdy neuváděj. Neslibuj výhru a nedoporučuj výši vkladu. "
        "Vrať pouze JSON objekt s polem tips. Každá položka musí mít match_index, market, "
        "pick, confidence, reason, risk a alternative. U tipu bez sázky nastav market na "
        "'Bez sázky', pick na 'Žádný tip' a alternative na prázdný řetězec. "
        "reason a risk napiš stručně, nejvýše ve dvou krátkých větách; alternative nejvýše v jedné.\n"
        "Následující JSON obsahuje zkrácená relevantní data z dostupných football-data.org endpointů. "
        "Využij dostupné informace, ale žádné hodnoty nedoplňuj ani nevymýšlej.\n"
        f"Data API: {json.dumps(api_data, ensure_ascii=False, separators=(',', ':'))}"
    )
