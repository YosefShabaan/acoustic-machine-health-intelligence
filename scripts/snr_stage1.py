import os
import shutil
import zipfile
import wave
import glob
import sys
import io


BASE = r"D:\PDM_Data"
ZIP_DIR = os.path.join(BASE, "Zips")
MIMII_DIR = os.path.join(BASE, "MIMII")
SEARCH_DIRS = [
    BASE,
    ZIP_DIR,
    r"C:\Users\joe\Downloads",
    r"C:\Users\joe\IOT",
]

SNRS = [
    {
        "label": "-6 dB",
        "key": "minus6",
        "zip": "-6_dB_fan.zip",
        "dest": os.path.join(MIMII_DIR, "fan_minus6dB", "id_00"),
        "tokens": ["-6_db", "minus6"],
    },
    {
        "label": "0 dB",
        "key": "0",
        "zip": "0_dB_fan.zip",
        "dest": os.path.join(MIMII_DIR, "fan_0dB", "id_00"),
        "tokens": ["0_db"],
    },
    {
        "label": "+6 dB",
        "key": "plus6",
        "zip": "6_dB_fan.zip",
        "dest": os.path.join(MIMII_DIR, "fan_plus6dB", "id_00"),
        "tokens": ["+6_db", "6_db", "plus6"],
    },
]

REQUIRED_DIRS = [
    ZIP_DIR,
    MIMII_DIR,
    os.path.join(MIMII_DIR, "fan_minus6dB", "id_00"),
    os.path.join(MIMII_DIR, "fan_0dB", "id_00"),
    os.path.join(MIMII_DIR, "fan_plus6dB", "id_00"),
    os.path.join(MIMII_DIR, "processed"),
]

stage1_summary = []
stage2_summary = {}
stage3_summary = {}
stage4_summary = {}
anomalies = []


def log(message):
    print(message)
    sys.stdout.flush()


def norm_zip_name(path):
    return os.path.basename(path).lower().replace(" ", "_")


def abspath(path):
    return os.path.abspath(path).lower()


def is_target_zip(path, snr):
    name = norm_zip_name(path)
    expected = snr["zip"].lower()
    if name == expected:
        return True
    if not name.endswith(".zip") or "fan" not in name:
        return False
    if snr["key"] == "plus6" and "-6_db" in name:
        return False
    for token in snr["tokens"]:
        if token in name:
            return True
    return False


def path_is_under(path, directory):
    try:
        return os.path.commonpath([os.path.abspath(path), os.path.abspath(directory)]) == os.path.abspath(directory)
    except ValueError:
        return False


def find_candidates(snr):
    candidates = []
    seen = {}
    for search_dir in SEARCH_DIRS:
        if not os.path.isdir(search_dir):
            continue
        for path in glob.glob(os.path.join(search_dir, "*.zip")):
            if is_target_zip(path, snr):
                full = os.path.abspath(path)
                key = full.lower()
                if key not in seen:
                    seen[key] = True
                    candidates.append(full)
    return candidates


def size_of(path):
    return os.path.getsize(path)


def classify_candidate(path):
    full = os.path.abspath(path)
    if abspath(os.path.dirname(full)) == abspath(BASE):
        return "D_ROOT"
    if path_is_under(full, ZIP_DIR):
        return "D_ZIPS"
    if full.lower().startswith("c:\\"):
        return "C"
    return "OTHER"


