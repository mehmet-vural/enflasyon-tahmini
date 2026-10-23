"""Aylık TÜFE endeksi (OECD) ve aylık ortalama USD/TRY kuru (ECB) verisini çeker.

Kaynaklar (ücretsiz, API anahtarı gerekmez):
- OECD Data Explorer, Consumer Price Indices (TUR, aylık, 2015 = 100)
- Frankfurter: Avrupa Merkez Bankası referans kurları
"""

import io
from pathlib import Path

import pandas as pd
import requests

VERI = Path(__file__).resolve().parent.parent / "veri"
OECD_URL = ("https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0/"
            "TUR.M.N.CPI.IX._T.N._Z?startPeriod=2003-01&format=csvfile")
KUR_URL = "https://api.frankfurter.dev/v1/2003-01-01..2025-12-31?from=USD&to=TRY"


def tufe_cek() -> pd.Series:
    d = pd.read_csv(io.StringIO(requests.get(OECD_URL, timeout=60).text))
    s = d.set_index(pd.PeriodIndex(d.TIME_PERIOD, freq="M")).OBS_VALUE.sort_index()
    return s.rename("tufe")


def kur_cek() -> pd.Series:
    oranlar = requests.get(KUR_URL, timeout=60).json()["rates"]
    gunluk = pd.Series({pd.Timestamp(t): v["TRY"] for t, v in oranlar.items()}).sort_index()
    return gunluk.groupby(gunluk.index.to_period("M")).mean().rename("usdtry")


def yukle(yenile: bool = False) -> pd.DataFrame:
    """Aylık TÜFE endeksi ve USD/TRY ortalaması; dönem indeksli tek tablo."""
    dosya = VERI / "aylik.csv"
    if yenile or not dosya.exists():
        VERI.mkdir(exist_ok=True)
        pd.concat([tufe_cek(), kur_cek()], axis=1).loc["2003-01":"2025-12"].round(4).to_csv(dosya, index_label="donem")
    d = pd.read_csv(dosya, index_col="donem")
    d.index = pd.PeriodIndex(d.index, freq="M")
    return d


if __name__ == "__main__":
    print(yukle(yenile=True).tail())
