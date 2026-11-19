#!/usr/bin/env python3
"""RF Link Budget, LoRa CSS Physical Layer, and Fresnel Clearance Analyzer.

Models the SX1278 433 MHz telemetry transceiver configuration used in
ESP32_Lora_TX.ino and ESP32_Lora_RX.ino (SF=12, BW=125 kHz, CR=4/8, P_tx=20 dBm).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict

# Semtech SX1278 minimum required SNR per Spreading Factor (dB)
LORA_SNR_LIMIT_DB: Dict[int, float] = {
    7: -7.5,
    8: -10.0,
    9: -12.5,
    10: -15.0,
    11: -17.5,
    12: -20.0,
}


@dataclass(frozen=True)
class LinkBudgetResult:
    distance_km: float
    freq_mhz: float
    fspl_db: float
    symbol_duration_ms: float
    symbol_rate_sps: float
    bit_rate_bps: float
    time_on_air_ms: float
    processing_gain_db: float
    rx_sensitivity_dbm: float
    received_power_dbm: float
    link_margin_db: float
    fresnel_r1_max_m: float
    fresnel_60pct_clearance_m: float


def compute_fspl_db(distance_km: float, freq_mhz: float) -> float:
    """Free-Space Path Loss in dB: 20*log10(d_km) + 20*log10(f_MHz) + 32.44."""
    if distance_km <= 0 or freq_mhz <= 0:
        raise ValueError("distance_km and freq_mhz must be positive.")
    return 20.0 * math.log10(distance_km) + 20.0 * math.log10(freq_mhz) + 32.44


def compute_processing_gain_db(sf: int) -> float:
    """LoRa Chirp Spread Spectrum processing gain: 10*log10(2^SF) dB."""
    if sf not in LORA_SNR_LIMIT_DB:
        raise ValueError(f"Unsupported spreading factor: {sf}")
    return 10.0 * math.log10(2 ** sf)


def compute_rx_sensitivity_dbm(bw_hz: float, sf: int, noise_figure_db: float = 6.0) -> float:
    """SX1278 theoretical sensitivity: -174 + 10*log10(BW) + NF + SNR_limit."""
    if bw_hz <= 0:
        raise ValueError("bw_hz must be positive.")
    snr_limit = LORA_SNR_LIMIT_DB[sf]
    return -174.0 + 10.0 * math.log10(bw_hz) + noise_figure_db + snr_limit


def compute_time_on_air_ms(
    payload_bytes: int,
    sf: int = 12,
    bw_hz: float = 125_000.0,
    cr_denom: int = 8,
    preamble_symbols: int = 8,
    explicit_header: bool = True,
    crc_enabled: bool = True,
) -> tuple[float, float, float, float]:
    """Compute symbol duration, symbol rate, bit rate, and packet Time-on-Air."""
    if payload_bytes < 0 or cr_denom not in (5, 6, 7, 8):
        raise ValueError("Invalid payload length or coding rate denominator (expected 5..8).")

    cr = cr_denom - 4  # Semtech CR coding parameter: 1..4 for 4/5..4/8
    t_sym_s = (2 ** sf) / bw_hz
    t_sym_ms = t_sym_s * 1000.0
    symbol_rate = 1.0 / t_sym_s
    bit_rate = sf * symbol_rate * (4.0 / (4.0 + cr))

    ih = 0 if explicit_header else 1
    crc = 1 if crc_enabled else 0
    de = 1 if t_sym_ms >= 16.0 else 0  # Low data rate optimization threshold

    numerator = 8 * payload_bytes - 4 * sf + 28 + 16 * crc - 20 * ih
    denom = 4 * (sf - 2 * de)
    payload_sym_nb = 8 + max(math.ceil(numerator / denom) * (cr + 4), 0)

    t_preamble_ms = (preamble_symbols + 4.25) * t_sym_ms
    t_payload_ms = payload_sym_nb * t_sym_ms
    return t_sym_ms, symbol_rate, bit_rate, t_preamble_ms + t_payload_ms


def compute_fresnel_radius_m(distance_km: float, freq_mhz: float) -> float:
    """Maximum First Fresnel Zone radius at path midpoint: 8.657 * sqrt(d_km / f_GHz)."""
    freq_ghz = freq_mhz / 1000.0
    return 8.657 * math.sqrt(distance_km / freq_ghz)


def analyze_lora_link(
    distance_km: float,
    freq_mhz: float = 433.0,
    tx_power_dbm: float = 20.0,
    tx_gain_dbi: float = 2.15,
    rx_gain_dbi: float = 9.0,
    cable_loss_db: float = 1.5,
    sf: int = 12,
    bw_hz: float = 125_000.0,
    cr_denom: int = 8,
    payload_bytes: int = 24,
    noise_figure_db: float = 6.0,
) -> LinkBudgetResult:
    """Compute complete end-to-end RF link budget and CSS modulation metrics."""
    fspl = compute_fspl_db(distance_km, freq_mhz)
    proc_gain = compute_processing_gain_db(sf)
    rx_sens = compute_rx_sensitivity_dbm(bw_hz, sf, noise_figure_db)
    t_sym_ms, r_s, r_b, toa_ms = compute_time_on_air_ms(
        payload_bytes=payload_bytes, sf=sf, bw_hz=bw_hz, cr_denom=cr_denom
    )
    rx_power = tx_power_dbm + tx_gain_dbi + rx_gain_dbi - cable_loss_db - fspl
    margin = rx_power - rx_sens
    fresnel_r1 = compute_fresnel_radius_m(distance_km, freq_mhz)

    return LinkBudgetResult(
        distance_km=distance_km,
        freq_mhz=freq_mhz,
        fspl_db=round(fspl, 2),
        symbol_duration_ms=round(t_sym_ms, 2),
        symbol_rate_sps=round(r_s, 2),
        bit_rate_bps=round(r_b, 2),
        time_on_air_ms=round(toa_ms, 2),
        processing_gain_db=round(proc_gain, 2),
        rx_sensitivity_dbm=round(rx_sens, 2),
        received_power_dbm=round(rx_power, 2),
        link_margin_db=round(margin, 2),
        fresnel_r1_max_m=round(fresnel_r1, 2),
        fresnel_60pct_clearance_m=round(0.6 * fresnel_r1, 2),
    )


if __name__ == "__main__":
    print("433 MHz LoRa CSS Link Budget (SF=12, BW=125 kHz, CR=4/8, P_tx=20 dBm, Yagi RX=9 dBi):")
    for d in (0.5, 1.0, 5.0, 10.0, 20.0):
        res = analyze_lora_link(distance_km=d)
        print(
            f"  d={res.distance_km:4.1f} km | FSPL={res.fspl_db:6.2f} dB | "
            f"P_rx={res.received_power_dbm:7.2f} dBm | Sens={res.rx_sensitivity_dbm:7.2f} dBm | "
            f"Margin={res.link_margin_db:6.2f} dB | F1(60%)={res.fresnel_60pct_clearance_m:5.2f} m | "
            f"ToA={res.time_on_air_ms:.2f} ms"
        )