def consolidate_zip(snr):
    expected_final = os.path.join(ZIP_DIR, snr["zip"])
    result = {
        "found": [],
        "final": expected_final,
        "final_size": None,
        "match": "N/A",
        "skip": False,
        "reason": "",
        "action": "",
    }
    candidates = find_candidates(snr)
    log("")
    log("SNR {0}: target zip {1}".format(snr["label"], snr["zip"]))
    if not candidates:
        result["skip"] = True
        result["reason"] = "missing"
        anomalies.append("{0}: zip missing".format(snr["label"]))
        log("  FOUND: MISSING")
        log("  SKIPPED: missing zip")
        return result

    for path in candidates:
        try:
            sz = size_of(path)
            result["found"].append((path, sz))
            log("  FOUND: {0} ({1} bytes)".format(path, sz))
        except Exception as exc:
            result["found"].append((path, None))
            anomalies.append("{0}: could not size {1}: {2}".format(snr["label"], path, exc))
            log("  FOUND: {0} (SIZE ERROR: {1})".format(path, exc))

    d_root = []
    d_zips = []
    c_sources = []
    for path, _ in result["found"]:
        kind = classify_candidate(path)
        if kind == "D_ROOT":
            d_root.append(path)
        elif kind == "D_ZIPS":
            d_zips.append(path)
        elif kind == "C":
            c_sources.append(path)

    try:
        if d_root:
            source = d_root[0]
            if abspath(source) == abspath(expected_final):
                result["action"] = "already in D:\\PDM_Data\\Zips"
            elif os.path.exists(expected_final):
                result["action"] = "kept existing D:\\PDM_Data\\Zips copy"
                anomalies.append("{0}: duplicate zip remains at D root because final path already exists".format(snr["label"]))
            else:
                shutil.move(source, expected_final)
                result["action"] = "moved from D:\\PDM_Data root"
        elif os.path.exists(expected_final):
            result["action"] = "already in D:\\PDM_Data\\Zips"
        elif d_zips:
            source = d_zips[0]
            if abspath(source) != abspath(expected_final):
                shutil.copy2(source, expected_final)
                result["action"] = "copied variant inside D:\\PDM_Data\\Zips to expected name"
            else:
                result["action"] = "already in D:\\PDM_Data\\Zips"
        elif c_sources:
            source = c_sources[0]
            shutil.copy2(source, expected_final)
            result["action"] = "copied from C:"
            c_size = size_of(source)
            d_size = size_of(expected_final)
            result["match"] = "MATCH" if c_size == d_size else "MISMATCH"
            if c_size != d_size:
                result["skip"] = True
                result["reason"] = "size mismatch after copy from C:"
                anomalies.append("{0}: copied size mismatch C={1} D={2}".format(snr["label"], c_size, d_size))
        else:
            result["skip"] = True
            result["reason"] = "no usable source location"
            anomalies.append("{0}: found zip candidates but no usable source location".format(snr["label"]))
    except Exception as exc:
        result["skip"] = True
        result["reason"] = str(exc)
        anomalies.append("{0}: Stage 2 exception: {1}".format(snr["label"], exc))

    if not os.path.exists(expected_final):
        result["skip"] = True
        if not result["reason"]:
            result["reason"] = "final zip missing after consolidation"
        anomalies.append("{0}: final zip missing after consolidation".format(snr["label"]))
    else:
        result["final_size"] = size_of(expected_final)

    log("  ACTION: {0}".format(result["action"] if result["action"] else "none"))
    log("  FINAL: {0} ({1} bytes)".format(expected_final, result["final_size"]))
    log("  COPY SIZE CHECK: {0}".format(result["match"]))
    if result["skip"]:
        log("  SKIPPED: {0}".format(result["reason"]))
    return result


def zip_norm(name):
    return name.replace("\\", "/")


def contains_part(name, part):
    return part in ("/" + zip_norm(name).lower())


