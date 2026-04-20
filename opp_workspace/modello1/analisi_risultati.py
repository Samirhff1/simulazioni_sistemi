#!/usr/bin/env python3
"""
Analisi dei risultati della simulazione
Bulk Service Vacation Queue con N-policy

1. Analisi del transiente iniziale (tramite file .vec)
2. Calcolo intervalli di confidenza per le misure di prestazione
3. Generazione grafici e tabelle riassuntive
"""

import os
import re
import glob
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ==========================================================================
# Configurazione
# ==========================================================================
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "analisi")
CONFIGS = ["m05", "m10", "m14", "m20"]
M_VALUES = {"m05": 0.5, "m10": 1.0, "m14": 1.4, "m20": 2.0}
TRANSIENT_CONFIGS = ["transient_m05", "transient_m10", "transient_m14", "transient_m20"]
BASE_CONFIG_FROM_TRANSIENT = {
    "transient_m05": "m05",
    "transient_m10": "m10",
    "transient_m14": "m14",
    "transient_m20": "m20"
}
NUM_RUNS = 20
CONFIDENCE = 0.95
EX_MEAN = 2.5

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ==========================================================================
# PARTE 1: Parsing dei file .sca
# ==========================================================================
def parse_time_to_seconds(raw_value):
    """Converte stringhe OMNeT++ tipo '100000s' o '1.5' in secondi"""
    value = raw_value.strip().strip('"')
    match = re.match(r"^(-?\d+(?:\.\d+)?)([a-zA-Z]*)$", value)
    if not match:
        return np.nan

    number = float(match.group(1))
    unit = match.group(2)
    factors = {
        "": 1.0,
        "s": 1.0,
        "ms": 1e-3,
        "us": 1e-6,
        "ns": 1e-9,
        "m": 60.0,
        "h": 3600.0,
        "d": 86400.0,
    }
    return number * factors.get(unit, np.nan)


def parse_sca_file(filepath):
    """Estrae scalari, metadati run e campi utili dei blocchi statistic"""
    results = {}
    current_stat = None

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()

            if line.startswith("config "):
                parts = line.split(maxsplit=2)
                if len(parts) == 3:
                    cfg_key = parts[1]
                    cfg_val = parts[2]
                    if cfg_key == "sim-time-limit":
                        results["_meta.sim_time_limit_s"] = parse_time_to_seconds(cfg_val)
                    elif cfg_key == "warmup-period":
                        results["_meta.warmup_period_s"] = parse_time_to_seconds(cfg_val)
                continue

            if line.startswith("scalar "):
                parts = line.split()
                # Format: scalar <module> <name> <value>
                if len(parts) >= 4:
                    module = parts[1]
                    name = parts[2]
                    try:
                        value = float(parts[3])
                    except ValueError:
                        continue
                    key = f"{module}.{name}"
                    results[key] = value
                continue

            if line.startswith("statistic "):
                parts = line.split()
                if len(parts) >= 3:
                    current_stat = f"{parts[1]}.{parts[2]}"
                else:
                    current_stat = None
                continue

            if line.startswith("field ") and current_stat is not None:
                parts = line.split()
                if len(parts) >= 3:
                    field_name = parts[1]
                    try:
                        field_value = float(parts[2])
                    except ValueError:
                        continue
                    key = f"{current_stat}.field.{field_name}"
                    results[key] = field_value
    return results


def collect_all_scalars():
    """Raccoglie gli scalari da tutti gli 80 run"""
    data = {}
    for config in CONFIGS:
        data[config] = []
        for run in range(NUM_RUNS):
            sca_file = os.path.join(RESULTS_DIR, f"{config}-#{run}.sca")
            if os.path.exists(sca_file):
                scalars = parse_sca_file(sca_file)
                data[config].append(scalars)
            else:
                print(f"  ATTENZIONE: file mancante {sca_file}")
    return data


