#!/usr/bin/env python3
"""Caso 4 - Deteccion de anomalias en trafico TCP/IP (linea base estadistica vs Isolation Forest).

Modos:
  python caso4_anomalias.py --demo
      Datos SINTETICOS (permitido por la guia: "telemetria sintetica"). Sirve para probar el pipeline.
  python caso4_anomalias.py --benign benigno.pcap --attack syn_flood.pcap [--flash rafaga_legitima.pcap] [--window 1]
      PCAP reales (requiere tshark en el PATH). El PCAP de ataque debe venir de la persona 1 o de un
      dataset publico; el benigno, de trafico de laboratorio propio.

Salidas en --out (por defecto ./salida_caso4): features.csv, metricas.json, scores.png, confusion.png, pr_curve.png
"""
import argparse, json, os, subprocess
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (precision_score, recall_score, f1_score, precision_recall_curve,
                             average_precision_score, confusion_matrix, roc_curve)

FEATURES = ["conns_per_min", "bytes_per_flow", "flow_duration", "syn_ratio",
            "rst_ratio", "fin_ratio", "req_resp_ratio", "unique_src"]
SEED = 42


# ---------------------------------------------------------------- extraccion
def _flag(v):  # tshark antiguo: True/False; nuevo: 1/0
    value = str(v).strip().lower()
    if value in ("1", "true", "yes"):
        return 1
    if value in ("0", "false", "no"):
        return 0
    raise ValueError(f"flag TCP no reconocida: {v!r}")


def packets_from_pcap(path):
    cmd = ["tshark", "-r", path, "-T", "fields", "-E", "separator=\t",
           "-e", "frame.time_epoch", "-e", "ip.src", "-e", "ip.dst", "-e", "frame.len",
           "-e", "tcp.stream", "-e", "tcp.flags.syn", "-e", "tcp.flags.ack",
           "-e", "tcp.flags.fin", "-e", "tcp.flags.reset", "-Y", "tcp"]
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                         errors="replace", check=True).stdout
    rows = []
    for ln in out.splitlines():
        p = ln.split("\t")
        if not ln.strip():
            continue
        if len(p) < 9 or not p[0].strip():
            raise ValueError(f"fila tshark incompleta en {path!r}: {ln!r}")
        if any(not p[i].strip() for i in (1, 2, 3, 4, 5, 6, 7, 8)):
            raise ValueError(f"fila tshark con campos faltantes en {path!r}: {ln!r}")
        try:
            timestamp = float(p[0].strip())
            frame_len = int(p[3].strip())
        except ValueError as exc:
            raise ValueError(f"fila tshark inválida en {path!r}: {ln!r}") from exc
        rows.append(dict(t=timestamp, src=p[1].strip(), dst=p[2].strip(),
                         bytes=frame_len, stream=p[4].strip(),
                         syn=_flag(p[5]), ack=_flag(p[6]),
                         fin=_flag(p[7]), rst=_flag(p[8])))
    return pd.DataFrame(rows)