def inspect_zip(snr, zip_path, skipped, skip_reason):
    result = {
        "normal_count": 0,
        "abnormal_count": 0,
        "framerate": None,
        "channels": None,
        "duration": None,
        "pass": False,
        "reason": skip_reason if skipped else "",
        "prefix": "N/A",
    }
    log("")
    log("SNR {0}: zip inspection".format(snr["label"]))
    if skipped:
        log("  SKIPPED: {0}".format(skip_reason))
        return result

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            normalized = [(name, zip_norm(name)) for name in names]
            id_entries = [(name, norm) for name, norm in normalized if "fan/id_00" in norm.lower()]
            fan_id_exists = len(id_entries) > 0
            if fan_id_exists:
                first_norm = id_entries[0][1]
                idx = first_norm.lower().find("fan/id_00")
                result["prefix"] = first_norm[:idx + len("fan/id_00")]

            normal_wavs = []
            abnormal_wavs = []
            normal_exists = False
            abnormal_exists = False
            for name, norm in normalized:
                lower = "/" + norm.lower()
                if "/id_00/normal/" in lower:
                    normal_exists = True
                    if lower.endswith(".wav"):
                        normal_wavs.append(name)
                if "/id_00/abnormal/" in lower:
                    abnormal_exists = True
                    if lower.endswith(".wav"):
                        abnormal_wavs.append(name)

            normal_wavs.sort()
            abnormal_wavs.sort()
            result["normal_count"] = len(normal_wavs)
            result["abnormal_count"] = len(abnormal_wavs)

            log("  fan/id_00 prefix: {0}".format(result["prefix"]))
            log("  fan/id_00 exists: {0}".format("YES" if fan_id_exists else "NO"))
            log("  id_00/normal exists: {0}".format("YES" if normal_exists else "NO"))
            log("  id_00/abnormal exists: {0}".format("YES" if abnormal_exists else "NO"))
            log("  normal wav count: {0}".format(result["normal_count"]))
            log("  abnormal wav count: {0}".format(result["abnormal_count"]))

            if normal_wavs:
                probe_name = normal_wavs[0]
                data = zf.read(probe_name)
                with wave.open(io.BytesIO(data), "rb") as wf:
                    result["framerate"] = wf.getframerate()
                    result["channels"] = wf.getnchannels()
                    frames = wf.getnframes()
                    result["duration"] = frames / float(result["framerate"]) if result["framerate"] else 0.0
                log("  probe wav: {0}".format(probe_name))
                log("  probe framerate: {0}".format(result["framerate"]))
                log("  probe channels: {0}".format(result["channels"]))
                log("  probe duration sec: {0:.3f}".format(result["duration"]))
            else:
                log("  probe wav: NONE")

            reasons = []
            if not fan_id_exists:
                reasons.append("fan/id_00 missing")
            if not normal_exists:
                reasons.append("normal missing")
            if not abnormal_exists:
                reasons.append("abnormal missing")
            if result["normal_count"] < 250:
                reasons.append("normal_count < 250")
            if result["abnormal_count"] < 50:
                reasons.append("abnormal_count < 50")
            if result["framerate"] != 16000:
                reasons.append("framerate != 16000")
            if result["channels"] != 8:
                reasons.append("channels != 8")
            if result["duration"] is None or result["duration"] < 9.5 or result["duration"] > 10.5:
                reasons.append("duration not about 10 sec")

            if reasons:
                result["pass"] = False
                result["reason"] = ", ".join(reasons)
                anomalies.append("{0}: Stage 3 FAIL: {1}".format(snr["label"], result["reason"]))
                log("  RESULT: FAIL({0})".format(result["reason"]))
            else:
                result["pass"] = True
                result["reason"] = "PASS"
                log("  RESULT: PASS")
    except Exception as exc:
        result["pass"] = False
        result["reason"] = str(exc)
        anomalies.append("{0}: Stage 3 exception: {1}".format(snr["label"], exc))
        log("  RESULT: FAIL({0})".format(exc))
    return result


def extract_passed_snr(snr, zip_path, inspect_result):
    result = {
        "normal_disk": 0,
        "abnormal_disk": 0,
        "status": "SKIPPED",
        "reason": "",
    }
    log("")
    log("SNR {0}: selective extraction".format(snr["label"]))
    normal_dir = os.path.join(snr["dest"], "normal")
    abnormal_dir = os.path.join(snr["dest"], "abnormal")
    if not inspect_result["pass"]:
        result["reason"] = inspect_result["reason"]
        log("  SKIPPED: {0}".format(result["reason"]))
        return result

    try:
        os.makedirs(normal_dir, exist_ok=True)
        os.makedirs(abnormal_dir, exist_ok=True)
        written = {}
        with zipfile.ZipFile(zip_path, "r") as zf:
            for name in zf.namelist():
                norm = zip_norm(name)
                lower = "/" + norm.lower()
                if not lower.endswith(".wav"):
                    continue
                if "/id_00/normal/" in lower:
                    dest_dir = normal_dir
                elif "/id_00/abnormal/" in lower:
                    dest_dir = abnormal_dir
                else:
                    continue

                filename = os.path.basename(norm)
                if not filename:
                    continue
                dest_path = os.path.join(dest_dir, filename)
                dest_key = dest_path.lower()
                if dest_key in written:
                    anomalies.append("{0}: duplicate flattened target {1}".format(snr["label"], dest_path))
                written[dest_key] = True
                with open(dest_path, "wb") as out:
                    out.write(zf.read(name))

        result["normal_disk"] = len(glob.glob(os.path.join(normal_dir, "*.wav")))
        result["abnormal_disk"] = len(glob.glob(os.path.join(abnormal_dir, "*.wav")))
        result["status"] = "DONE"
        log("  disk normal wav count: {0}".format(result["normal_disk"]))
        log("  disk abnormal wav count: {0}".format(result["abnormal_disk"]))

        if result["normal_disk"] != inspect_result["normal_count"]:
            anomalies.append("{0}: normal disk count {1} != zip count {2}".format(snr["label"], result["normal_disk"], inspect_result["normal_count"]))
        if result["abnormal_disk"] != inspect_result["abnormal_count"]:
            anomalies.append("{0}: abnormal disk count {1} != zip count {2}".format(snr["label"], result["abnormal_disk"], inspect_result["abnormal_count"]))

        if result["normal_disk"] == inspect_result["normal_count"] and result["abnormal_disk"] == inspect_result["abnormal_count"]:
            log("  verification: disk counts MATCH in-zip counts")
        else:
            log("  verification: disk counts MISMATCH in-zip counts")
    except Exception as exc:
        result["status"] = "FAILED"
        result["reason"] = str(exc)
        anomalies.append("{0}: Stage 4 exception: {1}".format(snr["label"], exc))
        log("  FAILED: {0}".format(exc))
    return result