# ==========================================================================
# PARTE 2: Analisi del transiente iniziale
# ==========================================================================
def parse_vec_file_for_transient(filepath, vector_name="numInSystem:vector"):
    """
    Legge un file .vec e estrae la serie temporale per l'analisi del transiente.
    Cerca il vettore specificato.
    """
    # Prima trova il vector ID dal file .vec
    vector_id = None
    with open(filepath, 'r') as f:
        for line in f:
            if line.startswith("vector ") and vector_name in line:
                parts = line.split()
                vector_id = parts[1]
                break

    if vector_id is None:
        return None, None

    # Poi legge i dati
    times = []
    values = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.startswith(vector_id + "\t"):
                parts = line.strip().split("\t")
                if len(parts) >= 4:
                    try:
                        t = float(parts[2])
                        v = float(parts[3])
                        times.append(t)
                        values.append(v)
                    except ValueError:
                        continue
    return np.array(times), np.array(values)


def analyze_transient_config(config, window_size=500):
    """
    Analizza il transiente su tutti i run disponibili di una config transient_m*.
    Produce un grafico con serie sovrapposte e media mobile media.
    """
    vec_pattern = os.path.join(RESULTS_DIR, f"{config}-#*.vec")
    vec_files = sorted(glob.glob(vec_pattern))
    if not vec_files:
        print(f"  Nessun file transient trovato per {config} ({vec_pattern})")
        return None

    base_cfg = BASE_CONFIG_FROM_TRANSIENT.get(config, config)
    m_value = M_VALUES.get(base_cfg)

    print(f"\n{'='*60}")
    print(f"  ANALISI DEL TRANSIENTE INIZIALE")
    print(f"  Config: {config} (m={m_value})")
    print(f"  Run trovati: {len(vec_files)}")
    print(f"{'='*60}")

    raw_series = []
    moving_series = []

    for vec_file in vec_files:
        times, values = parse_vec_file_for_transient(vec_file, "numInSystem:vector")
        if times is None or len(times) == 0:
            times, values = parse_vec_file_for_transient(vec_file, "queueLength:vector")
            if times is None or len(times) == 0:
                continue

        raw_series.append((times, values, os.path.basename(vec_file)))

        if len(values) > window_size:
            cumsum = np.cumsum(np.insert(values, 0, 0.0))
            moving_avg = (cumsum[window_size:] - cumsum[:-window_size]) / window_size
            moving_times = times[window_size - 1:]
            moving_series.append((moving_times, moving_avg))

    if not moving_series:
        print(f"  Dati insufficienti per calcolare media mobile su {config}")
        return None

    # Intervallo temporale comune tra tutti i run per media tra curve
    t_start = max(ts[0] for ts, _ in moving_series)
    t_end = min(ts[-1] for ts, _ in moving_series)
    if t_end <= t_start:
        print(f"  Intervallo comune non valido per {config}")
        return None

    time_grid = np.linspace(t_start, t_end, 2000)
    interpolated = [np.interp(time_grid, ts, mv) for ts, mv in moving_series]
    mean_curve = np.mean(interpolated, axis=0)

    # Media globale: escluso il primo 10% della serie
    global_mean = np.mean(mean_curve[int(0.1 * len(mean_curve)):])
    threshold = 0.05 * abs(global_mean) if abs(global_mean) > 1e-12 else 0.5

    # Stabilizzazione: primo punto in cui la media mobile resta entro la banda
    # per almeno 3 finestre consecutive.
    within_band = np.abs(mean_curve - global_mean) <= threshold
    stabilization_idx = len(mean_curve) - 1
    consecutive_windows = 3
    for i in range(0, len(mean_curve) - consecutive_windows + 1):
        if np.all(within_band[i:i + consecutive_windows]):
            stabilization_idx = i
            break

    stabilization_time = time_grid[stabilization_idx]
    stabilization_pct = 100.0 * stabilization_time / time_grid[-1]

    # Plot: run sovrapposti + medie mobili + curva media
    fig, ax = plt.subplots(1, 1, figsize=(14, 7))

    for times, values, run_name in raw_series:
        # downsampling grafico per mantenere leggibilità
        step = max(1, len(times) // 3000)
        ax.plot(times[::step], values[::step], alpha=0.08, linewidth=0.5, color='tab:blue')

    for ts, mv in moving_series:
        step = max(1, len(ts) // 2000)
        ax.plot(ts[::step], mv[::step], alpha=0.18, linewidth=0.7, color='tab:red')

    ax.plot(time_grid, mean_curve, color='black', linewidth=2.5, label='Media mobile media (run sovrapposti)')
    ax.axhline(global_mean, color='green', linestyle='--', linewidth=2,
               label=f'Media regime stazionario ≈ {global_mean:.2f}')
    ax.axvline(stabilization_time, color='purple', linestyle='--', linewidth=2,
               label=f'Stabilizzazione stimata ≈ {stabilization_time:.0f}s')

    ax.set_xlabel('Tempo di simulazione (s)')
    ax.set_ylabel('Numero utenti nel sistema')
    ax.set_title(f'Analisi transiente multi-run - {config} (m={m_value})')
    ax.grid(True, alpha=0.3)
    ax.legend()

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, f'transiente_{config}.png')
    plt.savefig(out_path, dpi=150)
    plt.close()

    print("\n  Risultati analisi transiente:")
    print(f"  - Media regime stazionario: {global_mean:.4f}")
    print(f"  - Stabilizzazione stimata: ~{stabilization_time:.0f}s ({stabilization_pct:.1f}% del tempo totale)")
    print(f"  - Grafico salvato: {out_path}")

    return {
        "config": config,
        "m": m_value,
        "num_runs": len(raw_series),
        "stabilization_time": stabilization_time,
        "steady_state_mean": global_mean,
    }


def analyze_transient_all_configs():
    """Analisi del transiente per tutte le configurazioni transient_m*"""
    print("\n" + "=" * 60)
    print("  ANALISI TRANSIENTE PER TUTTE LE CONFIGURAZIONI")
    print("=" * 60)

    warmup_results = {}
    for config in TRANSIENT_CONFIGS:
        result = analyze_transient_config(config=config, window_size=500)
        if result is not None:
            warmup_results[config] = result

    if not warmup_results:
        print("\n  Nessuna configurazione transient_m* disponibile nei risultati.")
        print("  Esegui prima i run: transient_m05, transient_m10, transient_m14, transient_m20")

    return warmup_results


def build_run_dataframe(all_data):
    """Costruisce un dataframe run-level utile per controlli aggiuntivi (es. Little)."""
    rows = []

    for config in CONFIGS:
        runs = all_data.get(config, [])
        for run_idx, r in enumerate(runs):
            jobs_out = r.get("Modello_progetto.source.batchSize:histogram.field.sum", np.nan)
            if np.isnan(jobs_out):
                jobs_out = r.get("Modello_progetto.source.created:sum", np.nan)

            sim_time_limit = r.get("_meta.sim_time_limit_s", np.nan)
            warmup_period = r.get("_meta.warmup_period_s", np.nan)

            if np.isnan(sim_time_limit):
                sim_time_limit = 100000.0
            if np.isnan(warmup_period):
                warmup_period = 0.0

            measurement_time = max(sim_time_limit - warmup_period, 0.0)

            rows.append({
                "config": config,
                "m": M_VALUES[config],
                "run": run_idx,
                "L": r.get("Modello_progetto.server.numInSystem:timeavg", np.nan),
                "W": r.get("Modello_progetto.sink.lifeTime:mean", np.nan),
                "rho": r.get("Modello_progetto.server.busy:timeavg", np.nan),
                "vacation_mean": r.get("Modello_progetto.server.vacationDuration:mean", np.nan),
                "jobs_out": jobs_out,
                "sim_time": measurement_time,
            })

    return pd.DataFrame(rows)


def verifica_little(df):
    """
    Verifica la legge di Little per ogni configurazione:
    - throughput osservato = jobs usciti / sim_time
    - lambda_eff = throughput_osservato (gia' in jobs/s)
    - W_little = L / lambda_eff
    """
    if df.empty:
        print("\n[Little] Nessun dato disponibile per la verifica.")
        return pd.DataFrame()

    rows = []
    print("\n" + "=" * 60)
    print("  VERIFICA DI LITTLE")
    print("=" * 60)

    for config in CONFIGS:
        subset = df[df["config"] == config]
        if subset.empty:
            continue

        L_mean = subset["L"].mean()
        W_measured = subset["W"].mean()
        jobs_out_total = subset["jobs_out"].sum(min_count=1)
        sim_time_total = subset["sim_time"].sum(min_count=1)

        if pd.isna(jobs_out_total) or sim_time_total <= 0:
            jobs_throughput = np.nan
            lambda_eff = np.nan
            W_little = np.nan
            little_error_pct = np.nan
        else:
            jobs_throughput = jobs_out_total / sim_time_total
            lambda_eff = jobs_throughput
            W_little = L_mean / lambda_eff if lambda_eff > 0 else np.nan
            little_error_pct = abs(W_little - W_measured) / W_measured * 100 if W_measured > 0 else np.nan

        rows.append({
            "config": config,
            "m": M_VALUES[config],
            "L": L_mean,
            "W_measured": W_measured,
            "jobs_throughput": jobs_throughput,
            "lambda_eff": lambda_eff,
            "E_X": EX_MEAN,
            "W_little": W_little,
            "little_error_pct": little_error_pct,
        })

        print(f"  {config} (m={M_VALUES[config]}): "
              f"lambda_eff={lambda_eff:.6f}, W_mis={W_measured:.6f}, "
              f"W_little={W_little:.6f}, errore={little_error_pct:.3f}%")

    little_df = pd.DataFrame(rows)
    out_path = os.path.join(OUTPUT_DIR, "little_check.csv")
    little_df.to_csv(out_path, index=False, sep=';')
    print(f"  CSV Little salvato: {out_path}")
    return little_df


# ==========================================================================
# PARTE 3: Calcolo intervalli di confidenza
# ==========================================================================
def confidence_interval(data, confidence=0.95):
    """Calcola media, errore e intervallo di confidenza"""
    n = len(data)
    if n < 2:
        return np.mean(data), 0, (np.mean(data), np.mean(data))

    mean = np.mean(data)
    se = stats.sem(data)
    t_crit = stats.t.ppf((1 + confidence) / 2, df=n - 1)
    margin = t_crit * se
    ci = (mean - margin, mean + margin)
    return mean, margin, ci


def compute_performance_measures(all_data):
    """
    Calcola le 4 misure di prestazione richieste:
    a) Numero medio di utenti nel sistema
    b) Tempo medio di permanenza nel sistema
    c) Fattore di utilizzo
    d) Durata media del periodo di vacation (SVR)
    """
    results = {}

    for config in CONFIGS:
        runs = all_data[config]
        if not runs:
            continue

        # a) Numero medio di utenti nel sistema (numInSystem:timeavg)
        num_in_system = [r.get("Modello_progetto.server.numInSystem:timeavg", np.nan) for r in runs]
        num_in_system = [x for x in num_in_system if not np.isnan(x)]

        # b) Tempo medio di permanenza (lifeTime:mean dal Sink)
        life_time = [r.get("Modello_progetto.sink.lifeTime:mean", np.nan) for r in runs]
        life_time = [x for x in life_time if not np.isnan(x)]

        # c) Fattore di utilizzo (busy:timeavg)
        utilization = [r.get("Modello_progetto.server.busy:timeavg", np.nan) for r in runs]
        utilization = [x for x in utilization if not np.isnan(x)]

        # d) Durata media vacation (vacationDuration:mean)
        vacation_dur = [r.get("Modello_progetto.server.vacationDuration:mean", np.nan) for r in runs]
        vacation_dur = [x for x in vacation_dur if not np.isnan(x)]

        results[config] = {
            "num_in_system": {
                "values": num_in_system,
                "stats": confidence_interval(num_in_system, CONFIDENCE) if num_in_system else (0, 0, (0, 0))
            },
            "life_time": {
                "values": life_time,
                "stats": confidence_interval(life_time, CONFIDENCE) if life_time else (0, 0, (0, 0))
            },
            "utilization": {
                "values": utilization,
                "stats": confidence_interval(utilization, CONFIDENCE) if utilization else (0, 0, (0, 0))
            },
            "vacation_duration": {
                "values": vacation_dur,
                "stats": confidence_interval(vacation_dur, CONFIDENCE) if vacation_dur else (0, 0, (0, 0))
            }
        }

    return results


def print_results_table(perf_results):
    """Stampa la tabella riassuntiva delle misure di prestazione"""
    print("\n" + "=" * 100)
    print("  MISURE DI PRESTAZIONE - STIMA PUNTUALE E INTERVALLI DI CONFIDENZA (95%)")
    print("=" * 100)

    measures = [
        ("num_in_system",    "a) N. medio utenti nel sistema"),
        ("life_time",        "b) Tempo medio permanenza (s)"),
        ("utilization",      "c) Fattore di utilizzo"),
        ("vacation_duration","d) Durata media vacation (s)")
    ]

    for measure_key, measure_name in measures:
        print(f"\n  {measure_name}")
        print(f"  {'Config':<10} {'m':<6} {'Media':<14} {'±Margine':<12} {'IC 95%':<28} {'N.run':<6}")
        print(f"  {'-'*76}")

        for config in CONFIGS:
            if config not in perf_results:
                continue
            m = perf_results[config][measure_key]
            mean, margin, ci = m["stats"]
            n = len(m["values"])
            print(f"  {config:<10} {M_VALUES[config]:<6} {mean:<14.6f} {margin:<12.6f} "
                  f"[{ci[0]:.6f}, {ci[1]:.6f}]  {n:<6}")


def generate_plots(perf_results):
    """Genera grafici riassuntivi"""

    measures = [
        ("num_in_system",    "Numero medio utenti nel sistema", "N. utenti"),
        ("life_time",        "Tempo medio di permanenza nel sistema", "Tempo (s)"),
        ("utilization",      "Fattore di utilizzo del server", "Utilizzo"),
        ("vacation_duration","Durata media periodo di vacation (SVR)", "Durata (s)")
    ]

    # --- Grafico combinato ---
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for idx, (key, title, ylabel) in enumerate(measures):
        ax = axes[idx]
        m_vals = []
        means = []
        margins = []

        for config in CONFIGS:
            if config not in perf_results:
                continue
            mean, margin, ci = perf_results[config][key]["stats"]
            m_vals.append(M_VALUES[config])
            means.append(mean)
            margins.append(margin)

        ax.errorbar(m_vals, means, yerr=margins, fmt='o-', capsize=5,
                     markersize=8, linewidth=2, color='steelblue',
                     ecolor='tomato', capthick=2)
        ax.set_xlabel('Media inter-arrivo (m)')
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.set_xticks(m_vals)

    plt.suptitle('Misure di prestazione vs. media inter-arrivo (m)', fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(os.path.join(OUTPUT_DIR, 'misure_prestazione.png'), dpi=150)
    plt.close()
    print(f"\n  Grafico salvato: {os.path.join(OUTPUT_DIR, 'misure_prestazione.png')}")

    # --- Boxplot per ogni misura ---
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for idx, (key, title, ylabel) in enumerate(measures):
        ax = axes[idx]
        data_per_config = []
        labels = []

        for config in CONFIGS:
            if config not in perf_results:
                continue
            data_per_config.append(perf_results[config][key]["values"])
            labels.append(f"m={M_VALUES[config]}")

        bp = ax.boxplot(data_per_config, tick_labels=labels, patch_artist=True)
        colors = ['#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True, alpha=0.3, axis='y')

    plt.suptitle('Distribuzione misure di prestazione su 20 run', fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(os.path.join(OUTPUT_DIR, 'boxplot_prestazioni.png'), dpi=150)
    plt.close()
    print(f"  Grafico salvato: {os.path.join(OUTPUT_DIR, 'boxplot_prestazioni.png')}")


def save_csv(perf_results):
    """Salva i risultati in formato CSV"""
    rows = []
    measures = ["num_in_system", "life_time", "utilization", "vacation_duration"]
    measure_names = {
        "num_in_system": "N. medio utenti sistema",
        "life_time": "Tempo medio permanenza (s)",
        "utilization": "Fattore di utilizzo",
        "vacation_duration": "Durata media vacation (s)"
    }

    for config in CONFIGS:
        if config not in perf_results:
            continue
        for key in measures:
            mean, margin, ci = perf_results[config][key]["stats"]
            rows.append({
                "Configurazione": config,
                "m": M_VALUES[config],
                "Misura": measure_names[key],
                "Media": mean,
                "Margine ±": margin,
                "IC_inf": ci[0],
                "IC_sup": ci[1],
                "N_run": len(perf_results[config][key]["values"])
            })

    df = pd.DataFrame(rows)
    csv_path = os.path.join(OUTPUT_DIR, "risultati_prestazioni.csv")
    df.to_csv(csv_path, index=False, sep=';')
    print(f"  CSV salvato: {csv_path}")

    # Salva anche valori singoli per ogni run
    rows_detail = []
    for config in CONFIGS:
        if config not in perf_results:
            continue
        n = len(perf_results[config]["num_in_system"]["values"])
        for i in range(n):
            row = {"Config": config, "m": M_VALUES[config], "Run": i}
            for key in measures:
                vals = perf_results[config][key]["values"]
                row[measure_names[key]] = vals[i] if i < len(vals) else np.nan
            rows_detail.append(row)

    df_detail = pd.DataFrame(rows_detail)
    detail_path = os.path.join(OUTPUT_DIR, "risultati_dettaglio.csv")
    df_detail.to_csv(detail_path, index=False, sep=';')
    print(f"  CSV dettaglio salvato: {detail_path}")


def genera_report_finale(perf_results, little_df):
    """
    Genera un report finale compatto con tutte le metriche richieste.
    Colonne:
        m, L, L_ci_low, L_ci_high,
        W, W_ci_low, W_ci_high,
        rho, rho_ci_low, rho_ci_high,
        vacation_mean, vacation_ci_low, vacation_ci_high,
        W_little, little_error_pct
    """
    rows = []

    for config in CONFIGS:
        if config not in perf_results:
            continue

        L_mean, _, L_ci = perf_results[config]["num_in_system"]["stats"]
        W_mean, _, W_ci = perf_results[config]["life_time"]["stats"]
        rho_mean, _, rho_ci = perf_results[config]["utilization"]["stats"]
        vac_mean, _, vac_ci = perf_results[config]["vacation_duration"]["stats"]

        little_row = little_df[little_df["config"] == config] if not little_df.empty else pd.DataFrame()
        if not little_row.empty:
            W_little = little_row.iloc[0]["W_little"]
            little_error_pct = little_row.iloc[0]["little_error_pct"]
        else:
            W_little = np.nan
            little_error_pct = np.nan

        rows.append({
            "m": M_VALUES[config],
            "L": L_mean,
            "L_ci_low": L_ci[0],
            "L_ci_high": L_ci[1],
            "W": W_mean,
            "W_ci_low": W_ci[0],
            "W_ci_high": W_ci[1],
            "rho": rho_mean,
            "rho_ci_low": rho_ci[0],
            "rho_ci_high": rho_ci[1],
            "vacation_mean": vac_mean,
            "vacation_ci_low": vac_ci[0],
            "vacation_ci_high": vac_ci[1],
            "W_little": W_little,
            "little_error_pct": little_error_pct,
        })

    report_df = pd.DataFrame(rows).sort_values("m")
    report_path = os.path.join(OUTPUT_DIR, "report_finale.csv")
    report_df.to_csv(report_path, index=False, sep=';')
    print(f"  Report finale salvato: {report_path}")
    return report_df


# ==========================================================================
# MAIN
# ==========================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  ANALISI RISULTATI SIMULAZIONE")
    print("  Bulk Service Vacation Queue con N-policy")
    print("=" * 60)

    # 1. Raccolta dati scalari
    print("\n[1/4] Raccolta dati dai file .sca...")
    all_data = collect_all_scalars()
    for config in CONFIGS:
        print(f"  {config}: {len(all_data[config])} run trovati")

    # 2. Analisi transiente iniziale
    print("\n[2/4] Analisi del transiente iniziale...")
    warmup_results = analyze_transient_all_configs()

    # 3. Calcolo misure di prestazione e IC
    print("\n[3/4] Calcolo misure di prestazione e intervalli di confidenza...")
    perf_results = compute_performance_measures(all_data)
    print_results_table(perf_results)
    run_df = build_run_dataframe(all_data)
    little_df = verifica_little(run_df)

    # 4. Generazione grafici e CSV
    print("\n[4/4] Generazione grafici e file CSV...")
    generate_plots(perf_results)
    save_csv(perf_results)
    genera_report_finale(perf_results, little_df)

    print("\n" + "=" * 60)
    print("  ANALISI COMPLETATA")
    print(f"  Risultati salvati in: {OUTPUT_DIR}")
    print("=" * 60)