def window_features(pk, window):
    """Una fila por ventana temporal de `window` segundos."""
    if window <= 0:
        raise ValueError("window debe ser mayor que cero")
    if pk.empty:
        return pd.DataFrame(columns=FEATURES + ["t_start"])
    pk = pk.copy()
    pk["t"] -= pk["t"].min()
    pk["w"] = (pk["t"] // window).astype(int)
    rows = []
    for w, g in pk.groupby("w"):
        n = len(g)
        syn_only = int(((g.syn == 1) & (g.ack == 0)).sum())
        synack = int(((g.syn == 1) & (g.ack == 1)).sum())
        flows = g.groupby("stream")
        dur = (flows["t"].max() - flows["t"].min()).mean() if g["stream"].nunique() else 0.0
        rows.append(dict(
            t_start=w * window,
            stream_ids=tuple(sorted(str(stream) for stream in g["stream"].unique())),
            conns_per_min=syn_only / window * 60.0,
            bytes_per_flow=g["bytes"].sum() / max(g["stream"].nunique(), 1),
            flow_duration=dur,
            syn_ratio=syn_only / n,
            rst_ratio=g.rst.sum() / n,
            fin_ratio=g.fin.sum() / n,
            req_resp_ratio=syn_only / max(synack, 1),   # SYN sin SYN/ACK => handshake incompleto
            unique_src=g["src"].nunique()))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- sinteticos
def synthetic(n_benign=600, n_attack=60, n_flash=40):
    """Benigno (ruido), 'flash crowd' legitimo (falso positivo esperable) y SYN flood."""
    r = np.random.default_rng(SEED)

    def block(n, conns, bpf, dur, syn, rst, fin, rr, usrc, label, kind):
        d = pd.DataFrame(dict(
            conns_per_min=r.normal(conns, conns * .15, n).clip(1),
            bytes_per_flow=r.normal(bpf, bpf * .15, n).clip(60),
            flow_duration=r.normal(dur, dur * .2, n).clip(.01),
            syn_ratio=r.normal(syn, syn * .15, n).clip(.001, 1),
            rst_ratio=r.normal(rst, rst * .3, n).clip(0, 1),
            fin_ratio=r.normal(fin, fin * .2, n).clip(0, 1),
            req_resp_ratio=r.normal(rr, rr * .08, n).clip(.5),
            unique_src=r.normal(usrc, max(usrc * .2, 1), n).clip(1).round()))
        d["label"], d["kind"] = label, kind
        return d

    ben = block(n_benign, 300, 9000, 1.5, .08, .01, .06, 1.02, 12, 0, "benigno")
    flash = block(n_flash, 900, 7000, 1.0, .14, .01, .08, 1.05, 60, 0, "flash_crowd")  # legitimo
    atk = block(n_attack, 18000, 120, .02, .85, .02, .005, 25.0, 700, 1, "syn_flood")
    ben["t_start"] = np.arange(len(ben))
    flash["t_start"] = np.arange(len(flash)) + len(ben)
    atk["t_start"] = np.arange(len(atk)) + len(ben) + len(flash)
    return ben, flash, atk


# ---------------------------------------------------------------- evaluacion
def recall_at_fpr(y, score, max_fpr=0.01):
    fpr, tpr, _ = roc_curve(y, score)
    ok = tpr[fpr <= max_fpr]
    return float(ok.max()) if len(ok) else 0.0


def evaluate(train, validation, test):
    if train.empty or validation.empty or test.empty:
        raise ValueError("train, validation y test deben contener ventanas")
    if len(np.unique(test["label"].values)) < 2:
        raise ValueError("test debe contener muestras normales y de ataque")
    sc = StandardScaler().fit(train[FEATURES])
    Xtr, Xte = sc.transform(train[FEATURES]), sc.transform(test[FEATURES])
    Xval = sc.transform(validation[FEATURES])
    y = test["label"].values

    # Linea base estadistica: |z| maximo > 3 (referencia de la guia)
    z = np.abs(Xte).max(axis=1)
    pred_stat = (z > 3).astype(int)

    # Isolation Forest entrenado SOLO con benigno; el umbral se calibra en
    # validación benigna, sin consultar las etiquetas ni scores de test.
    iso = IsolationForest(n_estimators=200, random_state=SEED).fit(Xtr)
    thr = np.percentile(-iso.score_samples(Xval), 99)
    s_if = -iso.score_samples(Xte)
    pred_if = (s_if > thr).astype(int)

    res = {
        "prevalencia_ataque_en_test": float(y.mean()),
        "nota_prevalencia": (
            "prevalencia determinada por la composición de las capturas; "
            "no representa necesariamente producción"
        ),
    }
    for name, pred, s in [("baseline_3sigma", pred_stat, z), ("isolation_forest", pred_if, s_if)]:
        tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
        res[name] = dict(precision=float(precision_score(y, pred, zero_division=0)),
                         recall=float(recall_score(y, pred, zero_division=0)),
                         f1=float(f1_score(y, pred, zero_division=0)),
                         pr_auc=float(average_precision_score(y, s)),
                         recall_at_fpr_1pct=recall_at_fpr(y, s),
                         tn=int(tn), fp=int(fp), fn=int(fn), tp=int(tp))
    if "kind" in test:  # falsos positivos por tipo de trafico benigno
        for k in test.loc[test.label == 0, "kind"].unique():
            m = (test.kind == k).values
            res[f"fp_rate_{k}"] = {"baseline_3sigma": float(pred_stat[m].mean()),
                                   "isolation_forest": float(pred_if[m].mean())}
    return res, s_if, z, thr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--benign"); ap.add_argument("--attack")
    ap.add_argument("--flash", help="PCAP de rafaga LEGITIMA (prueba de carga benigna); se evalua como benigno")
    ap.add_argument("--window", type=float, default=1.0, help="segundos por ventana")
    ap.add_argument("--out", default="salida_caso4")
    a = ap.parse_args()
    if a.window <= 0:
        ap.error("--window debe ser mayor que cero")
    os.makedirs(a.out, exist_ok=True)

    if a.demo:
        ben, flash, atk = synthetic()
    elif a.benign and a.attack:
        ben = window_features(packets_from_pcap(a.benign), a.window); ben["label"], ben["kind"] = 0, "benigno"
        atk = window_features(packets_from_pcap(a.attack), a.window); atk["label"], atk["kind"] = 1, "ataque"
        flash = ben.iloc[0:0]
        if a.flash:
            flash = window_features(packets_from_pcap(a.flash), a.window); flash["label"], flash["kind"] = 0, "flash_crowd"
    else:
        ap.error("usa --demo o (--benign y --attack)")

    # Split temporal: 60 % entrena, 10 % calibra el umbral y el resto evalúa.
    # Los flujos que atraviesan la frontera se excluyen de train/validación.
    ben = ben.sort_values("t_start").reset_index(drop=True)
    if len(ben) < 3:
        ap.error("el benigno debe producir al menos tres ventanas")
    cut = max(1, int(len(ben) * 0.6))
    val_end = min(cut + max(1, int(len(ben) * 0.1)), len(ben) - 1)
    train = ben.iloc[:cut].copy()
    validation = ben.iloc[cut:val_end].copy()
    benign_test = ben.iloc[val_end:].copy()

    if "stream_ids" in ben:
        def stream_set(frame):
            return {stream for ids in frame["stream_ids"] for stream in ids}

        heldout = stream_set(pd.concat([validation, benign_test], ignore_index=True))
        train = train[~train["stream_ids"].map(lambda ids: bool(set(ids) & heldout))]
        validation = validation[~validation["stream_ids"].map(
            lambda ids: bool(set(ids) & stream_set(benign_test)))]

    test = pd.concat([benign_test, flash, atk], ignore_index=True)
    if train.empty or validation.empty:
        ap.error("el split dejó train o validation vacío; revise las ventanas y los flujos")
    pd.concat([
        train.assign(split="train"),
        validation.assign(split="validation"),
        test.assign(split="test"),
    ]).to_csv(f"{a.out}/features.csv", index=False)

    res, s_if, z, thr = evaluate(train, validation, test)
    res["n_train"], res["n_validation"], res["n_test"] = len(train), len(validation), len(test)
    json.dump(res, open(f"{a.out}/metricas.json", "w"), indent=2)
    print(json.dumps(res, indent=2))

    fig, ax = plt.subplots(figsize=(9, 3.5))
    ax.plot(s_if, lw=.8, label="score Isolation Forest")
    ax.axhline(thr, color="r", ls="--", label="umbral (p99 validación)")
    ax.scatter(np.where(test.label.values == 1)[0], s_if[test.label.values == 1], s=8, c="k", label="ataque (etiqueta)")
    ax.set_xlabel("ventana de prueba (orden temporal)"); ax.set_ylabel("score"); ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(f"{a.out}/scores.png", dpi=150)

    # Matrices de confusion (una por detector) y curva Precision-Recall con la prevalencia como referencia
    fig, axs = plt.subplots(1, 2, figsize=(7, 3))
    for ax, n, t in zip(axs, ("baseline_3sigma", "isolation_forest"), ("Linea base 3-sigma", "Isolation Forest")):
        m = np.array([[res[n]["tn"], res[n]["fp"]], [res[n]["fn"], res[n]["tp"]]])
        ax.imshow(m, cmap="Blues")
        for (i, j), v in np.ndenumerate(m):
            ax.text(j, i, str(v), ha="center", va="center")
        ax.set_xticks([0, 1], ["pred normal", "pred anomalo"], fontsize=7)
        ax.set_yticks([0, 1], ["real normal", "real ataque"], fontsize=7); ax.set_title(t, fontsize=9)
    fig.tight_layout(); fig.savefig(f"{a.out}/confusion.png", dpi=150)

    p, r, _ = precision_recall_curve(test["label"].values, s_if)
    fig, ax = plt.subplots(figsize=(4, 3.2))
    ax.plot(r, p, label=f"IF (PR-AUC={res['isolation_forest']['pr_auc']:.3f})")
    ax.axhline(res["prevalencia_ataque_en_test"], color="gray", ls="--", label="prevalencia del test")
    ax.set_xlabel("recall"); ax.set_ylabel("precision"); ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(f"{a.out}/pr_curve.png", dpi=150)


if __name__ == "__main__":
    main()