def print_final_report():
    log("")
    log("FINAL REPORT")
    log("Stage 1:")
    for path, status in stage1_summary:
        log("  {0}: {1}".format(status, path))

    log("Stage 2:")
    for snr in SNRS:
        item = stage2_summary.get(snr["key"], {})
        log("  {0}: final={1}, size={2}, match={3}, skipped={4}, reason={5}".format(
            snr["label"],
            item.get("final", "N/A"),
            item.get("final_size", "N/A"),
            item.get("match", "N/A"),
            "YES" if item.get("skip") else "NO",
            item.get("reason", ""),
        ))

    log("Stage 3:")
    for snr in SNRS:
        item = stage3_summary.get(snr["key"], {})
        duration = item.get("duration")
        duration_text = "N/A" if duration is None else "{0:.3f}".format(duration)
        log("  {0}: normal={1}, abnormal={2}, framerate={3}, channels={4}, duration={5}, result={6}".format(
            snr["label"],
            item.get("normal_count", "N/A"),
            item.get("abnormal_count", "N/A"),
            item.get("framerate", "N/A"),
            item.get("channels", "N/A"),
            duration_text,
            "PASS" if item.get("pass") else "FAIL({0})".format(item.get("reason", "")),
        ))

    log("Stage 4:")
    for snr in SNRS:
        item = stage4_summary.get(snr["key"], {})
        log("  {0}: status={1}, disk_normal={2}, disk_abnormal={3}, reason={4}".format(
            snr["label"],
            item.get("status", "N/A"),
            item.get("normal_disk", "N/A"),
            item.get("abnormal_disk", "N/A"),
            item.get("reason", ""),
        ))

    if anomalies:
        log("Anomalies: {0}".format("; ".join(anomalies)))
    else:
        log("Anomalies: None")


def main():
    log("MIMII SNR STAGE 1")
    log("")
    log("STAGE 1 - Layout")
    for path in REQUIRED_DIRS:
        existed = os.path.isdir(path)
        os.makedirs(path, exist_ok=True)
        status = "existed" if existed else "created"
        stage1_summary.append((path, status))
        log("  {0}: {1}".format(status.upper(), path))

    log("")
    log("STAGE 2 - Consolidate zips into D:\\PDM_Data\\Zips")
    for snr in SNRS:
        stage2_summary[snr["key"]] = consolidate_zip(snr)

    log("")
    log("STAGE 3 - Inspect via zipfile")
    for snr in SNRS:
        stage2 = stage2_summary[snr["key"]]
        stage3_summary[snr["key"]] = inspect_zip(snr, stage2["final"], stage2["skip"], stage2["reason"])

    log("")
    log("STAGE 4 - Selective extraction")
    for snr in SNRS:
        stage2 = stage2_summary[snr["key"]]
        stage3 = stage3_summary[snr["key"]]
        stage4_summary[snr["key"]] = extract_passed_snr(snr, stage2["final"], stage3)

    print_final_report()


if __name__ == "__main__":
    main()
