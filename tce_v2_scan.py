"""
tce_v2_scan.py — wires the TCE v2 engine into the scanner pipeline.

build_tce_v2(data) -> [labeled per-holding records] for dashboard Tab 15 (data['tce_v2']).
STANDALONE module; scanner.py imports build_tce_v2 and assigns the result inside a try/except,
so if anything here fails the core scan is never affected (production-safe).

Freshness of each stream is surfaced per record:
  LIVE         fetched this run, tested in build sandbox (crude momentum, Pink Sheet)
  LIVE-on-run  fetched on the GitHub runner (per-name Yahoo momentum / RS); None in sandbox
  MANUAL       maintainable last-good in MANUAL_OVERRIDES (supply/revisions/margin/capital, bank NIM)
  PENDING      needs the broker/news layer (e.g. PSX revisions)

Live now: crude sector momentum (Tier-1 GitHub Brent CSV) + fertilizer s1/s4 (World Bank Pink Sheet).
Per-name relative momentum + RS guardrail fetch on the runner (Yahoo chart API). Remaining streams
are MANUAL until their fetchers/broker layer land — each labeled, so trust is always visible.
"""
import urllib.request, csv, io, json, datetime as dt
from collections import OrderedDict
from tce_v2_engine import run

try:
    from tce_feeds import _pink_sheet_series, _mom as _pink_mom
except Exception:
    _pink_sheet_series = None

UA = {'User-Agent': 'Mozilla/5.0'}
BRENT_CSV = "https://raw.githubusercontent.com/datasets/oil-prices/main/data/brent-daily.csv"
SECTOR_ETF = {'ep': 'XLE'}

# Portfolio holdings routed to a sector adapter (only sectors with an adapter today).
HOLDINGS = [('XOM', 'ep'), ('CVX', 'ep'), ('COP', 'ep'), ('EOG', 'ep'),
            ('OGDC', 'ep'), ('PPL', 'ep'), ('FFC', 'fert'), ('MCB', 'bank')]

# Maintainable last-good inputs for streams without a live feed yet. Update as you learn;
# everything here surfaces as MANUAL so it is never mistaken for a fetched value.
MANUAL_OVERRIDES = {
    'XOM':  dict(rigs_falling=True),
    'CVX':  dict(rigs_falling=True, capex_up=True),     # Hess close = capital event
    'EOG':  dict(rigs_falling=True, capex_up=True),     # Encino acquisition
    'COP':  dict(rigs_falling=True),
    'OGDC': dict(), 'PPL': dict(),
    'FFC':  dict(gas_curtailment=False, dividend_up=True, gas_cost=300, gas_cost_prev=300),
    'MCB':  dict(payout_up=True),                        # NIM/growth pending broker layer
}


def crude_sector_momentum():
    """Brent monthly momentum = latest-month avg vs prior-3-month avg (Tier-1 GitHub feed)."""
    try:
        d = urllib.request.urlopen(urllib.request.Request(BRENT_CSV, headers=UA), timeout=12).read().decode()
        monthly = OrderedDict()
        for row in list(csv.reader(io.StringIO(d)))[1:]:
            if len(row) < 2 or not row[1]:
                continue
            monthly.setdefault(row[0][:7], []).append(float(row[1]))
        avg = [(ym, sum(v) / len(v)) for ym, v in monthly.items()]
        if len(avg) < 4:
            return None, None
        latest = avg[-1][1]
        prior3 = sum(a[1] for a in avg[-4:-1]) / 3
        return round((latest - prior3) / prior3 * 100, 1), avg[-1][0]
    except Exception:
        return None, None


def _yahoo_closes(ticker, rng='3mo'):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range={rng}&interval=1d"
        d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=10))
        c = d['chart']['result'][0]['indicators']['quote'][0]['close']
        return [x for x in c if x is not None]
    except Exception:
        return None


def _ret(closes):
    return None if not closes or len(closes) < 2 or not closes[0] else (closes[-1] - closes[0]) / closes[0] * 100


def _lab(k, fired, value, src, fresh):
    return {'k': k, 'fired': fired, 'value': value, 'src': src, 'fresh': fresh}


def build_tce_v2(data=None):
    crude_mom, crude_asof = crude_sector_momentum()
    series, pink_asof = (_pink_sheet_series() if _pink_sheet_series else (None, None))
    records = []

    for tkr, sec in HOLDINGS:
        ov = dict(MANUAL_OVERRIDES.get(tkr, {}))
        labels = {}

        if sec == 'ep':
            etf = SECTOR_ETF['ep']
            name_mom = _ret(_yahoo_closes(tkr))
            rs = None
            nm, em = _ret(_yahoo_closes(tkr, '6mo')), _ret(_yahoo_closes(etf, '6mo'))
            if nm is not None and em is not None:
                rs = nm - em
            # s1 relative: fire only if the name beats crude by >=8pt (commodity common-factor fix)
            if name_mom is not None and crude_mom is not None:
                rel = name_mom - crude_mom
                ov['crude_mom_pct'] = rel; ov['crude_consec'] = 2; ov['crude_thresh'] = 8
                labels['s1'] = _lab('s1 sell-price', rel >= 8,
                                    f"{tkr} {name_mom:+.0f}% vs Brent {crude_mom:+.0f}% ({rel:+.0f}pt)",
                                    f"Yahoo {tkr} 3mo vs GitHub Brent ({crude_asof})", "LIVE-on-run")
            else:
                base = f"Brent sector {crude_mom:+.1f}% ({crude_asof})" if crude_mom is not None else "crude feed down"
                labels['s1'] = _lab('s1 sell-price', False, base + "; name px pending", "GitHub Brent CSV", "LIVE-on-run")
            if rs is not None:
                ov['rs_vs_xle'] = rs
                labels['s6'] = _lab('s6 RS guardrail', rs > 0, f"{tkr} vs {etf} {rs:+.0f}pt (6mo)", f"Yahoo {tkr} vs {etf}", "LIVE-on-run")
            else:
                labels['s6'] = _lab('s6 RS guardrail', False, "RS pending", f"Yahoo {tkr} vs {etf}", "LIVE-on-run")
            labels['s2'] = _lab('s2 supply', bool(ov.get('rigs_falling')), 'rigs falling' if ov.get('rigs_falling') else 'n/a', 'EIA rig direction', 'MANUAL')
            labels['s3'] = _lab('s3 revisions', False, 'pending', 'SEC/broker', 'PENDING')
            labels['s4'] = _lab('s4 margin', False, 'pending', 'reported financials', 'MANUAL')
            labels['s5'] = _lab('s5 capital', bool(ov.get('capex_up')), 'capital event' if ov.get('capex_up') else 'none', 'SEC 8-K / announcements', 'MANUAL')
            res = run('ep', ov)

        elif sec == 'fert':
            if series:
                um, dm = _pink_mom(series.get('Urea')), _pink_mom(series.get('DAP'))
                moms = [m for m in (um, dm) if m is not None]
                blend = sum(moms) / len(moms) if moms else None
                ov['urea_prices'] = series.get('Urea'); ov['dap_prices'] = series.get('DAP')
                if series.get('Urea'):
                    ov['urea_price'] = series['Urea'][-1]
                    ov['urea_price_prev'] = series['Urea'][-2] if len(series['Urea']) > 1 else None
                labels['s1'] = _lab('s1 sell-price', bool(blend and blend > 15),
                                    f"urea {um:+.1f}%/DAP {dm:+.1f}% (blend {blend:+.1f}%)" if blend is not None else "n/a",
                                    f"World Bank Pink Sheet (thru {pink_asof})", "LIVE")
            else:
                labels['s1'] = _lab('s1 sell-price', False, "Pink Sheet pending", "World Bank Pink Sheet", "LIVE-on-run")
            labels['s2'] = _lab('s2 supply', bool(ov.get('gas_curtailment')), 'gas curtailment' if ov.get('gas_curtailment') else 'none', 'SNGPL/SSGC notices', 'MANUAL')
            labels['s3'] = _lab('s3 revisions', False, 'pending broker layer', 'AKD/Topline/AHL', 'PENDING')
            labels['s4'] = _lab('s4 margin', False, 'urea - gas spread', 'Pink Sheet | SNGPL tariff', 'LIVE+MANUAL')
            labels['s5'] = _lab('s5 capital', bool(ov.get('dividend_up')), 'dividend' if ov.get('dividend_up') else 'none', 'PSX filings', 'MANUAL')
            labels['s6'] = _lab('s6 RS guardrail', False, 'RS pending', 'PSX-EOD vs KSE-100', 'LIVE-on-run')
            res = run('fert', ov)

        else:  # bank
            labels['s1'] = _lab('s1 sell-price', False, 'NIM pending broker', 'broker NIM forecast', 'PENDING')
            labels['s2'] = _lab('s2 supply', False, 'deposit/loan growth pending', 'broker/results', 'PENDING')
            labels['s3'] = _lab('s3 revisions', False, 'pending broker layer', 'AKD/Topline/AHL', 'PENDING')
            labels['s4'] = _lab('s4 margin', False, 'NIM delta pending', 'broker', 'PENDING')
            labels['s5'] = _lab('s5 capital', bool(ov.get('payout_up')), 'payout' if ov.get('payout_up') else 'none', 'PSX filings', 'MANUAL')
            labels['s6'] = _lab('s6 RS guardrail', False, 'RS pending', 'PSX-EOD vs KSE banks', 'LIVE-on-run')
            res = run('bank', ov)

        order = ['s1', 's2', 's3', 's4', 's5', 's6']
        records.append({
            'ticker': tkr, 'sector': res['sector'], 'tier': res['tier'],
            'score': res['score'], 'guardrail_ok': res['guardrail_ok'],
            'streams': [labels[s] for s in order if s in labels],
        })
    return records


if __name__ == "__main__":
    recs = build_tce_v2()
    print(f"build_tce_v2 -> {len(recs)} records\n" + "=" * 70)
    for r in recs:
        fired = [s['k'].split()[0] for s in r['streams'] if s['fired']]
        print(f"{r['ticker']:5s} {r['sector']:10s} {r['tier']:7s} {r['score']}/6  guardrail={'ok' if r['guardrail_ok'] else 'FAIL'}  fired={fired}")
    # spot-check one full record shape (what Tab 15 consumes)
    print("\nFFC streams (Tab-15 shape):")
    ffc = next(r for r in recs if r['ticker'] == 'FFC')
    for s in ffc['streams']:
        print(f"  [{'FIRED' if s['fired'] else '  -  '}] {s['k']}: {s['value']}  | {s['src']} [{s['fresh']}]")
